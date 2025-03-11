


import argparse
from trafilatura import fetch_url, extract
import openai

# 初始化本地部署的AI翻译客户端
client = openai.Client(base_url="http://10.65.249.237:30000/v1", api_key="EMPTY")
    
# TRANSLATE_PROMPT = r"""
# 请将以下 markdown 文档内容从英文精确翻译为简体中文, 保留 markdown 格式，对于错乱的格式直接丢弃
# """


TRANSLATE_PROMPT = r"""
请严格按照以下要求将英文学术论文的markdown内容翻译为中文：

**翻译要求**
1. **精准性**
   - 保留所有技术术语（如mAP、FPS、ResNet等）不翻译
   - 保持数学公式/方程完全不变（包括LaTeX格式）
   - 严格保留原文中的引用标记（如[1][2][3]）

2. **格式保留**
   - Table（表格）：完整保留表格结构和英文内容
   - Figure（图片）：保留"![Alt text]"格式的图片声明
   - Algorithm（算法）：保持伪代码结构和英文术语
   - Reference（参考文献）：完整保留该章节，包括编号和英文条目

3. **格式修复**
   - 自动纠正以下问题：
     * 不规范的标题层级（确保#号与标题间有空格）
     * 修复断裂的列表符号（修正错误的列表缩进）
     * 统一代码块声明（确保```前后空行）
   - 无法修复的复杂格式问题直接删除而非保留错误

4. **翻译质量**
   - 实现三级质量标准：
     1. 信：完整传达原文语义（无信息丢失/添加）
     2. 达：确保中文表述符合学术规范（使用专业领域惯用表达）
     3. 雅：优化句式结构（消除翻译腔，保持学术严谨性）

**处理流程**
1. 分段解析原始markdown结构
2. 选择性翻译文本段落（跳过表格/算法/公式等指定内容）
3. 执行格式验证和自动修正
4. 最终结果质量检查（格式完整性+翻译准确性）
5. 最后只将完整翻译的内容放入{{}}内，方便下一步提取
"""

from concurrent.futures import ThreadPoolExecutor
import re

def split_markdown_by_headings(md_content):
    """按标题层级拆分markdown文档为更细粒度的段落"""
    # 匹配任意层级的标题，并智能分割内容
    pattern = r'(^#{1,6} .+?)(?=^#{1,6} |\Z)'
    sections = []
    
    # 先按顶级标题分割
    top_level = re.findall(pattern, md_content, flags=re.MULTILINE|re.DOTALL)
    
    for section in top_level:
        # 对每个顶级标题下的内容进行二次分割
        sub_sections = re.split(r'\n(?=#{2,6} )', section)
        for sub in sub_sections:
            # 对二级标题下的内容进行三次分割（如果有三级标题）
            sub_sub = re.split(r'\n(?=#{3,6} )', sub)
            sections.extend(sub_sub)
    
    # 过滤空段落并标准化空白
    return [s.strip() for s in sections if s.strip()]

def translate_section(section):
    """翻译单个markdown段落"""
    try:
        response = client.chat.completions.create(
            model="default",
            messages=[
                {"role": "system", "content": TRANSLATE_PROMPT},
                {"role": "user", "content": section},
            ],
            temperature=0.5,
            max_tokens=128000,
        )
        trans_tex = response.choices[0].message.content
        if "</think>" in trans_tex:
            trans_tex = trans_tex.split('</think>')[-1]
        return trans_tex.strip()
    except Exception as e:
        print(f"⚠️ 翻译失败: {str(e)}")
        return section  # 返回原文作为降级处理

def translate_tex(tex):
    """并发翻译markdown内容"""
    sections = split_markdown_by_headings(tex)
    print(f"🔀 拆分出 {len(sections)} 个章节进行并发翻译...")
    max_workers = max(len(sections), 100)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = executor.map(translate_section, sections)
    
    # 合并翻译结果并保留原始空白行结构
    return '\n\n'.join(futures)

def main():
    parser = argparse.ArgumentParser(
        description='将arXiv论文转换为中文Markdown',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='示例:\n  python gen_zh_md_from_arxiv_id.py 2502.20622v1'
    )
    parser.add_argument('arxiv_id', type=str, help='arXiv论文ID (例如: 2502.20622v1)')
    args = parser.parse_args()

    try:
        print(f"🔄 正在处理 arXiv 论文 {args.arxiv_id}...")
        
        # 通过arXiv HTML页面获取并提取Markdown内容
        url = f"https://arxiv.org/html/{args.arxiv_id}"
        print(f"🌐 下载页面内容: {url}")
        downloaded = fetch_url(url)
        
        if not downloaded:
            raise ValueError("无法获取页面内容，请检查arXiv ID是否正确")

        print("🔧 提取Markdown内容...")
        markdown = extract(
            downloaded,
            output_format="markdown",
            include_links=False,
            include_tables=True,
            no_fallback=True
        )

        # 保存原始Markdown
        en_filename = f"{args.arxiv_id}.md"
        with open(en_filename, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"✅ 原始Markdown已保存至: {en_filename}")

        # 翻译并保存中文版
        print("🈵 翻译内容至中文...")
        zh_markdown = translate_tex(markdown)
        
        zh_filename = f"{args.arxiv_id}_zh.md"
        with open(zh_filename, "w", encoding="utf-8") as f:
            f.write(zh_markdown)
        print(f"✅ 中文Markdown已保存至: {zh_filename}")

    except Exception as e:
        print(f"❌ 处理过程中发生错误: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
