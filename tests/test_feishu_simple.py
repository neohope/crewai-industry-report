#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书工具简单测试
"""
import sys
import os
import json

# 添加项目路径
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)


def main():
    print("="*60)
    print("Feishu Tool Test")
    print("="*60)

    try:
        from src.tools.feishu_tool import FeishuDocumentTool, FeishuMessageTool
        print("[OK] Module import")
    except Exception as e:
        print(f"[FAIL] Module import: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # 测试文档工具
    print("\n--- Testing Document Tool ---")
    try:
        doc_tool = FeishuDocumentTool()
        print(f"[OK] Document tool created")
        print(f"skill available: {doc_tool.skill_available}")

        test_title = "Test Report"
        test_content = """# Test Report

## Overview
This is a test document.

## Data
- Point 1
- Point 2
"""

        test_input = json.dumps({
            "title": test_title,
            "content": test_content
        }, ensure_ascii=False)

        print(f"Testing create document...")
        result_str = doc_tool._run(test_input)
        result = json.loads(result_str)
        print(f"Result status: {result.get('status')}")

        if result.get('status') in ['success', 'logged']:
            print("[OK] Document tool works")
            if 'local_file' in result:
                print(f"  Local file: {result.get('local_file')}")
                if os.path.exists(result.get('local_file')):
                    print("  File exists")
        else:
            print(f"[FAIL] Document tool: {result}")
    except Exception as e:
        print(f"[FAIL] Document test: {e}")
        import traceback
        traceback.print_exc()

    # 测试消息工具
    print("\n--- Testing Message Tool ---")
    try:
        msg_tool = FeishuMessageTool()
        print(f"[OK] Message tool created")
        print(f"skill available: {msg_tool.skill_available}")

        test_input = json.dumps({
            "message": "Test notification",
            "receiver_id": "test_user"
        }, ensure_ascii=False)

        print(f"Testing send message...")
        result_str = msg_tool._run(test_input)
        result = json.loads(result_str)
        print(f"Result status: {result.get('status')}")

        if result.get('status') in ['success', 'logged']:
            print("[OK] Message tool works")
            if 'log_file' in result:
                print(f"  Log file: {result.get('log_file')}")
                if os.path.exists(result.get('log_file')):
                    print("  Log file exists")
        else:
            print(f"[FAIL] Message tool: {result}")
    except Exception as e:
        print(f"[FAIL] Message test: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("Test Complete")
    print("="*60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
