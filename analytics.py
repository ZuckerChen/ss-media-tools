"""
数据分析模块
实现内容表现分析、发布效果分析、用户行为分析等功能
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from collections import defaultdict, Counter
import json

from models import (
    ContentDraft, PublishRecord, HotTopic, AIModelConfig, 
    PlatformAccount, SystemLog
)


class ContentAnalyzer:
    """内容分析器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_content_performance(self, 
                                  days: int = 30,
                                  platform: Optional[str] = None) -> Dict[str, Any]:
        """分析内容表现"""
        # 获取指定时间范围内的发布记录
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = self.db.query(PublishRecord).filter(
            PublishRecord.created_at >= start_date,
            PublishRecord.created_at <= end_date
        )
        
        if platform:
            query = query.filter(PublishRecord.platform == platform)
        
        records = query.all()
        
        if not records:
            return {
                "total_posts": 0,
                "performance_summary": {
                    "success_rate": 0,
                    "failure_rate": 0,
                    "avg_daily_posts": 0
                },
                "platform_analysis": {},
                "time_analysis": {
                    "best_hours": [],
                    "hour_distribution": {}
                },
                "content_insights": {
                    "best_title_length": "medium",
                    "title_length_analysis": {},
                    "total_successful_posts": 0,
                    "total_failed_posts": 0,
                    "common_failure_reasons": {}
                }
            }
        
        # 基础统计
        total_posts = len(records)
        successful_posts = len([r for r in records if r.status == "success"])
        failed_posts = len([r for r in records if r.status == "failed"])
        
        # 平台分析
        platform_stats = defaultdict(lambda: {
            "posts": 0, "success": 0, "failed": 0,
            "total_views": 0, "total_likes": 0, "total_comments": 0, "total_shares": 0
        })
        
        for record in records:
            platform_stats[record.platform]["posts"] += 1
            if record.status == "success":
                platform_stats[record.platform]["success"] += 1
                platform_stats[record.platform]["total_views"] += record.view_count or 0
                platform_stats[record.platform]["total_likes"] += record.like_count or 0
                platform_stats[record.platform]["total_comments"] += record.comment_count or 0
                platform_stats[record.platform]["total_shares"] += record.share_count or 0
            elif record.status == "failed":
                platform_stats[record.platform]["failed"] += 1
        
        # 计算平台成功率和平均互动
        platform_analysis = {}
        for platform, stats in platform_stats.items():
            success_rate = (stats["success"] / stats["posts"] * 100) if stats["posts"] > 0 else 0
            avg_engagement = (
                (stats["total_views"] + stats["total_likes"] + 
                 stats["total_comments"] + stats["total_shares"]) / 
                max(stats["success"], 1)
            )
            
            platform_analysis[platform] = {
                "posts": stats["posts"],
                "success_rate": round(success_rate, 2),
                "avg_views": round(stats["total_views"] / max(stats["success"], 1), 2),
                "avg_likes": round(stats["total_likes"] / max(stats["success"], 1), 2),
                "avg_comments": round(stats["total_comments"] / max(stats["success"], 1), 2),
                "avg_shares": round(stats["total_shares"] / max(stats["success"], 1), 2),
                "avg_engagement": round(avg_engagement, 2)
            }
        
        # 时间分析（按小时统计最佳发布时间）
        hour_stats = defaultdict(lambda: {"posts": 0, "success": 0, "total_engagement": 0})
        
        for record in records:
            if record.publish_time:
                hour = record.publish_time.hour
                hour_stats[hour]["posts"] += 1
                if record.status == "success":
                    hour_stats[hour]["success"] += 1
                    engagement = (record.view_count or 0) + (record.like_count or 0) + \
                               (record.comment_count or 0) + (record.share_count or 0)
                    hour_stats[hour]["total_engagement"] += engagement
        
        # 找出最佳发布时间
        best_hours = []
        for hour, stats in hour_stats.items():
            if stats["success"] > 0:
                avg_engagement = stats["total_engagement"] / stats["success"]
                success_rate = stats["success"] / stats["posts"] * 100
                best_hours.append({
                    "hour": hour,
                    "success_rate": round(success_rate, 2),
                    "avg_engagement": round(avg_engagement, 2),
                    "score": round(success_rate * 0.7 + avg_engagement * 0.3, 2)
                })
        
        best_hours.sort(key=lambda x: x["score"], reverse=True)
        
        # 内容洞察
        content_insights = self._analyze_content_patterns(records)
        
        return {
            "total_posts": total_posts,
            "performance_summary": {
                "success_rate": round(successful_posts / total_posts * 100, 2),
                "failure_rate": round(failed_posts / total_posts * 100, 2),
                "avg_daily_posts": round(total_posts / days, 2)
            },
            "platform_analysis": platform_analysis,
            "time_analysis": {
                "best_hours": best_hours[:5],  # 前5个最佳时间
                "hour_distribution": dict(hour_stats)
            },
            "content_insights": content_insights,
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            }
        }
    
    def _analyze_content_patterns(self, records: List[PublishRecord]) -> Dict[str, Any]:
        """分析内容模式"""
        # 分析标题长度与表现的关系
        title_performance = []
        content_length_performance = []
        
        for record in records:
            if record.status == "success" and record.title:
                title_length = len(record.title)
                content_length = len(record.content or "")
                engagement = (record.view_count or 0) + (record.like_count or 0) + \
                           (record.comment_count or 0) + (record.share_count or 0)
                
                title_performance.append({"length": title_length, "engagement": engagement})
                content_length_performance.append({"length": content_length, "engagement": engagement})
        
        # 计算最佳标题长度范围
        if title_performance:
            df_title = pd.DataFrame(title_performance)
            title_ranges = {
                "short": df_title[df_title["length"] <= 20]["engagement"].mean(),
                "medium": df_title[(df_title["length"] > 20) & (df_title["length"] <= 40)]["engagement"].mean(),
                "long": df_title[df_title["length"] > 40]["engagement"].mean()
            }
            
            # 移除NaN值
            title_ranges = {k: v for k, v in title_ranges.items() if not pd.isna(v)}
            best_title_range = max(title_ranges.items(), key=lambda x: x[1])[0] if title_ranges else "medium"
        else:
            best_title_range = "medium"
            title_ranges = {}
        
        # 分析失败原因
        failed_records = [r for r in records if r.status == "failed"]
        failure_reasons = Counter([r.error_message[:50] if r.error_message else "未知错误" 
                                 for r in failed_records])
        
        return {
            "best_title_length": best_title_range,
            "title_length_analysis": title_ranges,
            "total_successful_posts": len([r for r in records if r.status == "success"]),
            "total_failed_posts": len(failed_records),
            "common_failure_reasons": dict(failure_reasons.most_common(5))
        }
    
    def get_content_recommendations(self, platform: Optional[str] = None) -> Dict[str, Any]:
        """获取内容创作建议"""
        # 分析最近30天的数据
        performance_data = self.analyze_content_performance(days=30, platform=platform)
        
        recommendations = []
        
        # 基于平台表现给出建议
        if performance_data["platform_analysis"]:
            best_platform = max(performance_data["platform_analysis"].items(), 
                              key=lambda x: x[1]["avg_engagement"])
            recommendations.append({
                "type": "platform",
                "title": "最佳发布平台",
                "description": f"{best_platform[0]} 平台表现最佳，平均互动量 {best_platform[1]['avg_engagement']:.0f}",
                "priority": "high"
            })
        
        # 基于时间分析给出建议
        if performance_data["time_analysis"]["best_hours"]:
            best_hour = performance_data["time_analysis"]["best_hours"][0]
            recommendations.append({
                "type": "timing",
                "title": "最佳发布时间",
                "description": f"{best_hour['hour']}:00 时段发布效果最好，成功率 {best_hour['success_rate']:.1f}%",
                "priority": "medium"
            })
        
        # 基于内容模式给出建议
        content_insights = performance_data["content_insights"]
        if content_insights["best_title_length"]:
            title_advice = {
                "short": "使用简短标题（20字以内）",
                "medium": "使用中等长度标题（20-40字）",
                "long": "使用较长标题（40字以上）"
            }
            recommendations.append({
                "type": "content",
                "title": "标题长度建议", 
                "description": title_advice.get(content_insights["best_title_length"], "保持标题适中长度"),
                "priority": "medium"
            })
        
        # 基于失败原因给出建议
        if content_insights["common_failure_reasons"]:
            top_failure = list(content_insights["common_failure_reasons"].items())[0]
            recommendations.append({
                "type": "error_prevention",
                "title": "避免常见错误",
                "description": f"注意避免：{top_failure[0]}（占失败原因 {top_failure[1]} 次）",
                "priority": "high"
            })
        
        return {
            "recommendations": recommendations,
            "performance_summary": performance_data["performance_summary"],
            "analysis_date": datetime.now().isoformat()
        }


class HotspotAnalyzer:
    """热点分析器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_trending_topics(self, days: int = 7) -> Dict[str, Any]:
        """分析热门话题趋势"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 获取热点数据
        topics = self.db.query(HotTopic).filter(
            HotTopic.created_at >= start_date,
            HotTopic.created_at <= end_date
        ).order_by(desc(HotTopic.hot_score)).all()
        
        if not topics:
            return {
                "message": "暂无热点数据",
                "total_topics": 0,
                "platform_analysis": {},
                "category_distribution": {},
                "sentiment_analysis": {},
                "top_keywords": {},
                "daily_trends": {},
                "content_opportunities": [],
                "analysis_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                }
            }
        
        # 平台分析
        platform_stats = defaultdict(lambda: {"count": 0, "avg_score": 0, "total_score": 0})
        
        for topic in topics:
            platform_stats[topic.platform]["count"] += 1
            platform_stats[topic.platform]["total_score"] += topic.hot_score
        
        for platform in platform_stats:
            platform_stats[platform]["avg_score"] = round(
                platform_stats[platform]["total_score"] / platform_stats[platform]["count"], 2
            )
        
        # 分类分析
        category_stats = Counter([topic.category for topic in topics])
        
        # 情感分析
        sentiment_stats = Counter([topic.sentiment for topic in topics])
        
        # 关键词分析
        all_keywords = []
        for topic in topics:
            if topic.keywords:
                keywords = [kw.strip() for kw in topic.keywords.split(",")]
                all_keywords.extend(keywords)
        
        keyword_frequency = Counter(all_keywords)
        
        # 热度趋势分析（按天分组）
        daily_trends = defaultdict(lambda: {"count": 0, "avg_score": 0, "total_score": 0})
        
        for topic in topics:
            date_key = topic.created_at.strftime("%Y-%m-%d")
            daily_trends[date_key]["count"] += 1
            daily_trends[date_key]["total_score"] += topic.hot_score
        
        for date in daily_trends:
            daily_trends[date]["avg_score"] = round(
                daily_trends[date]["total_score"] / daily_trends[date]["count"], 2
            )
        
        # 生成创作机会
        opportunities = self._identify_content_opportunities(topics)
        
        return {
            "total_topics": len(topics),
            "platform_analysis": dict(platform_stats),
            "category_distribution": dict(category_stats.most_common(10)),
            "sentiment_analysis": dict(sentiment_stats),
            "top_keywords": dict(keyword_frequency.most_common(20)),
            "daily_trends": dict(daily_trends),
            "content_opportunities": opportunities,
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            }
        }
    
    def _identify_content_opportunities(self, topics: List[HotTopic]) -> List[Dict[str, Any]]:
        """识别内容创作机会"""
        opportunities = []
        
        # 按热度排序，取前10个
        top_topics = sorted(topics, key=lambda x: x.hot_score, reverse=True)[:10]
        
        for i, topic in enumerate(top_topics):
            opportunity = {
                "rank": i + 1,
                "topic": topic.title,
                "platform": topic.platform,
                "hot_score": topic.hot_score,
                "category": topic.category,
                "keywords": topic.keywords.split(",")[:5] if topic.keywords else [],
                "sentiment": topic.sentiment,
                "created_at": topic.created_at.isoformat(),
                "suggestion": self._generate_content_suggestion(topic)
            }
            opportunities.append(opportunity)
        
        return opportunities
    
    def _generate_content_suggestion(self, topic: HotTopic) -> str:
        """生成内容创作建议"""
        suggestions = {
            "positive": f"可以从正面角度解读'{topic.title}'，分享相关的成功经验或积极影响",
            "negative": f"可以分析'{topic.title}'背后的问题，提供解决方案或预防措施",
            "neutral": f"可以客观分析'{topic.title}'的多个方面，提供深度解读"
        }
        
        base_suggestion = suggestions.get(topic.sentiment, "可以从多个角度分析这个话题")
        
        if topic.category:
            category_tips = {
                "科技": "重点关注技术发展趋势和应用场景",
                "教育": "结合学习方法和教育理念",
                "娱乐": "注意娱乐性和话题性的平衡",
                "健康": "提供科学可靠的健康知识",
                "综合": "可以从多个维度进行分析"
            }
            base_suggestion += f"。{category_tips.get(topic.category, '')}"
        
        return base_suggestion


class AIUsageAnalyzer:
    """AI使用分析器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_ai_usage_patterns(self, days: int = 30) -> Dict[str, Any]:
        """分析AI使用模式"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 获取AI配置和使用记录
        configs = self.db.query(AIModelConfig).all()
        
        # 从系统日志中获取AI使用记录
        ai_logs = self.db.query(SystemLog).filter(
            SystemLog.module == "ai_models",
            SystemLog.created_at >= start_date,
            SystemLog.created_at <= end_date
        ).all()
        
        # 分析使用模式
        usage_by_model = defaultdict(lambda: {"count": 0, "total_tokens": 0})
        daily_usage = defaultdict(lambda: {"count": 0, "tokens": 0})
        
        for log in ai_logs:
            if log.details:
                try:
                    details = json.loads(log.details) if isinstance(log.details, str) else log.details
                    model_name = details.get("model", "unknown")
                    tokens = details.get("tokens", 0)
                    
                    usage_by_model[model_name]["count"] += 1
                    usage_by_model[model_name]["total_tokens"] += tokens
                    
                    date_key = log.created_at.strftime("%Y-%m-%d")
                    daily_usage[date_key]["count"] += 1
                    daily_usage[date_key]["tokens"] += tokens
                    
                except (json.JSONDecodeError, TypeError):
                    continue
        
        # 计算成本估算（简化版本）
        cost_analysis = {}
        for model, usage in usage_by_model.items():
            # 简化的成本计算（实际需要根据具体模型定价）
            estimated_cost = usage["total_tokens"] * 0.0001  # 假设每1000token成本0.1元
            cost_analysis[model] = {
                "usage_count": usage["count"],
                "total_tokens": usage["total_tokens"],
                "estimated_cost": round(estimated_cost, 4),
                "avg_tokens_per_use": round(usage["total_tokens"] / max(usage["count"], 1), 2)
            }
        
        # 使用效率分析
        efficiency_insights = self._analyze_usage_efficiency(usage_by_model, configs)
        
        return {
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "total_requests": sum(usage["count"] for usage in usage_by_model.values()),
            "total_tokens": sum(usage["total_tokens"] for usage in usage_by_model.values()),
            "usage_by_model": dict(usage_by_model),
            "daily_usage": dict(daily_usage),
            "cost_analysis": cost_analysis,
            "efficiency_insights": efficiency_insights
        }
    
    def _analyze_usage_efficiency(self, usage_data: Dict, configs: List[AIModelConfig]) -> Dict[str, Any]:
        """分析使用效率"""
        insights = {
            "most_used_model": None,
            "most_efficient_model": None,
            "recommendations": []
        }
        
        if usage_data:
            # 最常用模型
            most_used = max(usage_data.items(), key=lambda x: x[1]["count"])
            insights["most_used_model"] = {
                "model": most_used[0],
                "usage_count": most_used[1]["count"],
                "percentage": round(most_used[1]["count"] / sum(u["count"] for u in usage_data.values()) * 100, 2)
            }
            
            # 最高效模型（基于平均token使用量）
            if len(usage_data) > 1:
                most_efficient = min(usage_data.items(), 
                                   key=lambda x: x[1]["total_tokens"] / max(x[1]["count"], 1))
                insights["most_efficient_model"] = {
                    "model": most_efficient[0],
                    "avg_tokens": round(most_efficient[1]["total_tokens"] / max(most_efficient[1]["count"], 1), 2)
                }
        
        # 生成建议
        recommendations = []
        
        # 检查是否有未使用的模型
        used_models = set(usage_data.keys())
        all_models = set(config.name for config in configs if config.is_active)
        unused_models = all_models - used_models
        
        if unused_models:
            recommendations.append({
                "type": "unused_models",
                "message": f"发现 {len(unused_models)} 个未使用的AI模型配置，可以考虑测试使用",
                "models": list(unused_models)
            })
        
        # 检查token使用量过高的情况
        for model, usage in usage_data.items():
            avg_tokens = usage["total_tokens"] / max(usage["count"], 1)
            if avg_tokens > 2000:  # 假设阈值
                recommendations.append({
                    "type": "high_token_usage",
                    "message": f"{model} 模型平均token使用量较高（{avg_tokens:.0f}），建议优化提示词",
                    "model": model
                })
        
        insights["recommendations"] = recommendations
        return insights


class AnalyticsManager:
    """分析管理器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.content_analyzer = ContentAnalyzer(db)
        self.hotspot_analyzer = HotspotAnalyzer(db)
        self.ai_analyzer = AIUsageAnalyzer(db)
    
    def generate_comprehensive_report(self, days: int = 30) -> Dict[str, Any]:
        """生成综合分析报告"""
        report = {
            "report_date": datetime.now().isoformat(),
            "analysis_period": days,
            "content_performance": {},
            "hotspot_analysis": {},
            "ai_usage": {},
            "summary": {},
            "recommendations": []
        }
        
        try:
            # 内容表现分析
            report["content_performance"] = self.content_analyzer.analyze_content_performance(days)
            
            # 热点分析
            report["hotspot_analysis"] = self.hotspot_analyzer.analyze_trending_topics(min(days, 7))
            
            # AI使用分析
            report["ai_usage"] = self.ai_analyzer.analyze_ai_usage_patterns(days)
            
            # 生成摘要
            report["summary"] = self._generate_summary(report)
            
            # 获取建议
            content_recs = self.content_analyzer.get_content_recommendations()
            report["recommendations"] = content_recs.get("recommendations", [])
            
        except Exception as e:
            report["error"] = f"生成报告时出错: {str(e)}"
        
        return report
    
    def _generate_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """生成报告摘要"""
        summary = {
            "total_posts": 0,
            "success_rate": 0,
            "total_ai_requests": 0,
            "total_hotspots": 0,
            "key_insights": []
        }
        
        # 内容摘要
        if "content_performance" in report and report["content_performance"]:
            content_data = report["content_performance"]
            summary["total_posts"] = content_data.get("total_posts", 0)
            summary["success_rate"] = content_data.get("performance_summary", {}).get("success_rate", 0)
        
        # AI使用摘要
        if "ai_usage" in report and report["ai_usage"]:
            ai_data = report["ai_usage"]
            summary["total_ai_requests"] = ai_data.get("total_requests", 0)
        
        # 热点摘要
        if "hotspot_analysis" in report and report["hotspot_analysis"]:
            hotspot_data = report["hotspot_analysis"]
            summary["total_hotspots"] = hotspot_data.get("total_topics", 0)
        
        # 关键洞察
        insights = []
        
        if summary["success_rate"] > 80:
            insights.append("内容发布成功率较高，运营状况良好")
        elif summary["success_rate"] < 50:
            insights.append("内容发布成功率偏低，需要优化发布策略")
        
        if summary["total_ai_requests"] > 100:
            insights.append("AI使用频率较高，建议关注成本控制")
        
        if summary["total_hotspots"] > 50:
            insights.append("热点数据丰富，有助于内容创作决策")
        
        summary["key_insights"] = insights
        
        return summary


# 工具函数
def calculate_engagement_rate(views: int, likes: int, comments: int, shares: int) -> float:
    """计算互动率"""
    if views == 0:
        return 0.0
    
    total_engagement = likes + comments + shares
    return round((total_engagement / views) * 100, 2)


def categorize_performance(score: float) -> str:
    """根据分数分类表现"""
    if score >= 80:
        return "excellent"
    elif score >= 60:
        return "good"
    elif score >= 40:
        return "average"
    else:
        return "poor"


if __name__ == "__main__":
    # 测试代码
    from models import SessionLocal
    
    db = SessionLocal()
    try:
        manager = AnalyticsManager(db)
        
        # 生成综合报告
        report = manager.generate_comprehensive_report(days=30)
        print("综合分析报告:")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        
    finally:
        db.close()
