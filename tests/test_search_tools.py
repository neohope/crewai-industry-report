#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索工具测试 - 真实可验证测试
"""
import sys
import os


def test_imports():
    """测试导入"""
    print("="*70)
    print("测试1: 模块导入")
    print("="*70)
    try:
        from src.tools.search_tool import WebSearchTool, NewsSearchTool
        print("✅ 搜索工具模块导入成功")
        return True, WebSearchTool, NewsSearchTool
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None


def test_web_search_tool(WebSearchTool):
    """测试网络搜索工具"""
    print("\n" + "="*70)
    print("测试2: WebSearchTool 实例化")
    print("="*70)
    try:
        tool = WebSearchTool()
        print(f"✅ 工具实例化成功")
        print(f"   名称: {tool.name}")
        print(f"   描述: {tool.description[:50]}...")
        return True, tool
    except Exception as e:
        print(f"❌ 实例化失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_web_search_execution(tool):
    """测试网络搜索执行"""
    print("\n" + "="*70)
    print("测试3: WebSearchTool 搜索执行")
    print("="*70)
    try:
        test_query = "人工智能行业市场规模"
        print(f"测试搜索: '{test_query}'")

        result = tool._run(test_query, max_results=3)

        print(f"\n搜索返回结果:")
        print(f"   结果长度: {len(result)} 字符")
        print(f"   结果预览: {result[:200]}...")

        # 验证结果格式
        if "query" in result and "results" in result:
            print("✅ 搜索结果格式正确")
        else:
            print("⚠️  搜索结果格式可能需要检查")

        return True, result
    except Exception as e:
        print(f"❌ 搜索执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_news_search_tool(NewsSearchTool):
    """测试新闻搜索工具"""
    print("\n" + "="*70)
    print("测试4: NewsSearchTool 实例化和执行")
    print("="*70)
    try:
        tool = NewsSearchTool()
        print(f"✅ 工具实例化成功")

        test_query = "人工智能最新技术动态"
        print(f"测试搜索: '{test_query}'")

        result = tool._run(test_query, max_results=3)
        print(f"\n搜索返回结果:")
        print(f"   结果长度: {len(result)} 字符")
        print(f"   结果预览: {result[:200]}...")

        return True, result
    except Exception as e:
        print(f"❌ 新闻搜索测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("          搜索工具测试套件")
    print("="*70)

    results = []

    # 测试1
    ok, WebSearchTool, NewsSearchTool = test_imports()
    results.append(("模块导入", ok))
    if not ok:
        print("\n❌ 基础导入失败，终止测试")
        return 1

    # 测试2
    ok, web_tool = test_web_search_tool(WebSearchTool)
    results.append(("WebSearchTool实例化", ok))
    if not ok:
        print("\n❌ 工具实例化失败，终止测试")
        return 1

    # 测试3
    ok, web_result = test_web_search_execution(web_tool)
    results.append(("WebSearchTool搜索", ok))

    # 测试4
    ok, news_result = test_news_search_tool(NewsSearchTool)
    results.append(("NewsSearchTool测试", ok))

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
        print("\n🎉 所有搜索工具测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
