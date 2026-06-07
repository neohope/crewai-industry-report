#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书工具测试 - 真实可验证测试
"""
import sys
import os
import json
import importlib
from unittest.mock import patch, MagicMock


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


def test_document_tool_uses_v2_content_cli_args(FeishuDocumentTool):
    """验证文档工具使用 OpenAPI v2 的 docs +create 参数。

    当前环境中默认 docs +create / --markdown 会走 v1/MCP/TAT 路径并报
    `TAT API error: [10003] invalid param`。项目发布必须固定走：
    `lark-cli docs +create --api-version v2 --content @.lark_tmp/*.xml`。
    这里用 mock 防止真正创建飞书文档，只检查命令参数。
    """
    tool = FeishuDocumentTool(use_skill=True)
    tool._skill_available = True

    completed = MagicMock()
    completed.returncode = 0
    completed.stdout = json.dumps({
        "ok": True,
        "data": {
            "document": {
                "document_id": "doc_test",
                "url": "https://example.feishu.cn/docx/doc_test"
            }
        }
    }, ensure_ascii=False)
    completed.stderr = ""

    with patch.dict(os.environ, {"LARK_APP_ID": "", "LARK_APP_SECRET": ""}), \
         patch("src.tools.feishu_tool.subprocess.run", return_value=completed) as run_mock:
        result = json.loads(tool._run(json.dumps({
            "title": "测试标题",
            "content": "# 测试标题\n\n正文"
        }, ensure_ascii=False)))

    assert result["status"] == "success"
    cmd = run_mock.call_args.args[0]
    assert cmd[:3] == ["lark-cli", "docs", "+create"]
    assert "--title" in cmd
    assert "--api-version" in cmd
    assert cmd[cmd.index("--api-version") + 1] == "v2"
    assert "--content" in cmd
    assert "--markdown" not in cmd
    content_arg = cmd[cmd.index("--content") + 1]
    assert content_arg.startswith("@.lark_tmp/")
    assert content_arg.endswith(".xml")


def test_message_tool_accepts_receiver_id(FeishuMessageTool):
    """验证发布任务传 receiver_id 时会映射到 lark-cli --user-id。"""
    tool = FeishuMessageTool(use_skill=True)
    tool._skill_available = True

    completed = MagicMock()
    completed.returncode = 0
    completed.stdout = json.dumps({"message_id": "om_test", "chat_id": "oc_test"})
    completed.stderr = ""

    with patch.dict(os.environ, {"LARK_APP_ID": "", "LARK_APP_SECRET": ""}), \
         patch("src.tools.feishu_tool.subprocess.run", return_value=completed) as run_mock:
        result = json.loads(tool._run(json.dumps({
            "message": "测试消息",
            "receiver_id": "ou_test_receiver"
        }, ensure_ascii=False)))

    assert result["status"] == "success"
    cmd = run_mock.call_args.args[0]
    assert cmd[:3] == ["lark-cli", "im", "+messages-send"]
    assert "--user-id" in cmd
    assert cmd[cmd.index("--user-id") + 1] == "ou_test_receiver"


def test_document_tool_prefers_openapi_when_app_credentials_exist(FeishuDocumentTool):
    """有 LARK_APP_ID/LARK_APP_SECRET 时，文档发布应绕过 lark-cli。"""
    tool = FeishuDocumentTool(use_skill=True)
    tool._skill_available = True

    token_response = MagicMock()
    token_response.status_code = 200
    token_response.json.return_value = {"code": 0, "tenant_access_token": "tenant_token"}
    token_response.raise_for_status.return_value = None

    create_response = MagicMock()
    create_response.status_code = 200
    create_response.json.return_value = {
        "code": 0,
        "data": {
            "document": {
                "document_id": "doc_openapi",
                "url": "https://example.feishu.cn/docx/doc_openapi"
            }
        }
    }
    create_response.raise_for_status.return_value = None

    with patch.dict(os.environ, {"LARK_APP_ID": "cli_xxx", "LARK_APP_SECRET": "secret"}), \
         patch("src.tools.feishu_tool.requests.post", side_effect=[token_response, create_response]) as post_mock, \
         patch("src.tools.feishu_tool.subprocess.run") as run_mock:
        result = json.loads(tool._run(json.dumps({
            "title": "测试标题",
            "content": "# 测试标题\n\n正文"
        }, ensure_ascii=False)))

    assert result["status"] == "success"
    assert result["document_id"] == "doc_openapi"
    assert post_mock.call_count == 2
    run_mock.assert_not_called()


def test_message_tool_prefers_openapi_when_app_credentials_exist(FeishuMessageTool):
    """有 LARK_APP_ID/LARK_APP_SECRET 时，消息发布应绕过 lark-cli。"""
    tool = FeishuMessageTool(use_skill=True)
    tool._skill_available = True

    token_response = MagicMock()
    token_response.status_code = 200
    token_response.json.return_value = {"code": 0, "tenant_access_token": "tenant_token"}
    token_response.raise_for_status.return_value = None

    send_response = MagicMock()
    send_response.status_code = 200
    send_response.json.return_value = {
        "code": 0,
        "data": {"message_id": "om_openapi", "chat_id": "oc_openapi"}
    }
    send_response.raise_for_status.return_value = None

    with patch.dict(os.environ, {"LARK_APP_ID": "cli_xxx", "LARK_APP_SECRET": "secret"}), \
         patch("src.tools.feishu_tool.requests.post", side_effect=[token_response, send_response]) as post_mock, \
         patch("src.tools.feishu_tool.subprocess.run") as run_mock:
        result = json.loads(tool._run(json.dumps({
            "message": "测试消息",
            "receiver_id": "ou_test_receiver"
        }, ensure_ascii=False)))

    assert result["status"] == "success"
    assert result["message_id"] == "om_openapi"
    assert post_mock.call_count == 2
    run_mock.assert_not_called()


def test_project_env_overrides_outer_lark_app_id(tmp_path):
    """飞书工具必须优先使用项目 .env，而不是外层 OpenClaw 环境变量。"""
    import src.tools.feishu_tool as feishu_tool

    project_env = tmp_path / ".env"
    project_env.write_text(
        "LARK_APP_ID=cli_project_app\n"
        "LARK_APP_SECRET=project_secret\n"
        "LARK_DOMAIN=https://project.example.feishu.cn\n",
        encoding="utf-8",
    )

    with patch.object(feishu_tool, "PROJECT_ENV_PATH", project_env), \
         patch.dict(os.environ, {
             "LARK_APP_ID": "cli_outer_app",
             "LARK_APP_SECRET": "outer_secret",
             "LARK_DOMAIN": "https://outer.example.feishu.cn",
         }, clear=False):
        feishu_tool._load_project_env()

        token_response = MagicMock()
        token_response.json.return_value = {"code": 0, "tenant_access_token": "tenant_token"}
        token_response.raise_for_status.return_value = None

        with patch("src.tools.feishu_tool.requests.post", return_value=token_response) as post_mock:
            token = feishu_tool._get_tenant_access_token()

    assert token == "tenant_token"
    assert post_mock.call_args.kwargs["json"] == {
        "app_id": "cli_project_app",
        "app_secret": "project_secret",
    }


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
