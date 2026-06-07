# 飞书功能实现总结

## 概述

`feishu_tool.py` 已实现飞书文档创建和消息通知。当前版本优先使用项目 `.env` 中的飞书自建应用凭据直接调用飞书 OpenAPI；`lark-cli` 仅作为未配置应用凭据时的 fallback。

这样做是为了避免调试器、OpenClaw 或其他外层进程预先设置的 `LARK_APP_ID` / `LARK_APP_SECRET` 污染项目发布身份。工具导入时会显式加载项目根目录 `.env`，并使用 `override=True` 覆盖外层环境变量。

## 功能实现

### FeishuDocumentTool - 文档工具

#### 功能

- 优先使用飞书 OpenAPI 创建飞书文档
- 未配置 `LARK_APP_ID` / `LARK_APP_SECRET` 时，可 fallback 到 `lark-cli`
- 本地文件系统作为最终备选方案
- 支持 Markdown 内容转换为飞书 DocxXML

#### 实现细节

1. **项目 `.env` 强制加载**
   ```python
   PROJECT_ROOT = Path(__file__).resolve().parents[2]
   PROJECT_ENV_PATH = PROJECT_ROOT / ".env"
   load_dotenv(PROJECT_ENV_PATH, override=True)
   ```

2. **获取 tenant_access_token**
   ```python
   POST /open-apis/auth/v3/tenant_access_token/internal
   ```

3. **飞书文档创建**
   ```python
   POST /open-apis/docs_ai/v1/documents
   ```
   请求体使用：
   ```json
   {
     "content": "<title>...</title>...",
     "format": "xml"
   }
   ```

4. **Markdown → DocxXML 转换**
   ```python
   def _convert_to_lark_xml(self, title: str, content: str) -> str
   ```
   支持：
   - 标题（h1-h6）
   - 段落
   - 分割线
   - 无序/有序列表
   - Markdown 表格
   - 代码块
   - XML 文本节点转义，避免 `&` / `<` / `>` 导致 invalid param

5. **`lark-cli` fallback**
   仅在未配置 `LARK_APP_ID` / `LARK_APP_SECRET` 时使用：
   ```bash
   lark-cli docs +create --api-version v2 --title <title> --content @.lark_tmp/<file>.xml
   ```

### FeishuMessageTool - 消息工具

#### 功能

- 优先使用飞书 OpenAPI 发送文本消息
- 支持群聊（`chat_id`）和单聊（`receiver_id` / `user_id`）
- 支持用 `LARK_RECEIVER_EMAIL` 或 `LARK_RECEIVER_MOBILE` 自动解析当前 app 下的 `open_id`
- 未配置应用凭据时可 fallback 到 `lark-cli`
- 本地日志记录作为最终备选方案

#### 实现细节

1. **消息发送**
   ```python
   POST /open-apis/im/v1/messages?receive_id_type=open_id
   POST /open-apis/im/v1/messages?receive_id_type=chat_id
   ```

2. **接收者解析**

   飞书 `open_id` 是 app 维度的，不能跨 app 复用。如果 `.env` 中的 `LARK_RECEIVER_ID` 属于其他 app，发送消息会返回：

   ```json
   {"code": 99992361, "msg": "open_id cross app"}
   ```

   推荐配置：

   ```env
   LARK_RECEIVER_EMAIL=your.name@example.com
   # 或
   LARK_RECEIVER_MOBILE=13800000000
   ```

   工具会调用：

   ```python
   POST /open-apis/contact/v3/users/batch_get_id?user_id_type=open_id
   ```

   用当前项目 app 换取正确的 `open_id`。

3. **本地日志记录**
   ```python
   def _log_message(self, message: str, receiver_id: str = None) -> dict
   ```
   日志文件：`message_log.jsonl`。

## 配置选项

| 变量 | 说明 | 默认 |
|------|------|------|
| `LARK_DOMAIN` | 飞书文档网页域名或 OpenAPI 域名 | `https://open.feishu.cn` / `https://feishu.cn` |
| `LARK_APP_ID` | 飞书自建应用 ID | - |
| `LARK_APP_SECRET` | 飞书自建应用密钥 | - |
| `LARK_RECEIVER_ID` | 当前 app 下的接收者 open_id | - |
| `LARK_RECEIVER_EMAIL` | 用于解析当前 app 下 open_id 的邮箱 | - |
| `LARK_RECEIVER_MOBILE` | 用于解析当前 app 下 open_id 的手机号 | - |
| `LARK_FOLDER_TOKEN` | 默认文档文件夹 Token（保留字段） | - |

## 使用示例

```python
import json
from src.tools.feishu_tool import FeishuDocumentTool, FeishuMessageTool

# 创建文档
doc_result = FeishuDocumentTool()._run(json.dumps({
    "title": "报告标题",
    "content": "# 报告内容\n\n正文..."
}, ensure_ascii=False))

# 发送消息
msg_result = FeishuMessageTool()._run(json.dumps({
    "message": "报告已发布",
    "receiver_id": "ou_xxx"
}, ensure_ascii=False))
```

## 测试

```bash
.venv/bin/python -m pytest tests/test_feishu_tools.py -q
```

测试覆盖：

1. 模块导入
2. 文档创建工具
3. 消息发送工具
4. OpenAPI 优先于 `lark-cli`
5. 项目 `.env` 覆盖外层环境变量
6. `receiver_id` 兼容
7. `lark-cli` fallback 参数

## 故障排除

### `open_id cross app`

原因：`LARK_RECEIVER_ID` 不是当前 `LARK_APP_ID` 对应 app 下的 open_id。

解决：

1. 将 `LARK_RECEIVER_ID` 改成当前 app 下的 open_id；或
2. 配置 `LARK_RECEIVER_EMAIL` / `LARK_RECEIVER_MOBILE`，让工具自动解析。

### `TAT API error: [10003] invalid param`

原因：当前环境中的 `lark-cli` 鉴权链路不可用或使用了错误身份。

解决：配置项目自己的 `LARK_APP_ID` / `LARK_APP_SECRET`，走项目 OpenAPI 路径。

## 后续优化建议

1. 支持文件夹 Token 的 OpenAPI 移动/归档逻辑。
2. 增强 Markdown 行内格式转换，如加粗、链接、引用。
3. 增加文档创建后权限授予逻辑。
4. 支持富文本消息卡片。
