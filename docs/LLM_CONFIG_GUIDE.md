# LLM 配置指南

本项目支持多种大模型提供商，包括官方 OpenAI API、OpenAI 兼容的第三方 API、Azure OpenAI 和 Anthropic Claude。

**重要：必须显式选择一个 LLM 提供商，没有默认选项。**

---

## 质量控制配置

除了 LLM 配置，还可以调整以下质量控制参数：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `MAX_REVIEW_ITERATIONS` | 最大审核迭代次数 | 2 |
| `PASSING_SCORE` | 通过评分阈值（0-100） | 95 |

**配置示例：**

```bash
MAX_REVIEW_ITERATIONS=3
PASSING_SCORE=90
```

## 目录

- [快速开始](#快速开始)
- [配置方式详解](#配置方式详解)
  - [1. 官方 OpenAI API](#1-官方-openai-api)
  - [2. OpenAI 兼容第三方 API](#2-openai-兼容第三方-api)
  - [3. Azure OpenAI](#3-azure-openai)
  - [4. Anthropic Claude](#4-anthropic-claude)
- [国内模型配置示例](#国内模型配置示例)
  - [通义千问](#通义千问)
  - [智谱 AI](#智谱-ai)
  - [豆包（火山引擎）](#豆包火山引擎)
- [常见问题](#常见问题)

---

## 快速开始

1. 复制 `.env.example` 为 `.env`
2. 选择一种配置方式，设置对应的 `USE_*=true` 并填写配置项
3. **必须**设置模型名称，没有默认值
4. 运行项目：`poetry run python src/main.py`

---

## 配置方式详解

### 1. 官方 OpenAI API

使用 OpenAI 官方 API。

**配置示例：**

```bash
# 在 .env 文件中
USE_OPENAI=true
USE_OPENAI_COMPATIBLE=false
USE_AZURE_OPENAI=false
USE_ANTHROPIC=false

OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL_NAME=gpt-4o  # 必须显式指定
```

**可用模型：**
- `gpt-4o`（推荐）
- `gpt-4-turbo`
- `gpt-4`
- `gpt-3.5-turbo`

---

### 2. OpenAI 兼容第三方 API

支持所有兼容 OpenAI API 格式的第三方服务，包括国内的大部分大模型服务。

**配置示例：**

```bash
# 在 .env 文件中
USE_OPENAI=false
USE_OPENAI_COMPATIBLE=true
USE_AZURE_OPENAI=false
USE_ANTHROPIC=false

OPENAI_COMPATIBLE_BASE_URL=https://api.example.com/v1
OPENAI_COMPATIBLE_API_KEY=your-api-key-here
OPENAI_COMPATIBLE_MODEL_NAME=your-model-name  # 必须显式指定
```

---

### 3. Azure OpenAI

使用微软 Azure 的 OpenAI 服务。

**配置示例：**

```bash
# 在 .env 文件中
USE_OPENAI=false
USE_OPENAI_COMPATIBLE=false
USE_AZURE_OPENAI=true
USE_ANTHROPIC=false

AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-azure-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name  # 必须显式指定
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

---

### 4. Anthropic Claude

使用 Anthropic 的 Claude 模型。

**前置要求：** 需要安装额外的依赖包：

```bash
# 方式一：使用 Poetry 安装
poetry add langchain-anthropic

# 方式二：安装可选依赖组
poetry install -E anthropic
```

**配置示例：**

```bash
# 在 .env 文件中
USE_OPENAI=false
USE_OPENAI_COMPATIBLE=false
USE_AZURE_OPENAI=false
USE_ANTHROPIC=true

ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_MODEL_NAME=claude-3-5-sonnet-20241022  # 必须显式指定
```

**可用模型：**
- `claude-3-5-sonnet-20241022`（推荐）
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`

---

## 国内模型配置示例

### 通义千问

阿里云的通义千问提供 OpenAI 兼容的 API。

```bash
USE_OPENAI_COMPATIBLE=true
USE_OPENAI=false
USE_AZURE_OPENAI=false
USE_ANTHROPIC=false

OPENAI_COMPATIBLE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_COMPATIBLE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_COMPATIBLE_MODEL_NAME=qwen-plus
```

**可用模型：**
- `qwen-max`（最高质量）
- `qwen-plus`（平衡质量与速度）
- `qwen-turbo`（最快速度）
- `qwen-long`（长文本）

---

### 智谱 AI

智谱 AI 的 GLM 系列模型提供 OpenAI 兼容的 API。

```bash
USE_OPENAI_COMPATIBLE=true
USE_OPENAI=false
USE_AZURE_OPENAI=false
USE_ANTHROPIC=false

OPENAI_COMPATIBLE_BASE_URL=https://open.bigmodel.cn/api/paas/v4
OPENAI_COMPATIBLE_API_KEY=your-api-key-here
OPENAI_COMPATIBLE_MODEL_NAME=glm-4
```

**可用模型：**
- `glm-4`
- `glm-3-turbo`
- `code-llama`

---

### 豆包（火山引擎）

字节跳动的豆包模型（火山引擎）。

```bash
USE_OPENAI_COMPATIBLE=true
USE_OPENAI=false
USE_AZURE_OPENAI=false
USE_ANTHROPIC=false

OPENAI_COMPATIBLE_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
OPENAI_COMPATIBLE_API_KEY=your-api-key-here
OPENAI_COMPATIBLE_MODEL_NAME=ep-20240605xxxxxx-xxxxx
```

**注意：** 火山引擎需要先创建模型接入点（Endpoint）。

---

### 其他 OpenAI 兼容服务

任何兼容 OpenAI API 格式的服务都可以使用，包括：

- **One API / New API**：多模型聚合网关
- **本地模型部署**：如 Llama.cpp、Ollama、vLLM 等
- **其他云服务商**：腾讯云、华为云等

---

## 本地模型配置

### 使用 Ollama

如果你已经安装了 Ollama 并在本地运行模型：

```bash
USE_OPENAI_COMPATIBLE=true
USE_OPENAI=false
USE_AZURE_OPENAI=false
USE_ANTHROPIC=false

OPENAI_COMPATIBLE_BASE_URL=http://localhost:11434/v1
OPENAI_COMPATIBLE_API_KEY=ollama
OPENAI_COMPATIBLE_MODEL_NAME=llama3
```

**前置步骤：**
1. 安装 Ollama：https://ollama.com/
2. 拉取模型：`ollama pull llama3`
3. 启动 Ollama 服务

---

### 使用 Llama.cpp 或 vLLM

如果你使用 Llama.cpp 或 vLLM 部署本地模型并提供 OpenAI 兼容接口：

```bash
USE_OPENAI_COMPATIBLE=true
USE_OPENAI=false
USE_AZURE_OPENAI=false
USE_ANTHROPIC=false

OPENAI_COMPATIBLE_BASE_URL=http://localhost:8000/v1
OPENAI_COMPATIBLE_API_KEY=not-needed
OPENAI_COMPATIBLE_MODEL_NAME=your-model-name
```

---

## 配置说明

### 必须显式选择

- 不能同时选择多个 `USE_*=true`
- 不能所有 `USE_*` 都为 `false`
- 必须显式指定模型名称，没有默认值

### 配置验证

启动时会自动验证配置：
- 检查是否选择了且仅选择了一个提供商
- 检查必要的配置项是否都已填写
- 检查所需的依赖包是否已安装

---

## 常见问题

### Q: 如何验证我的配置是否正确？

A: 运行项目时，系统会自动验证配置并显示当前使用的 LLM 提供商和模型名称。如果配置有误，会显示具体的错误信息。

### Q: 可以同时使用多个 LLM 提供商吗？

A: 不行，每次只能选择一个提供商。如果需要切换，修改 `.env` 文件后重启项目即可。

### Q: 我想为不同的 Agent 使用不同的模型怎么办？

A: 可以修改 `src/main.py` 中的 `IndustryResearchCrew` 类，为不同的 Agent 传入不同配置的 LLM。

### Q: 遇到连接超时怎么办？

A: 
1. 检查网络连接
2. 如果是国内访问 OpenAI，可能需要使用代理
3. 考虑使用国内的模型服务（如通义千问、智谱 AI 等）

### Q: 如何添加新的 LLM 提供商？

A: 可以修改 `src/tools/llm_config.py` 文件，添加新的 LLM 提供商支持。

### Q: 为什么没有默认模型？

A: 为了避免用户意外使用不符合预期的模型或产生不必要的费用，要求所有配置都显式指定。

---

## 获取帮助

如果遇到问题：

1. 检查 `.env` 配置是否正确，确保选择了且仅选择了一个 `USE_*=true`
2. 确保模型名称已显式设置
3. 查看错误信息中的提示
4. 确认所需的依赖包已安装
5. 检查 API Key 是否有效且有足够额度
