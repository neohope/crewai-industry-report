#!/usr/bin/env python3
"""
简化测试脚本
用于快速验证项目的核心功能
"""
import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=" * 60)
print("          简化测试脚本")
print("=" * 60)


def test_basic_imports():
    """测试基础导入"""
    print("\n📦 测试基础导入...")
    try:
        from crewai import Crew, Agent, Task
        print("✅ crewai 导入成功")

        from src.tools.search_tool import WebSearchTool
        print("✅ 搜索工具导入成功")

        from src.main import IndustryResearchCrew
        print("✅ 主模块导入成功")

        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_agent_creation():
    """测试代理创建"""
    print("\n🤖 测试代理创建...")
    try:
        from src.main import IndustryResearchCrew

        crew = IndustryResearchCrew("测试行业")

        # 创建几个关键代理
        collector = crew.create_data_collector_1()
        assert collector.role == "数据采集员-市场数据"
        print("✅ 数据采集员创建成功")

        analyst = crew.create_data_analyst()
        assert analyst.role == "数据分析师"
        print("✅ 数据分析师创建成功")

        writer = crew.create_report_writer()
        assert writer.role == "报告撰写师"
        print("✅ 报告撰写师创建成功")

        return True
    except Exception as e:
        print(f"❌ 代理创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_task_creation():
    """测试任务创建"""
    print("\n📋 测试任务创建...")
    try:
        from src.main import IndustryResearchCrew

        crew = IndustryResearchCrew("测试行业")
        collector = crew.create_data_collector_1()
        task = crew.create_collect_task_1(collector)

        assert task.agent == collector
        print("✅ 任务创建成功")
        print(f"   任务描述: {task.description[:50]}...")

        return True
    except Exception as e:
        print(f"❌ 任务创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_score_parsing():
    """测试分数解析"""
    print("\n📊 测试分数解析...")
    try:
        from src.main import IndustryResearchCrew

        crew = IndustryResearchCrew("测试行业")

        test_cases = [
            ("总分：92分", 92),
            ("总分: 95分", 95),
            ("评分：88分", 88),
            ("其他文本 总分：100分 其他", 100),
        ]

        all_pass = True
        for review_text, expected_score in test_cases:
            score = crew.parse_score(review_text)
            if score == expected_score:
                print(f"✅ 解析 '{review_text[:20]}...' -> {score}分")
            else:
                print(f"❌ 解析 '{review_text[:20]}...' -> {score}分 (期望: {expected_score})")
                all_pass = False

        return all_pass
    except Exception as e:
        print(f"❌ 分数解析失败: {e}")
        return False


def test_tool_initialization():
    """测试工具初始化"""
    print("\n🔧 测试工具初始化...")
    try:
        from src.tools.search_tool import WebSearchTool, NewsSearchTool
        from src.tools.feishu_tool import FeishuDocumentTool, FeishuMessageTool

        web_tool = WebSearchTool()
        print(f"✅ WebSearchTool: {web_tool.name}")

        news_tool = NewsSearchTool()
        print(f"✅ NewsSearchTool: {news_tool.name}")

        feishu_doc = FeishuDocumentTool()
        print(f"✅ FeishuDocumentTool: {feishu_doc.name}")

        feishu_msg = FeishuMessageTool()
        print(f"✅ FeishuMessageTool: {feishu_msg.name}")

        return True
    except Exception as e:
        print(f"❌ 工具初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_api_key():
    """检查API密钥"""
    print("\n🔑 检查API配置...")
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        if api_key.startswith("sk-"):
            print("✅ OPENAI_API_KEY 已配置 (格式正确)")
        else:
            print("⚠️  OPENAI_API_KEY 已配置 (格式可能不正确)")
        return True
    else:
        print("❌ OPENAI_API_KEY 未配置")
        print("   请复制 .env.example 为 .env 并填入你的 API 密钥")
        return False


def main():
    """主测试函数"""
    results = []

    results.append(("基础导入", test_basic_imports()))
    results.append(("工具初始化", test_tool_initialization()))
    results.append(("代理创建", test_agent_creation()))
    results.append(("任务创建", test_task_creation()))
    results.append(("分数解析", test_score_parsing()))
    results.append(("API配置", check_api_key()))

    passed = sum(1 for name, result in results if result)
    total = len(results)

    print("\n" + "=" * 60)
    print("          测试总结")
    print("=" * 60)
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    print("=" * 60)
    print(f"总计: {passed}/{total} 项测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        print("\n下一步:")
        print("1. 运行完整项目: poetry run python src/main.py")
        print("2. 或运行验证脚本: python verify.py")
        return 0
    else:
        print("\n⚠️  部分测试未通过")
        if not os.getenv("OPENAI_API_KEY"):
            print("\n提示: 请先配置 .env 文件")
        return 1


if __name__ == "__main__":
    sys.exit(main())
