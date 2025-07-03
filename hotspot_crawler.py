"""
热点抓取模块
实现多平台热点数据抓取功能
"""
import requests
import json
import time
import re
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup
import jieba
from config import settings
from models import HotTopic, SystemLog


class BaseHotspotCrawler(ABC):
    """热点抓取器基类"""
    
    def __init__(self, platform: str):
        self.platform = platform
        self.headers = {
            'User-Agent': settings.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    @abstractmethod
    def crawl_hotspots(self) -> List[Dict[str, Any]]:
        """抓取热点数据"""
        pass
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> str:
        """提取关键词"""
        try:
            # 使用jieba分词
            words = jieba.lcut(text)
            # 过滤长度小于2的词和标点符号
            keywords = [word for word in words if len(word) >= 2 and word.isalnum()]
            # 去重并限制数量
            keywords = list(dict.fromkeys(keywords))[:max_keywords]
            return ','.join(keywords)
        except Exception:
            return ""
    
    def calculate_hot_score(self, rank: int, engagement: int = 0) -> float:
        """计算热度分数"""
        # 基于排名和互动量计算热度分数
        rank_score = max(0, 100 - rank * 2)  # 排名越高分数越高
        engagement_score = min(50, engagement / 1000)  # 互动量加分，最多50分
        return round(rank_score + engagement_score, 2)
    
    def analyze_sentiment(self, text: str) -> str:
        """分析情感倾向（简化版本）"""
        positive_words = ['好', '棒', '赞', '优秀', '成功', '胜利', '开心', '快乐', '喜欢', '爱']
        negative_words = ['坏', '差', '糟', '失败', '难过', '生气', '讨厌', '恨', '问题', '错误']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'


class WeiboHotspotCrawler(BaseHotspotCrawler):
    """微博热搜抓取器"""
    
    def __init__(self):
        super().__init__("weibo")
        self.api_url = "https://weibo.com/ajax/side/hotSearch"
    
    def crawl_hotspots(self) -> List[Dict[str, Any]]:
        """抓取微博热搜"""
        hotspots = []
        
        try:
            # 请求微博热搜API
            response = self.session.get(self.api_url, timeout=settings.REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('ok') == 1 and 'data' in data:
                    realtime_data = data['data'].get('realtime', [])
                    
                    for i, item in enumerate(realtime_data[:50]):  # 取前50个热搜
                        try:
                            title = item.get('word', '').strip()
                            if not title:
                                continue
                            
                            # 提取热搜信息
                            hot_score = self.calculate_hot_score(i + 1, item.get('num', 0))
                            keywords = self.extract_keywords(title)
                            sentiment = self.analyze_sentiment(title)
                            
                            hotspot = {
                                'platform': self.platform,
                                'title': title,
                                'description': item.get('note', ''),
                                'keywords': keywords,
                                'hot_score': hot_score,
                                'rank_position': i + 1,
                                'category': item.get('category', '综合'),
                                'sentiment': sentiment,
                                'engagement_count': item.get('num', 0),
                                'raw_data': item  # 保存原始数据用于调试
                            }
                            
                            hotspots.append(hotspot)
                            
                        except Exception as e:
                            print(f"处理微博热搜项目时出错: {e}")
                            continue
                
        except Exception as e:
            print(f"抓取微博热搜失败: {e}")
        
        return hotspots


class ZhihuHotspotCrawler(BaseHotspotCrawler):
    """知乎热榜抓取器"""
    
    def __init__(self):
        super().__init__("zhihu")
        self.api_url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"
    
    def crawl_hotspots(self) -> List[Dict[str, Any]]:
        """抓取知乎热榜"""
        hotspots = []
        
        try:
            # 添加知乎特定的请求头
            headers = self.headers.copy()
            headers.update({
                'Referer': 'https://www.zhihu.com/',
                'x-requested-with': 'fetch'
            })
            
            response = self.session.get(self.api_url, headers=headers, timeout=settings.REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data:
                    for i, item in enumerate(data['data'][:50]):
                        try:
                            target = item.get('target', {})
                            title = target.get('title', '').strip()
                            
                            if not title:
                                continue
                            
                            # 提取信息
                            excerpt = target.get('excerpt', '')
                            hot_score = self.calculate_hot_score(i + 1, item.get('detail_text', ''))
                            keywords = self.extract_keywords(title + ' ' + excerpt)
                            sentiment = self.analyze_sentiment(title + ' ' + excerpt)
                            
                            hotspot = {
                                'platform': self.platform,
                                'title': title,
                                'description': excerpt[:200],  # 限制描述长度
                                'keywords': keywords,
                                'hot_score': hot_score,
                                'rank_position': i + 1,
                                'category': '知识',
                                'sentiment': sentiment,
                                'engagement_count': 0,  # 知乎API不提供具体数值
                                'raw_data': item
                            }
                            
                            hotspots.append(hotspot)
                            
                        except Exception as e:
                            print(f"处理知乎热榜项目时出错: {e}")
                            continue
                
        except Exception as e:
            print(f"抓取知乎热榜失败: {e}")
        
        return hotspots


class ToutiaoHotspotCrawler(BaseHotspotCrawler):
    """今日头条热点抓取器"""
    
    def __init__(self):
        super().__init__("toutiao")
    
    def crawl_hotspots(self) -> List[Dict[str, Any]]:
        """抓取今日头条热点（模拟数据）"""
        # 注意：实际的头条API需要认证，这里提供一个模拟实现
        hotspots = []
        
        # 模拟热点数据
        mock_topics = [
            "科技创新推动经济发展",
            "教育改革新政策发布",
            "环保技术取得新突破",
            "文化产业迎来新机遇",
            "健康生活方式受关注"
        ]
        
        for i, topic in enumerate(mock_topics):
            hotspot = {
                'platform': self.platform,
                'title': topic,
                'description': f"{topic}相关讨论热度持续上升",
                'keywords': self.extract_keywords(topic),
                'hot_score': self.calculate_hot_score(i + 1),
                'rank_position': i + 1,
                'category': '综合',
                'sentiment': 'positive',
                'engagement_count': 1000 - i * 100,
                'raw_data': {'mock': True}
            }
            hotspots.append(hotspot)
        
        return hotspots


class HotspotCrawlerManager:
    """热点抓取管理器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.crawlers = {
            'weibo': WeiboHotspotCrawler(),
            'zhihu': ZhihuHotspotCrawler(),
            'toutiao': ToutiaoHotspotCrawler(),
        }
    
    def crawl_all_platforms(self, platforms: Optional[List[str]] = None) -> Dict[str, Any]:
        """抓取所有平台的热点数据"""
        if platforms is None:
            platforms = list(self.crawlers.keys())
        
        results = {
            'success': True,
            'platforms': {},
            'total_count': 0,
            'errors': []
        }
        
        for platform in platforms:
            if platform not in self.crawlers:
                results['errors'].append(f"不支持的平台: {platform}")
                continue
            
            try:
                print(f"正在抓取 {platform} 热点...")
                crawler = self.crawlers[platform]
                hotspots = crawler.crawl_hotspots()
                
                # 保存到数据库
                saved_count = self.save_hotspots(hotspots)
                
                results['platforms'][platform] = {
                    'crawled': len(hotspots),
                    'saved': saved_count,
                    'success': True
                }
                results['total_count'] += saved_count
                
                # 记录日志
                self.log_crawl_result(platform, len(hotspots), saved_count, None)
                
                # 添加延迟，避免请求过于频繁
                time.sleep(1)
                
            except Exception as e:
                error_msg = f"{platform} 抓取失败: {str(e)}"
                results['errors'].append(error_msg)
                results['platforms'][platform] = {
                    'crawled': 0,
                    'saved': 0,
                    'success': False,
                    'error': str(e)
                }
                
                # 记录错误日志
                self.log_crawl_result(platform, 0, 0, str(e))
        
        return results
    
    def save_hotspots(self, hotspots: List[Dict[str, Any]]) -> int:
        """保存热点数据到数据库"""
        saved_count = 0
        
        for hotspot_data in hotspots:
            try:
                # 检查是否已存在相同的热点（24小时内）
                existing = self.db.query(HotTopic).filter(
                    HotTopic.platform == hotspot_data['platform'],
                    HotTopic.title == hotspot_data['title'],
                    HotTopic.created_at >= datetime.now() - timedelta(hours=24)
                ).first()
                
                if existing:
                    # 更新现有记录
                    existing.hot_score = hotspot_data['hot_score']
                    existing.rank_position = hotspot_data['rank_position']
                    existing.engagement_count = hotspot_data['engagement_count']
                    existing.updated_at = datetime.now()
                else:
                    # 创建新记录
                    hot_topic = HotTopic(
                        platform=hotspot_data['platform'],
                        title=hotspot_data['title'],
                        description=hotspot_data.get('description', ''),
                        keywords=hotspot_data.get('keywords', ''),
                        hot_score=hotspot_data['hot_score'],
                        rank_position=hotspot_data['rank_position'],
                        category=hotspot_data.get('category', '综合'),
                        sentiment=hotspot_data.get('sentiment', 'neutral'),
                        engagement_count=hotspot_data.get('engagement_count', 0)
                    )
                    self.db.add(hot_topic)
                
                saved_count += 1
                
            except Exception as e:
                print(f"保存热点数据失败: {e}")
                continue
        
        try:
            self.db.commit()
        except Exception as e:
            print(f"提交数据库事务失败: {e}")
            self.db.rollback()
            return 0
        
        return saved_count
    
    def log_crawl_result(self, platform: str, crawled: int, saved: int, error: Optional[str]):
        """记录抓取结果日志"""
        try:
            log = SystemLog(
                level="ERROR" if error else "INFO",
                module="hotspot_crawler",
                message=f"热点抓取 - {platform}",
                details={
                    "platform": platform,
                    "crawled_count": crawled,
                    "saved_count": saved,
                    "error": error,
                    "timestamp": datetime.now().isoformat()
                }
            )
            self.db.add(log)
            self.db.commit()
        except Exception as e:
            print(f"记录日志失败: {e}")
    
    def get_hot_topics(self, 
                      platform: Optional[str] = None,
                      category: Optional[str] = None,
                      hours: int = 24,
                      limit: int = 50) -> List[HotTopic]:
        """获取热点话题列表"""
        query = self.db.query(HotTopic)
        
        # 时间过滤
        time_threshold = datetime.now() - timedelta(hours=hours)
        query = query.filter(HotTopic.created_at >= time_threshold)
        
        # 平台过滤
        if platform:
            query = query.filter(HotTopic.platform == platform)
        
        # 分类过滤
        if category:
            query = query.filter(HotTopic.category == category)
        
        # 按热度分数排序
        query = query.order_by(HotTopic.hot_score.desc())
        
        return query.limit(limit).all()
    
    def get_trending_keywords(self, hours: int = 24, limit: int = 20) -> List[Dict[str, Any]]:
        """获取热门关键词"""
        # 获取最近的热点话题
        topics = self.get_hot_topics(hours=hours, limit=200)
        
        # 统计关键词频率
        keyword_count = {}
        keyword_score = {}
        
        for topic in topics:
            if topic.keywords:
                keywords = topic.keywords.split(',')
                for keyword in keywords:
                    keyword = keyword.strip()
                    if len(keyword) >= 2:
                        keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
                        keyword_score[keyword] = keyword_score.get(keyword, 0) + topic.hot_score
        
        # 计算综合分数并排序
        trending_keywords = []
        for keyword, count in keyword_count.items():
            if count >= 2:  # 至少出现2次
                avg_score = keyword_score[keyword] / count
                trending_keywords.append({
                    'keyword': keyword,
                    'count': count,
                    'avg_score': round(avg_score, 2),
                    'total_score': round(keyword_score[keyword], 2)
                })
        
        # 按总分数排序
        trending_keywords.sort(key=lambda x: x['total_score'], reverse=True)
        
        return trending_keywords[:limit]
    
    def cleanup_old_data(self, days: int = 7):
        """清理旧的热点数据"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = self.db.query(HotTopic).filter(
                HotTopic.created_at < cutoff_date
            ).delete()
            
            self.db.commit()
            print(f"清理了 {deleted_count} 条过期热点数据")
            return deleted_count
            
        except Exception as e:
            print(f"清理旧数据失败: {e}")
            self.db.rollback()
            return 0


# 定时任务函数
def scheduled_crawl_task(db: Session):
    """定时抓取任务"""
    manager = HotspotCrawlerManager(db)
    
    # 执行抓取
    result = manager.crawl_all_platforms()
    
    # 清理旧数据（保留7天）
    manager.cleanup_old_data(days=7)
    
    return result


if __name__ == "__main__":
    # 测试代码
    from models import SessionLocal
    
    db = SessionLocal()
    try:
        manager = HotspotCrawlerManager(db)
        result = manager.crawl_all_platforms(['weibo'])
        print("抓取结果:", json.dumps(result, ensure_ascii=False, indent=2))
        
        # 获取热门关键词
        keywords = manager.get_trending_keywords()
        print("热门关键词:", keywords[:10])
        
    finally:
        db.close() 