"""
工具配置模块 - 管理搜索工具和飞书工具的配置选项
"""
import os
from pathlib import Path


class ToolConfig:
    """工具配置基类"""

    @classmethod
    def get_bool(cls, key: str, default: bool = False) -> bool:
        """获取布尔配置"""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "yes", "1", "y")

    @classmethod
    def get_int(cls, key: str, default: int = 0) -> int:
        """获取整数配置"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    @classmethod
    def get_str(cls, key: str, default: str = "") -> str:
        """获取字符串配置"""
        return os.getenv(key, default)


class SearchConfig(ToolConfig):
    """搜索工具配置"""

    @classmethod
    def use_skill(cls) -> bool:
        """是否使用byted-web-search技能"""
        return cls.get_bool("USE_BYTED_WEB_SEARCH", True)

    @classmethod
    def default_max_results(cls) -> int:
        """默认最大返回结果数"""
        return cls.get_int("DEFAULT_MAX_RESULTS", 10)

    @classmethod
    def default_auth_level(cls) -> int:
        """默认权威等级"""
        return cls.get_int("DEFAULT_AUTH_LEVEL", 0)

    @classmethod
    def enable_query_rewrite(cls) -> bool:
        """是否启用查询改写"""
        return cls.get_bool("ENABLE_QUERY_REWRITE", False)


class FeishuConfig(ToolConfig):
    """飞书工具配置"""

    @classmethod
    def use_skill(cls) -> bool:
        """是否使用飞书技能"""
        return cls.get_bool("USE_LARK_SKILL", True)

    @classmethod
    def use_local_fallback(cls) -> bool:
        """是否允许使用本地文件系统作为后备"""
        return cls.get_bool("USE_LOCAL_FALLBACK", True)

    @classmethod
    def default_receiver_id(cls) -> str:
        """默认接收者ID"""
        return cls.get_str("LARK_RECEIVER_ID", "")

    @classmethod
    def default_folder_token(cls) -> str:
        """默认文件夹Token"""
        return cls.get_str("LARK_FOLDER_TOKEN", "")

    @classmethod
    def lark_app_id(cls) -> str:
        """飞书应用ID"""
        return cls.get_str("LARK_APP_ID", "")

    @classmethod
    def lark_app_secret(cls) -> str:
        """飞书应用密钥"""
        return cls.get_str("LARK_APP_SECRET", "")


class Config:
    """统一配置入口"""
    search = SearchConfig
    feishu = FeishuConfig

    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """验证配置有效性"""
        errors = []

        # 检查OpenAI API Key（用于主程序，非工具）
        if not os.getenv("OPENAI_API_KEY"):
            errors.append("OPENAI_API_KEY未配置")

        # 检查飞书配置
        has_lark_any = bool(os.getenv("LARK_APP_ID") or os.getenv("LARK_APP_SECRET"))
        if has_lark_any:
            if not (os.getenv("LARK_APP_ID") and os.getenv("LARK_APP_SECRET")):
                errors.append("飞书配置不完整：需要同时配置LARK_APP_ID和LARK_APP_SECRET")

        return (len(errors) == 0, errors)

    @classmethod
    def info(cls) -> str:
        """获取配置信息摘要"""
        lines = []
        lines.append("=== 工具配置 ===")
        lines.append(f"搜索: {'使用技能' if cls.search.use_skill() else '不使用技能'}")
        lines.append(f"默认结果数: {cls.search.default_max_results()}")
        lines.append(f"飞书: {'使用技能' if cls.feishu.use_skill() else '不使用技能'}")
        lines.append(f"本地后备: {'启用' if cls.feishu.use_local_fallback() else '禁用'}")

        if cls.feishu.default_receiver_id():
            lines.append(f"默认接收者: {cls.feishu.default_receiver_id()}")
        if cls.feishu.lark_app_id():
            lines.append(f"飞书AppId: {cls.feishu.lark_app_id()[:8]}...")

        return "\n".join(lines)
