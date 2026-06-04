#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主程序测试 - 真实可验证测试（完整版本）
"""
import sys
import os
import json


def test_imports():
    """测试导入"""
    print("="*70)
    print("测试1: 模块导入")
    print("="*70)
    try:
        from src.main import IndustryResearchCrew
        print("✅ 主程序模块导入成功")
        return True, IndustryResearchCrew
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_crew_initialization(IndustryResearchCrew):
    """测试Crew初始化"""
    print("\n" + "="*70)
    print("测试2: IndustryResearchCrew 初始化")
    print("="*70)
    try:
        crew = IndustryResearchCrew("测试行业")
        print(f"✅ Crew初始化成功")
        print(f"   主题: {crew.industry_topic}")
        print(f"   搜索工具: {crew.web_search is not None}")
        print(f"   飞书工具: {crew.feishu_doc is not None}")
        return True, crew
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_agent_creation(crew):
    """测试代理创建"""
    print("\n" + "="*70)
    print("测试3: 代理创建")
    print("="*70)
    try:
        # 测试所有代理
        agents = [
            ("数据采集员1", crew.create_data_collector_1),
            ("数据采集员2", crew.create_data_collector_2),
            ("数据采集员3", crew.create_data_collector_3),
            ("数据分析师", crew.create_data_analyst),
            ("报告撰写师", crew.create_report_writer),
            ("报告评价师", crew.create_report_reviewer),
            ("报告发布师", crew.create_report_publisher),
        ]

        all_ok = True
        for name, create_func in agents:
            agent = create_func()
            if agent:
                print(f"✅ {name}: 创建成功")
                print(f"   角色: {agent.role}")
            else:
                print(f"❌ {name}: 创建失败")
                all_ok = False

        return all_ok
    except Exception as e:
        print(f"❌ 代理创建测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_task_creation(crew):
    """测试任务创建"""
    print("\n" + "="*70)
    print("测试4: 任务创建")
    print("="*70)
    try:
        # 创建一些测试代理
        collector1 = crew.create_data_collector_1()
        analyst = crew.create_data_analyst()
        writer = crew.create_report_writer()

        # 测试任务创建
        tasks = [
            ("采集任务1", crew.create_collect_task_1, (collector1,)),
            ("分析任务", crew.create_analysis_task, (analyst, [])),
            ("撰写任务", crew.create_write_task, (writer, [], None)),
        ]

        all_ok = True
        for name, create_func, args in tasks:
            task = create_func(*args)
            if task:
                print(f"✅ {name}: 创建成功")
                print(f"   描述长度: {len(task.description)}")
                print(f"   期望输出: {task.expected_output[:40]}...")
            else:
                print(f"❌ {name}: 创建失败")
                all_ok = False

        return all_ok
    except Exception as e:
        print(f"❌ 任务创建测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_score_parsing(crew):
    """测试分数解析"""
    print("\n" + "="*70)
    print("测试5: 分数解析")
    print("="*70)
    try:
        test_cases = [
            ("总分：95分", 95),
            ("总分: 87分", 87),
            ("【评分结果】\n总分：100分\n是否通过：是", 100),
            ("评分：92分", 92),
        ]

        all_ok = True
        for review_text, expected in test_cases:
            score = crew.parse_score(review_text)
            if score == expected:
                print(f"✅ 解析正确: '{review_text[:30]}...' -> {score}分")
            else:
                print(f"❌ 解析错误: '{review_text[:30]}...' -> {score}分 (期望: {expected})")
                all_ok = False

        return all_ok
    except Exception as e:
        print(f"❌ 分数解析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_approval_check(crew):
    """测试通过检查"""
    print("\n" + "="*70)
    print("测试6: 通过检查")
    print("="*70)
    try:
        test_cases = [
            ("总分：95分", 95, True),
            ("总分：90分", 90, False),
            ("总分：100分\n是否通过：是", 100, True),
            ("总分：80分\n是否通过：否", 80, False),
        ]

        all_ok = True
        for review_text, score, expected in test_cases:
            approved = crew.is_approved(review_text, score)
            if approved == expected:
                status = "通过" if expected else "不通过"
                print(f"✅ 判断正确: {score}分 -> {status}")
            else:
                status = "通过" if expected else "不通过"
                actual = "通过" if approved else "不通过"
                print(f"❌ 判断错误: {score}分 -> {actual} (期望: {status})")
                all_ok = False

        return all_ok
    except Exception as e:
        print(f"❌ 通过检查测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("          主程序测试套件")
    print("="*70)

    results = []

    # 测试1
    ok, IndustryResearchCrew = test_imports()
    results.append(("模块导入", ok))
    if not ok:
        print("\n❌ 基础导入失败，终止测试")
        return 1

    # 测试2
    ok, crew = test_crew_initialization(IndustryResearchCrew)
    results.append(("Crew初始化", ok))
    if not ok:
        print("\n❌ 初始化失败，终止测试")
        return 1

    # 测试3
    ok = test_agent_creation(crew)
    results.append(("代理创建", ok))

    # 测试4
    ok = test_task_creation(crew)
    results.append(("任务创建", ok))

    # 测试5
    ok = test_score_parsing(crew)
    results.append(("分数解析", ok))

    # 测试6
    ok = test_approval_check(crew)
    results.append(("通过检查", ok))

    # 总结
    print("\n" + "="*70)
    print("          测试总结")
    print("="*70)
    for name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {name}: {status}")

    passed = sum(1 for _, ok in results)
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有主程序测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
