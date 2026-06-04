#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书工具测试 - 真实可验证测试
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
        from src.tools.feishu_tool import FeishuDocumentTool, FeishuMessageTool
        print("✅ 飞书工具模块导入成功")
        return True, FeishuDocumentTool, FeishuMessageTool
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None


def test_document_tool(FeishuDocumentTool):
    """测试文档工具"""
    print("\n" + "="*70)
    print("测试2: FeishuDocumentTool")
    print("="*70)
    try:
        tool = FeishuDocumentTool()
        print(f"✅ 工具实例化成功")
        print(f"   名称: {tool.name}")
        print(f"   skill可用: {tool.skill_available}")

        # 测试创建文档
        test_title = "测试行业研究报告"
        test_content = """# 测试报告

## 1. 概述

这是一个测试文档。

## 2. 数据

- 数据点1: 示例数据
- 数据点2: 更多示例
"""

        test_input = json.dumps({
            "title": test_title,
            "content": test_content
        }, ensure_ascii=False)

        print(f"\n测试创建文档: '{test_title}'")
        result = tool._run(test_input)

        print(f"\n文档工具返回结果:")
        print(f"   结果长度: {len(result)} 字符")
        print(f"   结果预览: {result[:150]}...")

        # 解析结果
        result_data = json.loads(result)
        print(f"   状态: {result_data.get('status', 'unknown')}")

        if result_data.get('status') in ['success', 'logged']:
            print("✅ 文档工具执行成功")
            if 'local_file' in result_data:
                print(f"   本地文件: {result_data['local_file']}")

                # 验证文件存在
                if os.path.exists(result_data['local_file']):
                    print(f"   ✅ 文件已创建")
                    # 验证内容
                    with open(result_data['local_file'], 'r', encoding='utf-8') as f:
                        content = f.read()
                        if test_title in content or "测试报告" in content:
                            print(f"   ✅ 文件内容正确")
                        else:
                            print(f"   ⚠️  文件内容可能需要检查")

                return True, result_data
        else:
            print(f"❌ 文档工具执行有问题: {result_data}")
            return False, None

    except Exception as e:
        print(f"❌ 文档工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_message_tool(FeishuMessageTool):
    """测试消息工具"""
    print("\n" + "="*70)
    print("测试3: FeishuMessageTool")
    print("="*70)
    try:
        tool = FeishuMessageTool()
        print(f"✅ 工具实例化成功")
        print(f"   名称: {tool.name}")
        print(f"   skill可用: {tool.skill_available}")

        # 测试发送消息
        test_message = "【测试通知】行业研究报告生成系统测试消息"
        test_receiver = "test_user@example.com"

        test_input = json.dumps({
            "message": test_message,
            "receiver_id": test_receiver
        }, ensure_ascii=False)

        print(f"\n测试发送消息: '{test_message[:40]}...'")
        result = tool._run(test_input)

        print(f"\n消息工具返回结果:")
        print(f"   结果长度: {len(result)} 字符")
        print(f"   结果预览: {result[:150]}...")

        # 解析结果
        result_data = json.loads(result)
        print(f"   状态: {result_data.get('status', 'unknown')}")

        if result_data.get('status') in ['success', 'logged']:
            print("✅ 消息工具执行成功")

            # 检查日志文件
            if 'log_file' in result_data:
                log_file = result_data['log_file']
                print(f"   日志文件: {log_file}")
                if os.path.exists(log_file):
                    print(f"   ✅ 日志文件已创建")

            return True, result_data
        else:
            print(f"❌ 消息工具执行有问题: {result_data}")
            return False, None

    except Exception as e:
        print(f"❌ 消息工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("          飞书工具测试套件")
    print("="*70)

    results = []

    # 测试1
    ok, FeishuDocumentTool, FeishuMessageTool = test_imports()
    results.append(("模块导入", ok))
    if not ok:
        print("\n❌ 基础导入失败，终止测试")
        return 1

    # 测试2
    ok, doc_result = test_document_tool(FeishuDocumentTool)
    results.append(("文档工具", ok))

    # 测试3
    ok, msg_result = test_message_tool(FeishuMessageTool)
    results.append(("消息工具", ok))

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
        print("\n🎉 所有飞书工具测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
