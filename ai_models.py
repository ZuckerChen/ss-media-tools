"""
AI模型管理模块
支持多个AI模型提供商的统一接入和管理
"""
import json
import time
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import openai
import requests
from sqlalchemy.orm import Session
from config import settings, AI_MODEL_CONFIGS
from models import AIModelConfig, SystemLog


class BaseAIModel(ABC):
    """AI模型基类"""
    
    def __init__(self, config: AIModelConfig):
        self.config = config
        
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """生成文本"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """测试连接"""
        pass


class OpenAIModel(BaseAIModel):
    """OpenAI模型"""
    
    def __init__(self, config: AIModelConfig):
        super().__init__(config)
        openai.api_key = config.api_key
        if hasattr(config, 'api_base') and config.api_secret:
            openai.api_base = config.api_secret  # 用于自定义API地址
    
    def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """生成文本"""
        try:
            response = openai.ChatCompletion.create(
                model=self.config.model_name or "gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
                n=kwargs.get('n', 1),
                stop=kwargs.get('stop'),
            )
            
            content = response.choices[0].message.content
            usage = response.usage
            
            return {
                "success": True,
                "content": content,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                },
                "model": response.model
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            response = openai.ChatCompletion.create(
                model=self.config.model_name or "gpt-3.5-turbo",
                messages=[{"role": "user", "content": "测试连接"}],
                max_tokens=10
            )
            return True
        except Exception:
            return False


class BaiduModel(BaseAIModel):
    """百度文心一言模型"""
    
    def __init__(self, config: AIModelConfig):
        super().__init__(config)
        self.access_token = None
        self._get_access_token()
    
    def _get_access_token(self):
        """获取访问令牌"""
        try:
            url = "https://aip.baidubce.com/oauth/2.0/token"
            params = {
                "grant_type": "client_credentials",
                "client_id": self.config.api_key,
                "client_secret": self.config.api_secret
            }
            response = requests.post(url, params=params)
            result = response.json()
            self.access_token = result.get("access_token")
        except Exception as e:
            print(f"获取百度访问令牌失败: {e}")
    
    def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """生成文本"""
        if not self.access_token:
            return {"success": False, "error": "未获取到访问令牌", "content": None}
        
        try:
            model_name = self.config.model_name or "ernie-bot-turbo"
            url = f"https://aip.baidubce.com/rpc/2.0/ai/v1/chat/{model_name}?access_token={self.access_token}"
            
            payload = {
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get('temperature', self.config.temperature),
                "max_output_tokens": kwargs.get('max_tokens', self.config.max_tokens)
            }
            
            response = requests.post(url, json=payload)
            result = response.json()
            
            if "result" in result:
                return {
                    "success": True,
                    "content": result["result"],
                    "usage": result.get("usage", {}),
                    "model": model_name
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error_msg", "未知错误"),
                    "content": None
                }
        except Exception as e:
            return {"success": False, "error": str(e), "content": None}
    
    def test_connection(self) -> bool:
        """测试连接"""
        result = self.generate_text("测试", max_tokens=10)
        return result["success"]


class DashScopeModel(BaseAIModel):
    """阿里通义千问模型"""
    
    def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """生成文本"""
        try:
            import dashscope
            dashscope.api_key = self.config.api_key
            
            response = dashscope.Generation.call(
                model=self.config.model_name or "qwen-turbo",
                prompt=prompt,
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature)
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "content": response.output.text,
                    "usage": response.usage,
                    "model": self.config.model_name
                }
            else:
                return {
                    "success": False,
                    "error": response.message,
                    "content": None
                }
        except Exception as e:
            return {"success": False, "error": str(e), "content": None}
    
    def test_connection(self) -> bool:
        """测试连接"""
        result = self.generate_text("测试", max_tokens=10)
        return result["success"]


class AIModelManager:
    """AI模型管理器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.models = {
            "openai": OpenAIModel,
            "baidu": BaiduModel,
            "dashscope": DashScopeModel,
        }
    
    def get_model(self, config_id: Optional[int] = None) -> Optional[BaseAIModel]:
        """获取AI模型实例"""
        if config_id:
            config = self.db.query(AIModelConfig).filter(
                AIModelConfig.id == config_id,
                AIModelConfig.is_active == True
            ).first()
        else:
            # 获取默认模型
            config = self.db.query(AIModelConfig).filter(
                AIModelConfig.is_default == True,
                AIModelConfig.is_active == True
            ).first()
        
        if not config:
            return None
        
        model_class = self.models.get(config.provider)
        if not model_class:
            return None
        
        return model_class(config)
    
    def generate_content(self, prompt: str, config_id: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """生成内容"""
        model = self.get_model(config_id)
        if not model:
            return {"success": False, "error": "未找到可用的AI模型", "content": None}
        
        # 记录使用
        start_time = time.time()
        result = model.generate_text(prompt, **kwargs)
        end_time = time.time()
        
        # 更新使用统计
        if result["success"]:
            model.config.usage_count += 1
            if "usage" in result and "total_tokens" in result["usage"]:
                model.config.total_tokens += result["usage"]["total_tokens"]
            self.db.commit()
        
        # 记录日志
        log = SystemLog(
            level="INFO" if result["success"] else "ERROR",
            module="ai_models",
            message=f"AI内容生成 - 模型: {model.config.name}",
            details={
                "config_id": model.config.id,
                "prompt_length": len(prompt),
                "success": result["success"],
                "error": result.get("error"),
                "response_time": end_time - start_time,
                "usage": result.get("usage")
            }
        )
        self.db.add(log)
        self.db.commit()
        
        return result
    
    def list_configs(self) -> List[AIModelConfig]:
        """列出所有AI模型配置"""
        return self.db.query(AIModelConfig).filter(AIModelConfig.is_active == True).all()
    
    def add_config(self, name: str, provider: str, api_key: str, **kwargs) -> AIModelConfig:
        """添加AI模型配置"""
        config = AIModelConfig(
            name=name,
            provider=provider,
            api_key=api_key,
            api_secret=kwargs.get('api_secret'),
            model_name=kwargs.get('model_name'),
            max_tokens=kwargs.get('max_tokens', 2000),
            temperature=kwargs.get('temperature', 0.7),
            is_default=kwargs.get('is_default', False)
        )
        
        # 如果设为默认，取消其他默认设置
        if config.is_default:
            self.db.query(AIModelConfig).filter(AIModelConfig.is_default == True).update({
                "is_default": False
            })
        
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def update_config(self, config_id: int, **kwargs) -> Optional[AIModelConfig]:
        """更新AI模型配置"""
        config = self.db.query(AIModelConfig).filter(AIModelConfig.id == config_id).first()
        if not config:
            return None
        
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        # 如果设为默认，取消其他默认设置
        if kwargs.get('is_default'):
            self.db.query(AIModelConfig).filter(
                AIModelConfig.id != config_id,
                AIModelConfig.is_default == True
            ).update({"is_default": False})
        
        self.db.commit()
        self.db.refresh(config)
        return config
    
    def test_config(self, config_id: int) -> Dict[str, Any]:
        """测试AI模型配置"""
        model = self.get_model(config_id)
        if not model:
            return {"success": False, "error": "配置不存在"}
        
        try:
            success = model.test_connection()
            return {"success": success, "error": None if success else "连接测试失败"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_usage_stats(self, config_id: Optional[int] = None) -> Dict[str, Any]:
        """获取使用统计"""
        if config_id:
            configs = self.db.query(AIModelConfig).filter(AIModelConfig.id == config_id).all()
        else:
            configs = self.db.query(AIModelConfig).all()
        
        stats = []
        total_usage = 0
        total_tokens = 0
        
        for config in configs:
            stats.append({
                "id": config.id,
                "name": config.name,
                "provider": config.provider,
                "usage_count": config.usage_count,
                "total_tokens": config.total_tokens,
                "is_active": config.is_active,
                "is_default": config.is_default
            })
            total_usage += config.usage_count
            total_tokens += config.total_tokens
        
        return {
            "configs": stats,
            "total_usage": total_usage,
            "total_tokens": total_tokens
        }


# 内容生成相关的提示词模板
class PromptTemplates:
    """提示词模板"""
    
    TITLE_GENERATION = """
你是一个专业的新媒体内容创作专家，请根据以下主题和要求生成吸引人的标题：

主题：{topic}
平台：{platform}
风格：{style}
要求：{requirements}

请生成5个不同风格的标题，每个标题都要：
1. 吸引眼球，激发点击欲望
2. 符合{platform}平台的特点
3. 字数控制在适当范围内
4. 避免标题党，内容要有价值

格式：请按编号列出5个标题
"""
    
    CONTENT_OUTLINE = """
你是一个专业的内容策划师，请为以下标题制作详细的内容大纲：

标题：{title}
平台：{platform}
目标受众：{audience}
内容长度：{length}

请创建一个结构清晰的内容大纲，包括：
1. 开头（吸引注意力）
2. 主体内容（3-5个要点）
3. 结尾（总结和行动号召）

要求：
- 逻辑清晰，层次分明
- 每个部分都要有具体的内容提示
- 符合{platform}平台的内容特点
- 能够引起{audience}的共鸣
"""
    
    CONTENT_REWRITE = """
你是一个专业的内容编辑，请对以下内容进行改写，保持核心观点不变但改变表达方式：

原内容：{original_content}
改写要求：{requirements}
目标平台：{platform}

改写要求：
1. 保持原文的核心观点和主要信息
2. 改变句式结构和表达方式
3. 确保内容的原创性
4. 符合{platform}平台的风格
5. 保持内容的可读性和吸引力

请提供改写后的内容：
""" 