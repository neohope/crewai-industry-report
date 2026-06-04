"""
飞书工具模块 - 完整实现：支持lark-doc和lark-im技能，同时有本地文件系统作为后备
"""
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from crewai.tools import BaseTool


class LarkCommandError(Exception):
    """飞书命令执行错误"""
    pass


class FeishuDocumentTool(BaseTool):
    """飞书文档工具 - 优先使用lark-doc技能，不可用时回退到本地文件系统"""
    name = "feishu_document"
    description = "创建飞书文档并写入内容。输入：JSON格式，包含title和content。输出：文档URL和状态。"

    def __init__(self, use_skill: bool = True):
        self.use_skill = use_skill
        self.skill_available = self._check_lark_cli()
        super().__init__()

    def _check_lark_cli(self) -> bool:
        """检查lark-cli是否可用"""
        try:
            result = subprocess.run(
                ["lark-cli", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _convert_to_lark_xml(self, title: str, content: str) -> str:
        """将Markdown内容转换为飞书XML格式"""
        # 简单转换：提取标题，处理基础格式
        lines = content.split("\n")
        blocks = [f"<title>{title}</title>"]

        in_code_block = False
        code_language = ""
        code_content = []

        for line in lines:
            line = line.strip()

            if line.startswith("```"):
                if in_code_block:
                    # 结束代码块
                    code_text = "\n".join(code_content)
                    blocks.append(f"<code language=\"{code_language}\">{code_text}</code>")
                    code_content = []
                    in_code_block = False
                else:
                    # 开始代码块
                    code_language = line[3:].strip() or "text"
                    in_code_block = True
            elif in_code_block:
                code_content.append(line)
            elif line.startswith("#"):
                # 标题
                level = min(len(line) - len(line.lstrip("#")), 6)
                heading_text = line.lstrip("#").strip()
                blocks.append(f"<h{level}>{heading_text}</h{level}>")
            elif line.startswith("- "):
                # 列表
                list_item = line[2:].strip()
                blocks.append(f"<ul><li>{list_item}</li></ul>")
            elif line.startswith("1. "):
                # 有序列表
                list_item = line[3:].strip()
                blocks.append(f"<ol><li>{list_item}</li></ol>")
            elif line == "":
                continue
            else:
                # 普通段落
                blocks.append(f"<p>{line}</p>")

        return "".join(blocks)

    def _create_doc_with_skill(self, title: str, content: str, folder_token: str = None) -> dict:
        """使用lark-doc技能创建文档"""
        if not self.skill_available:
            return {
                "status": "error",
                "error": "lark-cli不可用",
                "message": "飞书技能不可用，请使用本地模式"
            }

        try:
            # 准备命令
            xml_content = self._convert_to_lark_xml(title, content)

            cmd = [
                "lark-cli", "docs", "+create",
                "--api-version", "v2",
                "--content", xml_content
            ]

            if folder_token:
                cmd.extend(["--parent-token", folder_token])

            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60
            )

            if result.returncode == 0:
                # 成功
                try:
                    response_data = json.loads(result.stdout)
                    if response_data.get("ok"):
                        doc_data = response_data.get("data", {}).get("document", {})
                        return {
                            "status": "success",
                            "title": title,
                            "document_id": doc_data.get("document_id"),
                            "url": doc_data.get("url"),
                            "message": f"文档已成功创建: {doc_data.get('url')}"
                        }
                except json.JSONDecodeError:
                    pass

            return {
                "status": "error",
                "error": result.stderr or "未知错误",
                "stdout": result.stdout,
                "message": "飞书文档创建失败"
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": "命令执行超时",
                "message": "飞书文档创建超时"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "飞书文档创建异常"
            }

    def _save_local(self, title: str, content: str) -> dict:
        """保存到本地文件系统"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).rstrip()
        if not safe_title:
            safe_title = "report"
        filename = f"{safe_title}_{timestamp}.md"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)

            return {
                "status": "success",
                "title": title,
                "local_file": filename,
                "full_path": str(Path(filename).absolute()),
                "message": f"文档已保存到本地文件：{filename}",
                "note": "飞书技能不可用，已保存到本地文件系统。"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "本地文件保存失败"
            }

    def _run(self, tool_input: str) -> str:
        """执行文档创建

        Args:
            tool_input: JSON格式字符串，包含title和content字段

        Returns:
            JSON格式的执行结果
        """
        try:
            input_data = json.loads(tool_input)
        except json.JSONDecodeError:
            input_data = {
                "title": "文档",
                "content": tool_input
            }

        title = input_data.get("title", "文档")
        content = input_data.get("content", "")
        folder_token = input_data.get("folder_token", os.getenv("LARK_FOLDER_TOKEN"))

        if self.use_skill and self.skill_available:
            result = self._create_doc_with_skill(title, content, folder_token)
            if result.get("status") == "success":
                return json.dumps(result, ensure_ascii=False)
            else:
                print(f"飞书技能失败，回退到本地保存：{result.get('error')}")

        result = self._save_local(title, content)
        return json.dumps(result, ensure_ascii=False)


class FeishuMessageTool(BaseTool):
    """飞书消息工具 - 优先使用lark-im技能，不可用时回退到本地日志"""
    name = "feishu_message"
    description = "发送飞书消息通知。输入：JSON格式，包含message和可选的receiver_id/chat_id。输出：发送状态。"

    def __init__(self, use_skill: bool = True):
        self.use_skill = use_skill
        self.skill_available = self._check_lark_cli()
        super().__init__()

    def _check_lark_cli(self) -> bool:
        """检查lark-cli是否可用"""
        try:
            result = subprocess.run(
                ["lark-cli", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _send_message_with_skill(self, message: str, chat_id: str = None, user_id: str = None) -> dict:
        """使用lark-im技能发送消息"""
        if not self.skill_available:
            return {
                "status": "error",
                "error": "lark-cli不可用",
                "message": "飞书技能不可用，请使用本地模式"
            }

        try:
            cmd = ["lark-cli", "im", "+messages-send"]

            if chat_id:
                cmd.extend(["--chat-id", chat_id])
            elif user_id:
                cmd.extend(["--user-id", user_id])
            else:
                return {
                    "status": "error",
                    "error": "缺少接收者信息",
                    "message": "请提供chat_id或user_id"
                }

            cmd.extend(["--text", message])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60
            )

            if result.returncode == 0:
                try:
                    response_data = json.loads(result.stdout)
                    return {
                        "status": "success",
                        "message_id": response_data.get("message_id"),
                        "chat_id": response_data.get("chat_id"),
                        "message": "消息发送成功"
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "success",
                        "message": "消息发送成功",
                        "stdout": result.stdout
                    }

            return {
                "status": "error",
                "error": result.stderr or "未知错误",
                "stdout": result.stdout,
                "message": "消息发送失败"
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": "命令执行超时",
                "message": "消息发送超时"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "消息发送异常"
            }

    def _log_message(self, message: str, receiver_id: str = None) -> dict:
        """记录消息到本地日志"""
        log_file = "message_log.jsonl"
        timestamp = datetime.now().isoformat()

        log_entry = {
            "timestamp": timestamp,
            "message": message,
            "receiver_id": receiver_id or os.getenv("LARK_RECEIVER_ID", "default_receiver"),
            "sent": False,
            "note": "消息已记录到本地日志，飞书技能未配置或不可用"
        }

        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            return {
                "status": "logged",
                "message": message,
                "receiver_id": log_entry["receiver_id"],
                "log_file": log_file,
                "note": "消息已记录到本地日志，飞书技能未配置或不可用。"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "日志记录失败"
            }

    def _run(self, tool_input: str) -> str:
        """执行消息发送

        Args:
            tool_input: JSON格式字符串，包含message和可选的receiver_id/chat_id

        Returns:
            JSON格式的执行结果
        """
        try:
            input_data = json.loads(tool_input)
        except json.JSONDecodeError:
            input_data = {
                "message": tool_input
            }

        message = input_data.get("message", "")
        chat_id = input_data.get("chat_id")
        user_id = input_data.get("user_id")

        if not user_id and not chat_id:
            user_id = os.getenv("LARK_RECEIVER_ID")

        if self.use_skill and self.skill_available:
            result = self._send_message_with_skill(message, chat_id, user_id)
            if result.get("status") == "success":
                return json.dumps(result, ensure_ascii=False)
            else:
                print(f"飞书技能失败，回退到本地日志：{result.get('error')}")

        result = self._log_message(message, user_id or chat_id)
        return json.dumps(result, ensure_ascii=False)
