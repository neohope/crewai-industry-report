"""
配置管理模块
处理超时、kill、质量控制等配置
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class TimeoutConfig:
    """超时配置"""

    # 整个项目超时
    PROJECT_TIMEOUT = int(os.getenv("PROJECT_TIMEOUT", "7200"))  # 2小时

    # 阶段超时
    STAGE_TIMEOUT = int(os.getenv("STAGE_TIMEOUT", "3600"))  # 1小时

    # 任务超时
    TASK_TIMEOUT = int(os.getenv("TASK_TIMEOUT", "1800"))  # 30分钟

    # 各阶段超时
    COLLECTION_TIMEOUT = int(os.getenv("COLLECTION_TIMEOUT", "2400"))  # 40分钟
    ANALYSIS_TIMEOUT = int(os.getenv("ANALYSIS_TIMEOUT", "600"))  # 10分钟
    WRITE_TIMEOUT = int(os.getenv("WRITE_TIMEOUT", "1200"))  # 20分钟
    REVIEW_TIMEOUT = int(os.getenv("REVIEW_TIMEOUT", "600"))  # 10分钟
    PUBLISH_TIMEOUT = int(os.getenv("PUBLISH_TIMEOUT", "300"))  # 5分钟


class QualityConfig:
    """质量控制配置"""

    # 最大迭代次数
    MAX_REVIEW_ITERATIONS = int(os.getenv("MAX_REVIEW_ITERATIONS", "2"))

    # 通过分数阈值
    PASSING_SCORE = int(os.getenv("PASSING_SCORE", "95"))


class APIConfig:
    """API配置"""

    # OpenAI配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")

    # 飞书配置
    LARK_APP_ID = os.getenv("LARK_APP_ID", "")
    LARK_APP_SECRET = os.getenv("LARK_APP_SECRET", "")
    LARK_RECEIVER_ID = os.getenv("LARK_RECEIVER_ID", "")
    LARK_FOLDER_TOKEN = os.getenv("LARK_FOLDER_TOKEN", "")


class LogConfig:
    """日志配置"""

    VERBOSE = os.getenv("VERBOSE", "true").lower() == "true"
    SAVE_INTERMEDIATE_RESULTS = os.getenv("SAVE_INTERMEDIATE_RESULTS", "true").lower() == "true"


class SafetyConfig:
    """安全配置"""

    ENABLE_RATE_LIMIT = os.getenv("ENABLE_RATE_LIMIT", "true").lower() == "true"
    API_CALL_INTERVAL = float(os.getenv("API_CALL_INTERVAL", "0.1"))


class Config:
    """统一配置类"""

    # 超时配置
    timeout = TimeoutConfig()

    # 质量配置
    quality = QualityConfig()

    # API配置
    api = APIConfig()

    # 日志配置
    log = LogConfig()

    # 安全配置
    safety = SafetyConfig()

    @classmethod
    def validate(cls):
        """验证配置是否合理"""
        errors = []

        # 验证API Key
        if not cls.api.OPENAI_API_KEY or cls.api.OPENAI_API_KEY == "your-openai-api-key-here":
            errors.append("OPENAI_API_KEY 未配置")

        # 验证超时配置
        if cls.timeout.PROJECT_TIMEOUT < 60:
            errors.append("PROJECT_TIMEOUT 太短，建议至少 60 秒")

        if cls.timeout.STAGE_TIMEOUT < 30:
            errors.append("STAGE_TIMEOUT 太短，建议至少 30 秒")

        if cls.timeout.TASK_TIMEOUT < 10:
            errors.append("TASK_TIMEOUT 太短，建议至少 10 秒")

        # 验证分数配置
        if cls.quality.PASSING_SCORE < 0 or cls.quality.PASSING_SCORE > 100:
            errors.append("PASSING_SCORE 应在 0-100 之间")

        if cls.quality.MAX_REVIEW_ITERATIONS < 1:
            errors.append("MAX_REVIEW_ITERATIONS 至少为 1")

        return errors

    @classmethod
    def print_config(cls):
        """打印当前配置（隐藏敏感信息）"""
        print("=" * 60)
        print("  当前配置")
        print("=" * 60)
        print(f"项目超时: {cls.timeout.PROJECT_TIMEOUT} 秒")
        print(f"阶段超时: {cls.timeout.STAGE_TIMEOUT} 秒")
        print(f"任务超时: {cls.timeout.TASK_TIMEOUT} 秒")
        print(f"采集阶段: {cls.timeout.COLLECTION_TIMEOUT} 秒")
        print(f"分析阶段: {cls.timeout.ANALYSIS_TIMEOUT} 秒")
        print(f"撰写阶段: {cls.timeout.WRITE_TIMEOUT} 秒")
        print(f"评价阶段: {cls.timeout.REVIEW_TIMEOUT} 秒")
        print(f"发布阶段: {cls.timeout.PUBLISH_TIMEOUT} 秒")
        print(f"最大迭代: {cls.quality.MAX_REVIEW_ITERATIONS} 次")
        print(f"通过分数: {cls.quality.PASSING_SCORE} 分")
        print(f"详细日志: {'是' if cls.log.VERBOSE else '否'}")
        print("=" * 60)

    @classmethod
    def get_timeout_for_stage(cls, stage_name):
        """获取指定阶段的超时时间"""
        timeout_map = {
            "collection": cls.timeout.COLLECTION_TIMEOUT,
            "analysis": cls.timeout.ANALYSIS_TIMEOUT,
            "write": cls.timeout.WRITE_TIMEOUT,
            "review": cls.timeout.REVIEW_TIMEOUT,
            "publish": cls.timeout.PUBLISH_TIMEOUT,
        }
        return timeout_map.get(stage_name.lower(), cls.timeout.STAGE_TIMEOUT)
