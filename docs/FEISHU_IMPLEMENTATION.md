# 飞书功能实现总结

## 概述

已完成 `feishu_tool.py` 的完整实现，通过 lark-cli 调用。

## 功能实现

### FeishuDocumentTool - 文档工具

#### 功能
- 优先使用 lark-cli 创建飞书文档
- 本地文件系统作为后备方案
- 支持 Markdown 内容自动转换为飞书 XML 格式

#### 实现细节

1. **Lark CLI 检测**
   ```python
   def _check_lark_cli(self) -> bool
   ```
   自动检测 `lark-cli` 命令是否可用

2. **Markdown → XML 转换**
   ```python
   def _convert_to_lark_xml(self, title: str, content: str) -> str
   ```
   支持：
   - 标题（h1-h6）
   - 列表（ul/ol）
   - 代码块
   - 普通段落

3. **飞书文档创建**
   ```python
   def _create_doc_with_skill(self, title: str, content: str, folder_token: str = None) -> dict
   ```
   使用命令：
   ```bash
   lark-cli docs +create --api-version v2 --content <xml>
   lark-cli docs +create --api-version v2 --parent-token <folder> --content <xml>
   ```

4. **本地文件保存**
   ```python
   def _save_local(self, title: str, content: str) -> dict
   ```
   文件名格式：`title_YYYYMMDD_HHMMSS.md`

### FeishuMessageTool - 消息工具

#### 功能
- 优先使用 lark-cli 发送飞书消息
- 支持群聊（chat_id）和单聊（user_id）
- 本地日志记录作为后备方案

#### 实现细节

1. **消息发送**
   ```python
   def _send_message_with_skill(self, message: str, chat_id: str = None, user_id: str = None) -> dict
   ```
   使用命令：
   ```bash
   # 群聊
   lark-cli im +messages-send --chat-id <chat_id> --text <msg>

   # 单聊
   lark-cli im +messages-send --user-id <user_id> --text <msg>
   ```

2. **本地日志记录**
   ```python
   def _log_message(self, message: str, receiver_id: str = None) -> dict
   ```
   日志文件：`message_log.jsonl`（JSON Lines 格式）

## 配置选项

### 环境变量

| 变量 | 说明 | 默认 |
|------|------|------|
| `LARK_APP_ID` | 飞书应用 ID | - |
| `LARK_APP_SECRET` | 飞书应用密钥 | - |
| `LARK_RECEIVER_ID` | 默认接收者 ID | `default_receiver` |
| `LARK_FOLDER_TOKEN` | 默认文档文件夹 Token | - |

## 使用示例

### Python API 使用

```python
from src.tools.feishu_tool import FeishuDocumentTool, FeishuMessageTool

# 文档工具
doc_tool = FeishuDocumentTool()
result = doc_tool._run(json.dumps({
    "title": "报告标题",
    "content": "# 报告内容\n\n正文...",
    "folder_token": "fld_xxx"  # 可选
}))

# 消息工具
msg_tool = FeishuMessageTool()
result = msg_tool._run(json.dumps({
    "message": "消息内容",
    "chat_id": "oc_xxx"  # 或者用 user_id
}))
```

### CrewAI Agent 中的使用

```python
def create_report_publisher(self) -> Agent:
    return Agent(
        role="报告发布师",
        goal="将审核通过的最终报告发布到飞书文档平台，并发送消息通知相关人员",
        backstory="...",
        tools=[FeishuDocumentTool(), FeishuMessageTool()],
        allow_delegation=False,
        verbose=True
    )
```

## 测试

### 运行测试

```bash
# 使用已提供的测试脚本
python tests/test_feishu_tools.py

# 或者使用简单版本（需要安装依赖）
python test_feishu_simple.py
```

### 测试内容

1. 模块导入测试
2. 文档工具功能测试（创建文档、本地文件保存）
3. 消息工具功能测试（发送消息、日志记录）

## 回退机制

### 文档工具
```
lark-cli 可用
    ↓ (成功)
返回飞书文档 URL
    ↓ (失败)
尝试本地文件保存
```

### 消息工具
```
lark-cli 可用
    ↓ (成功)
返回消息发送结果
    ↓ (失败)
记录到本地日志
```

## Skill 路径

项目已包含以下技能：
- `skills/lark-doc/` - 飞书文档技能
- `skills/lark-im/` - 飞书即时消息技能
- `skills/lark-drive/` - 飞书云空间技能
- `skills/byted-web-search/` - 火山引擎搜索技能

## 参考文档

技能文档位于：
- `skills/lark-doc/references/`
- `skills/lark-im/references/`

关键参考：
- `lark-doc-create.md` - 文档创建命令
- `lark-im-messages-send.md` - 消息发送命令

## 后续优化建议

1. **身份选择**
   - 支持 `--as user` 或 `--as bot`
   - 提供配置选项

2. **更丰富的内容格式**
   - 支持图片插入
   - 支持画板
   - 支持表格

3. **更好的错误处理**
   - 提供具体的错误提示
   - 支持重试机制

4. **飞书 Drive 集成**
   - 支持上传文件
   - 支持文件夹管理
