# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于 CrewAI 的行业研究报告生成系统，采用多代理协作模式完成从数据采集到报告发布的全流程。

## 技术栈

- **框架**: CrewAI
- **语言**: Python 3.10+
- **依赖管理**: Poetry
- **搜索**: byted-web-search技能
- **企业集成**: 飞书 (Lark)

## 常用命令

```bash
# 安装依赖
poetry install

# 运行项目
poetry run python src/main.py

# 运行测试
poetry run pytest

# 代码格式化
poetry run black src/ tests/
poetry run isort src/ tests/
```

## 项目架构

### 核心文件

- `src/main.py` - 主入口，包含完整的代理和工作流定义
- `src/tools/search_tool.py` - 网络搜索工具（支持byted-web-search技能）
- `src/tools/feishu_tool.py` - 飞书文档和消息工具（支持lark-doc/lark-im技能）
- `src/tools/config.py` - 工具配置管理

### 代理角色

1. **数据采集员1** - 市场数据采集（规模、趋势、份额）
2. **数据采集员2** - 技术趋势采集（技术发展、创新、研发）
3. **数据采集员3** - 竞争格局采集（企业、产品、策略）
4. **数据分析师** - 交叉验证、清洗去重
5. **报告撰写师** - 撰写报告、迭代修改
6. **报告评价师** - 质量审核（≥95分通过）
7. **报告发布师** - 飞书平台发布

### 工作流程

```
阶段1: 并行数据采集（3个采集员同时工作）
   ↓
阶段2: 数据验证与分析（分析师处理）
   ↓
阶段3: 报告撰写与审核循环（最多3次迭代）
   ↓
阶段4: 报告发布（飞书平台）
```

## 飞书Skills集成

项目预置了飞书集成功能，可使用以下Skills：

- `lark-doc` - 创建和管理飞书文档
- `lark-im` - 发送飞书消息通知
- `lark-contact` - 查询用户信息
- `lark-markdown` - 处理Markdown内容

详见 `docs/SKILLS_INTEGRATION_GUIDE.md` 中的集成说明。
