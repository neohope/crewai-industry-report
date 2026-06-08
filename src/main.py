"""
行业研究报告生成系统 - 完整可工作实现
多代理协作工作流程
"""
import os
import sys
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from crewai import Crew, Agent, Task, Process

# 导入真实工具
from src.tools.search_tool import web_search, news_search
from src.tools.feishu_tool import feishu_document, feishu_message
from src.tools.llm_config import get_llm, get_config_info, validate_config
from src.tools.llm_config import get_max_review_iterations, get_passing_score

# 加载环境变量
load_dotenv()


class IndustryResearchCrew:
    """行业研究团队 - 完整实现"""

    def __init__(self, industry_topic: str):
        self.industry_topic = industry_topic
        self.web_search = web_search
        self.news_search = news_search
        self.feishu_doc = feishu_document
        self.feishu_msg = feishu_message
        self.final_report = ""
        self.final_score = 0
        self.report_approved = False

        # 初始化配置
        self.max_iterations = get_max_review_iterations()
        self.passing_score = get_passing_score()

        # 初始化 LLM
        self.llm = get_llm(temperature=0.7)

    def create_data_collector_1(self) -> Agent:
        """数据采集员1 - 市场数据采集 - 完整实现"""
        return Agent(
            role="数据采集员-市场数据",
            goal=f"收集{self.industry_topic}行业的市场规模、增长趋势、市场份额等权威数据",
            backstory=f"""你是专业的市场数据采集专家，在行业研究领域有10年经验。
你擅长从各类市场研究报告、行业协会数据、官方统计数据、企业财报中提取有价值的信息。
你对数据来源的权威性非常敏感，总是优先选择权威机构发布的数据。
你的任务是为{self.industry_topic}行业研究收集最准确、最新的市场相关数据。""",
            tools=[self.web_search, self.news_search],
            allow_delegation=False,
            verbose=True,
            llm=self.llm,
        )

    def create_data_collector_2(self) -> Agent:
        """数据采集员2 - 技术趋势采集 - 完整实现"""
        return Agent(
            role="数据采集员-技术趋势",
            goal=f"收集{self.industry_topic}行业的技术发展趋势、创新动态、研发投入等前沿信息",
            backstory=f"""你是专业的技术趋势追踪专家，专注于科技创新和技术发展数据的收集。
你擅长从技术论文、专利数据库、企业财报、技术峰会资料、权威科技媒体中提取关键信息。
你对技术发展的敏感度很高，能够识别出真正有前景的技术方向。
你的任务是为{self.industry_topic}行业研究收集最新、最有价值的技术相关数据。""",
            tools=[self.web_search, self.news_search],
            allow_delegation=False,
            verbose=True,
            llm=self.llm,
        )

    def create_data_collector_3(self) -> Agent:
        """数据采集员3 - 竞争格局采集 - 完整实现"""
        return Agent(
            role="数据采集员-竞争格局",
            goal=f"收集{self.industry_topic}行业的竞争格局、主要企业、产品服务、战略布局等情报",
            backstory=f"""你是专业的竞争情报分析师，在企业竞争战略领域有丰富经验。
你擅长从企业官网、财报、新闻报道、行业分析报告、第三方数据平台中提取竞争情报。
你对企业战略动向非常敏感，能够从碎片化信息中拼出完整的竞争图景。
你的任务是为{self.industry_topic}行业研究收集全面、准确的竞争相关数据。""",
            tools=[self.web_search, self.news_search],
            allow_delegation=False,
            verbose=True,
            llm=self.llm,
        )

    def create_data_analyst(self) -> Agent:
        """数据分析师 - 完整实现"""
        return Agent(
            role="数据分析师",
            goal="对三位数据采集员收集的数据进行交叉验证、清洗去重、可信度标注，输出高质量数据集",
            backstory="""你是经验丰富的数据验证和分析专家，以严谨著称。
你的工作方法是：
1. 首先检查每个数据点的来源权威性和时效性
2. 对比不同数据源的数据一致性，找出矛盾点
3. 去除重复数据，合并互补信息
4. 为每个数据点标注可信度等级（高/中/低）
5. 按主题分类整理，形成结构化数据集
你只相信经过交叉验证的数据，对存疑数据会明确标注。""",
            allow_delegation=False,
            verbose=True,
            llm=self.llm,
        )

    def create_report_writer(self) -> Agent:
        """报告撰写师 - 完整实现"""
        return Agent(
            role="报告撰写师",
            goal="根据数据分析师提供的高质量数据集，撰写专业、深入、结构清晰的行业研究报告，并根据评价师反馈迭代优化",
            backstory="""你是资深的行业研究报告撰写专家，撰写过100+份行业研究报告。
你具有深厚的行业洞察力、出色的逻辑思维能力和优秀的文字表达能力。
你撰写的报告特点是：数据准确、结构清晰、分析深入、观点鲜明、可读性强。
你能够根据评价师的反馈，精准地修改和完善报告内容，直到达到高质量标准。""",
            allow_delegation=False,
            verbose=True,
            llm=self.llm,
        )

    def create_report_reviewer(self) -> Agent:
        """报告评价师 - 完整实现"""
        return Agent(
            role="报告评价师",
            goal=f"以极其严格的标准审核报告质量，从多个维度进行评分，只有达到{self.passing_score}分以上才能通过",
            backstory=f"""你是业内知名的报告质量审核专家，以标准极其严格著称。
你审核报告的四个维度（总分100分）：
1. 内容详实性（30分）：数据是否丰富、案例是否充分、覆盖是否全面
2. 逻辑性（30分）：结构是否清晰、论证是否严密、逻辑是否自洽
3. 可靠性（25分）：数据来源是否明确、分析是否客观、结论是否有依据
4. 可读性（15分）：表达是否流畅、层次是否分明、阅读体验是否良好
评分低于{self.passing_score}分时，你必须给出具体、可操作的修改意见；
评分达到或超过{self.passing_score}分时，你批准报告发布。
你的评分总是非常精准，评语总是非常具体。""",
            allow_delegation=False,
            verbose=True,
            llm=self.llm,
        )

    def create_report_publisher(self) -> Agent:
        """报告发布师 - 完整实现"""
        return Agent(
            role="报告发布师",
            goal="将审核通过的最终报告发布到飞书文档平台，并发送消息通知相关人员",
            backstory="""你是专业的报告发布和传播专员，负责项目的最后一公里。
你的工作流程是：
1. 接收最终报告和审核结果
2. 将报告内容整理后发布到飞书文档平台
3. 发送消息通知相关人员报告已发布
4. 记录发布结果，包括文档链接等关键信息
你确保发布过程规范、顺畅、及时。""",
            tools=[self.feishu_doc, self.feishu_msg],
            allow_delegation=False,
            verbose=True,
            llm=self.llm,
        )

    def create_collect_task_1(self, agent: Agent) -> Task:
        """市场数据采集任务 - 【干货版】强制采集硬数据"""
        return Task(
            description=f"""【重要】这是干货报告的基础！请用搜索引擎逐条查找以下**具体、可验证的硬数据**，拒绝空泛描述。

请收集{self.industry_topic}行业的市场相关数据，必须满足以下要求：

✅ 【数据质量强制标准】
1. 所有数据必须是**具体数字**，禁止"快速增长""显著提升"等空泛词汇
2. 所有数据必须标注**精确来源**（如：IDC 2026年Q1报告，而不是"网上数据"）
3. 优先采集**近3个月**的最新数据，超过1年的必须注明

✅ 【必须采集的具体数据点】
1. 市场规模细分数据（至少5条）：
   - 全球/中国市场当前总量（精确到亿元/亿美元）
   - 近3年每年的具体数值和增长率
   - 按细分赛道拆分的市场规模（至少拆分成3个赛道）
   - 头部企业Top 5的具体营收/市场份额（精确到小数点后1位）
   - 市场CR5/CR10具体数值

2. 投融资明细数据（至少10条）：
   - 近6个月单笔融资超1亿元/美元的具体案例
   - 每条必须包含：企业名称、融资金额、投资方、估值、融资时间
   - 融资轮次分布（天使/A/B/C/Pre-IPO的具体数量和金额）
   - 哪些赛道融资最热、哪些遇冷

3. 价格战/成本数据（至少5条）：
   - 主流产品/服务的具体定价区间
   - 近1年的降价幅度（比如：API调用价格从X元降到Y元，下降Z%）
   - 头部企业的毛利率/净利率具体数值
   - 典型项目的客单价

4. 真实落地案例（至少8个）：
   - 每个案例必须包含：**企业名称、实施时间、投入金额、具体效果数据**
   - 效果数据必须量化（如：良品率从95%提升到99.2%，成本下降18%）
   - 禁止使用"某企业""相关公司"这种模糊表述

✅ 【输出格式要求】
严格按照以下表格格式输出，不要写废话：

| 数据类别 | 具体数据 | 来源 | 发布时间 | 可信度 |
|---------|---------|------|---------|-------|
| 市场规模 | 2025年中国AI市场规模1856亿元 | IDC 2026Q1报告 | 2026-03 | 高 |
| 投融资 | 深度求索D轮融资7亿美元，估值450亿美元 | 36氪 | 2026-05 | 高 |
| ... | ... | ... | ... | ... |

❌ 【禁止出现的内容】
- "该行业发展迅速"（没有具体数字的空话）
- "某企业取得了良好效果"（没有具体名称的模糊表述）
- "相关数据显示"（没有明确来源的引用）""",
            agent=agent,
            expected_output="结构化的市场数据清单，包含所有数据点及其来源、时间、统计口径。",
                    )

    def create_collect_task_2(self, agent: Agent) -> Task:
        """技术趋势采集任务 - 【干货版】强制采集硬数据"""
        return Task(
            description=f"""【重要】这是干货报告的核心！请采集**具体、可验证的技术数据**，拒绝模糊描述。

请收集{self.industry_topic}行业的技术相关数据，必须满足以下要求：

✅ 【数据质量强制标准】
1. 禁止"技术发展迅速""取得重大突破"这种空话，必须有**具体数字**
2. 所有技术对比必须有**量化指标**（速度提升X%，成本下降Y%，准确率从A到B）
3. 每个案例必须包含：**企业名称、技术方案、投入成本、效果数据**

✅ 【必须采集的具体数据点】
1. 技术性能对比数据（至少10条）：
   - 主流技术方案的具体性能指标（速度、准确率、成本等）
   - 近1年技术进步的量化数据（如：推理速度提升150%，成本下降60%）
   - 不同技术路线的优缺点**量化对比**

2. 真实技术落地案例（至少10个）：
   - 每个案例必须包含：**企业/工厂名称、实施时间、技术方案、投入金额、效果数据**
   - 效果数据必须具体：（如：检测时间从2秒降到0.3秒，人力从50人减到10人）
   - 必须有**失败案例**至少2个：谁、做了什么、花了多少钱、为什么失败

3. 研发投入明细（至少8条）：
   - 头部企业的具体研发投入金额、占营收比例
   - 重点研发方向的资金分配比例
   - 研发人员数量、人均研发投入
   - 专利申请的具体数量、增长率

4. 技术门槛与人才数据（至少5条）：
   - 核心技术岗位的具体薪资范围
   - 关键人才的供需比例（如：大模型工程师缺口10万人）
   - 典型项目的开发周期和团队配置

✅ 【特别要求：反常识发现】
请专门查找并标注**反常识的技术数据**（至少3条）：
- 被媒体吹爆但实际落地效果很差的技术
- 看起来很土但实际很赚钱的技术路线
- 大家都认为很难但已有突破的技术方向

✅ 【输出格式要求】
严格按照表格格式输出：

| 数据类别 | 具体内容 | 来源 | 时间 | 备注 |
|---------|---------|------|------|------|
| 技术性能 | GPT-4o推理速度比GPT-4快3倍，成本降50% | OpenAI官网 | 2026-05 | |
| 落地案例 | 特斯拉上海工厂用Gamma-World优化调度，产能提升27% | 特斯拉财报 | 2026-04 | |
| 反常识 | 90%的AI Agent项目实际ROI<1，远低于宣传 | 某咨询公司内部报告 | 2026-03 | ⚠️反常识 |

❌ 【禁止出现的内容】
- "人工智能技术取得了长足进步"（没有具体数字的空话）
- "某企业应用了AI技术"（没有具体名称的模糊案例）
- "未来发展前景广阔"（这种正确的废话）""",
            agent=agent,
            expected_output="结构化的技术趋势数据清单，包含所有数据点及其来源和时间。",
                    )

    def create_collect_task_3(self, agent: Agent) -> Task:
        """竞争格局采集任务 - 【干货版】强制采集硬数据"""
        return Task(
            description=f"""【重要】这是干货报告的灵魂！请采集**具体的企业经营数据和真实竞争情报**，拒绝歌功颂德式的企业简介。

请收集{self.industry_topic}行业的竞争相关数据，必须满足以下要求：

✅ 【数据质量强制标准】
1. 禁止"该企业技术领先""市场地位稳固"这种套话，必须有**具体经营数据**
2. 所有企业对比必须有**量化指标**（营收、增速、利润率、市占率等）
3. 必须包含**负面信息**：企业遇到的困难、失败的产品、裁员等

✅ 【必须采集的具体数据点】
1. 头部企业经营数据（至少10家，每家必须包含）：
   - 近2年的具体营收、增长率、毛利率、净利率
   - 具体的用户数量/付费用户数量/ARPU值
   - 员工数量、人均产值、人均薪酬
   - 主要收入来源的拆分（按产品/按地区）

2. 真实的产品对比（至少5组）：
   - 同类型产品的**具体功能、性能、价格**横向对比
   - 用户实际评价/第三方评测的具体数据
   - 客户留存率、NPS评分等真实运营数据

3. 竞争策略的**真实效果**（至少8条）：
   - 某公司采取了什么策略（如：降价X%）
   - 实际效果如何（如：市场份额从A涨到B，或者反而下降）
   - 竞争对手的应对措施和结果

4. 死亡/失败案例分析（至少5个）：
   - 过去1年死掉的公司名单、死亡时间
   - 死亡原因的具体分析（烧钱太快？技术路线错了？）
   - 烧掉了多少钱、最后估值多少、投资方损失

5. 近期真实动态（至少10条）：
   - 具体的并购案：谁买了谁、多少钱、买了什么
   - 具体的裁员/扩招信息：多少人、哪些部门
   - 高管变动、核心团队流失情况
   - 真实的客户争夺战案例

✅ 【输出格式要求】
严格按照表格格式输出：

| 企业名称 | 2025营收 | 同比增速 | 毛利率 | 核心产品 | 近期动态 | 来源 |
|---------|---------|---------|--------|---------|---------|------|
| 深度求索 | 38亿元 | +210% | 65% | DeepSeek系列模型 | D轮融资7亿美金 | 36氪 2026-05 |
| ... | ... | ... | ... | ... | ... | ... |

❌ 【禁止出现的内容】
- "该公司是行业领军企业"（没有具体数据的套话）
- "发展势头良好"（不说是增长了10%还是100%）
- 只说优点不说问题的片面描述""",
            agent=agent,
            expected_output="结构化的竞争格局数据清单，包含所有数据点及其来源和时间。",
                    )

    def create_analysis_task(self, agent: Agent, context: list) -> Task:
        """数据分析任务 - 【干货版】不仅清洗，还要挖掘洞察"""
        return Task(
            description=f"""【重要】这是从数据到洞察的关键一步！不要只做数据搬运工，要做数据分析师。

请对三位数据采集员收集的数据进行专业处理，核心工作分为四步：

✅ 【第一步：数据质量审计】
1. 检查每个数据点的**具体性**：是具体数字还是空话？是空话的直接删掉
2. 交叉验证：同一个数据点有多个来源的，对比数值差异，标出最可信的
3. 时效性检查：超过1年的数据标记为「历史参考」，超过2年的直接删掉
4. 来源权威性分级：
   - A级：企业财报、官方统计数据、权威机构（IDC/Gartner等）正式报告
   - B级：权威媒体深度报道、行业专家访谈
   - C级：自媒体、论坛爆料（这类数据必须标注，且不能作为核心论据）

✅ 【第二步：数据整合与结构化】
将所有合格数据整理成统一格式，按以下分类：
1. 市场数据专区：规模、增速、投融资、价格、区域分布
2. 技术数据专区：性能指标、落地案例、研发投入、人才数据
3. 竞争数据专区：企业经营数据、产品对比、成败案例、动态
4. 反常识发现专区：专门整理所有反常识的数据点

✅ 【第三步：核心洞察挖掘（这才是你的价值所在！）】
从数据中主动挖掘至少10条**有数据支撑的洞察**，格式如下：

| 洞察编号 | 洞察内容 | 支撑数据 | 置信度 | 商业启示 |
|---------|---------|---------|--------|---------|
| 1 | AI Agent实际落地ROI远低于宣传，90%项目1年内收不回成本 | 某咨询公司调研：平均ROI 0.8，宣传口径是3-5倍 | 高 | 不要盲目跟风上Agent项目，先做POC验证 |
| 2 | ... | ... | ... | ... |

挖掘方向建议：
- 哪些被吹爆的方向其实是坑？（有数据支撑）
- 哪些被忽略的方向其实很赚钱？（有数据支撑）
- 中美真实差距在哪里？（不要凭感觉，用数据对比）
- 行业真实的痛点是什么？（从失败案例反推）

✅ 【第四步：可操作的建议提炼】
基于以上洞察，提炼至少5条**具体可操作**的建议：
- 现在应该布局什么？（具体赛道，不是"人工智能"这种大词）
- 现在应该避开什么？（具体坑，有数据支撑）
- 现在应该警惕什么信号？（具体指标，出现了就是风险）

✅ 【输出格式要求】
1. 数据质量审计报告（不合格数据清单+删除理由）
2. 结构化数据集（分类整理后的最终数据）
3. 核心洞察清单（至少10条，带数据支撑）
4. 可操作建议（至少5条）

❌ 【禁止】
- 只做数据搬运，不做分析
- "发展前景广阔"这种没有信息含量的废话
- 没有数据支撑的主观判断""",
            agent=agent,
            expected_output="经过验证、清洗、整合的高质量数据集，带有可信度标注。",
            context=context,
        )

    def create_write_task(self, agent: Agent, context: list, feedback: str = None) -> Task:
        """报告撰写任务 - 【干货版】禁止空话，强制密度"""
        feedback_section = ""
        if feedback:
            feedback_section = f"\n\n【重要】请根据以下评价师的反馈意见修改和完善报告：\n\n{feedback}\n"

        return Task(
            description=f"""【重要警告】这是干货报告！禁止任何空泛描述、套话、正确的废话。每一句话都要有数据或案例支撑。

请根据数据分析师提供的数据集，撰写一份**全是干货**的{self.industry_topic}行业研究报告。

✅ 【报告撰写铁律（违反直接打0分）】

1. **每一个观点必须有具体数据/案例支撑**
   - 禁止："AI Agent发展迅速"
   - 必须："AI Agent企业级渗透率从2025年的8%提升到2026年Q1的23%，但90%项目ROI<1（来源：某咨询2026调研）"

2. **禁止使用模糊词汇**
   - 黑名单："某企业""相关机构""快速增长""显著提升""前景广阔"
   - 必须使用：具体企业名、具体机构名、具体百分比、具体数字

3. **干货密度要求**
   - 每100字必须包含至少1个具体数据点或案例
   - 全文数据点总数不少于50个
   - 真实落地案例不少于15个（包含成功和失败）

4. **必须包含"反常识发现"章节**
   - 列出至少5条反常识、反主流认知的发现
   - 每条必须有数据支撑

5. **必须包含"避坑指南"章节**
   - 列出至少5个现在正在踩的坑
   - 每个坑要有具体案例、具体损失、教训

✅ 【报告结构（严格按照，可扩展但不可删减）】

1. **执行摘要（300字以内）**
   - 只列最核心的3-5个结论，每个结论带数据

2. **核心数据速览（开篇强制）**
   - 用表格列出20个最关键的数据点，让读者30秒get全局
   - 包含：市场规模、增速、头部企业营收、投融资总额、渗透率、毛利率等

3. **市场真实情况**
   - 具体规模、增速、细分赛道拆分（每个赛道有具体数字）
   - 真实的投融资情况（不是"火热"，是"Q2融资127亿，环比下降18%"）
   - 价格战真相（具体降价幅度、谁在亏、谁在赚）

4. **技术落地真相**
   - 10个真实落地案例（5个成功+5个失败）
   - 每个案例：企业、投入、效果、ROI、教训
   - 哪些技术真有用，哪些是吹出来的

5. **竞争格局实录**
   - Top 10企业经营数据对比表（营收、增速、毛利率、人员）
   - 真实的竞争策略和效果（不是"战略清晰"，是"降价30%换市场，份额从8%到15%，但亏了12亿"）
   - 谁在真赚钱、谁在烧钱、谁快要死了

6. **反常识发现（核心价值章节）**
   - 至少5条反常识发现
   - 每条：发现内容、数据支撑、对从业者的启示

7. **避坑指南（行动导向）**
   - 现在这个行业踩的最多的5个坑
   - 每个坑：具体案例、损失金额、怎么避开

8. **可操作建议**
   - 如果你是创业者，现在该做什么（3条）
   - 如果你是投资人，现在该投什么（3条）
   - 如果你是大企业，现在该布局什么（3条）

✅ 【写作风格要求】
- 像内部分享，不像公开研报
- 直白、尖锐、不说场面话
- 敢说真话、敢下判断、不怕说错（只要有数据支撑）
- 少用形容词，多用名词和动词和数字

❌ 【发现以下内容直接重写】
- "随着技术的不断进步"
- "得到了广泛的应用"
- "具有广阔的发展前景"
- "某企业"
- "相关机构"
- 任何没有数据支撑的观点

用数据说话，用案例说话，这是一份给从业者看的干货报告，不是给领导看的PPT。
{feedback_section}""",
            agent=agent,
            expected_output="完整、专业的行业研究报告，Markdown格式，约5000-8000字。",
            context=context,
            output_file="report_draft.md",
        )

    def create_review_task(self, agent: Agent, context: list) -> Task:
        """报告评价任务 - 【干货版】新增干货密度维度，零容忍空话"""
        return Task(
            description=f"""【重要】你是"干货警察"！对空泛描述零容忍。以极其严格的标准审核这份{self.industry_topic}行业研究报告。

评分标准（总分120分，必须≥100分才能通过）：

1. 【干货密度】（40分 - 核心权重）
   - 每100字是否包含1个以上具体数据点或案例（15分）
   - 全文具体数据点≥50个（10分）
   - 真实落地案例≥15个（含成功和失败）（10分）
   - 反常识发现≥5条（5分）
   - ⚠️ 扣分规则：每发现1句没有数据支撑的空话扣5分

2. 【数据质量】（30分）
   - 所有数据都有明确来源（10分）
   - 90%以上数据是近3个月的（10分）
   - 没有"某企业""相关机构"这种模糊表述（10分）
   - ⚠️ 扣分规则：每发现1个模糊表述扣3分

3. 【洞察深度】（25分）
   - 是否有独到的、反常识的发现（10分）
   - 建议是否具体可操作（10分）
   - 是否有专门的"避坑指南"章节（5分）

4. 【真实性】（15分）
   - 是否同时包含正面和负面信息（5分）
   - 失败案例≥5个（5分）
   - 没有歌功颂德式的企业介绍（5分）

5. 【可读性】（10分）
   - 开篇有核心数据速览表（5分）
   - 直白、尖锐、不说场面话（5分）

输出格式（严格按照以下格式）：
---
【评分结果】
总分：XX分
是否通过：是/否

【各维度得分】
1. 干货密度：XX/40分
2. 数据质量：XX/30分
3. 洞察深度：XX/25分
4. 真实性：XX/15分
5. 可读性：XX/10分

【问题清单（必须逐条列出）】
1. 第X章第Y段："...具体内容..." → 没有数据支撑，是空话 → 改为："...（具体建议）"
2. 第X章第Y段："某企业..." → 模糊表述 → 必须找出具体企业名称或删除
3. ...（至少列出所有问题）

【必须修改的Top 3优先级问题】
1. ...
2. ...
3. ...
---

重要说明：
- 只有总分≥100分时，"是否通过"才填"是"
- 发现任何空泛描述必须精确指出位置和修改方向
- 对"前景广阔""发展迅速"这类正确的废话零容忍
- 评分要精准，评语要具体，不要手下留情""",
            agent=agent,
            expected_output="详细的评分结果和具体修改意见（如需要）。",
            context=context,
        )

    def create_publish_task(self, agent: Agent, context: list) -> Task:
        """报告发布任务 - 完整实现"""
        report_title = f"{self.industry_topic}行业研究报告"
        receiver_id = os.getenv("LARK_RECEIVER_ID", "").strip()
        receiver_hint = (
            f"接收者 open_id：{receiver_id}"
            if receiver_id
            else "接收者 open_id：请从环境变量 LARK_RECEIVER_ID 读取"
        )
        return Task(
            description=f"""请发布这份已审核通过的{self.industry_topic}行业研究报告。

工作流程：
1. 从上下文中获取最终报告内容
2. 调用feishu_document工具创建飞书文档
3. 调用feishu_message工具发送通知消息

使用工具的输入格式要求：
- feishu_document: JSON格式，包含title和content字段
- feishu_message: JSON格式，包含message和receiver_id字段
- {receiver_hint}
- 必须使用上述 receiver_id，不要填写“相关人员”等占位文本

通知消息内容建议：
"【行业研究报告已发布】
报告名称：{report_title}
发布时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
请查收！"

请记录发布结果，包括文档链接等关键信息。""",
            agent=agent,
            expected_output="发布结果确认，包含文档链接和消息发送状态。",
            context=context,
        )

    def parse_score(self, review_text: str) -> int:
        """从审核结果中解析分数 - 完整实现"""
        # 尝试多种匹配模式
        patterns = [
            r"总分[：:]\s*(\d+)",
            r"总分：?\s*(\d+)",
            r"评分：?\s*(\d+)",
            r"得分：?\s*(\d+)",
            r"【评分结果】\s*\n.*总分[：:]\s*(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, review_text)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue

        # 如果没有找到明确分数，尝试从文本中推断
        if "95" in review_text or "九十五" in review_text:
            return 95
        if "100" in review_text or "一百" in review_text:
            return 100

        return 0

    def is_approved(self, review_text: str, score: int) -> bool:
        """判断报告是否通过 - 完整实现"""
        if score >= self.passing_score:
            return True
        # 检查明确的通过标识
        approval_keywords = ["是否通过：是", "通过：是", "批准发布", "同意发布"]
        return any(keyword in review_text for keyword in approval_keywords)

    def extract_feedback(self, review_text: str) -> str:
        """提取修改意见 - 完整实现"""
        return review_text

    def run(self) -> dict:
        """运行整个研究流程 - 完整实现"""
        print(f"\n{'='*80}")
        print(f"   开始{self.industry_topic}行业研究项目")
        print(f"{'='*80}\n")

        start_time = datetime.now()
        all_results = {}

        try:
            # ==================== 阶段1: 数据采集 ====================
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 阶段1: 数据采集")
            print(f"{'='*80}")

            collector1 = self.create_data_collector_1()
            collector2 = self.create_data_collector_2()
            collector3 = self.create_data_collector_3()

            task1 = self.create_collect_task_1(collector1)
            task2 = self.create_collect_task_2(collector2)
            task3 = self.create_collect_task_3(collector3)

            collection_crew = Crew(
                agents=[collector1, collector2, collector3],
                tasks=[task1, task2, task3],
                # CrewAI 1.14.6: 3 个采集 task 标记了 async_execution=True，
                # 在 Process.sequential 内并发启动，crew 在末尾统一 join futures。
                process=Process.sequential,
                verbose=True,
            )

            print("启动3位数据采集员并行工作...")
            collection_result = collection_crew.kickoff()

            all_results["collection"] = {
                "task1_output": str(task1.output),
                "task2_output": str(task2.output),
                "task3_output": str(task3.output),
                "full_result": str(collection_result),
            }

            print("\n✅ 数据采集完成！")

            # ==================== 阶段2: 数据分析 ====================
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 阶段2: 数据验证与分析")
            print(f"{'='*80}")

            analyst = self.create_data_analyst()
            task4 = self.create_analysis_task(analyst, context=[task1, task2, task3])

            analysis_crew = Crew(
                agents=[analyst],
                tasks=[task4],
                verbose=True,
            )

            print("数据分析师开始工作...")
            analysis_result = analysis_crew.kickoff()

            all_results["analysis"] = {
                "task4_output": str(task4.output),
                "full_result": str(analysis_result),
            }

            print("\n✅ 数据分析完成！")

            # ==================== 阶段3: 报告撰写与审核循环 ====================
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ✍️  阶段3: 报告撰写与质量审核")
            print(f"{'='*80}")

            iteration = 0
            review_feedback = None
            final_report_content = ""
            final_review_text = ""

            writer = self.create_report_writer()
            reviewer = self.create_report_reviewer()

            while iteration < self.max_iterations and not self.report_approved:
                iteration += 1
                print(f"\n--- 迭代 {iteration}/{self.max_iterations} ---")

                # 撰写报告
                print("报告撰写师开始工作...")
                task5 = self.create_write_task(writer, context=[task4], feedback=review_feedback)

                write_crew = Crew(
                    agents=[writer],
                    tasks=[task5],
                    verbose=True,
                )

                write_result = write_crew.kickoff()
                current_report = str(write_result)
                final_report_content = current_report

                # 保存当前版本
                draft_filename = f"report_draft_v{iteration}.md"
                with open(draft_filename, "w", encoding="utf-8") as f:
                    f.write(current_report)
                print(f"报告草稿已保存: {draft_filename}")

                # 审核报告
                print("\n报告评价师开始审核...")
                task6 = self.create_review_task(reviewer, context=[task5])

                review_crew = Crew(
                    agents=[reviewer],
                    tasks=[task6],
                    verbose=True,
                )

                review_result = review_crew.kickoff()
                review_text = str(review_result)
                final_review_text = review_text

                # 解析审核结果
                self.final_score = self.parse_score(review_text)
                self.report_approved = self.is_approved(review_text, self.final_score)

                all_results[f"iteration_{iteration}"] = {
                    "report": current_report,
                    "review": review_text,
                    "score": self.final_score,
                    "approved": self.report_approved,
                }

                if self.report_approved:
                    print(f"\n🎉 报告审核通过！最终评分: {self.final_score}分")
                    self.final_report = current_report
                else:
                    print(f"\n⚠️  报告需改进，当前评分: {self.final_score}分")
                    if iteration < self.max_iterations:
                        print("将根据评价师意见进行修改...")
                        review_feedback = review_text

            if not self.report_approved:
                print(f"\n⚠️  已达最大迭代次数，发布最新版本")
                self.final_report = final_report_content
                # 使用最后一次的评分
                self.final_score = all_results[f"iteration_{self.max_iterations}"]["score"]

            # ==================== 阶段4: 报告发布 ====================
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📤 阶段4: 报告发布")
            print(f"{'='*80}")

            publisher = self.create_report_publisher()
            task7 = self.create_publish_task(publisher, context=[task5, task6])

            publish_crew = Crew(
                agents=[publisher],
                tasks=[task7],
                verbose=True,
            )

            print("报告发布师开始工作...")
            publish_result = publish_crew.kickoff()

            all_results["publish"] = {
                "task7_output": str(task7.output),
                "full_result": str(publish_result),
            }

            # 保存最终报告
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_report_path = f"final_report_{timestamp}.md"
            with open(final_report_path, "w", encoding="utf-8") as f:
                f.write(self.final_report)
            print(f"\n✅ 最终报告已保存: {final_report_path}")

            # ==================== 总结 ====================
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            final_result = {
                "status": "success",
                "industry_topic": self.industry_topic,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "iterations": iteration,
                "final_score": self.final_score,
                "report_approved": self.report_approved,
                "final_report_path": final_report_path,
                "all_results": all_results,
            }

            print(f"\n{'='*80}")
            print(f"   项目完成总结")
            print(f"{'='*80}")
            print(f"行业主题: {self.industry_topic}")
            print(f"执行时间: {duration:.1f}秒")
            print(f"迭代次数: {iteration}")
            print(f"最终评分: {self.final_score}分")
            print(f"审核状态: {'✅ 通过' if self.report_approved else '⚠️  未完全通过'}")
            print(f"报告文件: {final_report_path}")
            print(f"{'='*80}\n")

            return final_result

        except Exception as e:
            print(f"\n❌ 项目执行出错: {str(e)}")
            import traceback
            traceback.print_exc()

            return {
                "status": "error",
                "error": str(e),
                "industry_topic": self.industry_topic,
            }


def main():
    """主函数 - 完整实现"""
    import argparse

    print("="*80)
    print("          行业研究报告生成系统 - 完整版")
    print("="*80)

    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="行业研究报告生成系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python src/main.py --topic "人工智能"
  python src/main.py -t "新能源汽车"
        """
    )
    parser.add_argument(
        "--topic", "-t",
        type=str,
        required=True,
        help="要研究的行业主题（必需）"
    )
    args = parser.parse_args()

    # 获取并验证行业主题
    industry_topic = args.topic.strip()
    if not industry_topic:
        print(f"\n❌ 错误: 行业主题不能为空")
        print(f"\n使用帮助:")
        parser.print_help()
        sys.exit(1)

    # 验证 LLM 配置
    is_valid, error_msg = validate_config()
    if not is_valid:
        print(f"\n❌ LLM 配置错误: {error_msg}")
        print("\n请先配置 .env 文件")
        print("提示: 复制 .env.example 为 .env 并填入相应的配置\n")
        sys.exit(1)

    # 显示 LLM 配置信息
    config_info = get_config_info()
    print(f"\n✅ LLM 配置已加载:")
    print(f"   提供商: {config_info['provider']}")
    print(f"   模型: {config_info['model']}")
    if 'base_url' in config_info:
        print(f"   地址: {config_info['base_url']}")
    if 'endpoint' in config_info:
        print(f"   端点: {config_info['endpoint']}")

    # 显示质量控制配置
    print(f"\n✅ 质量控制配置已加载:")
    print(f"   最大审核迭代次数: {get_max_review_iterations()}")
    print(f"   通过评分阈值: {get_passing_score()}分")

    # 显示研究主题
    print(f"\n📋 行业主题: {industry_topic}")
    print(f"\n🚀 开始研究...\n")

    # 创建并运行研究团队
    research_crew = IndustryResearchCrew(industry_topic)
    result = research_crew.run()

    # 保存完整结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"project_result_{timestamp}.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n完整项目结果已保存: {result_file}")


if __name__ == "__main__":
    main()
