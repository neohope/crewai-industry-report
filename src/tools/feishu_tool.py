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
from html import escape
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, List, Optional
import requests
from dotenv import load_dotenv
from crewai.tools import BaseTool
from pydantic import PrivateAttr


# 飞书工具经常在 OpenClaw/调试器等外层进程中被单独导入；这些外层进程
# 也可能设置了 LARK_APP_ID/LARK_APP_SECRET。必须显式加载“项目根目录”的
# .env，并允许其覆盖外部环境变量，避免发布时误用其他应用的 app id。
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ENV_PATH = PROJECT_ROOT / ".env"


def _load_project_env() -> None:
    """加载项目根目录 .env，并覆盖外层进程环境变量。"""
    load_dotenv(PROJECT_ENV_PATH, override=True)


_load_project_env()


class LarkCommandError(Exception):
    """飞书命令执行错误"""
    pass


def _get_lark_api_base() -> str:
    """获取飞书 OpenAPI Base URL。

    LARK_DOMAIN 在旧配置里可能用于文档域名或 OpenAPI 域名；这里做保守处理：
    - 未配置时使用官方 OpenAPI 域名
    - 配置了 feishu.cn/larksuite.com 但不是 open-apis 域名时，仍使用官方 OpenAPI 域名
    """
    domain = (os.getenv("LARK_DOMAIN") or "").strip().rstrip("/")
    if domain and "open.feishu.cn" in domain:
        return domain
    if domain and "open.larksuite.com" in domain:
        return domain
    return "https://open.feishu.cn"


def _get_lark_web_base() -> str:
    """获取飞书文档网页域名，用于拼接 docx URL。"""
    domain = (os.getenv("LARK_DOMAIN") or "").strip().rstrip("/")
    if domain and "open.feishu.cn" not in domain and "open.larksuite.com" not in domain:
        return domain
    return "https://feishu.cn"


def _get_tenant_access_token() -> str:
    """使用项目 .env 中的自建应用凭据获取 tenant_access_token。"""
    app_id = os.getenv("LARK_APP_ID")
    app_secret = os.getenv("LARK_APP_SECRET")
    if not app_id or not app_secret:
        raise LarkCommandError("缺少 LARK_APP_ID 或 LARK_APP_SECRET")

    url = f"{_get_lark_api_base()}/open-apis/auth/v3/tenant_access_token/internal"
    response = requests.post(
        url,
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("code") != 0:
        raise LarkCommandError(f"获取 tenant_access_token 失败: {data}")
    token = data.get("tenant_access_token")
    if not token:
        raise LarkCommandError(f"tenant_access_token 为空: {data}")
    return token


def _resolve_open_id_by_contact(token: str) -> Optional[str]:
    """通过邮箱/手机号换取当前 app 下的 open_id。

    飞书 open_id 是 app 维度的，不能跨 app 复用。若 .env 中只保存了另一个
    app 下的 ou_xxx，当前项目 app 发送 IM 会报 `open_id cross app`。
    推荐在 .env 中配置 LARK_RECEIVER_EMAIL 或 LARK_RECEIVER_MOBILE，
    由当前项目 app 实时换取自己的 open_id。
    """
    email = (os.getenv("LARK_RECEIVER_EMAIL") or "").strip()
    mobile = (os.getenv("LARK_RECEIVER_MOBILE") or "").strip()
    if not email and not mobile:
        return None

    body: dict[str, Any] = {"include_resigned": False}
    if email:
        body["emails"] = [email]
    if mobile:
        body["mobiles"] = [mobile]

    response = requests.post(
        f"{_get_lark_api_base()}/open-apis/contact/v3/users/batch_get_id",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        params={"user_id_type": "open_id"},
        json=body,
        timeout=30,
    )
    data = response.json()
    if response.status_code >= 400 or data.get("code") != 0:
        raise LarkCommandError(f"通过邮箱/手机号解析 open_id 失败: {data}")

    users = data.get("data", {}).get("user_list", [])
    if not users:
        raise LarkCommandError("通过邮箱/手机号未找到飞书用户")
    open_id = users[0].get("user_id")
    if not open_id:
        raise LarkCommandError(f"联系人解析结果缺少 open_id: {data}")
    return open_id


class FeishuDocumentTool(BaseTool):
    """飞书文档工具 - 优先使用lark-doc技能，不可用时回退到本地文件系统"""
    name: str = "feishu_document"
    description: str = "创建飞书文档并写入内容。输入：JSON格式，包含title和content。输出：文档URL和状态。"

    _use_skill: bool = PrivateAttr(default=True)
    _skill_available: bool = PrivateAttr(default=False)

    def __init__(self, use_skill: bool = True):
        super().__init__()
        self._use_skill = use_skill
        self._skill_available = self._check_lark_cli()

    @property
    def use_skill(self) -> bool:
        """是否优先使用飞书 CLI 技能（兼容旧代码/测试读取）。"""
        return self._use_skill

    @property
    def skill_available(self) -> bool:
        """飞书 CLI 是否可用（兼容旧代码/测试读取）。"""
        return self._skill_available

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
        def xml_text(text: str) -> str:
            """转义 XML 文本节点内容，标签本身不转义。"""
            return escape(text, quote=False).replace("\n", "<br/>")

        def inline_xml(text: str) -> str:
            """处理最基础的行内 Markdown 样式，并确保文本安全转义。"""
            # 当前目标是生成合法 DocxXML，优先保证不因 &, <, > 等字符导致 API invalid param。
            # 粗体/链接等复杂嵌套后续可继续增强；这里先安全保留原文语义。
            return xml_text(text)

        def flush_paragraph(paragraph_lines: list[str]) -> None:
            if paragraph_lines:
                paragraph = " ".join(line.strip() for line in paragraph_lines if line.strip())
                if paragraph:
                    blocks.append(f"<p>{inline_xml(paragraph)}</p>")
                paragraph_lines.clear()

        def flush_list(list_type: str | None, list_items: list[str]) -> None:
            if not list_type or not list_items:
                return
            if list_type == "ul":
                blocks.append("<ul>" + "".join(f"<li>{inline_xml(item)}</li>" for item in list_items) + "</ul>")
            else:
                blocks.append("<ol>" + "".join(f"<li seq=\"auto\">{inline_xml(item)}</li>" for item in list_items) + "</ol>")
            list_items.clear()

        def is_table_line(line: str) -> bool:
            stripped = line.strip()
            return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2

        def is_table_separator(line: str) -> bool:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            return bool(cells) and all(cell and set(cell) <= {"-", ":"} for cell in cells)

        def table_cells(line: str) -> list[str]:
            return [cell.strip() for cell in line.strip().strip("|").split("|")]

        def flush_table(table_lines: list[str]) -> None:
            if not table_lines:
                return

            rows = [table_cells(line) for line in table_lines if is_table_line(line)]
            if not rows:
                table_lines.clear()
                return

            # Markdown 表格第二行通常是 --- 分隔符。
            header = rows[0]
            body_rows = rows[1:]
            if len(table_lines) > 1 and is_table_separator(table_lines[1]):
                body_rows = rows[2:]

            header_xml = "".join(f"<th background-color=\"light-gray\">{inline_xml(cell)}</th>" for cell in header)
            body_xml = "".join(
                "<tr>" + "".join(f"<td>{inline_xml(cell)}</td>" for cell in row) + "</tr>"
                for row in body_rows
            )
            blocks.append(f"<table><thead><tr>{header_xml}</tr></thead><tbody>{body_xml}</tbody></table>")
            table_lines.clear()

        lines = content.split("\n")
        blocks = [f"<title>{xml_text(title)}</title>"]

        in_code_block = False
        code_language = ""
        code_content = []
        paragraph_lines: list[str] = []
        list_type: str | None = None
        list_items: list[str] = []
        table_lines: list[str] = []

        for line in lines:
            raw_line = line.rstrip()
            stripped = raw_line.strip()

            if stripped.startswith("```"):
                if in_code_block:
                    # 结束代码块
                    code_text = "\n".join(code_content)
                    blocks.append(f"<pre lang=\"{xml_text(code_language)}\"><code>{xml_text(code_text)}</code></pre>")
                    code_content = []
                    in_code_block = False
                else:
                    flush_paragraph(paragraph_lines)
                    flush_list(list_type, list_items)
                    list_type = None
                    flush_table(table_lines)
                    # 开始代码块
                    code_language = stripped[3:].strip() or "text"
                    in_code_block = True
            elif in_code_block:
                code_content.append(raw_line)
            elif is_table_line(stripped):
                flush_paragraph(paragraph_lines)
                flush_list(list_type, list_items)
                list_type = None
                table_lines.append(stripped)
            elif stripped.startswith("#"):
                flush_paragraph(paragraph_lines)
                flush_list(list_type, list_items)
                list_type = None
                flush_table(table_lines)
                # 标题
                level = min(len(stripped) - len(stripped.lstrip("#")), 6)
                heading_text = stripped.lstrip("#").strip()
                blocks.append(f"<h{level}>{inline_xml(heading_text)}</h{level}>")
            elif stripped.startswith("---") and set(stripped) <= {"-"}:
                flush_paragraph(paragraph_lines)
                flush_list(list_type, list_items)
                list_type = None
                flush_table(table_lines)
                blocks.append("<hr/>")
            elif stripped.startswith("- "):
                flush_paragraph(paragraph_lines)
                flush_table(table_lines)
                # 列表
                if list_type not in (None, "ul"):
                    flush_list(list_type, list_items)
                    list_type = None
                list_type = "ul"
                list_items.append(stripped[2:].strip())
            elif len(stripped) > 3 and stripped[0].isdigit() and stripped[1:3] == ". ":
                flush_paragraph(paragraph_lines)
                flush_table(table_lines)
                # 有序列表
                if list_type not in (None, "ol"):
                    flush_list(list_type, list_items)
                    list_type = None
                list_type = "ol"
                list_items.append(stripped[3:].strip())
            elif stripped == "":
                flush_paragraph(paragraph_lines)
                flush_list(list_type, list_items)
                list_type = None
                flush_table(table_lines)
                continue
            else:
                flush_list(list_type, list_items)
                list_type = None
                flush_table(table_lines)
                # 普通段落
                paragraph_lines.append(stripped)

        flush_paragraph(paragraph_lines)
        flush_list(list_type, list_items)
        flush_table(table_lines)

        if in_code_block and code_content:
            code_text = "\n".join(code_content)
            blocks.append(f"<pre lang=\"{xml_text(code_language or 'text')}\"><code>{xml_text(code_text)}</code></pre>")

        return "\n".join(blocks)

    def _parse_lark_doc_response(self, stdout: str, title: str) -> dict:
        """解析 lark-cli docs +create 的返回。

        不同版本 lark-cli/lark-doc skill 返回结构并不完全一致：
        - OpenAPI v2 可能返回 data.document.document_id/url
        - MCP create-doc 可能返回 document/url/docx_url 等字段
        因此这里做宽松解析，尽量提取 document_id 和 url。
        """
        try:
            response_data = json.loads(stdout)
        except json.JSONDecodeError:
            return {
                "status": "success",
                "title": title,
                "stdout": stdout,
                "message": "文档创建命令执行成功，但返回不是JSON，需人工查看stdout。"
            }

        if response_data.get("ok") is False:
            return {
                "status": "error",
                "error": response_data.get("error") or response_data,
                "stdout": stdout,
                "message": "飞书文档创建失败"
            }

        candidates = [
            response_data,
            response_data.get("data", {}),
            response_data.get("data", {}).get("document", {}),
            response_data.get("document", {}),
            response_data.get("result", {}),
        ]

        document_id = None
        url = None
        for item in candidates:
            if not isinstance(item, dict):
                continue
            document_id = document_id or item.get("document_id") or item.get("doc_token") or item.get("token")
            url = url or item.get("url") or item.get("doc_url") or item.get("document_url")

        return {
            "status": "success",
            "title": title,
            "document_id": document_id,
            "url": url,
            "raw": response_data,
            "message": f"文档已成功创建: {url or document_id or '请查看raw返回'}"
        }

    def _create_doc_with_openapi(self, title: str, content: str) -> dict:
        """使用飞书 OpenAPI 直接创建文档，避免依赖 lark-cli/TAT。"""
        try:
            token = _get_tenant_access_token()
            xml_content = self._convert_to_lark_xml(title, content)
            url = f"{_get_lark_api_base()}/open-apis/docs_ai/v1/documents"
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json; charset=utf-8",
                },
                json={
                    "content": xml_content,
                    "format": "xml",
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("code") not in (0, None):
                return {
                    "status": "error",
                    "error": data,
                    "message": "飞书 OpenAPI 创建文档失败",
                }

            doc_data = data.get("data", {}).get("document", {}) or data.get("data", {})
            document_id = (
                doc_data.get("document_id")
                or doc_data.get("doc_token")
                or doc_data.get("token")
            )
            doc_url = doc_data.get("url") or doc_data.get("document_url")
            if not doc_url and document_id:
                doc_url = f"{_get_lark_web_base()}/docx/{document_id}"

            if not document_id and not doc_url:
                return {
                    "status": "error",
                    "error": data,
                    "message": "飞书 OpenAPI 返回中未找到 document_id/url",
                }

            return {
                "status": "success",
                "title": title,
                "document_id": document_id,
                "url": doc_url,
                "raw": data,
                "message": f"文档已成功创建: {doc_url or document_id}",
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "飞书 OpenAPI 创建文档异常",
            }

    def _create_doc_with_skill(self, title: str, content: str, folder_token: str = None) -> dict:
        """使用lark-doc技能创建文档"""
        if not self._skill_available:
            return {
                "status": "error",
                "error": "lark-cli不可用",
                "message": "飞书技能不可用，请使用本地模式"
            }

        tmp_path = None
        try:
            # 当前环境 lark-cli 1.0.44 的 docs +create 有两条路径：
            # - 默认 v1/MCP：使用 --markdown，但会走 TAT 鉴权，本机报 TAT API error [10003]
            # - OpenAPI v2：必须显式传 --api-version v2，并使用 --content（DocxXML）
            # 因此这里固定走 OpenAPI v2 + DocxXML。
            xml_content = self._convert_to_lark_xml(title, content)
            tmp_dir = Path(".lark_tmp")
            tmp_dir.mkdir(exist_ok=True)
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".xml",
                prefix="doc_create_",
                dir=tmp_dir,
                delete=False,
            ) as tmp_file:
                tmp_file.write(xml_content)
                tmp_path = Path(tmp_file.name)

            content_file_arg = Path(os.path.relpath(tmp_path, Path.cwd())).as_posix()

            cmd = [
                "lark-cli", "docs", "+create",
                "--api-version", "v2",
                "--title", title,
                "--content", f"@{content_file_arg}",
            ]

            if folder_token:
                cmd.extend(["--folder-token", folder_token])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120
            )

            if result.returncode == 0:
                parsed = self._parse_lark_doc_response(result.stdout, title)
                if parsed.get("status") == "success":
                    return parsed

            return {
                "status": "error",
                "error": result.stderr or result.stdout or "未知错误",
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
        finally:
            if tmp_path:
                try:
                    tmp_path.unlink(missing_ok=True)
                except Exception:
                    pass

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

        # 优先使用项目自有飞书 OpenAPI 凭据，避免 lark-cli 的 TAT 鉴权链路问题。
        # 若项目 OpenAPI 失败，直接返回错误，不再 fallback 到 lark-cli，避免误用外层 OpenClaw app。
        if os.getenv("LARK_APP_ID") and os.getenv("LARK_APP_SECRET"):
            result = self._create_doc_with_openapi(title, content)
            return json.dumps(result, ensure_ascii=False)

        if self._use_skill and self._skill_available:
            result = self._create_doc_with_skill(title, content, folder_token)
            if result.get("status") == "success":
                return json.dumps(result, ensure_ascii=False)
            else:
                print(f"飞书技能失败，回退到本地保存：{result.get('error')}")

        result = self._save_local(title, content)
        return json.dumps(result, ensure_ascii=False)


class FeishuMessageTool(BaseTool):
    """飞书消息工具 - 优先使用lark-im技能，不可用时回退到本地日志"""
    name: str = "feishu_message"
    description: str = "发送飞书消息通知。输入：JSON格式，包含message和可选的receiver_id/chat_id。输出：发送状态。"

    _use_skill: bool = PrivateAttr(default=True)
    _skill_available: bool = PrivateAttr(default=False)

    def __init__(self, use_skill: bool = True):
        super().__init__()
        self._use_skill = use_skill
        self._skill_available = self._check_lark_cli()

    @property
    def use_skill(self) -> bool:
        """是否优先使用飞书 CLI 技能（兼容旧代码/测试读取）。"""
        return self._use_skill

    @property
    def skill_available(self) -> bool:
        """飞书 CLI 是否可用（兼容旧代码/测试读取）。"""
        return self._skill_available

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
        if not self._skill_available:
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

    def _send_message_with_openapi(self, message: str, chat_id: str = None, user_id: str = None) -> dict:
        """使用飞书 OpenAPI 直接发送文本消息。"""
        if not chat_id and not user_id:
            return {
                "status": "error",
                "error": "缺少接收者信息",
                "message": "请提供chat_id或user_id"
            }

        try:
            token = _get_tenant_access_token()
            receive_id_type = "chat_id" if chat_id else "open_id"
            receive_id = chat_id or _resolve_open_id_by_contact(token) or user_id
            url = f"{_get_lark_api_base()}/open-apis/im/v1/messages"
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json; charset=utf-8",
                },
                params={"receive_id_type": receive_id_type},
                json={
                    "receive_id": receive_id,
                    "msg_type": "text",
                    "content": json.dumps({"text": message}, ensure_ascii=False),
                },
                timeout=60,
            )
            try:
                data = response.json()
            except Exception:
                data = {"http_status": response.status_code, "text": response.text}
            if response.status_code >= 400 or data.get("code") != 0:
                return {
                    "status": "error",
                    "error": data,
                    "message": "飞书 OpenAPI 消息发送失败",
                }

            msg_data = data.get("data", {})
            return {
                "status": "success",
                "message_id": msg_data.get("message_id"),
                "chat_id": msg_data.get("chat_id"),
                "raw": data,
                "message": "消息发送成功",
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "飞书 OpenAPI 消息发送异常",
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
        # 兼容任务提示里的 receiver_id 字段；飞书 CLI 的 --user-id 需要 open_id（ou_xxx）。
        user_id = input_data.get("user_id") or input_data.get("receiver_id")

        if not user_id and not chat_id:
            user_id = os.getenv("LARK_RECEIVER_ID")

        # 优先使用项目自有飞书 OpenAPI 凭据，避免 lark-cli 的 TAT 鉴权链路问题。
        # 若 OpenAPI 失败，不再 fallback 到 lark-cli，避免误用外层 OpenClaw app。
        if os.getenv("LARK_APP_ID") and os.getenv("LARK_APP_SECRET"):
            result = self._send_message_with_openapi(message, chat_id, user_id)
            return json.dumps(result, ensure_ascii=False)

        if self._use_skill and self._skill_available:
            result = self._send_message_with_skill(message, chat_id, user_id)
            if result.get("status") == "success":
                return json.dumps(result, ensure_ascii=False)
            else:
                print(f"飞书技能失败，回退到本地日志：{result.get('error')}")

        result = self._log_message(message, user_id or chat_id)
        return json.dumps(result, ensure_ascii=False)
