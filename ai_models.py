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
    def generate_text_stream(self, prompt: str, **kwargs):
        """流式生成文本"""
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
    
    def generate_text_stream(self, prompt: str, **kwargs):
        """流式生成文本"""
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
                stream=True
            )
            
            content = ""
            for chunk in response:
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        chunk_content = delta.content
                        content += chunk_content
                        yield {
                            "success": True,
                            "content": chunk_content,
                            "full_content": content,
                            "finished": False
                        }
            
            # 流式生成完成
            yield {
                "success": True,
                "content": "",
                "full_content": content,
                "finished": True
            }
            
        except Exception as e:
            yield {"error": str(e)}
    
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
    
    def generate_text_stream(self, prompt: str, **kwargs):
        """流式生成文本（模拟流式，因为百度API不支持真正的流式）"""
        try:
            # 百度API不支持真正的流式，所以我们模拟流式输出
            result = self.generate_text(prompt, **kwargs)
            
            if not result["success"]:
                yield {"error": result.get("error", "生成失败")}
                return
            
            content = result["content"]
            
            # 模拟逐字符流式输出
            import time
            current_content = ""
            for i, char in enumerate(content):
                current_content += char
                yield {
                    "success": True,
                    "content": char,
                    "full_content": current_content,
                    "finished": False
                }
                # 短暂延迟模拟流式效果
                time.sleep(0.01)
            
            # 流式生成完成
            yield {
                "success": True,
                "content": "",
                "full_content": content,
                "finished": True,
                "usage": result.get("usage", {})
            }
            
        except Exception as e:
            yield {"error": str(e)}
    
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
    
    def generate_text_stream(self, prompt: str, **kwargs):
        """流式生成文本（模拟流式，因为通义千问API可能不支持真正的流式）"""
        try:
            # 通义千问API不支持真正的流式，所以我们模拟流式输出
            result = self.generate_text(prompt, **kwargs)
            
            if not result["success"]:
                yield {"error": result.get("error", "生成失败")}
                return
            
            content = result["content"]
            
            # 模拟逐字符流式输出
            import time
            current_content = ""
            for i, char in enumerate(content):
                current_content += char
                yield {
                    "success": True,
                    "content": char,
                    "full_content": current_content,
                    "finished": False
                }
                # 短暂延迟模拟流式效果
                time.sleep(0.01)
            
            # 流式生成完成
            yield {
                "success": True,
                "content": "",
                "full_content": content,
                "finished": True,
                "usage": result.get("usage", {})
            }
            
        except Exception as e:
            yield {"error": str(e)}
    
    def test_connection(self) -> bool:
        """测试连接"""
        result = self.generate_text("测试", max_tokens=10)
        return result["success"]


class DeepSeekModel(BaseAIModel):
    """DeepSeek模型"""
    
    def __init__(self, config: AIModelConfig):
        super().__init__(config)
        self.base_url = config.api_secret or "https://api.deepseek.com"
        
    def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """生成文本"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}"
            }
            
            payload = {
                "model": self.config.model_name or "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
                "temperature": kwargs.get('temperature', self.config.temperature),
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                choice = result["choices"][0]
                usage = result.get("usage", {})
                
                return {
                    "success": True,
                    "content": choice["message"]["content"],
                    "usage": {
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0)
                    },
                    "model": result.get("model", self.config.model_name)
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                return {
                    "success": False,
                    "error": error_msg,
                    "content": None
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    def generate_text_stream(self, prompt: str, **kwargs):
        """流式生成文本"""
        try:
            headers = {
                "Content-Type": "application/json", 
                "Authorization": f"Bearer {self.config.api_key}"
            }
            
            payload = {
                "model": self.config.model_name or "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
                "temperature": kwargs.get('temperature', self.config.temperature),
                "stream": True
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=60
            )
            
            if response.status_code != 200:
                yield {"error": f"HTTP {response.status_code}: {response.text}"}
                return
            
            content = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]  # 移除 'data: ' 前缀
                        if data.strip() == '[DONE]':
                            break
                        
                        try:
                            chunk = json.loads(data)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    chunk_content = delta['content']
                                    content += chunk_content
                                    yield {
                                        "success": True,
                                        "content": chunk_content,
                                        "full_content": content,
                                        "finished": False
                                    }
                        except json.JSONDecodeError:
                            continue
            
            # 流式生成完成
            yield {
                "success": True,
                "content": "",
                "full_content": content,
                "finished": True
            }
            
        except Exception as e:
            yield {"error": str(e)}
    
    def test_connection(self) -> bool:
        """测试连接"""
        result = self.generate_text("测试连接", max_tokens=10)
        return result["success"]


class AIModelManager:
    """AI模型管理器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.models = {
            "openai": OpenAIModel,
            "baidu": BaiduModel,
            "dashscope": DashScopeModel,
            "deepseek": DeepSeekModel,
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
    
    def generate_content_stream(self, prompt: str, config_id: Optional[int] = None, **kwargs):
        """流式生成内容"""
        model = self.get_model(config_id)
        if not model:
            yield {"error": "未找到可用的AI模型"}
            return
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            for chunk in model.generate_text_stream(prompt, **kwargs):
                if "error" in chunk:
                    # 记录错误日志
                    log = SystemLog(
                        level="ERROR",
                        module="ai_models",
                        message=f"AI流式生成失败 - 模型: {model.config.name}",
                        details={
                            "config_id": model.config.id,
                            "prompt_length": len(prompt),
                            "error": chunk["error"]
                        }
                    )
                    self.db.add(log)
                    self.db.commit()
                    yield chunk
                    return
                
                yield chunk
                
                # 如果是最后一个chunk，更新使用统计
                if chunk.get("finished", False):
                    end_time = time.time()
                    model.config.usage_count += 1
                    if "usage" in chunk:
                        usage = chunk["usage"]
                        if "total_tokens" in usage:
                            model.config.total_tokens += usage["total_tokens"]
                    self.db.commit()
                    
                    # 记录成功日志
                    log = SystemLog(
                        level="INFO",
                        module="ai_models",
                        message=f"AI流式生成完成 - 模型: {model.config.name}",
                        details={
                            "config_id": model.config.id,
                            "prompt_length": len(prompt),
                            "success": True,
                            "response_time": end_time - start_time,
                            "content_length": len(chunk.get("full_content", "")),
                            "usage": chunk.get("usage")
                        }
                    )
                    self.db.add(log)
                    self.db.commit()
                    
        except Exception as e:
            # 记录异常日志
            end_time = time.time()
            log = SystemLog(
                level="ERROR",
                module="ai_models",
                message=f"AI流式生成异常 - 模型: {model.config.name}",
                details={
                    "config_id": model.config.id,
                    "prompt_length": len(prompt),
                    "error": str(e),
                    "response_time": end_time - start_time
                }
            )
            self.db.add(log)
            self.db.commit()
            yield {"error": str(e)}
    
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
    
    COMPREHENSIVE_CREATION = """
你是一个专业的新媒体内容创作专家，请根据以下主题和要求，一次性生成完整的内容方案：

主题：{topic}
平台：{platform}
风格：{style}
目标受众：{audience}
内容长度：{length}
关键字：{keywords}
特殊要求：{requirements}

请按以下格式生成完整的内容方案：

【标题】
生成3个不同风格的标题选项，每个标题都要：
- 吸引眼球，激发点击欲望
- 符合{platform}平台的特点
- 包含关键字：{keywords}
- 避免标题党，内容要有价值

【正文】
创建一篇完整的{length}内容，包括：
- 开头：吸引注意力的引言
- 主体：3-5个核心观点，每个观点要有具体例子或论据
- 结尾：总结和行动号召
- 确保内容符合{style}风格
- 自然融入关键字：{keywords}
- 针对{audience}的兴趣点

【推荐标签】
推荐5-8个相关的标签（hashtag），要求：
- 与主题高度相关
- 符合{platform}平台习惯
- 包含热门和细分标签的组合
- 有助于内容传播和发现

请确保整个内容方案连贯统一，标题、正文和标签都围绕同一个主题展开。
"""
    
    CONTENT_REWRITE = """
你是一个专业的内容编辑，请对以下内容进行改写，保持核心观点不变但改变表达方式：

原内容：{original_content}
改写类型：{rewrite_type}
改写强度：{rewrite_strength}
目标平台：{platform}
目标受众：{audience}
风格要求：{style}
长度要求：{length_requirement}
关键字：{keywords}
特殊要求：{requirements}

改写要求：
1. 保持原文的核心观点和主要信息
2. 根据改写类型调整：
   - 风格转换：改变语言风格和表达方式
   - 平台适配：调整为适合{platform}平台的格式
   - 受众调整：针对{audience}重新组织内容
   - 长度调整：根据{length_requirement}调整内容长度
3. 改写强度：
   - 轻度：保持原文结构，主要改变用词和句式
   - 中度：调整段落结构，重新组织内容
   - 重度：完全重写，仅保留核心观点
4. 确保内容的原创性和可读性
5. 符合{platform}平台的风格特点
6. 自然融入关键字：{keywords}
7. 针对{audience}的阅读习惯和兴趣点

请提供改写后的内容：
""" 