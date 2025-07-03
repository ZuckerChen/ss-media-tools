"""
数据库模型定义
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings

Base = declarative_base()


class AIModelConfig(Base):
    """AI模型配置表"""
    __tablename__ = "ai_model_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)  # 模型名称
    provider = Column(String(20), nullable=False)  # 提供商：openai, baidu, dashscope, tencent
    api_key = Column(String(200))  # API密钥
    api_secret = Column(String(200))  # API密钥（如果需要）
    model_name = Column(String(50))  # 具体模型名称
    max_tokens = Column(Integer, default=2000)
    temperature = Column(Float, default=0.7)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)  # 使用次数
    total_tokens = Column(Integer, default=0)  # 总使用token数
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContentDraft(Base):
    """内容草稿表"""
    __tablename__ = "content_drafts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    outline = Column(Text)  # 大纲
    tags = Column(String(500))  # 标签，逗号分隔
    category = Column(String(50))  # 分类
    platform_type = Column(String(20))  # 目标平台类型
    status = Column(String(20), default="draft")  # draft, published, deleted
    version = Column(Integer, default=1)  # 版本号
    parent_id = Column(Integer, ForeignKey("content_drafts.id"))  # 父版本ID
    ai_generated = Column(Boolean, default=False)  # 是否AI生成
    ai_model_used = Column(String(50))  # 使用的AI模型
    word_count = Column(Integer, default=0)  # 字数
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    children = relationship("ContentDraft", cascade="all, delete-orphan")


class PublishRecord(Base):
    """发布记录表"""
    __tablename__ = "publish_records"
    
    id = Column(Integer, primary_key=True, index=True)
    draft_id = Column(Integer, ForeignKey("content_drafts.id"))
    platform = Column(String(20), nullable=False)  # 发布平台
    platform_post_id = Column(String(100))  # 平台文章ID
    title = Column(String(200))
    content = Column(Text)
    status = Column(String(20), default="pending")  # pending, success, failed
    publish_time = Column(DateTime)  # 发布时间（计划或实际）
    error_message = Column(Text)  # 错误信息
    view_count = Column(Integer, default=0)  # 浏览量
    like_count = Column(Integer, default=0)  # 点赞数
    comment_count = Column(Integer, default=0)  # 评论数
    share_count = Column(Integer, default=0)  # 分享数
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    draft = relationship("ContentDraft")


class HotTopic(Base):
    """热点话题表"""
    __tablename__ = "hot_topics"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(20), nullable=False)  # 平台来源
    title = Column(String(200), nullable=False)
    description = Column(Text)
    keywords = Column(String(500))  # 关键词，逗号分隔
    hot_score = Column(Float, default=0.0)  # 热度分数
    rank_position = Column(Integer)  # 排名位置
    category = Column(String(50))  # 分类
    sentiment = Column(String(20))  # 情感倾向：positive, negative, neutral
    engagement_count = Column(Integer, default=0)  # 互动总数
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PlatformAccount(Base):
    """平台账号表"""
    __tablename__ = "platform_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(20), nullable=False)  # 平台名称
    account_name = Column(String(100), nullable=False)  # 账号名称
    account_id = Column(String(100))  # 平台账号ID
    access_token = Column(String(500))  # 访问令牌
    refresh_token = Column(String(500))  # 刷新令牌
    token_expires_at = Column(DateTime)  # 令牌过期时间
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SystemLog(Base):
    """系统日志表"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(10), nullable=False)  # DEBUG, INFO, WARNING, ERROR
    module = Column(String(50))  # 模块名称
    message = Column(Text, nullable=False)
    details = Column(JSON)  # 详细信息，JSON格式
    created_at = Column(DateTime, default=datetime.utcnow)


# 数据库连接
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)
    
    # 创建默认AI模型配置
    db = SessionLocal()
    try:
        # 检查是否已有配置
        existing_config = db.query(AIModelConfig).first()
        if not existing_config:
            # 创建默认DeepSeek配置
            default_config = AIModelConfig(
                name="默认DeepSeek模型",
                provider="deepseek",
                model_name="deepseek-chat",
                max_tokens=4000,
                temperature=0.7,
                is_default=True
            )
            db.add(default_config)
            db.commit()
            print("已创建默认DeepSeek模型配置")
    except Exception as e:
        print(f"初始化数据库出错: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("数据库初始化完成") 