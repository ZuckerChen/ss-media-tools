"""
项目配置文件
"""
import os
from typing import Dict, Any
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """项目设置"""
    
    # 应用基本设置
    APP_NAME: str = "自媒体运营工具"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库设置
    DATABASE_URL: str = "sqlite:///./media_tools.db"
    
    # AI模型配置
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # 百度文心一言
    BAIDU_API_KEY: str = ""
    BAIDU_SECRET_KEY: str = ""
    
    # 阿里通义千问
    DASHSCOPE_API_KEY: str = ""
    
    # 腾讯混元
    TENCENT_SECRET_ID: str = ""
    TENCENT_SECRET_KEY: str = ""
    
    # 默认模型设置
    DEFAULT_AI_MODEL: str = "openai"
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.7
    
    # 文件存储设置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # 爬虫设置
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    REQUEST_TIMEOUT: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局设置实例
settings = Settings()

# AI模型配置映射
AI_MODEL_CONFIGS = {
    "openai": {
        "name": "OpenAI GPT",
        "api_key_field": "OPENAI_API_KEY",
        "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"],
        "max_tokens": 4000,
        "support_functions": True
    },
    "baidu": {
        "name": "百度文心一言",
        "api_key_field": "BAIDU_API_KEY",
        "models": ["ernie-bot", "ernie-bot-turbo"],
        "max_tokens": 2000,
        "support_functions": False
    },
    "dashscope": {
        "name": "阿里通义千问",
        "api_key_field": "DASHSCOPE_API_KEY", 
        "models": ["qwen-turbo", "qwen-plus", "qwen-max"],
        "max_tokens": 2000,
        "support_functions": True
    },
    "tencent": {
        "name": "腾讯混元",
        "api_key_field": "TENCENT_SECRET_ID",
        "models": ["hunyuan-lite", "hunyuan-standard", "hunyuan-pro"],
        "max_tokens": 2000,
        "support_functions": False
    }
}

# 支持的平台配置
PLATFORM_CONFIGS = {
    "weibo": {
        "name": "微博",
        "max_length": 140,
        "support_images": True,
        "support_video": True
    },
    "wechat": {
        "name": "微信公众号",
        "max_length": 20000,
        "support_images": True,
        "support_video": False
    },
    "xiaohongshu": {
        "name": "小红书",
        "max_length": 1000,
        "support_images": True,
        "support_video": True
    },
    "douyin": {
        "name": "抖音",
        "max_length": 55,
        "support_images": False,
        "support_video": True
    }
}

def get_ai_model_config(model_name: str) -> Dict[str, Any]:
    """获取AI模型配置"""
    return AI_MODEL_CONFIGS.get(model_name, {})

def get_platform_config(platform: str) -> Dict[str, Any]:
    """获取平台配置"""
    return PLATFORM_CONFIGS.get(platform, {}) 