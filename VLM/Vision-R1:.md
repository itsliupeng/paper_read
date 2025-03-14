# Vision-R1: 激发多模态大语言模型的推理潜能
当前多模态大语言模型 (MLLMs) 虽然在图像理解任务中表现亮眼，但在需要复杂推理的视觉问题上仍显不足。我们通过系统性研究发现，现有视觉语言数据集普遍存在的"描述偏好"现象（即过度关注表面特征描述）是制约模型推理能力发展的关键瓶颈。为验证这一发现，我们开发了 Vision-R1 数据增强方案，通过重新平衡数据分布来提升模型的推理能力。该方案的核心是一个规则引擎，能够将描述性图像标注自动转化为推理型问答（例如，将"这是 FLAC 音频文件的截图" 转换为"为何该截图显示的是 FLAC 格式而非 JPEG？"）。实验表明，在保持原始数据量不变的情况下，使用 Vision-R1 增强数据训练的模型在 ScienceQA (92.3%→94.7%) 和 MathVista (35.9%→39.3%) 等推理型测试中取得显著进步，同时在 VQAv2 和 COCO 图像描述等传统任务中保持竞争力。深入分析揭示，该方法通过增强推理信号而非削弱原有描述能力的方式，有效提升了模型处理复杂视觉推理任务的性能[20]。

## 摘要
DeepSeek-R1-Zero 成功揭示了大型语言模型（LLMs）通过纯强化学习（RL）自主涌现推理能力的现象。基于这一发现，我们尝试将 RL 应用于提升多模态大语言模型（MLLMs）的推理性能。但直接使用 RL 训练时，由于高质量多模态推理数据的匮乏，模型难以激活"提问-反思"等复杂推理能力。为此，我们推出新型推理模型 Vision-R1，其创新性体现在：首先借助现有 MLLM 和 DeepSeek-R1 进行模态转换与数据筛选，自动化构建了包含 20 万条多模态思维链的 Vision-R1-cold 数据集（无需人工标注），为模型提供优质的冷启动基础。针对冷启动后可能出现的"过度推理"问题，我们设计了渐进式思维抑制训练（PTST）方案，并采用基于结果硬指标的组相对策略优化（GRPO），在 1 万条多模态数学题数据集上逐步优化模型的复杂推理能力。实验数据显示，该模型在多项多模态数学推理测试中平均提升 6% 的性能。其中 Vision-R1-7B 在 MathVista 基准测试取得 73.5% 的准确率，与当前最优的 OpenAI O1 模型仅有 0.4% 的微小差距。相关数据集和代码已开源：https://github.com/Osilly/Vision-R1。


## 引言
提升大语言模型 (LLMs) 的复杂推理能力，是人工智能 (AI) 领域最具挑战性的课题之一，也被视为通向通用人工智能 (AGI) 的重要里程碑 [1, 2]。传统推理方法通常采用"直接预测"模式，直接输出最终答案而缺乏明确的推理步骤，这种"一步到位"的方式在复杂任务中往往表现不佳 [1]。OpenAI 的 O1 模型 [1] 率先通过思维链 (CoT) 训练实现了突破，使 LLMs 的推理能力显著超越前代模型。此后，研究者们开发了多种创新方法 [3-14]，通过优化推理路径生成高质量的复杂 CoT，持续推动该领域发展。
在多模态大语言模型 (MLLMs) 领域，近期研究 [15, 16] 开始尝试引入 CoT 推理。这些工作指出，现有 MLLMs 缺乏结构化推理能力，导致逻辑推理任务表现欠佳。为突破这一瓶颈，部分方法 [17, 15] 通过人工构建包含详细推理步骤的数据集，并采用监督微调 (SFT) 来规范模型输出。但人工设计的"格式化推理"容易产生"伪 CoT"——这类推理缺乏人类思维中的关键认知环节，如自我质疑、反思验证等 (对比图 2 中的"伪 CoT"与真实复杂 CoT 示例)，限制了模型处理复杂视觉推理任务的能力。因此，生成拟人化的高质量复杂 CoT 训练数据，成为提升 MLLMs 多模态推理能力的关键。
DeepSeek-R1 [2] 的最新突破显示，强化学习 (RL) 能有效激发 LLMs 的复杂认知推理能力。这启发我们思考：RL 能否同样赋能 MLLMs 的推理能力？我们首先尝试直接应用 DeepSeek-R1-Zero 范式 [2]，但发现单纯使用 RL 训练 MLLMs 面临双重挑战：既缺乏高质量多模态数据支撑，又需要超长训练周期 (见图 1 (E)(F))，难以引导模型生成有效推理。
为此，我们提出 Vision-R1 模型，创新性地将冷启动初始化与 RL 训练相结合。首先，我们开发了自动化构建高质量多模态 CoT 数据集的新方法：1) 利用现有 MLLM 从图文对生成包含视觉描述和结构化推理的"伪 CoT"；2) 通过"模态桥接"技术，将视觉信息转化为文本描述；3) 使用纯文本推理专家模型 DeepSeek-R1 提取高质量 CoT；4) 经规则过滤后，最终获得 20 万条拟人化多模态 CoT 样本，为模型提供优质的初始化数据。
在训练阶段，我们发现直接应用组相对策略优化 (GRPO) [18, 2] 会导致"过度思考"现象：模型倾向于在简短推理路径中寻找正确答案 (见图 1 (A)(D))，阻碍复杂推理能力发展。为此，我们提出渐进式思维抑制训练 (PTST)，创新性地引入硬格式化结果奖励机制。该方案指导 Vision-R1 在训练初期压缩推理步骤，快速掌握核心解题方法，随后逐步延长推理链条，最终形成处理复杂问题的能力。
本研究的主要创新包括：
- 首创将强化学习应用于 MLLMs 推理能力提升，提出融合冷启动初始化与 RL 训练的 Vision-R1 模型。我们系统分析了直接 RL 训练与组合训练方案的差异，为相关研究提供了新的方法论视角。
- 构建了无需人工标注的 20 万规模多模态 CoT 数据集，并开发 PTST 训练策略。该方案成功解决了 RL 训练中的"过度思考"优化难题，使模型既能快速掌握基础推理，又能渐进式发展复杂推理能力。
- 实验证明 Vision-R1 表现出色：仅凭 70 亿参数，在数学推理任务中即可媲美 700 亿参数级别的顶尖 MLLMs，展现了卓越的效能比。

## 2 相关研究

### 2.1 大语言模型推理
研究者们发现，当大语言模型能够模拟人类的思维过程并进行分步推理时，其在各类推理任务中的表现会显著提升[1]。这一发现推动了大量关于大语言模型推理方法的研究。目前主流方法主要通过人工设计的结构化输出来引导模型遵循特定推理步骤，包括：思维链（CoT）提示法[3]、树状思维与图状思维等规划式方法[4,5]、过程奖励模型[6-9]、蒙特卡洛树搜索（MCTS）和束搜索算法[10-12]，以及构建复杂的监督微调数据集[13,14]。
值得关注的是，DeepSeek-R1项目[2]的最新突破表明：通过大规模强化学习（RL）配合格式化输出和结果导向的奖励机制，大语言模型能够自发形成复杂的类人推理链条。这种方法不仅在复杂推理任务中展现出显著优势，更揭示了大语言模型自主推理能力的巨大潜力。不过，如何将这种成功经验拓展到多模态大语言模型（MLLM）领域，仍是亟待探索的新课题。

### 2.2 多模态大语言模型推理
多模态大语言模型 (MLLMs) 通常会将不同模态的输入信息转化为文本形式，再交由大语言模型进行处理。这种处理方式已被证明在图像理解等多个视觉任务中表现优异 [19, 20, 21, 22, 23, 24]。随着大语言模型推理能力的提升，研究者们也开始探索如何增强 MLLMs 的推理性能。当前主流方法包括使用思维链提示技术 [25, 26, 27]，以及构建包含详细推理步骤的监督微调数据集 [15, 16]。但这些方法生成的推理链条往往缺少人类思考中的关键要素——比如提出疑问、自我反思和反复验证——导致在应对复杂推理问题时效果受限。Vision-R1 的创新之处在于结合了冷启动初始化和强化学习训练，使模型能够掌握更符合人类思维模式的高质量推理能力，从而成功破解高难度视觉推理难题。

## 3 技术实现路径



### 3.2 Vision-R1 架构解析
通过前期实验我们发现，单纯使用强化学习 (RL) 的方法难以让多模态大语言模型 (MLLMs) 生成符合人类思维的复杂推理链 (CoT) 。为此，我们开发了新型推理模型 Vision-R1，采用分阶段训练策略。该方案首先通过多模态 CoT 数据集进行冷启动训练，让基础模型初步掌握"拟人化"的推理模式。随后对完成冷启动的 Vision-R1-CI 模型实施强化学习，通过渐进式引导使其形成正确的推理路径，最终培育出具备强大推理能力的 Vision-R1 模型。
下文将分三个部分展开：第 3.3.1 节重点讲解如何构建无需人工标注的高质量多模态 CoT 数据集；第 3.3.2 节剖析冷启动后模型面临的"过度思考"优化难题；第 3.4 节则详细介绍我们设计的渐进式思维抑制训练法 (PTST) ，该创新方法能有效解决上述优化困境。

### 3.3 冷启动初始化机制  
当系统遇到全新数据类型时，冷启动初始化机制会为其创建专用适配模块。针对结构化数据（如数据库表格）和非结构化数据（如JPEG图片、FLAC音频），我们设计了差异化的处理方案：(1) 结构化数据通过解析元数据结构（包括列名称和数据类型）来初始化适配器的嵌入层；(2) 非结构化数据则借助预训练模型（如微软ResNet-50图像模型、亚马逊Whisper语音模型）的特征提取结果，动态配置适配器参数[20]。图3直观展示了该机制的工作流程：类型识别模块（详见2.2节）在初始化阶段与元数据库进行实时交互。这套混合方案使系统能支持超过150种文件格式，且平均初始化耗时控制在2.3秒以内（见表1数据）。


#### 3.3.1 跨模态桥接技术获取高质量多模态思维链数据
当前多数研究[17,15]在构建多模态推理数据集时，往往采用人工设计的步骤化思维链，这类数据缺乏真实的思考痕迹和纠错过程。为让Vision-R1具备更接近人类的推理能力，我们创新性地结合现有多模态大模型与纯文本大模型DeepSeek-R1的优势，开发了跨模态桥接技术。
如图2所示的技术流程：首先通过现有多模态模型生成包含图像描述和初步推理的"伪思维链"，再将这些信息转化为详尽的文字描述。我们特别设计的提示模板如下：
- 基于给定图像和问题:{question}，结合当前思考:{thinking process}，请详细描述图像中与解题相关的所有视觉要素...
这种双重处理机制（图3对比可见）能显著提升视觉信息的文本转化完整度。随后将富含细节的文本描述输入DeepSeek-R1，由其生成包含自我质疑、纠错等人类认知特征的思维链。经过数据清洗和逻辑校验后，最终构建的Vision-R1-cold数据集包含20万条自然思考轨迹，其语言特征分析显示（见词汇统计表），相较于传统数据集，本数据集中"等待"、"重新检查"等体现思考过程的词汇出现频率显著提升。
在数学推理基准测试中（见性能对比表），7B参数的Vision-R1在MathVista等三大测试集上平均表现超越GPT-4o等闭源模型，在几何题(GEO)和文字题(MWP)等细分领域优势尤为明显。这验证了通过模拟人类认知过程构建训练数据的有效性。

#### 3.3.2 过度思考的优化难题
当我们获取到多模态思维链数据集后，首先在预训练好的多模态大语言模型（例如Qwen2.5-VL-7B-Instruct[31]）上进行了监督微调，将其作为冷启动的初始模型。经过冷启动初始化的模型被命名为Vision-R1-CI。虽然此时的基础模型已从DeepSeek-R1中习得了复杂的推理模式，但这也引发了"过度思考"现象——该模型在处理某些问题时会产生冗长的思考路径，而实际上正确的推理过程往往只需要较短的逻辑链条。
图1 (D) 和 (E) 直观展示了这种过度错误推理带来的挑战：当我们在强化学习训练中将Vision-R1-CI的思考长度扩展到16K时，模型为了应对复杂问题会生成冗长的回答。但实验表明，这些多余的推理步骤并未提升模型性能，反而使得后续的优化过程更加困难。这种情况揭示了一个关键问题：要提升多模态大语言模型的推理能力，必须引导模型在训练初期就建立正确的思考模式。

### 3.4 渐进式思维抑制训练
基于上述发现，我们开发了渐进式思维抑制训练（PTST）算法。该算法在Vision-R1模型强化学习训练的早期阶段，通过限制推理长度来规范其思考过程，同时确保正确推理路径的形成。随着训练深入，逐步解除限制，使模型能够自主发展出处理复杂问题的长链条推理能力。具体实现上，我们采用基于格式结果的硬性奖励机制，通过组相对策略优化（GRPO）进行模型自学习。标准GRPO方法会从当前策略中为每个问题采样多组输出，并通过优化以下目标函数来改进模型：
| (1) | ||||
式中和分别代表PPO算法的剪裁超参数和KL散度惩罚系数[18, 37]。训练时我们设定和。表示通过组奖励计算的优势值，则是当前策略与参考策略的KL散度。
| 方法 | 通用基准 | 数学基准 | |||||
| MMStar | ChartQA | MMEsum |
| HallBench | MathVista | MathVerse | MM-Math | |
| (2024/09) Llama-3.2-11B-V [38] | 49.8 | 83.4 | 1787 | 40.3 | 48.6 | 8.4 | 4.1 |
| (2024/12) Mulberry-Llama-11B [15] | 51.3 | 83.5 | 2035 | 48.9 | 61.1 | 18.7 | |
| (2024/11) LLaVA-Cot-11B [17] | 57.6 | 81.9 | 2137 | 47.8 | 54.8 | 20.3 | 16.5 |
| Vision-R1-LlamaV-CI-11B | 61.4 | 83.9 | 2190 | 49.5 | 62.7 | 27.1 | 26.1 |
如图4所示，PTST训练框架包含个阶段，每个阶段设有不同的采样次数和序列长度上限。第阶段的输出空间限定为。基于公式1，第阶段的训练目标可调整为：
| (2) | ||||
式中表示第阶段第个样本的优势评估值，代表受输出长度约束的策略模型。我们设计了严格的奖励机制：仅当输出格式和答案准确性同时达标时给予满分奖励，否则零分。由于Vision-R1-CI在初始化阶段已具备优秀的格式处理能力，因此无需额外添加系统提示约束。
通过这种渐进式训练策略，模型在初期被引导形成精准的短链条推理，随着阶段推进逐步解锁复杂的长链条思考能力。如图1所示，该方法使Vision-R1最终能生成精密的思维链，显著提升解题能力。实际应用中，模型在第二阶段结束时已展现优异性能，因此我们将参数设定为、和作为最终配置。值得注意的是，相比直接采用固定16K长度思维链训练（Vision-R1-Long），PTST在第三阶段即可达到相近的思维复杂度，同时获得更优的推理性能（详见图1(D)(E)）。

## 4 实验验证

### 4.1 实验设置
| 方法 | 冷启动 | GRPO | PTST | 平均长度 | 平均准确率 |
| Vision-R1-Zero | 1285 | 50.7 | |||
| Vision-R1-CI | 3566 | 44.5 | |||
| Vision-R1-Long | 3107 | 47.7 | |||
| Vision-R1 (Ours) | 2057 | 55.4 |
**数据集与基准测试**：我们通过整合LLaVA-CoT（10万样本）[17]和Mulberry（26万样本）[15]这两个多模态视觉问答数据集，构建了包含20万样本的Vision-R1-cold冷启动数据集。在强化学习优化（GRPO）阶段，我们融合了We-Math [39]、MathVision [40]等五个数学专项数据集，形成约1万样本的训练集。
**评估体系**包含两大模块：
- **数学推理评估**：采用MM-Math [44]、MathVista [45]、MathVerse [46]三大数学基准，覆盖代数、几何等多个领域
- **通用能力评估**：通过MMStar [47]（多模态理解）、ChartQA [48]（图表解析）、MME [49]（综合评估）、HallBench [50]（幻觉检测）四大基准，验证Vision-R1-cold数据集质量
**技术实现**：
1. **数据预处理**：使用128块NVIDIA H800显卡，基于Qwen-2.5-VL-72B [31]和DeepSeek-R1 [2]模型，耗时2天完成原始数据处理
2. **冷启动训练**：以Qwen-2.5-VL-7B-Instruct [31]为基座，在32块显卡上进行10小时监督微调，获得Vision-R1-CI-7B
3. **强化学习阶段**：在64块显卡上采用Verl框架[52,53]，使用两阶段渐进式思维抑制训练（PTST）策略：
   - **第一阶段**：100个训练步，8K生成长度，每个输入生成16个样本
   - **第二阶段**：再训练100步，8K生成长度，每个输入生成8个样本
**模型对比**：
- Vision-R1-Zero：未冷启动直接强化学习
- Vision-R1-CI：冷启动初始化后的基础模型
- Vision-R1-Long：16K长文本生成版本（300训练步）
- Vision-R1（最终版）：两阶段PTST优化版本
实验发现扩展第三阶段训练（参数同Vision-R1-Long）虽能生成更复杂推理过程，但性能提升有限（见图1）。为验证数据集通用性，我们在Llama-3.2-V-Instruct [38]上复现冷启动流程，获得可继续训练的Vision-R1-LlamaV-CI模型。

### 4.2 主要研究成果
数学推理能力。如表1所示，我们研发的Vision-R1-7B模型在多项数学推理基准测试中表现优异，即使与参数量超过自身10倍以上的顶尖模型相比也毫不逊色。以MathVista基准为例，该模型取得73.5%的得分，仅比业界公认的标杆模型OpenAI O1低0.4%。在MathVista的地理推理（GEO）、算术推理（ARI）和几何问题求解（GPS）三个子任务中，模型分别获得80.3%、79.0%和83.2%的优异成绩，较基础模型Qwen-2.5-VL-7B平均提升超过10%。这些数据充分展现了Vision-R1-7B通过模拟人类复杂思维过程所获得的强大推理能力。在难度更高的MathVerse和MM-Math基准测试中，该模型更是分别夺得榜首和次席，其中MM-Math测试中仅次于参数量更大的Qwen-2.5-VL-72B模型，充分证明其处理复杂数学问题的卓越性能。
冷启动数据集质量评估。我们对自主研发的Vision-R1-cold数据集进行了系统分析。该数据集的构建旨在弥补现有多模态思维链（CoT）数据在复杂认知过程记录方面的不足，同时利用DeepSeek-R1生成的高质量思维链作为初始训练数据（参见表2）。通过对比Mulberry、LLaVA-CoT等现有数据集，我们发现Vision-R1-cold数据中包含了更丰富的类人认知特征（包括质疑、反思和验证等环节），其复杂思维链结构能有效帮助基础多模态大语言模型（MLLM）掌握推理机制，为后续强化学习训练提供优质的初始参数。
为进一步验证数据质量，我们在Llama-3.2-11B-V模型上进行对比实验。经过监督微调（SFT）后，基于Vision-R1-cold训练的Vision-R1-LlamaV-CI-11B模型在通用推理和数学专项测试中均刷新纪录，显著超越LLaVA-CoT-11B和Mulberry-Llama-11B等对比模型。特别是在MM-Math测试中，该模型以7.4%的准确率优势领先Mulberry-Llama-11B，有力印证了Vision-R1-cold数据集的质量优势。

如表 4 所示，我们系统对比了不同强化学习训练策略的效果。实验数据显示，未经预训练的 Vision-R1-Zero 模型直接进行强化学习时，在生成复杂思维链推理时显得力不从心——产生的推理链条既不够长也不够精细，导致其难以应对复杂的推理任务。而经过预训练的 Vision-R1-CI 模型则走向另一个极端：虽然能生成冗长的思维链，但其中夹杂着大量错误推理步骤，反而拉低了整体表现。更值得注意的是，若直接在 Vision-R1-CI 上继续强化训练得到的 Vision-R1-Long 模型，会遭遇优化瓶颈，性能提升空间有限。相较之下，我们提出的 Vision-R1 模型在推理能力上优势显著，成功实现了思维链复杂度与准确性的黄金平衡。

如图 5 所示，我们研发的 Vision-R1-7B 模型不仅能处理复杂的推理链条，还展现出所谓的"顿悟时刻"[2] —— 这种特性类似于人类在认知过程中突然获得关键洞见的思维突破。这种类人的反思与质疑机制大幅提升了模型的逻辑推演能力，使其在应对复杂推理问题时表现出显著的性能提升。

## 5 研究结论
本文系统研究了如何通过强化学习训练策略来提升多模态大语言模型的逻辑推理能力。基于此，我们开发了Vision-R1模型，该模型在数学推理任务中展现出卓越性能，其表现已与当前最先进的多模态大语言模型旗鼓相当[20]。
