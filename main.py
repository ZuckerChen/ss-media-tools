"""
FastAPI后端主文件
提供自媒体运营工具的API接口
"""
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import json
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from config import settings
from models import get_db, init_db, AIModelConfig, ContentDraft, PublishRecord, PlatformAccount, HotTopic
from ai_models import AIModelManager, PromptTemplates
from publisher import PublishManager, ScheduledPublishManager
from hotspot_crawler import HotspotCrawlerManager
from analytics import AnalyticsManager


# 请求/响应模型
class AIModelConfigCreate(BaseModel):
    name: str
    provider: str
    api_key: str
    api_secret: Optional[str] = None
    model_name: Optional[str] = None
    max_tokens: Optional[int] = 2000
    temperature: Optional[float] = 0.7
    is_default: Optional[bool] = False


class AIModelConfigUpdate(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    model_name: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class ContentGenerateRequest(BaseModel):
    prompt: str
    config_id: Optional[int] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None





class ContentRewriteRequest(BaseModel):
    original_content: str
    rewrite_type: str = "风格转换"
    rewrite_strength: str = "中度"
    platform: str = "通用"
    audience: str = "通用受众"
    style: str = "专业"
    length_requirement: str = "保持原长度"
    keywords: str = ""
    requirements: str = ""
    config_id: Optional[int] = None


class ContentDraftCreate(BaseModel):
    title: str
    content: Optional[str] = None
    outline: Optional[str] = None
    tags: Optional[str] = None
    category: Optional[str] = None
    platform_type: Optional[str] = None


class PlatformAccountCreate(BaseModel):
    platform: str
    account_name: str
    account_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class ContentPublishRequest(BaseModel):
    draft_id: int
    platforms: List[str]
    publish_time: Optional[str] = None  # ISO格式时间字符串


class ContentCheckRequest(BaseModel):
    title: str
    content: str
    platform: str


# 新增综合创作请求模型
class ComprehensiveCreationRequest(BaseModel):
    topic: str
    platform: str = "通用"
    style: str = "专业"
    audience: str = "通用受众"
    length: str = "中等长度"
    keywords: str = ""
    requirements: str = ""
    config_id: Optional[int] = None


# 应用启动和关闭事件
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    init_db()
    print("数据库初始化完成")
    yield
    # 关闭时清理资源
    print("应用正在关闭...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="自媒体运营工具API",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": f"内部服务器错误: {str(exc)}"}
    )


# 根路径
@app.get("/")
async def root():
    return {
        "message": "自媒体运营工具API",
        "version": settings.APP_VERSION,
        "status": "运行中"
    }


# AI模型管理相关API
@app.get("/api/ai/configs", summary="获取AI模型配置列表")
async def list_ai_configs(db: Session = Depends(get_db)):
    """获取所有AI模型配置"""
    manager = AIModelManager(db)
    configs = manager.list_configs()
    return [
        {
            "id": config.id,
            "name": config.name,
            "provider": config.provider,
            "model_name": config.model_name,
            "is_active": config.is_active,
            "is_default": config.is_default,
            "usage_count": config.usage_count,
            "total_tokens": config.total_tokens,
            "created_at": config.created_at
        }
        for config in configs
    ]


@app.post("/api/ai/configs", summary="添加AI模型配置")
async def create_ai_config(config_data: AIModelConfigCreate, db: Session = Depends(get_db)):
    """添加新的AI模型配置"""
    manager = AIModelManager(db)
    try:
        config = manager.add_config(**config_data.dict())
        return {
            "id": config.id,
            "name": config.name,
            "provider": config.provider,
            "message": "AI模型配置创建成功"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建配置失败: {str(e)}")


@app.put("/api/ai/configs/{config_id}", summary="更新AI模型配置")
async def update_ai_config(config_id: int, config_data: AIModelConfigUpdate, db: Session = Depends(get_db)):
    """更新AI模型配置"""
    manager = AIModelManager(db)
    config = manager.update_config(config_id, **config_data.dict(exclude_unset=True))
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    return {
        "id": config.id,
        "name": config.name,
        "message": "配置更新成功"
    }


@app.post("/api/ai/configs/{config_id}/test", summary="测试AI模型配置")
async def test_ai_config(config_id: int, db: Session = Depends(get_db)):
    """测试AI模型配置连接"""
    manager = AIModelManager(db)
    result = manager.test_config(config_id)
    if result["success"]:
        return {"message": "连接测试成功", "status": "success"}
    else:
        return {"message": f"连接测试失败: {result['error']}", "status": "failed"}


@app.get("/api/ai/stats", summary="获取AI使用统计")
async def get_ai_stats(config_id: Optional[int] = None, db: Session = Depends(get_db)):
    """获取AI模型使用统计"""
    manager = AIModelManager(db)
    return manager.get_usage_stats(config_id)


# 内容生成相关API
@app.post("/api/content/generate", summary="生成内容")
async def generate_content(request: ContentGenerateRequest, db: Session = Depends(get_db)):
    """使用AI生成内容"""
    manager = AIModelManager(db)
    result = manager.generate_content(
        prompt=request.prompt,
        config_id=request.config_id,
        max_tokens=request.max_tokens,
        temperature=request.temperature
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "content": result["content"],
        "usage": result.get("usage"),
        "model": result.get("model")
    }


@app.post("/api/content/generate/stream", summary="流式生成内容")
async def generate_content_stream(request: ContentGenerateRequest, db: Session = Depends(get_db)):
    """使用AI流式生成内容"""
    def stream_generator():
        manager = AIModelManager(db)
        
        for chunk in manager.generate_content_stream(
            prompt=request.prompt,
            config_id=request.config_id,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        ):
            # 将chunk转换为SSE格式
            data = json.dumps(chunk, ensure_ascii=False)
            yield f"data: {data}\n\n"
        
        # 发送结束标记
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/plain; charset=utf-8"
        }
    )





# 新增综合创作API端点
@app.post("/api/content/comprehensive", summary="综合创作 - 生成标题+正文+标签")
async def create_comprehensive_content(request: ComprehensiveCreationRequest, db: Session = Depends(get_db)):
    """基于主题一次性生成完整内容方案（标题+正文+标签）"""
    manager = AIModelManager(db)
    
    # 构建综合创作提示词
    prompt = PromptTemplates.COMPREHENSIVE_CREATION.format(
        topic=request.topic,
        platform=request.platform,
        style=request.style,
        audience=request.audience,
        length=request.length,
        keywords=request.keywords,
        requirements=request.requirements
    )
    
    try:
        result = manager.generate_content(prompt, request.config_id)
        return {
            "content": result["content"],
            "usage": result.get("usage", {}),
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"综合创作失败: {str(e)}")


# 新增综合创作流式API端点
@app.post("/api/content/comprehensive/stream", summary="流式综合创作 - 生成标题+正文+标签")
async def create_comprehensive_content_stream(request: ComprehensiveCreationRequest, db: Session = Depends(get_db)):
    """流式综合创作 - 实时生成完整内容方案"""
    manager = AIModelManager(db)
    
    # 构建综合创作提示词
    prompt = PromptTemplates.COMPREHENSIVE_CREATION.format(
        topic=request.topic,
        platform=request.platform,
        style=request.style,
        audience=request.audience,
        length=request.length,
        keywords=request.keywords,
        requirements=request.requirements
    )
    
    def stream_generator():
        try:
            for chunk in manager.generate_content_stream(prompt, request.config_id):
                # 统一输出格式
                if "error" in chunk:
                    yield f"data: {json.dumps({'error': chunk['error']})}\n\n"
                else:
                    yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield f"data: [DONE]\n\n"
    
    return StreamingResponse(stream_generator(), media_type="text/plain")


# 更新内容改写API端点
@app.post("/api/content/rewrite", summary="内容改写")
async def rewrite_content(request: ContentRewriteRequest, db: Session = Depends(get_db)):
    """改写内容"""
    manager = AIModelManager(db)
    
    # 构建改写提示词
    prompt = PromptTemplates.CONTENT_REWRITE.format(
        original_content=request.original_content,
        rewrite_type=request.rewrite_type,
        rewrite_strength=request.rewrite_strength,
        platform=request.platform,
        audience=request.audience,
        style=request.style,
        length_requirement=request.length_requirement,
        keywords=request.keywords,
        requirements=request.requirements
    )
    
    try:
        result = manager.generate_content(prompt, request.config_id)
        return {
            "rewritten_content": result["content"],
            "usage": result.get("usage", {}),
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"内容改写失败: {str(e)}")


# 更新内容改写流式API端点
@app.post("/api/content/rewrite/stream", summary="流式内容改写")
async def rewrite_content_stream(request: ContentRewriteRequest, db: Session = Depends(get_db)):
    """流式内容改写"""
    manager = AIModelManager(db)
    
    # 构建改写提示词
    prompt = PromptTemplates.CONTENT_REWRITE.format(
        original_content=request.original_content,
        rewrite_type=request.rewrite_type,
        rewrite_strength=request.rewrite_strength,
        platform=request.platform,
        audience=request.audience,
        style=request.style,
        length_requirement=request.length_requirement,
        keywords=request.keywords,
        requirements=request.requirements
    )
    
    def stream_generator():
        try:
            for chunk in manager.generate_content_stream(prompt, request.config_id):
                # 统一输出格式
                if "error" in chunk:
                    yield f"data: {json.dumps({'error': chunk['error']})}\n\n"
                else:
                    yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield f"data: [DONE]\n\n"
    
    return StreamingResponse(stream_generator(), media_type="text/plain")


# 草稿管理相关API
@app.get("/api/drafts", summary="获取草稿列表")
async def list_drafts(
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取草稿列表"""
    query = db.query(ContentDraft)
    
    if category:
        query = query.filter(ContentDraft.category == category)
    if status:
        query = query.filter(ContentDraft.status == status)
    
    drafts = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": draft.id,
            "title": draft.title,
            "category": draft.category,
            "platform_type": draft.platform_type,
            "status": draft.status,
            "word_count": draft.word_count,
            "ai_generated": draft.ai_generated,
            "created_at": draft.created_at,
            "updated_at": draft.updated_at
        }
        for draft in drafts
    ]


@app.post("/api/drafts", summary="创建草稿")
async def create_draft(draft_data: ContentDraftCreate, db: Session = Depends(get_db)):
    """创建新草稿"""
    draft = ContentDraft(
        title=draft_data.title,
        content=draft_data.content,
        outline=draft_data.outline,
        tags=draft_data.tags,
        category=draft_data.category,
        platform_type=draft_data.platform_type,
        word_count=len(draft_data.content or "")
    )
    
    db.add(draft)
    db.commit()
    db.refresh(draft)
    
    return {
        "id": draft.id,
        "title": draft.title,
        "message": "草稿创建成功"
    }


@app.get("/api/drafts/{draft_id}", summary="获取草稿详情")
async def get_draft(draft_id: int, db: Session = Depends(get_db)):
    """获取草稿详情"""
    draft = db.query(ContentDraft).filter(ContentDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="草稿不存在")
    
    return {
        "id": draft.id,
        "title": draft.title,
        "content": draft.content,
        "outline": draft.outline,
        "tags": draft.tags,
        "category": draft.category,
        "platform_type": draft.platform_type,
        "status": draft.status,
        "version": draft.version,
        "ai_generated": draft.ai_generated,
        "ai_model_used": draft.ai_model_used,
        "word_count": draft.word_count,
        "created_at": draft.created_at,
        "updated_at": draft.updated_at
    }


@app.put("/api/drafts/{draft_id}", summary="更新草稿")
async def update_draft(draft_id: int, draft_data: ContentDraftCreate, db: Session = Depends(get_db)):
    """更新草稿"""
    draft = db.query(ContentDraft).filter(ContentDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="草稿不存在")
    
    # 更新字段
    for field, value in draft_data.dict(exclude_unset=True).items():
        setattr(draft, field, value)
    
    draft.word_count = len(draft.content or "")
    
    db.commit()
    db.refresh(draft)
    
    return {
        "id": draft.id,
        "title": draft.title,
        "message": "草稿更新成功"
    }


@app.delete("/api/drafts/{draft_id}", summary="删除草稿")
async def delete_draft(draft_id: int, db: Session = Depends(get_db)):
    """删除草稿"""
    draft = db.query(ContentDraft).filter(ContentDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="草稿不存在")
    
    db.delete(draft)
    db.commit()
    
    return {"message": "草稿删除成功"}


# 发布管理相关API
@app.get("/api/publish/platforms", summary="获取支持的平台列表")
async def list_platforms():
    """获取支持的发布平台列表"""
    from config import PLATFORM_CONFIGS
    return [
        {
            "platform": key,
            "name": config["name"],
            "max_length": config["max_length"],
            "support_images": config["support_images"],
            "support_video": config["support_video"]
        }
        for key, config in PLATFORM_CONFIGS.items()
    ]


@app.get("/api/publish/accounts", summary="获取平台账号列表")
async def list_platform_accounts(platform: Optional[str] = None, db: Session = Depends(get_db)):
    """获取平台账号列表"""
    manager = PublishManager(db)
    accounts = manager.get_platform_accounts(platform)
    
    return [
        {
            "id": account.id,
            "platform": account.platform,
            "account_name": account.account_name,
            "account_id": account.account_id,
            "is_active": account.is_active,
            "last_used": account.last_used,
            "created_at": account.created_at
        }
        for account in accounts
    ]


@app.post("/api/publish/accounts", summary="添加平台账号")
async def create_platform_account(account_data: PlatformAccountCreate, db: Session = Depends(get_db)):
    """添加平台账号"""
    manager = PublishManager(db)
    try:
        account = manager.add_platform_account(**account_data.dict())
        return {
            "id": account.id,
            "platform": account.platform,
            "account_name": account.account_name,
            "message": "平台账号添加成功"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"添加账号失败: {str(e)}")


@app.post("/api/publish/check", summary="检查内容适配性")
async def check_content_compatibility(request: ContentCheckRequest, db: Session = Depends(get_db)):
    """检查内容是否适合指定平台"""
    manager = PublishManager(db)
    
    content = {
        "title": request.title,
        "content": request.content
    }
    
    if request.platform == "all":
        # 检查所有平台
        suggestions = manager.get_platform_suggestions(content)
        return {"platform_suggestions": suggestions}
    else:
        # 检查指定平台
        result = manager.check_platform_content(request.platform, content)
        return {
            "platform": request.platform,
            "valid": result.get("valid", False),
            "error": result.get("error"),
            "suggestions": result
        }


@app.post("/api/publish", summary="发布内容")
async def publish_content(request: ContentPublishRequest, db: Session = Depends(get_db)):
    """发布内容到指定平台"""
    manager = PublishManager(db)
    
    # 处理发布时间
    publish_time = None
    if request.publish_time:
        try:
            from datetime import datetime
            publish_time = datetime.fromisoformat(request.publish_time.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="发布时间格式错误，请使用ISO格式")
    
    result = manager.publish_content(
        draft_id=request.draft_id,
        platforms=request.platforms,
        publish_time=publish_time
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "发布失败"))
    
    return result


@app.get("/api/publish/records", summary="获取发布记录")
async def list_publish_records(
    draft_id: Optional[int] = None,
    platform: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取发布记录列表"""
    manager = PublishManager(db)
    records = manager.get_publish_records(draft_id, platform)
    
    # 分页
    total = len(records)
    records = records[skip:skip + limit]
    
    return {
        "total": total,
        "records": [
            {
                "id": record.id,
                "draft_id": record.draft_id,
                "platform": record.platform,
                "platform_post_id": record.platform_post_id,
                "title": record.title,
                "status": record.status,
                "publish_time": record.publish_time,
                "error_message": record.error_message,
                "created_at": record.created_at
            }
            for record in records
        ]
    }


@app.get("/api/publish/stats", summary="获取发布统计")
async def get_publish_stats(db: Session = Depends(get_db)):
    """获取发布统计数据"""
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    # 获取所有发布记录
    all_records = db.query(PublishRecord).all()
    
    # 按平台统计
    platform_counts = defaultdict(lambda: {"total": 0, "success": 0, "failed": 0})
    
    for record in all_records:
        platform_counts[record.platform]["total"] += 1
        if record.status == "success":
            platform_counts[record.platform]["success"] += 1
        elif record.status == "failed":
            platform_counts[record.platform]["failed"] += 1
    
    platform_stats = []
    for platform, counts in platform_counts.items():
        success_rate = round(counts["success"] / counts["total"] * 100, 1) if counts["total"] > 0 else 0
        platform_stats.append({
            "platform": platform,
            "total": counts["total"],
            "success": counts["success"],
            "failed": counts["failed"],
            "success_rate": success_rate
        })
    
    # 按日期统计（最近7天）
    week_ago = datetime.now() - timedelta(days=7)
    daily_counts = defaultdict(int)
    
    for record in all_records:
        if record.created_at >= week_ago:
            date_str = record.created_at.strftime('%Y-%m-%d')
            daily_counts[date_str] += 1
    
    daily_stats = [
        {"date": date, "count": count}
        for date, count in sorted(daily_counts.items())
    ]
    
    return {
        "platform_stats": platform_stats,
        "daily_stats": daily_stats
    }


# 数据分析相关API
@app.get("/api/analytics/content", summary="获取内容表现分析")
async def get_content_analytics(
    days: int = 30,
    platform: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取内容表现分析"""
    try:
        manager = AnalyticsManager(db)
        result = manager.content_analyzer.analyze_content_performance(days=days, platform=platform)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.get("/api/analytics/hotspot", summary="获取热点分析")
async def get_hotspot_analytics(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """获取热点分析"""
    try:
        manager = AnalyticsManager(db)
        result = manager.hotspot_analyzer.analyze_trending_topics(days=days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.get("/api/analytics/recommendations", summary="获取内容创作建议")
async def get_content_recommendations(
    platform: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取内容创作建议"""
    try:
        manager = AnalyticsManager(db)
        result = manager.content_analyzer.get_content_recommendations(platform=platform)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取建议失败: {str(e)}")


@app.get("/api/analytics/report", summary="获取综合分析报告")
async def get_comprehensive_report(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """获取综合分析报告"""
    try:
        manager = AnalyticsManager(db)
        result = manager.generate_comprehensive_report(days=days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成报告失败: {str(e)}")


# 热点抓取相关API
@app.post("/api/hotspot/crawl", summary="抓取热点数据")
async def crawl_hotspots(
    platforms: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """手动抓取热点数据"""
    try:
        manager = HotspotCrawlerManager(db)
        result = manager.crawl_all_platforms(platforms)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"抓取失败: {str(e)}")


@app.get("/api/hotspot/topics", summary="获取热点话题")
async def get_hot_topics(
    platform: Optional[str] = None,
    category: Optional[str] = None,
    hours: int = 24,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取热点话题列表"""
    try:
        manager = HotspotCrawlerManager(db)
        topics = manager.get_hot_topics(platform, category, hours, limit)
        
        return {
            "total": len(topics),
            "topics": [
                {
                    "id": topic.id,
                    "platform": topic.platform,
                    "title": topic.title,
                    "description": topic.description,
                    "keywords": topic.keywords,
                    "hot_score": topic.hot_score,
                    "rank_position": topic.rank_position,
                    "category": topic.category,
                    "sentiment": topic.sentiment,
                    "engagement_count": topic.engagement_count,
                    "created_at": topic.created_at,
                    "updated_at": topic.updated_at
                }
                for topic in topics
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取热点失败: {str(e)}")


@app.get("/api/hotspot/keywords", summary="获取热门关键词")
async def get_trending_keywords(
    hours: int = 24,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取热门关键词"""
    try:
        manager = HotspotCrawlerManager(db)
        keywords = manager.get_trending_keywords(hours, limit)
        return {
            "keywords": keywords
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取关键词失败: {str(e)}")


@app.get("/api/hotspot/platforms", summary="获取支持的抓取平台")
async def get_hotspot_platforms():
    """获取支持的热点抓取平台"""
    return {
        "platforms": [
            {"platform": "weibo", "name": "微博热搜", "description": "微博实时热搜榜"},
            {"platform": "zhihu", "name": "知乎热榜", "description": "知乎热门话题"},
            {"platform": "toutiao", "name": "今日头条", "description": "头条热点话题"}
        ]
    }


@app.delete("/api/hotspot/cleanup", summary="清理旧数据")
async def cleanup_old_hotspots(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """清理旧的热点数据"""
    try:
        manager = HotspotCrawlerManager(db)
        deleted_count = manager.cleanup_old_data(days)
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"已清理 {deleted_count} 条过期数据"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")


@app.get("/api/hotspot/stats", summary="获取热点统计")
async def get_hotspot_stats(db: Session = Depends(get_db)):
    """获取热点数据统计"""
    try:
        from datetime import datetime, timedelta
        from collections import defaultdict
        
        # 获取最近24小时的数据
        recent_topics = db.query(HotTopic).filter(
            HotTopic.created_at >= datetime.now() - timedelta(hours=24)
        ).all()
        
        # 按平台统计
        platform_stats = defaultdict(lambda: {"count": 0, "avg_score": 0})
        total_score = defaultdict(float)
        
        for topic in recent_topics:
            platform_stats[topic.platform]["count"] += 1
            total_score[topic.platform] += topic.hot_score
        
        # 计算平均分数
        for platform in platform_stats:
            if platform_stats[platform]["count"] > 0:
                platform_stats[platform]["avg_score"] = round(
                    total_score[platform] / platform_stats[platform]["count"], 2
                )
        
        # 按类别统计
        category_stats = defaultdict(int)
        for topic in recent_topics:
            category_stats[topic.category] += 1
        
        # 情感分析统计
        sentiment_stats = defaultdict(int)
        for topic in recent_topics:
            sentiment_stats[topic.sentiment] += 1
        
        return {
            "total_topics": len(recent_topics),
            "platform_stats": dict(platform_stats),
            "category_stats": dict(category_stats),
            "sentiment_stats": dict(sentiment_stats),
            "time_range": "最近24小时"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


# 健康检查
@app.get("/health", summary="健康检查")
async def health_check():
    return {"status": "healthy", "timestamp": "now"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.DEBUG
    ) 