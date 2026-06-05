"""
工具配置模块 - 管理飞书工具的配置选项
"""
import os


class FeishuConfig:
    """飞书工具配置"""

    @classmethod
    def default_receiver_id(cls) -> str:
        """默认接收者 ID"""
        return os.getenv("LARK_RECEIVER_ID", "")

    @classmethod
    def default_folder_token(cls) -> str:
        """默认文件夹 Token"""
        return os.getenv("LARK_FOLDER_TOKEN", "")

    @classmethod
    def lark_app_id(cls) -> str:
        """飞书应用 ID"""
        return os.getenv("LARK_APP_ID", "")

    @classmethod
    def lark_app_secret(cls) -> str:
        """飞书应用密钥"""
        return os.getenv("LARK_APP_SECRET", "")


class Config:
    """统一配置入口"""
    feishu = FeishuConfig
