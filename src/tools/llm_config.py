"""
LLM 配置模块 - 支持多种大模型提供商
- 官方 OpenAI API
- OpenAI 兼容第三方 API（国内模型等）
- Azure OpenAI
- Anthropic Claude

CrewAI 1.14.6 起，所有 provider 都通过 `crewai.LLM` 原生 SDK 路径访问，
不再依赖 langchain-openai / langchain-anthropic。

注意：必须显式选择一种 LLM 提供商，没有默认选项。
"""
import os
from typing import Optional

from dotenv import load_dotenv
from crewai import LLM


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
    def _normalize_openai_compatible_model(model_name: str) -> str:
        """
        将 OpenClaw 内部模型别名转换为 OpenAI-compatible 可识别的模型名。

        CrewAI 不理解 `volcengine-plan/doubao-seed-2.0-pro` 这种 OpenClaw 内部 catalog ID。
        OpenAI-compatible 接口通常只需要后半段的真实模型名，例如 `doubao-seed-2.0-pro`。
        另外，去掉前缀也避免 `crewai.LLM.__new__` 把它当作 provider 前缀路由。
        """
        if model_name.startswith("volcengine-plan/"):
            return model_name.split("/", 1)[1]
        return model_name

    @staticmethod
    def get_llm(temperature: float = 0.7, **kwargs):
        """
        根据环境变量配置获取 LLM 实例

        Args:
            temperature: 温度参数，默认 0.7
            **kwargs: 其他传递给 LLM 的参数

        Returns:
            配置好的 `crewai.LLM` 实例（实际为原生 provider 子类）

        Raises:
            ValueError: 如果配置不正确
            ImportError: 如果 provider 所需的原生 SDK 未安装（如 azure-ai-inference）
        """
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

        if os.getenv("USE_OPENAI", "false").lower() == "true":
            return LLMConfig._get_openai_llm(temperature, **kwargs)
        elif os.getenv("USE_OPENAI_COMPATIBLE", "false").lower() == "true":
            return LLMConfig._get_compatible_llm(temperature, **kwargs)
        elif os.getenv("USE_AZURE_OPENAI", "false").lower() == "true":
            return LLMConfig._get_azure_llm(temperature, **kwargs)
        elif os.getenv("USE_ANTHROPIC", "false").lower() == "true":
            return LLMConfig._get_anthropic_llm(temperature, **kwargs)

        raise ValueError("未知错误")

    @staticmethod
    def _get_openai_llm(temperature: float, **kwargs):
        """获取官方 OpenAI LLM（crewai 原生 provider）"""
        api_key = os.getenv("OPENAI_API_KEY")
        model_name = os.getenv("OPENAI_MODEL_NAME")

        if not api_key:
            raise ValueError("OPENAI_API_KEY 未设置，请在 .env 文件中配置")
        if not model_name:
            raise ValueError("OPENAI_MODEL_NAME 未设置，请在 .env 文件中配置")

        # `openai/` 前缀让 LLM 工厂路由到 OpenAICompletion。
        return LLM(
            model=f"openai/{model_name}",
            api_key=api_key,
            temperature=temperature,
            **kwargs,
        )

    @staticmethod
    def _get_compatible_llm(temperature: float, **kwargs):
        """获取 OpenAI 兼容第三方 LLM（如豆包/Qwen 等）"""
        base_url = os.getenv("OPENAI_COMPATIBLE_BASE_URL")
        api_key = os.getenv("OPENAI_COMPATIBLE_API_KEY")
        model_name = os.getenv("OPENAI_COMPATIBLE_MODEL_NAME")

        if not base_url:
            raise ValueError("OPENAI_COMPATIBLE_BASE_URL 未设置，请在 .env 文件中配置")
        if not api_key:
            raise ValueError("OPENAI_COMPATIBLE_API_KEY 未设置，请在 .env 文件中配置")
        if not model_name:
            raise ValueError("OPENAI_COMPATIBLE_MODEL_NAME 未设置，请在 .env 文件中配置")

        model_name = LLMConfig._normalize_openai_compatible_model(model_name)

        # 显式 provider="openai" + 自定义 base_url 让 LLM 工厂走 OpenAICompletion 原生分支；
        # OpenAICompletion._get_client_params 会优先用 self.base_url 构造客户端。
        return LLM(
            model=model_name,
            provider="openai",
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            **kwargs,
        )

    @staticmethod
    def _get_azure_llm(temperature: float, **kwargs):
        """获取 Azure OpenAI LLM（crewai 原生 AzureCompletion）"""
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        # crewai AzureCompletion 的默认 api_version 是 "2024-06-01"，与 crewai 内部默认对齐。
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")

        if not azure_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT 未设置，请在 .env 文件中配置")
        if not api_key:
            raise ValueError("AZURE_OPENAI_API_KEY 未设置，请在 .env 文件中配置")
        if not deployment_name:
            raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME 未设置，请在 .env 文件中配置")

        # `azure/` 前缀路由到 AzureCompletion；该 provider 用字段名 `endpoint`（不是 api_base）。
        return LLM(
            model=f"azure/{deployment_name}",
            api_key=api_key,
            endpoint=azure_endpoint,
            api_version=api_version,
            temperature=temperature,
            **kwargs,
        )

    @staticmethod
    def _get_anthropic_llm(temperature: float, **kwargs):
        """获取 Anthropic Claude LLM（crewai 原生 AnthropicCompletion）"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model_name = os.getenv("ANTHROPIC_MODEL_NAME")

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY 未设置，请在 .env 文件中配置")
        if not model_name:
            raise ValueError("ANTHROPIC_MODEL_NAME 未设置，请在 .env 文件中配置")

        # `anthropic/` 前缀路由到 AnthropicCompletion；需要 `crewai[anthropic]` extras
        # 提供 anthropic SDK（本项目 pyproject.toml 已默认带）。
        return LLM(
            model=f"anthropic/{model_name}",
            api_key=api_key,
            temperature=temperature,
            **kwargs,
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

            if os.getenv("USE_OPENAI", "false").lower() == "true":
                if not os.getenv("OPENAI_API_KEY"):
                    return False, "OPENAI_API_KEY 未设置"
                if not os.getenv("OPENAI_MODEL_NAME"):
                    return False, "OPENAI_MODEL_NAME 未设置"
                return True, None

            elif os.getenv("USE_OPENAI_COMPATIBLE", "false").lower() == "true":
                required = ["OPENAI_COMPATIBLE_BASE_URL", "OPENAI_COMPATIBLE_API_KEY", "OPENAI_COMPATIBLE_MODEL_NAME"]
                for key in required:
                    if not os.getenv(key):
                        return False, f"{key} 未设置"
                model_name = os.getenv("OPENAI_COMPATIBLE_MODEL_NAME", "")
                if model_name.startswith("volcengine-plan/"):
                    return False, (
                        "OPENAI_COMPATIBLE_MODEL_NAME 不要使用 OpenClaw 内部模型 ID "
                        f"'{model_name}'；请改为真实模型名 "
                        f"'{LLMConfig._normalize_openai_compatible_model(model_name)}'。"
                    )
                return True, None

            elif os.getenv("USE_AZURE_OPENAI", "false").lower() == "true":
                required = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT_NAME"]
                for key in required:
                    if not os.getenv(key):
                        return False, f"{key} 未设置"
                try:
                    import azure.ai.inference  # noqa: F401
                except ImportError:
                    return False, (
                        "Azure 原生 provider 需要 azure-ai-inference 库。请运行: "
                        "poetry add 'crewai[azure-ai-inference]'"
                    )
                return True, None

            elif os.getenv("USE_ANTHROPIC", "false").lower() == "true":
                if not os.getenv("ANTHROPIC_API_KEY"):
                    return False, "ANTHROPIC_API_KEY 未设置"
                if not os.getenv("ANTHROPIC_MODEL_NAME"):
                    return False, "ANTHROPIC_MODEL_NAME 未设置"
                try:
                    import anthropic  # noqa: F401
                except ImportError:
                    return False, (
                        "anthropic SDK 未安装。请运行: "
                        "poetry add 'crewai[anthropic]'"
                    )
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
