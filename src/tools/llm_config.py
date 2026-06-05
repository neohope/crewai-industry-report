"""
LLM 配置模块 - 支持多种大模型提供商
- 官方 OpenAI API（可选）
- OpenAI 兼容第三方 API（国内模型等）
- Azure OpenAI
- Anthropic Claude

注意：必须显式选择一种 LLM 提供商，没有默认选项。
"""
import os
from typing import Optional, Any
from dotenv import load_dotenv

# 尝试导入 LLM 库
try:
    from langchain_openai import ChatOpenAI, AzureChatOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from langchain_anthropic import ChatAnthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


load_dotenv()


class QualityConfig:
    """质量控制配置"""

    @staticmethod
    def max_review_iterations() -> int:
        """最大审核迭代次数，默认2次"""
        try:
            return int(os.getenv("MAX_REVIEW_ITERATIONS", "2"))
        except ValueError:
            return 2

    @staticmethod
    def passing_score() -> int:
        """通过评分阈值，默认95分"""
        try:
            return int(os.getenv("PASSING_SCORE", "95"))
        except ValueError:
            return 95


class LLMConfig:
    """LLM 配置管理器"""

    @staticmethod
    def get_llm(temperature: float = 0.7, **kwargs):
        """
        根据环境变量配置获取 LLM 实例

        Args:
            temperature: 温度参数，默认 0.7
            **kwargs: 其他传递给 LLM 的参数

        Returns:
            配置好的 LLM 实例

        Raises:
            ImportError: 如果所需的 LLM 库未安装
            ValueError: 如果配置不正确
        """
        # 检查是否选择了 LLM 提供商
        providers = []
        if os.getenv("USE_OPENAI", "false").lower() == "true":
            providers.append("OpenAI")
        if os.getenv("USE_OPENAI_COMPATIBLE", "false").lower() == "true":
            providers.append("OpenAI Compatible")
        if os.getenv("USE_AZURE_OPENAI", "false").lower() == "true":
            providers.append("Azure OpenAI")
        if os.getenv("USE_ANTHROPIC", "false").lower() == "true":
            providers.append("Anthropic")

        if len(providers) == 0:
            raise ValueError(
                "未选择 LLM 提供商！请在 .env 文件中设置以下选项之一：\n"
                "  USE_OPENAI=true\n"
                "  USE_OPENAI_COMPATIBLE=true\n"
                "  USE_AZURE_OPENAI=true\n"
                "  USE_ANTHROPIC=true"
            )

        if len(providers) > 1:
            raise ValueError(
                f"只能选择一个 LLM 提供商，但当前选择了：{', '.join(providers)}\n"
                "请在 .env 文件中只保留一个 USE_*=true"
            )

        # 根据选择创建 LLM
        if os.getenv("USE_OPENAI", "false").lower() == "true":
            return LLMConfig._get_openai_llm(temperature, **kwargs)
        elif os.getenv("USE_OPENAI_COMPATIBLE", "false").lower() == "true":
            return LLMConfig._get_compatible_llm(temperature, **kwargs)
        elif os.getenv("USE_AZURE_OPENAI", "false").lower() == "true":
            return LLMConfig._get_azure_llm(temperature, **kwargs)
        elif os.getenv("USE_ANTHROPIC", "false").lower() == "true":
            return LLMConfig._get_anthropic_llm(temperature, **kwargs)

        # 理论上不会走到这里
        raise ValueError("未知错误")

    @staticmethod
    def _get_openai_llm(temperature: float, **kwargs):
        """获取官方 OpenAI LLM"""
        if not HAS_OPENAI:
            raise ImportError(
                "需要安装 langchain-openai: "
                "poetry add langchain-openai"
            )

        api_key = os.getenv("OPENAI_API_KEY")
        model_name = os.getenv("OPENAI_MODEL_NAME")

        if not api_key:
            raise ValueError("OPENAI_API_KEY 未设置，请在 .env 文件中配置")
        if not model_name:
            raise ValueError("OPENAI_MODEL_NAME 未设置，请在 .env 文件中配置")

        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=temperature,
            **kwargs
        )

    @staticmethod
    def _get_compatible_llm(temperature: float, **kwargs):
        """获取 OpenAI 兼容第三方 LLM"""
        if not HAS_OPENAI:
            raise ImportError(
                "需要安装 langchain-openai: "
                "poetry add langchain-openai"
            )

        base_url = os.getenv("OPENAI_COMPATIBLE_BASE_URL")
        api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY")
        model_name = os.getenv("OPENAI_COMPATIBLE_MODEL_NAME")

        if not base_url:
            raise ValueError("OPENAI_COMPATIBLE_BASE_URL 未设置，请在 .env 文件中配置")
        if not api_key:
            raise ValueError("OPENAI_COMPATIBLE_API_KEY 未设置，请在 .env 文件中配置")
        if not model_name:
            raise ValueError("OPENAI_COMPATIBLE_MODEL_NAME 未设置，请在 .env 文件中配置")

        return ChatOpenAI(
            base_url=base_url,
            api_key=api_key,
            model=model_name,
            temperature=temperature,
            **kwargs
        )

    @staticmethod
    def _get_azure_llm(temperature: float, **kwargs):
        """获取 Azure OpenAI LLM"""
        if not HAS_OPENAI:
            raise ImportError(
                "需要安装 langchain-openai: "
                "poetry add langchain-openai"
            )

        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

        if not azure_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT 未设置，请在 .env 文件中配置")
        if not api_key:
            raise ValueError("AZURE_OPENAI_API_KEY 未设置，请在 .env 文件中配置")
        if not deployment_name:
            raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME 未设置，请在 .env 文件中配置")

        return AzureChatOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            azure_deployment=deployment_name,
            api_version=api_version,
            temperature=temperature,
            **kwargs
        )

    @staticmethod
    def _get_anthropic_llm(temperature: float, **kwargs):
        """获取 Anthropic Claude LLM"""
        if not HAS_ANTHROPIC:
            raise ImportError(
                "需要安装 langchain-anthropic: "
                "poetry add langchain-anthropic"
            )

        api_key = os.getenv("ANTHROPIC_API_KEY")
        model_name = os.getenv("ANTHROPIC_MODEL_NAME")

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY 未设置，请在 .env 文件中配置")
        if not model_name:
            raise ValueError("ANTHROPIC_MODEL_NAME 未设置，请在 .env 文件中配置")

        return ChatAnthropic(
            model=model_name,
            api_key=api_key,
            temperature=temperature,
            **kwargs
        )

    @staticmethod
    def get_config_info() -> dict:
        """获取当前 LLM 配置信息（不包含敏感信息）"""
        info = {
            "provider": "unknown",
            "model": "unknown",
        }

        if os.getenv("USE_ANTHROPIC", "false").lower() == "true":
            info["provider"] = "Anthropic"
            info["model"] = os.getenv("ANTHROPIC_MODEL_NAME", "未设置")
        elif os.getenv("USE_AZURE_OPENAI", "false").lower() == "true":
            info["provider"] = "Azure OpenAI"
            info["model"] = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "未设置")
            info["endpoint"] = os.getenv("AZURE_OPENAI_ENDPOINT", "未设置")
        elif os.getenv("USE_OPENAI_COMPATIBLE", "false").lower() == "true":
            info["provider"] = "OpenAI Compatible"
            info["model"] = os.getenv("OPENAI_COMPATIBLE_MODEL_NAME", "未设置")
            info["base_url"] = os.getenv("OPENAI_COMPATIBLE_BASE_URL", "未设置")
        elif os.getenv("USE_OPENAI", "false").lower() == "true":
            info["provider"] = "OpenAI"
            info["model"] = os.getenv("OPENAI_MODEL_NAME", "未设置")

        return info

    @staticmethod
    def validate_config() -> tuple[bool, Optional[str]]:
        """
        验证 LLM 配置是否有效

        Returns:
            (是否有效, 错误信息)
        """
        try:
            # 检查是否选择了 LLM 提供商
            providers = []
            if os.getenv("USE_OPENAI", "false").lower() == "true":
                providers.append("OpenAI")
            if os.getenv("USE_OPENAI_COMPATIBLE", "false").lower() == "true":
                providers.append("OpenAI Compatible")
            if os.getenv("USE_AZURE_OPENAI", "false").lower() == "true":
                providers.append("Azure OpenAI")
            if os.getenv("USE_ANTHROPIC", "false").lower() == "true":
                providers.append("Anthropic")

            if len(providers) == 0:
                return False, (
                    "未选择 LLM 提供商！请在 .env 文件中设置以下选项之一：\n"
                    "  USE_OPENAI=true\n"
                    "  USE_OPENAI_COMPATIBLE=true\n"
                    "  USE_AZURE_OPENAI=true\n"
                    "  USE_ANTHROPIC=true"
                )

            if len(providers) > 1:
                return False, (
                    f"只能选择一个 LLM 提供商，但当前选择了：{', '.join(providers)}\n"
                    "请在 .env 文件中只保留一个 USE_*=true"
                )

            # 验证具体选择的配置
            if os.getenv("USE_OPENAI", "false").lower() == "true":
                if not os.getenv("OPENAI_API_KEY"):
                    return False, "OPENAI_API_KEY 未设置"
                if not os.getenv("OPENAI_MODEL_NAME"):
                    return False, "OPENAI_MODEL_NAME 未设置"
                if not HAS_OPENAI:
                    return False, "langchain-openai 未安装，请运行: poetry add langchain-openai"
                return True, None

            elif os.getenv("USE_OPENAI_COMPATIBLE", "false").lower() == "true":
                required = ["OPENAI_COMPATIBLE_BASE_URL", "OPENAI_COMPATIBLE_API_KEY", "OPENAI_COMPATIBLE_MODEL_NAME"]
                for key in required:
                    if not os.getenv(key):
                        return False, f"{key} 未设置"
                if not HAS_OPENAI:
                    return False, "langchain-openai 未安装，请运行: poetry add langchain-openai"
                return True, None

            elif os.getenv("USE_AZURE_OPENAI", "false").lower() == "true":
                required = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT_NAME"]
                for key in required:
                    if not os.getenv(key):
                        return False, f"{key} 未设置"
                if not HAS_OPENAI:
                    return False, "langchain-openai 未安装，请运行: poetry add langchain-openai"
                return True, None

            elif os.getenv("USE_ANTHROPIC", "false").lower() == "true":
                if not os.getenv("ANTHROPIC_API_KEY"):
                    return False, "ANTHROPIC_API_KEY 未设置"
                if not os.getenv("ANTHROPIC_MODEL_NAME"):
                    return False, "ANTHROPIC_MODEL_NAME 未设置"
                if not HAS_ANTHROPIC:
                    return False, "langchain-anthropic 未安装，请运行: poetry add langchain-anthropic"
                return True, None

            return False, "未知的 LLM 提供商"

        except Exception as e:
            return False, str(e)


# 便捷函数
def get_llm(temperature: float = 0.7, **kwargs):
    """便捷函数：获取配置好的 LLM 实例"""
    return LLMConfig.get_llm(temperature, **kwargs)


def get_config_info() -> dict:
    """便捷函数：获取当前配置信息"""
    return LLMConfig.get_config_info()


def validate_config() -> tuple[bool, Optional[str]]:
    """便捷函数：验证配置"""
    return LLMConfig.validate_config()


def get_max_review_iterations() -> int:
    """获取最大审核迭代次数"""
    return QualityConfig.max_review_iterations()


def get_passing_score() -> int:
    """获取通过评分阈值"""
    return QualityConfig.passing_score()
