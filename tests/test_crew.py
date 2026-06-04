"""
测试行业研究Crew
"""
import pytest
from src.main import IndustryResearchCrew


def test_crew_initialization():
    """测试Crew初始化"""
    crew = IndustryResearchCrew("人工智能")
    assert crew.industry_topic == "人工智能"


def test_agent_creation():
    """测试代理创建"""
    crew = IndustryResearchCrew("新能源")

    collector1 = crew.create_data_collector_1()
    assert collector1.role == "数据采集员-市场数据"

    collector2 = crew.create_data_collector_2()
    assert collector2.role == "数据采集员-技术趋势"

    collector3 = crew.create_data_collector_3()
    assert collector3.role == "数据采集员-竞争格局"

    analyst = crew.create_data_analyst()
    assert analyst.role == "数据分析师"

    writer = crew.create_report_writer()
    assert writer.role == "报告撰写师"

    reviewer = crew.create_report_reviewer()
    assert reviewer.role == "报告评价师"

    publisher = crew.create_report_publisher()
    assert publisher.role == "报告发布师"


def test_task_creation():
    """测试任务创建"""
    crew = IndustryResearchCrew("生物医药")

    collector1 = crew.create_data_collector_1()
    task1 = crew.create_collect_task_1(collector1)
    assert task1.agent == collector1

    analyst = crew.create_data_analyst()
    task4 = crew.create_analysis_task(analyst)
    assert task4.agent == analyst
