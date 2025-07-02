"""
发布管理模块
实现多平台内容发布功能
"""
import json
import time
import requests
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from config import settings, PLATFORM_CONFIGS
from models import PublishRecord, ContentDraft, PlatformAccount, SystemLog


class BasePlatformPublisher(ABC):
    """平台发布器基类"""
    
    def __init__(self, account: PlatformAccount):
        self.account = account
        self.platform_config = PLATFORM_CONFIGS.get(account.platform, {})
    
    @abstractmethod
    def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """发布内容"""
        pass
    
    @abstractmethod
    def check_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """检查内容是否符合平台要求"""
        pass
    
    def format_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """格式化内容以适应平台要求"""
        title = content.get('title', '')
        text = content.get('content', '')
        
        # 字数限制
        max_length = self.platform_config.get('max_length', 1000)
        if len(text) > max_length:
            text = text[:max_length-3] + "..."
        
        return {
            'title': title,
            'content': text,
            'images': content.get('images', []),
            'tags': content.get('tags', [])
        }


class WeiboPublisher(BasePlatformPublisher):
    """微博发布器"""
    
    def check_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """检查微博内容"""
        text = content.get('content', '')
        
        # 微博字数限制140字
        if len(text) > 140:
            return {
                "valid": False,
                "error": f"内容超过140字限制，当前{len(text)}字"
            }
        
        # 检查是否包含敏感词（简单示例）
        sensitive_words = ['违法', '政治', '色情']
        for word in sensitive_words:
            if word in text:
                return {
                    "valid": False,
                    "error": f"内容包含敏感词：{word}"
                }
        
        return {"valid": True, "error": None}
    
    def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """发布到微博"""
        try:
            # 格式化内容
            formatted_content = self.format_content(content)
            
            # 检查内容
            check_result = self.check_content(formatted_content)
            if not check_result["valid"]:
                return {
                    "success": False,
                    "error": check_result["error"],
                    "platform_post_id": None
                }
            
            # 模拟微博API调用（实际项目中需要真实的微博API）
            # 这里只是演示流程，实际需要微博开发者权限和API密钥
            
            # 构造发布数据
            post_data = {
                'status': formatted_content['content'],
                'access_token': self.account.access_token
            }
            
            # 模拟API响应
            # 在真实环境中，这里应该是：
            # response = requests.post('https://api.weibo.com/2/statuses/update.json', data=post_data)
            
            # 模拟成功响应
            mock_response = {
                'id': f"wb_{int(time.time())}",
                'created_at': datetime.now().isoformat(),
                'text': formatted_content['content']
            }
            
            return {
                "success": True,
                "platform_post_id": mock_response['id'],
                "published_url": f"https://weibo.com/{mock_response['id']}",
                "response": mock_response
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "platform_post_id": None
            }


class WeChatPublisher(BasePlatformPublisher):
    """微信公众号发布器"""
    
    def check_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """检查微信公众号内容"""
        title = content.get('title', '')
        text = content.get('content', '')
        
        if not title:
            return {"valid": False, "error": "标题不能为空"}
        
        if len(title) > 50:
            return {"valid": False, "error": "标题不能超过50字"}
        
        if len(text) < 100:
            return {"valid": False, "error": "内容不能少于100字"}
        
        return {"valid": True, "error": None}
    
    def publish(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """发布到微信公众号"""
        try:
            # 格式化内容
            formatted_content = self.format_content(content)
            
            # 检查内容
            check_result = self.check_content(formatted_content)
            if not check_result["valid"]:
                return {
                    "success": False,
                    "error": check_result["error"],
                    "platform_post_id": None
                }
            
            # 模拟微信公众号API调用
            # 实际需要微信公众号的access_token和相关权限
            
            # 构造发布数据
            article_data = {
                'title': formatted_content['title'],
                'content': formatted_content['content'],
                'author': '自媒体运营工具',
                'digest': formatted_content['content'][:100] + '...',
                'access_token': self.account.access_token
            }
            
            # 模拟API响应
            mock_response = {
                'media_id': f"wechat_{int(time.time())}",
                'created_at': datetime.now().isoformat(),
                'title': formatted_content['title']
            }
            
            return {
                "success": True,
                "platform_post_id": mock_response['media_id'],
                "published_url": f"https://mp.weixin.qq.com/s/{mock_response['media_id']}",
                "response": mock_response
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "platform_post_id": None
            }


class PublishManager:
    """发布管理器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.publishers = {
            'weibo': WeiboPublisher,
            'wechat': WeChatPublisher,
        }
    
    def get_platform_accounts(self, platform: Optional[str] = None) -> List[PlatformAccount]:
        """获取平台账号列表"""
        query = self.db.query(PlatformAccount).filter(PlatformAccount.is_active == True)
        if platform:
            query = query.filter(PlatformAccount.platform == platform)
        return query.all()
    
    def add_platform_account(self, platform: str, account_name: str, **kwargs) -> PlatformAccount:
        """添加平台账号"""
        account = PlatformAccount(
            platform=platform,
            account_name=account_name,
            account_id=kwargs.get('account_id'),
            access_token=kwargs.get('access_token'),
            refresh_token=kwargs.get('refresh_token'),
            token_expires_at=kwargs.get('token_expires_at')
        )
        
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account
    
    def publish_content(self, draft_id: int, platforms: List[str], publish_time: Optional[datetime] = None) -> Dict[str, Any]:
        """发布内容到指定平台"""
        # 获取草稿
        draft = self.db.query(ContentDraft).filter(ContentDraft.id == draft_id).first()
        if not draft:
            return {"success": False, "error": "草稿不存在"}
        
        # 准备发布内容
        content = {
            'title': draft.title,
            'content': draft.content,
            'tags': draft.tags.split(',') if draft.tags else []
        }
        
        results = {}
        
        for platform in platforms:
            try:
                # 获取平台账号
                account = self.db.query(PlatformAccount).filter(
                    PlatformAccount.platform == platform,
                    PlatformAccount.is_active == True
                ).first()
                
                if not account:
                    results[platform] = {
                        "success": False,
                        "error": f"未找到{platform}平台的有效账号"
                    }
                    continue
                
                # 获取发布器
                publisher_class = self.publishers.get(platform)
                if not publisher_class:
                    results[platform] = {
                        "success": False,
                        "error": f"不支持的平台：{platform}"
                    }
                    continue
                
                publisher = publisher_class(account)
                
                # 立即发布还是定时发布
                if publish_time and publish_time > datetime.now():
                    # 定时发布（这里先创建记录，实际需要定时任务）
                    publish_record = PublishRecord(
                        draft_id=draft_id,
                        platform=platform,
                        title=content['title'],
                        content=content['content'],
                        status='scheduled',
                        publish_time=publish_time
                    )
                    self.db.add(publish_record)
                    
                    results[platform] = {
                        "success": True,
                        "message": f"已安排定时发布到{platform}",
                        "publish_time": publish_time.isoformat()
                    }
                else:
                    # 立即发布
                    result = publisher.publish(content)
                    
                    # 创建发布记录
                    publish_record = PublishRecord(
                        draft_id=draft_id,
                        platform=platform,
                        platform_post_id=result.get('platform_post_id'),
                        title=content['title'],
                        content=content['content'],
                        status='success' if result['success'] else 'failed',
                        publish_time=datetime.now(),
                        error_message=result.get('error')
                    )
                    self.db.add(publish_record)
                    
                    results[platform] = result
                
                # 更新账号最后使用时间
                account.last_used = datetime.now()
                
            except Exception as e:
                results[platform] = {
                    "success": False,
                    "error": str(e)
                }
                
                # 记录错误日志
                log = SystemLog(
                    level="ERROR",
                    module="publisher",
                    message=f"发布到{platform}失败",
                    details={
                        "draft_id": draft_id,
                        "platform": platform,
                        "error": str(e)
                    }
                )
                self.db.add(log)
        
        self.db.commit()
        
        # 统计结果
        success_count = sum(1 for result in results.values() if result.get('success'))
        total_count = len(results)
        
        return {
            "success": success_count > 0,
            "summary": f"成功发布到{success_count}/{total_count}个平台",
            "results": results
        }
    
    def get_publish_records(self, draft_id: Optional[int] = None, platform: Optional[str] = None) -> List[PublishRecord]:
        """获取发布记录"""
        query = self.db.query(PublishRecord)
        
        if draft_id:
            query = query.filter(PublishRecord.draft_id == draft_id)
        if platform:
            query = query.filter(PublishRecord.platform == platform)
        
        return query.order_by(PublishRecord.created_at.desc()).all()
    
    def check_platform_content(self, platform: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """检查内容是否适合指定平台"""
        # 获取平台账号
        account = self.db.query(PlatformAccount).filter(
            PlatformAccount.platform == platform,
            PlatformAccount.is_active == True
        ).first()
        
        if not account:
            return {"valid": False, "error": f"未配置{platform}账号"}
        
        # 获取发布器
        publisher_class = self.publishers.get(platform)
        if not publisher_class:
            return {"valid": False, "error": f"不支持的平台：{platform}"}
        
        publisher = publisher_class(account)
        return publisher.check_content(content)
    
    def get_platform_suggestions(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """获取平台适配建议"""
        suggestions = {}
        
        for platform in self.publishers.keys():
            check_result = self.check_platform_content(platform, content)
            
            config = PLATFORM_CONFIGS.get(platform, {})
            suggestion = {
                "platform_name": config.get('name', platform),
                "valid": check_result.get('valid', False),
                "error": check_result.get('error'),
                "max_length": config.get('max_length'),
                "current_length": len(content.get('content', '')),
                "support_images": config.get('support_images', False),
                "support_video": config.get('support_video', False)
            }
            
            # 添加优化建议
            if not suggestion["valid"] and suggestion["error"]:
                if "超过" in suggestion["error"] and "字限制" in suggestion["error"]:
                    suggestion["optimization"] = f"建议将内容缩短至{config.get('max_length')}字以内"
                elif "不能为空" in suggestion["error"]:
                    suggestion["optimization"] = "请添加必要的内容"
                else:
                    suggestion["optimization"] = "请根据错误提示调整内容"
            else:
                suggestion["optimization"] = "内容符合平台要求"
            
            suggestions[platform] = suggestion
        
        return suggestions


# 定时发布任务管理（简化版本）
class ScheduledPublishManager:
    """定时发布管理器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.publish_manager = PublishManager(db)
    
    def check_and_execute_scheduled_posts(self):
        """检查并执行定时发布任务"""
        now = datetime.now()
        
        # 获取待发布的记录
        scheduled_records = self.db.query(PublishRecord).filter(
            PublishRecord.status == 'scheduled',
            PublishRecord.publish_time <= now
        ).all()
        
        for record in scheduled_records:
            try:
                # 获取草稿和平台信息
                draft = self.db.query(ContentDraft).filter(ContentDraft.id == record.draft_id).first()
                if not draft:
                    record.status = 'failed'
                    record.error_message = '草稿不存在'
                    continue
                
                # 执行发布
                result = self.publish_manager.publish_content(
                    draft_id=record.draft_id,
                    platforms=[record.platform]
                )
                
                # 更新记录状态
                platform_result = result['results'].get(record.platform, {})
                record.status = 'success' if platform_result.get('success') else 'failed'
                record.platform_post_id = platform_result.get('platform_post_id')
                record.error_message = platform_result.get('error')
                
            except Exception as e:
                record.status = 'failed'
                record.error_message = str(e)
        
        self.db.commit()
        return len(scheduled_records) 