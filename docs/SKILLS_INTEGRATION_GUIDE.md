# 技能集成指南

本项目已集成以下技能：

## 1. byted-web-search (火山引擎联网搜索)

### 状态
- ✅ 已集成到 `src/tools/search_tool.py`
- ✅ 完整配置选项

### 功能
- 网页搜索（WebSearch）
- 图片搜索（ImageSearch）
- 时间范围过滤
- 权威等级过滤
- 查询改写

### 配置
```env
# 是否使用byted-web-search技能（默认true）
USE_BYTED_WEB_SEARCH=true

# 默认搜索结果数
DEFAULT_MAX_RESULTS=10

# 权威等级（0=全部，1=仅权威来源）
DEFAULT_AUTH_LEVEL=0

# 是否启用查询改写
ENABLE_QUERY_REWRITE=false
```

### 获取API Key
1. 访问[火山引擎联网搜索控制台](https://console.volcengine.com/search-infinity/api-key)
2. 创建API Key
3. 在聊天窗口中直接发送API Key即可自动配置

### 使用方式
搜索工具会自动优先使用byted-web-search技能。

---

## 2. lark-doc (飞书文档)

### 状态
- ✅ 已集成到 `src/tools/feishu_tool.py`
- ✅ 本地文件系统作为后备方案
- ⏳ 技能具体实现需要进一步集成

### 功能
- 创建文档
- 读取文档
- 更新文档
- 媒体操作（上传/下载/预览）
- 画板操作

### 配置
```env
# 是否使用lark-doc技能（默认true）
USE_LARK_SKILL=true

# 飞书应用凭证
LARK_APP_ID=your-app-id
LARK_APP_SECRET=your-app-secret

# 默认文件夹Token（可选）
LARK_FOLDER_TOKEN=folder-token
```

### 注意事项
由于lark-doc技能需要特定的CLI工具和认证方式，当前版本使用本地文件系统作为后备方案。
如需完整的飞书文档功能，请先熟悉lark-doc技能的使用方式。

---

## 3. lark-drive (飞书云空间)

### 状态
- ✅ 技能目录已存在
- ⏳ 待进一步集成

### 功能
- 文件上传/下载
- 文件夹管理
- 搜索文档
- 评论管理
- 权限管理
- 版本控制

### 说明
lark-drive技能提供云空间管理功能，可用于存储和管理生成的报告文件。

---

## 4. lark-im (飞书即时通讯)

### 状态
- ✅ 已集成到 `src/tools/feishu_tool.py`
- ✅ 本地日志作为后备方案
- ⏳ 技能具体实现需要进一步集成

### 功能
- 发送消息
- 搜索聊天记录
- 管理群聊
- 表情回复
- 消息加急

### 配置
```env
# 飞书接收者ID
LARK_RECEIVER_ID=user@example.com
```

### 说明
当前版本使用本地日志系统记录消息通知，完整的飞书消息功能需要进一步集成lark-im技能。

---

## 架构设计

### 工具类设计

#### 搜索工具
```python
WebSearchTool:
  - 优先使用byted-web-search技能
  - 支持多种搜索参数

NewsSearchTool:
  - 支持新闻搜索
  - 同样的回退机制
```

#### 飞书工具
```python
FeishuDocumentTool:
  - 优先使用lark-doc技能
  - 失败时保存到本地文件系统

FeishuMessageTool:
  - 优先使用lark-im技能
  - 失败时记录到本地日志
```

### 配置管理
- 统一配置入口: `src/tools/config.py`
- 环境变量驱动
- 支持运行时配置变更
- 配置验证功能

---

## 扩展开发

### 添加新的技能支持

1. 在 `src/tools/` 下创建新的工具类
2. 继承 `BaseTool`
3. 实现 `_run` 方法
4. 添加配置选项
5. 实现后备方案

### 技能集成要点
- 提供优雅的回退机制
- 统一的错误处理
- 配置驱动的行为
- 完整的日志记录

---

## 故障排查

### byted-web-search技能不可用
- 检查是否有正确的API Key
- 检查网络连接

### lark技能不可用
- 检查飞书凭证配置
- 系统会自动使用本地文件系统/日志作为后备
- 确保相关目录有写入权限

---

## 下一步计划

1. 完全集成lark-cli工具
2. 添加技能认证流程
3. 实现更丰富的飞书文档操作
4. 添加技能使用统计
5. 优化错误处理和用户提示
