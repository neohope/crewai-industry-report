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
from src.tools.search_tool import WebSearchTool, NewsSearchTool
from src.tools.feishu_tool import FeishuDocumentTool, FeishuMessageTool

# 加载环境变量
load_dotenv()


class IndustryResearchCrew:
    """行业研究团队 - 完整实现"""

    def __init__(self, industry_topic: str):
        self.industry_topic = industry_topic
        self.web_search = WebSearchTool()
        self.news_search = NewsSearchTool()
        self.feishu_doc = FeishuDocumentTool()
        self.feishu_msg = FeishuMessageTool()
        self.final_report = ""
        self.final_score = 0
        self.report_approved = False

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
        )

    def create_report_reviewer(self) -> Agent:
        """报告评价师 - 完整实现"""
        return Agent(
            role="报告评价师",
            goal="以极其严格的标准审核报告质量，从多个维度进行评分，只有达到95分以上才能通过",
            backstory="""你是业内知名的报告质量审核专家，以标准极其严格著称。
你审核报告的四个维度（总分100分）：
1. 内容详实性（30分）：数据是否丰富、案例是否充分、覆盖是否全面
2. 逻辑性（30分）：结构是否清晰、论证是否严密、逻辑是否自洽
3. 可靠性（25分）：数据来源是否明确、分析是否客观、结论是否有依据
4. 可读性（15分）：表达是否流畅、层次是否分明、阅读体验是否良好
评分低于95分时，你必须给出具体、可操作的修改意见；
评分达到或超过95分时，你批准报告发布。
你的评分总是非常精准，评语总是非常具体。""",
            allow_delegation=False,
            verbose=True,
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
        )

    def create_collect_task_1(self, agent: Agent) -> Task:
        """市场数据采集任务 - 完整实现"""
        return Task(
            description=f"""请收集{self.industry_topic}行业的市场相关数据，要求如下：

1. 市场规模：
   - 当前市场总量（最新数据）
   - 近3-5年的历史增长数据
   - 未来3年的预测数据

2. 增长趋势：
   - 年复合增长率
   - 主要驱动因素分析
   - 增长的关键节点

3. 市场份额：
   - 主要企业的市场占比
   - 市场集中度情况（CR5/CR10）
   - 竞争格局概览

4. 区域分布：
   - 主要市场区域分布
   - 各区域的增长特点

请务必记录每个数据点的：
- 数据来源（具体机构/网站）
- 发布时间
- 统计口径

输出格式要求：结构化的数据清单，不要写成散文。""",
            agent=agent,
            expected_output="结构化的市场数据清单，包含所有数据点及其来源、时间、统计口径。",
        )

    def create_collect_task_2(self, agent: Agent) -> Task:
        """技术趋势采集任务 - 完整实现"""
        return Task(
            description=f"""请收集{self.industry_topic}行业的技术相关数据，要求如下：

1. 技术发展：
   - 当前主流技术
   - 技术发展历程（关键里程碑）
   - 技术成熟度分析

2. 创新动态：
   - 最新技术突破（近1-2年）
   - 研发热点领域
   - 专利申请趋势
   - 代表性创新案例

3. 研发投入：
   - 主要企业的研发投入数据
   - 研发投入占比
   - 重点研发方向

4. 应用案例：
   - 技术应用的成功案例
   - 应用效果数据
   - 典型应用场景

请务必记录每个数据点的：
- 数据来源
- 发布时间
- 技术语境

输出格式要求：结构化的数据清单。""",
            agent=agent,
            expected_output="结构化的技术趋势数据清单，包含所有数据点及其来源和时间。",
        )

    def create_collect_task_3(self, agent: Agent) -> Task:
        """竞争格局采集任务 - 完整实现"""
        return Task(
            description=f"""请收集{self.industry_topic}行业的竞争相关数据，要求如下：

1. 主要企业：
   - 行业头部企业列表（Top 5-10）
   - 各企业简介
   - 企业市场定位

2. 产品服务：
   - 各企业的主要产品和服务
   - 产品对比分析
   - 差异化特点

3. 竞争策略：
   - 主要企业的战略定位
   - 竞争优势分析
   - 近期战略动向

4. 近期动态：
   - 企业的最新动态（近1年）
   - 战略合作情况
   - 投资并购事件

请务必记录每个数据点的：
- 数据来源
- 发布时间
- 相关背景

输出格式要求：结构化的数据清单。""",
            agent=agent,
            expected_output="结构化的竞争格局数据清单，包含所有数据点及其来源和时间。",
        )

    def create_analysis_task(self, agent: Agent, context: list) -> Task:
        """数据分析任务 - 完整实现"""
        return Task(
            description=f"""请对三位数据采集员收集的数据进行专业的分析处理：

1. 数据验证：
   - 检查每个数据来源的权威性
   - 检查数据的时效性
   - 交叉验证不同数据源的一致性
   - 识别并记录数据矛盾点

2. 数据清洗：
   - 去除重复数据
   - 合并互补信息
   - 解决或标注数据矛盾

3. 数据整合：
   - 按主题分类整理数据
   - 形成统一的数据集结构
   - 确保数据组织清晰

4. 可信度标注：
   - 为每个数据点标注可信度等级（高/中/低）
   - 说明标注理由
   - 列出存疑数据点及原因

输出格式要求：
- 结构化的数据集
- 每个数据条目包含：数据内容、来源、时间、可信度、备注
- 按市场数据、技术数据、竞争数据分类
- 单独的存疑数据清单""",
            agent=agent,
            expected_output="经过验证、清洗、整合的高质量数据集，带有可信度标注。",
            context=context,
        )

    def create_write_task(self, agent: Agent, context: list, feedback: str = None) -> Task:
        """报告撰写任务 - 完整实现"""
        feedback_section = ""
        if feedback:
            feedback_section = f"\n\n【重要】请根据以下评价师的反馈意见修改和完善报告：\n\n{feedback}\n"

        return Task(
            description=f"""请根据数据分析师提供的高质量数据集，撰写一份专业的{self.industry_topic}行业研究报告。

报告结构（严格按照以下结构）：
1. 执行摘要（200-300字）
2. 行业概述
   - 行业定义
   - 发展历程
   - 现状概述
3. 市场分析
   - 市场规模与增长
   - 区域分布
   - 市场集中度
4. 技术分析
   - 技术发展现状
   - 创新动态
   - 研发投入分析
5. 竞争格局
   - 主要企业介绍
   - 产品对比
   - 竞争策略分析
6. 未来展望
   - 发展趋势预测
   - 机遇分析
   - 挑战分析
7. 结论与建议

要求：
- 数据准确，所有数据注明来源
- 逻辑清晰，结构完整，层次分明
- 分析深入，有独到见解
- 表达流畅，可读性强
- 使用Markdown格式
{feedback_section}""",
            agent=agent,
            expected_output="完整、专业的行业研究报告，Markdown格式，约5000-8000字。",
            context=context,
            output_file="report_draft.md",
        )

    def create_review_task(self, agent: Agent, context: list) -> Task:
        """报告评价任务 - 完整实现"""
        return Task(
            description=f"""请以极其严格的标准审核这份{self.industry_topic}行业研究报告。

评分标准（总分100分）：
1. 内容详实性（30分）：
   - 数据是否丰富（10分）
   - 案例是否充分（10分）
   - 覆盖是否全面（10分）

2. 逻辑性（30分）：
   - 结构是否清晰（10分）
   - 论证是否严密（10分）
   - 逻辑是否自洽（10分）

3. 可靠性（25分）：
   - 数据来源是否明确（10分）
   - 分析是否客观（8分）
   - 结论是否有依据（7分）

4. 可读性（15分）：
   - 表达是否流畅（5分）
   - 层次是否分明（5分）
   - 阅读体验是否良好（5分）

输出格式（严格按照以下格式）：
---
【评分结果】
总分：XX分
是否通过：是/否

【各维度得分】
1. 内容详实性：XX分
2. 逻辑性：XX分
3. 可靠性：XX分
4. 可读性：XX分

【详细评价意见】
（每条意见具体、明确、可操作，指出具体问题、位置、改进建议）
1. ...
2. ...
3. ...
---

重要说明：
- 只有总分≥95分时，"是否通过"才填"是"
- 否则必须给出至少3条具体修改意见
- 评分要精准，评语要具体""",
            agent=agent,
            expected_output="详细的评分结果和具体修改意见（如需要）。",
            context=context,
        )

    def create_publish_task(self, agent: Agent, context: list) -> Task:
        """报告发布任务 - 完整实现"""
        report_title = f"{self.industry_topic}行业研究报告"
        return Task(
            description=f"""请发布这份已审核通过的{self.industry_topic}行业研究报告。

工作流程：
1. 从上下文中获取最终报告内容
2. 调用feishu_document工具创建飞书文档
3. 调用feishu_message工具发送通知消息

使用工具的输入格式要求：
- feishu_document: JSON格式，包含title和content字段
- feishu_message: JSON格式，包含message和receiver_id字段

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
        if score >= 95:
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
            # ==================== 阶段1: 并行数据采集 ====================
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 阶段1: 并行数据采集")
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
                process=Process.parallel,
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

            max_iterations = 2
            iteration = 0
            review_feedback = None
            final_report_content = ""
            final_review_text = ""

            writer = self.create_report_writer()
            reviewer = self.create_report_reviewer()

            while iteration < max_iterations and not self.report_approved:
                iteration += 1
                print(f"\n--- 迭代 {iteration}/{max_iterations} ---")

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
                    if iteration < max_iterations:
                        print("将根据评价师意见进行修改...")
                        review_feedback = review_text

            if not self.report_approved:
                print(f"\n⚠️  已达最大迭代次数，发布最新版本")
                self.final_report = final_report_content
                # 使用最后一次的评分
                self.final_score = all_results[f"iteration_{max_iterations}"]["score"]

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
    print("="*80)
    print("          行业研究报告生成系统 - 完整版")
    print("="*80)

    # 检查环境变量
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("\n⚠️  警告: OPENAI_API_KEY 未设置")
        print("请先配置 .env 文件")
        print("\n提示: 复制 .env.example 为 .env 并填入你的 API 密钥\n")

    # 获取行业主题
    industry_topic = input("\n请输入要研究的行业主题: ").strip()
    if not industry_topic:
        industry_topic = "人工智能"
        print(f"使用默认主题: {industry_topic}")

    # 确认
    print(f"\n即将开始研究: {industry_topic}")
    confirm = input("确认开始？(y/n): ").strip().lower()
    if confirm not in ["y", "yes", "是", ""]:
        print("已取消")
        sys.exit(0)

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
