"""
自媒体运营工具 - Streamlit前端应用
"""
import streamlit as st
import requests
import json
from typing import Dict, Any, Optional, List, Iterator
import pandas as pd
from datetime import datetime
import time

# 配置页面
st.set_page_config(
    page_title="自媒体运营工具",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API基础URL
API_BASE_URL = "http://localhost:8000"

# 工具函数
def call_api(endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
    """调用API接口"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        # 添加超时设置
        timeout = 30
        
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=timeout)
        elif method == "DELETE":
            response = requests.delete(url, timeout=timeout)
        else:
            return {
                "success": False,
                "error": f"不支持的HTTP方法: {method}",
                "data": {},
                "status_code": 400
            }
        
        # 检查响应状态
        if response.status_code >= 400:
            try:
                error_data = response.json()
                error_message = error_data.get('detail', error_data.get('message', f'HTTP {response.status_code}'))
            except:
                error_message = f'HTTP {response.status_code} - {response.reason}'
            
            return {
                "success": False,
                "error": error_message,
                "data": {},
                "status_code": response.status_code
            }
        
        # 解析响应数据
        try:
            response_data = response.json() if response.content else {}
        except json.JSONDecodeError:
            response_data = {"raw_response": response.text}
        
        return {
            "success": True,
            "data": response_data,
            "status_code": response.status_code
        }
        
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "请求超时，请检查网络连接或稍后重试",
            "data": {},
            "status_code": 408
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "无法连接到服务器，请检查后端服务是否正常运行",
            "data": {},
            "status_code": 503
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"请求异常: {str(e)}",
            "data": {},
            "status_code": 500
        }


def call_stream_api(endpoint: str, data: Dict = None) -> Iterator[Dict[str, Any]]:
    """调用流式API接口"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        timeout = 60
        response = requests.post(url, json=data, stream=True, timeout=timeout)
        
        if response.status_code != 200:
            try:
                error_data = response.json()
                error_message = error_data.get('detail', f'HTTP {response.status_code}')
            except:
                error_message = f'HTTP {response.status_code} - {response.reason}'
            
            yield {
                "success": False,
                "error": error_message,
                "status_code": response.status_code
            }
            return
        
        # 处理流式响应
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # 移除 'data: ' 前缀
                    if data_str.strip() == '[DONE]':
                        break
                    
                    try:
                        chunk = json.loads(data_str)
                        yield chunk
                    except json.JSONDecodeError:
                        continue
    
    except requests.exceptions.Timeout:
        yield {
            "success": False,
            "error": "请求超时，请检查网络连接或稍后重试",
            "status_code": 408
        }
    except requests.exceptions.ConnectionError:
        yield {
            "success": False,
            "error": "无法连接到服务器，请检查后端服务是否正常运行",
            "status_code": 503
        }
    except Exception as e:
        yield {
            "success": False,
            "error": f"请求异常: {str(e)}",
            "status_code": 500
        }


def format_datetime(dt_str: str) -> str:
    """格式化日期时间"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return dt_str


# 初始化session state
def init_session_state():
    """初始化session state"""
    if 'generated_content' not in st.session_state:
        st.session_state.generated_content = {}
    if 'last_operation' not in st.session_state:
        st.session_state.last_operation = None
    if 'operation_result' not in st.session_state:
        st.session_state.operation_result = None

def save_operation_result(operation_type: str, result: Dict[str, Any], additional_data: Dict = None):
    """保存操作结果到session state"""
    st.session_state.last_operation = operation_type
    st.session_state.operation_result = {
        'result': result,
        'timestamp': datetime.now().isoformat(),
        'additional_data': additional_data or {}
    }

def display_operation_result():
    """显示保存的操作结果"""
    if st.session_state.operation_result and st.session_state.last_operation:
        result_data = st.session_state.operation_result
        result = result_data['result']
        
        if result['success']:
            st.success(f"✅ {st.session_state.last_operation}成功!")
            # 根据操作类型显示不同的结果
            if 'content' in result.get('data', {}):
                st.markdown(result['data']['content'])
            elif 'titles' in result.get('data', {}):
                st.markdown("### 生成的标题：")
                st.markdown(result['data']['titles'])
            elif 'outline' in result.get('data', {}):
                st.markdown("### 内容大纲：")
                st.markdown(result['data']['outline'])
        else:
            st.error(f"❌ {st.session_state.last_operation}失败: {result.get('error', '未知错误')}")

def show_success_feedback(operation: str, details: Dict = None):
    """显示成功操作的详细反馈"""
    # 主要成功消息
    st.success(f"🎉 {operation}成功完成！")
    
    # 显示详细信息
    if details:
        info_cols = st.columns(len(details))
        for i, (key, value) in enumerate(details.items()):
            with info_cols[i]:
                st.metric(key, value)
    
    # 显示时间戳
    st.caption(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def show_operation_summary(operation_type: str, success_count: int, total_count: int, details: List[Dict] = None):
    """显示批量操作的汇总信息"""
    if success_count == total_count:
        st.success(f"🎉 {operation_type}全部成功！({success_count}/{total_count})")
    elif success_count > 0:
        st.warning(f"⚠️ {operation_type}部分成功 ({success_count}/{total_count})")
    else:
        st.error(f"❌ {operation_type}全部失败 ({success_count}/{total_count})")
    
    # 显示详细结果
    if details:
        with st.expander("📊 详细结果"):
            for detail in details:
                status_icon = "✅" if detail.get('success') else "❌"
                st.write(f"{status_icon} {detail.get('item', '')}: {detail.get('message', '')}")


def display_stream_content(placeholder, endpoint: str, data: Dict, content_key: str = "content", full_content_key: str = "full_content"):
    """显示流式内容生成"""
    full_content = ""
    error_occurred = False
    
    try:
        for chunk in call_stream_api(endpoint, data):
            if "error" in chunk:
                placeholder.error(f"❌ 生成失败: {chunk['error']}")
                error_occurred = True
                break
            
            if chunk.get("success", True):
                # 获取当前块的内容
                chunk_content = chunk.get(content_key, "")
                if chunk_content:
                    full_content += chunk_content
                    # 实时更新显示
                    placeholder.markdown(full_content)
                
                # 检查是否完成
                if chunk.get("finished", False):
                    # 显示最终结果和使用统计
                    usage = chunk.get("usage", {})
                    if usage:
                        st.caption(f"📊 Token使用: {usage.get('total_tokens', 0)} | 完成时间: {datetime.now().strftime('%H:%M:%S')}")
                    break
        
        if not error_occurred:
            st.success("✅ 内容生成完成！")
            return full_content
        else:
            return None
            
    except Exception as e:
        placeholder.error(f"❌ 流式生成异常: {str(e)}")
        return None


def create_stream_ui(title: str, endpoint: str, data: Dict, content_key: str = "content"):
    """创建流式生成UI组件"""
    st.subheader(f"🔄 {title}")
    
    # 创建占位符
    content_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # 开始流式生成
    with status_placeholder:
        st.info("🔄 正在生成内容，请稍候...")
    
    # 显示流式内容
    result = display_stream_content(content_placeholder, endpoint, data, content_key)
    
    # 清除状态信息
    status_placeholder.empty()
    
    return result

# 初始化
init_session_state()

# 侧边栏导航
st.sidebar.title("🚀 自媒体运营工具")
page = st.sidebar.selectbox(
    "选择功能模块",
    ["🏠 首页", "🤖 AI模型管理", "✍️ 内容创作", "📝 草稿管理", "🚀 发布管理", "🔥 热点分析", "📊 使用统计"]
)

# 首页
if page == "🏠 首页":
    st.title("🎯 自媒体运营工具")
    st.markdown("### 一站式智能内容创作平台")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("🤖 **AI模型管理**\n\n集成多个AI大模型\n统一配置和管理")
    
    with col2:
        st.success("✍️ **智能创作**\n\n标题生成、大纲制作\n内容改写、原创检测")
    
    with col3:
        st.warning("📝 **草稿管理**\n\n版本控制、分类存储\n协作编辑、发布管理")
    
    st.markdown("---")
    
    # 系统状态检查
    st.subheader("📈 系统状态")
    
    # 检查API连接
    health_result = call_api("/health")
    if health_result["success"]:
        st.success("✅ API服务正常运行")
        
        # 获取统计信息
        stats_result = call_api("/api/ai/stats")
        if stats_result["success"]:
            stats = stats_result["data"]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("AI模型数量", len(stats.get("configs", [])))
            with col2:
                st.metric("总使用次数", stats.get("total_usage", 0))
            with col3:
                st.metric("总Token消耗", stats.get("total_tokens", 0))
            with col4:
                st.metric("活跃配置", len([c for c in stats.get("configs", []) if c["is_active"]]))
    else:
        st.error("❌ API服务连接失败，请检查后端是否启动")


# AI模型管理页面
elif page == "🤖 AI模型管理":
    st.title("🤖 AI模型管理")
    
    # 获取模型配置列表
    configs_result = call_api("/api/ai/configs")
    
    if not configs_result["success"]:
        st.error(f"获取模型配置失败: {configs_result.get('error', '未知错误')}")
        st.stop()
    
    configs = configs_result["data"]
    
    # 添加新配置
    with st.expander("➕ 添加新的AI模型配置"):
        with st.form("add_config"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("配置名称", placeholder="例如: 我的GPT模型")
                provider = st.selectbox("提供商", ["deepseek", "openai", "baidu", "dashscope", "tencent"])
                api_key = st.text_input("API密钥", type="password")
            
            with col2:
                api_secret = st.text_input("API密钥2 (可选)", type="password")
                model_name = st.text_input("模型名称", placeholder="例如: gpt-3.5-turbo")
                max_tokens = st.number_input("最大Token数", value=2000, min_value=1, max_value=32000)
            
            col3, col4 = st.columns(2)
            with col3:
                temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
            with col4:
                is_default = st.checkbox("设为默认模型")
            
            if st.form_submit_button("添加配置"):
                config_data = {
                    "name": name,
                    "provider": provider,
                    "api_key": api_key,
                    "api_secret": api_secret if api_secret else None,
                    "model_name": model_name if model_name else None,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "is_default": is_default
                }
                
                result = call_api("/api/ai/configs", "POST", config_data)
                if result["success"]:
                    st.success("配置添加成功！")
                    st.rerun()
                else:
                    st.error(f"添加失败: {result.get('error', '未知错误')}")
    
    # 显示现有配置
    st.subheader("📋 现有配置")
    
    if not configs:
        st.info("暂无AI模型配置，请先添加配置")
    else:
        for config in configs:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    status_icon = "✅" if config["is_active"] else "❌"
                    default_icon = "⭐" if config["is_default"] else ""
                    st.write(f"{status_icon} **{config['name']}** {default_icon}")
                    st.write(f"🏢 {config['provider']} | 🧠 {config['model_name']}")
                
                with col2:
                    st.metric("使用次数", config["usage_count"])
                
                with col3:
                    st.metric("消耗Token", config["total_tokens"])
                
                with col4:
                    # 测试连接按钮
                    test_button_key = f"test_{config['id']}"
                    if st.button(f"🔗 测试", key=test_button_key):
                        with st.spinner("测试连接中..."):
                            test_result = call_api(f"/api/ai/configs/{config['id']}/test", "POST")
                            if test_result["success"]:
                                if test_result["data"].get("status") == "success":
                                    st.success("✅ 连接正常！")
                                else:
                                    st.error(f"❌ 连接失败: {test_result['data'].get('message', '未知错误')}")
                            else:
                                st.error(f"❌ 测试失败: {test_result.get('error', '未知错误')}")
                                # 显示详细错误信息
                                if test_result.get('status_code'):
                                    st.error(f"状态码: {test_result['status_code']}")
                        
                        # 短暂延迟后重新运行，确保状态更新
                        time.sleep(0.1)
                
                st.write(f"⏰ 创建时间: {format_datetime(config['created_at'])}")
                st.divider()


# 内容创作页面
elif page == "✍️ 内容创作":
    st.title("✍️ 智能内容创作")
    
    # 获取可用的AI模型
    configs_result = call_api("/api/ai/configs")
    if configs_result["success"]:
        configs = configs_result["data"]
        active_configs = [c for c in configs if c["is_active"]]
        
        if not active_configs:
            st.error("没有可用的AI模型配置，请先在AI模型管理页面添加配置")
            st.stop()
    else:
        st.error("无法获取AI模型配置")
        st.stop()
    
    # 模型选择
    config_options = {f"{c['name']} ({c['provider']})": c['id'] for c in active_configs}
    selected_config_name = st.selectbox("选择AI模型", list(config_options.keys()))
    selected_config_id = config_options[selected_config_name]
    
    # 创作功能选择
    creation_type = st.radio(
        "选择创作类型",
        ["🎯 综合创作", "🔄 内容改写"],
        horizontal=True
    )
    
    if creation_type == "🎯 综合创作":
        st.subheader("🎯 综合创作 - 一键生成完整内容")
        st.markdown("🚀 **根据主题一次性生成标题、正文和推荐标签**")
        
        # 流式输出选项
        enable_stream = st.checkbox("🔄 启用流式输出", value=True, help="实时显示AI生成过程，提供更好的用户体验")
        
        with st.form("comprehensive_creation"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 基本信息")
                topic = st.text_area("主题内容", placeholder="请输入要创作的主题内容...", height=100)
                platform = st.selectbox("目标平台", ["通用", "微信公众号", "微博", "小红书", "抖音", "知乎", "头条号"])
                style = st.selectbox("创作风格", ["专业", "通俗易懂", "风趣幽默", "权威严谨", "温暖亲切", "时尚潮流", "科技感"])
            
            with col2:
                st.markdown("#### 个性化设置")
                audience = st.text_input("目标受众", placeholder="例如：年轻女性、科技爱好者、职场人士...", value="通用受众")
                length = st.selectbox("内容长度", ["短文(500-800字)", "中等长度(800-1200字)", "长文(1200-2000字)", "深度文章(2000+字)"])
                keywords = st.text_input("关键词", placeholder="用逗号分隔，例如：健康,养生,生活方式")
                requirements = st.text_area("特殊要求", placeholder="例如：包含具体案例、添加数据支撑、突出实用性等...", height=80)
            
            if st.form_submit_button("🚀 开始创作"):
                if not topic:
                    st.error("请输入主题内容")
                else:
                    data = {
                        "topic": topic,
                        "platform": platform,
                        "style": style,
                        "audience": audience,
                        "length": length,
                        "keywords": keywords,
                        "requirements": requirements,
                        "config_id": selected_config_id
                    }
                    
                    generated_content = ""
                    
                    if enable_stream:
                        # 流式生成
                        st.markdown("### 📝 AI正在创作中...")
                        content_placeholder = st.empty()
                        
                        try:
                            full_content = ""
                            for chunk in call_stream_api("/api/content/comprehensive/stream", data):
                                if "error" in chunk:
                                    st.error(f"❌ 生成失败: {chunk['error']}")
                                    break
                                
                                if chunk.get("success", True):
                                    chunk_content = chunk.get("content", "")
                                    if chunk_content:
                                        full_content += chunk_content
                                        content_placeholder.markdown(full_content)
                                    
                                    if chunk.get("finished", False):
                                        usage = chunk.get("usage", {})
                                        if usage:
                                            st.info(f"📊 本次消耗Token: {usage.get('total_tokens', '未知')} | 完成时间: {datetime.now().strftime('%H:%M:%S')}")
                                        st.success("✅ 综合创作完成！")
                                        generated_content = full_content
                                        break
                        except Exception as e:
                            st.error(f"❌ 流式生成异常: {str(e)}")
                    else:
                        # 普通生成
                        with st.spinner("AI正在进行综合创作..."):
                            result = call_api("/api/content/comprehensive", "POST", data)
                            
                            if result["success"]:
                                st.success("✅ 综合创作成功！")
                                st.markdown("### 📝 创作结果：")
                                st.markdown(result["data"]["content"])
                                generated_content = result["data"]["content"]
                                
                                # 显示使用统计
                                if "usage" in result["data"]:
                                    usage = result["data"]["usage"]
                                    st.info(f"📊 本次消耗Token: {usage.get('total_tokens', '未知')}")
                            else:
                                st.error(f"❌ 生成失败: {result.get('error', '未知错误')}")
                                if result.get('status_code'):
                                    st.error(f"状态码: {result['status_code']}")
                                
                                # 显示调试信息
                                with st.expander("🔍 详细错误信息"):
                                    st.json(result)
                    
                    # 保存生成的内容到session state（只在生成成功时）
                    if generated_content:
                        st.session_state[f"generated_comprehensive_{hash(topic)}"] = {
                            "title": topic[:50] + "..." if len(topic) > 50 else topic,
                            "content": generated_content,
                            "category": "综合创作",
                            "platform_type": platform,
                            "ai_generated": True
                        }
        
        # 表单外部：显示保存草稿按钮（如果有生成的内容）
        for key in st.session_state.keys():
            if key.startswith("generated_comprehensive_"):
                draft_data = st.session_state[key]
                save_draft_key = f"save_draft_{key}"
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.info(f"📝 综合创作结果: {draft_data['title']}")
                with col2:
                    if st.button("💾 保存为草稿", key=save_draft_key):
                        with st.spinner("正在保存草稿..."):
                            draft_result = call_api("/api/drafts", "POST", draft_data)
                            if draft_result["success"]:
                                st.success("✅ 已保存为草稿！")
                                st.info(f"草稿ID: {draft_result['data'].get('id', '未知')}")
                                # 保存成功后移除session state
                                del st.session_state[key]
                                st.rerun()
                            else:
                                st.error(f"❌ 保存失败: {draft_result.get('error', '未知错误')}")
                                if draft_result.get('status_code'):
                                    st.error(f"状态码: {draft_result['status_code']}")
                break  # 只显示最新的一个
    
    elif creation_type == "🔄 内容改写":
        st.subheader("🔄 智能内容改写")
        st.markdown("🎨 **将现有内容改写为不同风格、适配不同平台的版本**")
        
        # 流式输出选项
        enable_stream = st.checkbox("🔄 启用流式输出", value=True, help="实时显示AI生成过程，提供更好的用户体验", key="rewrite_stream")
        
        with st.form("content_rewrite"):
            st.markdown("#### 原始内容")
            original_content = st.text_area("原始内容", placeholder="请输入需要改写的内容...", height=200)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 改写设置")
                rewrite_type = st.selectbox("改写类型", ["风格转换", "平台适配", "受众调整", "长度调整"])
                rewrite_strength = st.selectbox("改写强度", ["轻度", "中度", "重度"])
                platform = st.selectbox("目标平台", ["通用", "微信公众号", "微博", "小红书", "抖音", "知乎", "头条号"])
                audience = st.text_input("目标受众", placeholder="例如：年轻女性、科技爱好者、职场人士...", value="通用受众")
            
            with col2:
                st.markdown("#### 个性化选项")
                style = st.selectbox("风格要求", ["专业", "通俗易懂", "风趣幽默", "权威严谨", "温暖亲切", "时尚潮流", "科技感"])
                length_requirement = st.selectbox("长度要求", ["保持原长度", "压缩内容", "扩展内容", "大幅扩展"])
                keywords = st.text_input("关键词", placeholder="需要融入的关键词，用逗号分隔")
                requirements = st.text_area("特殊要求", placeholder="例如：更口语化、更正式、增加案例等...", height=80)
            
            if st.form_submit_button("✨ 开始改写"):
                if not original_content:
                    st.error("请输入原始内容")
                else:
                    data = {
                        "original_content": original_content,
                        "rewrite_type": rewrite_type,
                        "rewrite_strength": rewrite_strength,
                        "platform": platform,
                        "audience": audience,
                        "style": style,
                        "length_requirement": length_requirement,
                        "keywords": keywords,
                        "requirements": requirements,
                        "config_id": selected_config_id
                    }
                    
                    generated_rewrite = ""
                    
                    if enable_stream:
                        # 流式生成
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("### 📄 原始内容：")
                            st.markdown(original_content)
                        
                        with col2:
                            st.markdown("### ✨ 改写结果：")
                            content_placeholder = st.empty()
                            
                            try:
                                full_content = ""
                                for chunk in call_stream_api("/api/content/rewrite/stream", data):
                                    if "error" in chunk:
                                        st.error(f"❌ 改写失败: {chunk['error']}")
                                        break
                                    
                                    if chunk.get("success", True):
                                        chunk_content = chunk.get("content", "")
                                        if chunk_content:
                                            full_content += chunk_content
                                            content_placeholder.markdown(full_content)
                                        
                                        if chunk.get("finished", False):
                                            usage = chunk.get("usage", {})
                                            if usage:
                                                st.info(f"📊 本次消耗Token: {usage.get('total_tokens', '未知')} | 完成时间: {datetime.now().strftime('%H:%M:%S')}")
                                            st.success("✅ 内容改写完成！")
                                            generated_rewrite = full_content
                                            break
                            except Exception as e:
                                st.error(f"❌ 流式生成异常: {str(e)}")
                    else:
                        # 普通生成
                        with st.spinner("AI正在改写内容..."):
                            result = call_api("/api/content/rewrite", "POST", data)
                            
                            if result["success"]:
                                st.success("✅ 内容改写成功！")
                                
                                # 显示使用统计
                                if "usage" in result["data"]:
                                    usage = result["data"]["usage"]
                                    st.info(f"📊 本次消耗Token: {usage.get('total_tokens', '未知')}")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown("### 📄 原始内容：")
                                    st.markdown(original_content)
                                
                                with col2:
                                    st.markdown("### ✨ 改写结果：")
                                    st.markdown(result["data"]["rewritten_content"])
                                    generated_rewrite = result["data"]["rewritten_content"]
                            else:
                                st.error(f"❌ 改写失败: {result.get('error', '未知错误')}")
                                if result.get('status_code'):
                                    st.error(f"状态码: {result['status_code']}")
                                
                                # 显示调试信息
                                with st.expander("🔍 详细错误信息"):
                                    st.json(result)
                    
                    # 保存改写结果到session state（只在改写成功时）
                    if generated_rewrite:
                        st.session_state[f"generated_rewrite_{hash(original_content)}"] = {
                            "title": f"改写版本 - {original_content[:30]}..." if len(original_content) > 30 else f"改写版本 - {original_content}",
                            "content": generated_rewrite,
                            "category": "内容改写",
                            "platform_type": platform,
                            "ai_generated": True
                        }
        
        # 表单外部：显示保存草稿按钮（如果有改写结果）
        for key in st.session_state.keys():
            if key.startswith("generated_rewrite_"):
                draft_data = st.session_state[key]
                save_rewrite_key = f"save_rewrite_{key}"
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.info(f"✨ 改写结果: {draft_data['title']}")
                with col2:
                    if st.button("💾 保存为草稿", key=save_rewrite_key):
                        with st.spinner("正在保存草稿..."):
                            draft_result = call_api("/api/drafts", "POST", draft_data)
                            if draft_result["success"]:
                                st.success("✅ 已保存为草稿！")
                                st.info(f"草稿ID: {draft_result['data'].get('id', '未知')}")
                                # 保存成功后移除session state
                                del st.session_state[key]
                                st.rerun()
                            else:
                                st.error(f"❌ 保存失败: {draft_result.get('error', '未知错误')}")
                                if draft_result.get('status_code'):
                                    st.error(f"状态码: {draft_result['status_code']}")
                break  # 只显示最新的一个
    

    



# 草稿管理页面
elif page == "📝 草稿管理":
    st.title("📝 草稿管理")
    
    # 获取草稿列表
    drafts_result = call_api("/api/drafts")
    
    if not drafts_result["success"]:
        st.error("无法获取草稿列表")
        st.stop()
    
    drafts = drafts_result["data"]
    
    # 筛选选项
    col1, col2, col3 = st.columns(3)
    with col1:
        category_filter = st.selectbox("分类筛选", ["全部"] + list(set([d.get("category", "未分类") for d in drafts if d.get("category")])))
    with col2:
        status_filter = st.selectbox("状态筛选", ["全部", "draft", "published", "deleted"])
    with col3:
        if st.button("📝 新建草稿", key="new_draft_btn"):
            st.session_state.show_new_draft = True
    
    # 新建草稿表单
    if st.session_state.get("show_new_draft", False):
        with st.expander("✏️ 新建草稿", expanded=True):
            with st.form("new_draft"):
                title = st.text_input("标题")
                content = st.text_area("内容", height=200)
                
                col1, col2 = st.columns(2)
                with col1:
                    category = st.text_input("分类", placeholder="例如：营销文案")
                    tags = st.text_input("标签", placeholder="用逗号分隔，例如：营销,推广")
                with col2:
                    platform_type = st.selectbox("目标平台", ["通用", "微信公众号", "微博", "小红书", "知乎"])
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 保存草稿"):
                        if not title:
                            st.error("请输入标题")
                        else:
                            draft_data = {
                                "title": title,
                                "content": content,
                                "category": category,
                                "tags": tags,
                                "platform_type": platform_type
                            }
                            
                            result = call_api("/api/drafts", "POST", draft_data)
                            if result["success"]:
                                st.success("草稿保存成功！")
                                st.session_state.show_new_draft = False
                                st.rerun()
                            else:
                                st.error("保存失败")
                
                with col2:
                    if st.form_submit_button("❌ 取消"):
                        st.session_state.show_new_draft = False
                        st.rerun()
    
    # 显示草稿列表
    if not drafts:
        st.info("暂无草稿")
    else:
        # 应用筛选
        filtered_drafts = drafts
        if category_filter != "全部":
            filtered_drafts = [d for d in filtered_drafts if d.get("category") == category_filter]
        if status_filter != "全部":
            filtered_drafts = [d for d in filtered_drafts if d.get("status") == status_filter]
        
        st.subheader(f"📋 草稿列表 ({len(filtered_drafts)}篇)")
        
        for draft in filtered_drafts:
            with st.container():
                col1, col2, col3, col4 = st.columns([4, 2, 2, 2])
                
                with col1:
                    st.write(f"**{draft['title']}**")
                    st.write(f"🏷️ {draft.get('category', '未分类')} | 📱 {draft.get('platform_type', '通用')}")
                
                with col2:
                    status_color = {"draft": "🟡", "published": "🟢", "deleted": "🔴"}
                    st.write(f"{status_color.get(draft['status'], '⚪')} {draft['status']}")
                    st.write(f"📝 {draft['word_count']}字")
                
                with col3:
                    ai_icon = "🤖" if draft.get("ai_generated") else "👤"
                    st.write(f"{ai_icon} {'AI生成' if draft.get('ai_generated') else '手动创建'}")
                    st.write(f"⏰ {format_datetime(draft['created_at'])}")
                
                with col4:
                    if st.button("👁️ 查看", key=f"view_{draft['id']}"):
                        st.session_state.view_draft_id = draft['id']
                
                st.divider()
        
        # 查看草稿详情
        if st.session_state.get("view_draft_id"):
            draft_id = st.session_state.view_draft_id
            draft_result = call_api(f"/api/drafts/{draft_id}")
            
            if draft_result["success"]:
                draft = draft_result["data"]
                
                with st.expander(f"📖 草稿详情：{draft['title']}", expanded=True):
                    st.markdown(f"**标题：** {draft['title']}")
                    st.markdown(f"**分类：** {draft.get('category', '未分类')}")
                    st.markdown(f"**标签：** {draft.get('tags', '无')}")
                    st.markdown(f"**平台：** {draft.get('platform_type', '通用')}")
                    st.markdown(f"**字数：** {draft['word_count']}")
                    
                    if draft.get('outline'):
                        st.markdown("**大纲：**")
                        st.markdown(draft['outline'])
                    
                    if draft.get('content'):
                        st.markdown("**内容：**")
                        st.markdown(draft['content'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("❌ 关闭", key="close_draft_detail"):
                            del st.session_state.view_draft_id
                            st.rerun()
                    with col2:
                        if st.button("🗑️ 删除草稿", key="delete_draft_btn"):
                            delete_result = call_api(f"/api/drafts/{draft_id}", "DELETE")
                            if delete_result["success"]:
                                st.success("草稿已删除")
                                del st.session_state.view_draft_id
                                st.rerun()
                            else:
                                st.error("删除失败")


# 发布管理页面
elif page == "🚀 发布管理":
    st.title("🚀 发布管理")
    
    # 标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📤 内容发布", "🔧 平台账号", "📋 发布记录", "📊 发布统计"])
    
    # 内容发布标签页
    with tab1:
        st.subheader("📤 发布内容到各平台")
        
        # 获取草稿列表
        drafts_result = call_api("/api/drafts")
        if not drafts_result["success"]:
            st.error("无法获取草稿列表")
            st.stop()
        
        drafts = drafts_result["data"]
        
        if not drafts:
            st.warning("暂无草稿可发布，请先在草稿管理中创建内容")
        else:
            # 选择草稿
            draft_options = {f"{draft['title']} (ID: {draft['id']})": draft['id'] for draft in drafts}
            selected_draft_name = st.selectbox("选择要发布的草稿", list(draft_options.keys()))
            selected_draft_id = draft_options[selected_draft_name]
            
            # 显示草稿预览
            selected_draft = next(d for d in drafts if d['id'] == selected_draft_id)
            
            with st.expander("📖 草稿预览", expanded=True):
                st.markdown(f"**标题：** {selected_draft['title']}")
                st.markdown(f"**字数：** {selected_draft['word_count']}")
                if selected_draft.get('content'):
                    st.markdown("**内容预览：**")
                    content_preview = selected_draft['content'][:200] + "..." if len(selected_draft['content']) > 200 else selected_draft['content']
                    st.markdown(content_preview)
            
            # 平台选择和内容检查
            st.subheader("🎯 选择发布平台")
            
            # 获取支持的平台
            platforms_result = call_api("/api/publish/platforms")
            if platforms_result["success"]:
                platforms = platforms_result["data"]
                
                # 平台选择
                selected_platforms = []
                
                col1, col2 = st.columns(2)
                for i, platform in enumerate(platforms):
                    with col1 if i % 2 == 0 else col2:
                        if st.checkbox(f"{platform['name']} (最大{platform['max_length']}字)", key=f"platform_{platform['platform']}"):
                            selected_platforms.append(platform['platform'])
                
                if selected_platforms:
                    st.subheader("✅ 内容适配检查")
                    
                    # 检查内容适配性
                    check_data = {
                        "title": selected_draft['title'],
                        "content": selected_draft.get('content', ''),
                        "platform": "all"
                    }
                    
                    check_result = call_api("/api/publish/check", "POST", check_data)
                    if check_result["success"]:
                        suggestions = check_result["data"]["platform_suggestions"]
                        
                        for platform in selected_platforms:
                            if platform in suggestions:
                                suggestion = suggestions[platform]
                                
                                with st.container():
                                    col1, col2 = st.columns([3, 1])
                                    with col1:
                                        st.write(f"**{suggestion['platform_name']}**")
                                        if suggestion['valid']:
                                            st.success(f"✅ {suggestion['optimization']}")
                                        else:
                                            st.error(f"❌ {suggestion['error']}")
                                            st.write(f"💡 {suggestion['optimization']}")
                                    
                                    with col2:
                                        st.metric("字数", f"{suggestion['current_length']}/{suggestion['max_length']}")
                    
                    # 发布选项
                    st.subheader("⚙️ 发布设置")
                    
                    publish_now = st.radio("发布时间", ["立即发布", "定时发布"])
                    
                    publish_time = None
                    if publish_now == "定时发布":
                        col1, col2 = st.columns(2)
                        with col1:
                            publish_date = st.date_input("发布日期")
                        with col2:
                            publish_time_input = st.time_input("发布时间")
                        
                        # 组合日期和时间
                        import datetime
                        publish_time = datetime.datetime.combine(publish_date, publish_time_input).isoformat()
                    
                    # 发布按钮
                    if st.button("🚀 开始发布", type="primary", key="start_publish_btn"):
                        publish_data = {
                            "draft_id": selected_draft_id,
                            "platforms": selected_platforms,
                            "publish_time": publish_time
                        }
                        
                        with st.spinner("发布中..."):
                            publish_result = call_api("/api/publish", "POST", publish_data)
                            
                            if publish_result["success"]:
                                result_data = publish_result["data"]
                                st.success(f"✅ {result_data['summary']}")
                                
                                # 显示详细结果
                                for platform, result in result_data["results"].items():
                                    if result["success"]:
                                        if result.get("message"):
                                            st.info(f"📅 {platform}: {result['message']}")
                                        else:
                                            st.success(f"✅ {platform}: 发布成功")
                                    else:
                                        st.error(f"❌ {platform}: {result['error']}")
                            else:
                                st.error(f"发布失败: {publish_result.get('error', '未知错误')}")
                
                else:
                    st.info("请选择至少一个发布平台")
            else:
                st.error("无法获取平台列表")
    
    # 平台账号管理标签页
    with tab2:
        st.subheader("🔧 平台账号管理")
        
        # 添加新账号
        with st.expander("➕ 添加平台账号"):
            with st.form("add_account"):
                col1, col2 = st.columns(2)
                with col1:
                    platform = st.selectbox("平台", ["weibo", "wechat"])
                    account_name = st.text_input("账号名称")
                with col2:
                    account_id = st.text_input("账号ID（可选）")
                    access_token = st.text_input("Access Token", type="password")
                
                if st.form_submit_button("添加账号"):
                    account_data = {
                        "platform": platform,
                        "account_name": account_name,
                        "account_id": account_id,
                        "access_token": access_token
                    }
                    
                    result = call_api("/api/publish/accounts", "POST", account_data)
                    if result["success"]:
                        st.success("账号添加成功！")
                        st.rerun()
                    else:
                        st.error(f"添加失败: {result.get('error', '未知错误')}")
        
        # 显示现有账号
        accounts_result = call_api("/api/publish/accounts")
        if accounts_result["success"]:
            accounts = accounts_result["data"]
            
            if accounts:
                st.subheader("📋 已配置账号")
                for account in accounts:
                    with st.container():
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            status_icon = "✅" if account["is_active"] else "❌"
                            st.write(f"{status_icon} **{account['account_name']}**")
                            st.write(f"平台: {account['platform']}")
                        
                        with col2:
                            if account.get("last_used"):
                                st.write(f"最后使用: {format_datetime(account['last_used'])}")
                            else:
                                st.write("尚未使用")
                            st.write(f"创建时间: {format_datetime(account['created_at'])}")
                        
                        with col3:
                            if st.button("🗑️", key=f"del_account_{account['id']}", help="删除账号"):
                                st.warning("删除功能待实现")
                        
                        st.divider()
            else:
                st.info("暂无配置的平台账号")
        else:
            st.error("无法获取账号列表")
    
    # 发布记录标签页
    with tab3:
        st.subheader("📋 发布记录")
        
        # 筛选选项
        col1, col2, col3 = st.columns(3)
        with col1:
            platform_filter = st.selectbox("平台筛选", ["全部", "weibo", "wechat"])
        with col2:
            status_filter = st.selectbox("状态筛选", ["全部", "success", "failed", "scheduled"])
        with col3:
            limit = st.selectbox("显示数量", [10, 20, 50], index=1)
        
        # 获取发布记录
        records_result = call_api(f"/api/publish/records?limit={limit}")
        if records_result["success"]:
            records_data = records_result["data"]
            records = records_data["records"]
            
            if records:
                # 应用筛选
                if platform_filter != "全部":
                    records = [r for r in records if r["platform"] == platform_filter]
                if status_filter != "全部":
                    records = [r for r in records if r["status"] == status_filter]
                
                st.write(f"共 {len(records)} 条记录")
                
                for record in records:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                        
                        with col1:
                            st.write(f"**{record['title']}**")
                            st.write(f"平台: {record['platform']}")
                        
                        with col2:
                            status_color = {"success": "🟢", "failed": "🔴", "scheduled": "🟡"}
                            st.write(f"{status_color.get(record['status'], '⚪')} {record['status']}")
                        
                        with col3:
                            if record.get('publish_time'):
                                st.write(f"发布时间: {format_datetime(record['publish_time'])}")
                        
                        with col4:
                            if record.get('platform_post_id'):
                                st.code(record['platform_post_id'])
                        
                        if record.get('error_message'):
                            st.error(f"错误: {record['error_message']}")
                        
                        st.divider()
            else:
                st.info("暂无发布记录")
        else:
            st.error("无法获取发布记录")
    
    # 发布统计标签页
    with tab4:
        st.subheader("📊 发布统计")
        
        # 获取统计数据
        stats_result = call_api("/api/publish/stats")
        if stats_result["success"]:
            stats = stats_result["data"]
            
            # 平台统计
            if stats.get("platform_stats"):
                st.subheader("📈 平台发布统计")
                
                platform_stats = stats["platform_stats"]
                
                # 创建指标显示
                cols = st.columns(len(platform_stats))
                for i, stat in enumerate(platform_stats):
                    with cols[i]:
                        st.metric(
                            f"{stat['platform']} 平台",
                            f"{stat['total']} 次",
                            f"成功率 {stat['success_rate']}%"
                        )
                
                # 创建DataFrame用于详细展示
                df_data = []
                for stat in platform_stats:
                    df_data.append({
                        "平台": stat["platform"],
                        "总发布数": stat["total"],
                        "成功数": stat["success"],
                        "失败数": stat["failed"],
                        "成功率": f"{stat['success_rate']}%"
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
            
            # 日期统计
            if stats.get("daily_stats"):
                st.subheader("📅 最近发布趋势")
                daily_stats = stats["daily_stats"]
                
                if daily_stats:
                    # 创建图表数据
                    chart_data = {stat["date"]: stat["count"] for stat in daily_stats}
                    st.line_chart(chart_data)
                else:
                    st.info("最近7天暂无发布记录")
        else:
            st.error("无法获取统计数据")


# 热点分析页面
elif page == "🔥 热点分析":
    st.title("🔥 热点分析")
    
    # 标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📈 热点监控", "🎯 关键词分析", "📊 数据统计", "⚙️ 抓取设置"])
    
    # 热点监控标签页
    with tab1:
        st.subheader("📈 实时热点监控")
        
        # 筛选选项
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            platform_filter = st.selectbox("平台筛选", ["全部", "weibo", "zhihu", "toutiao"])
        with col2:
            category_filter = st.selectbox("分类筛选", ["全部", "综合", "知识", "娱乐", "科技"])
        with col3:
            hours_filter = st.selectbox("时间范围", [24, 48, 72, 168], format_func=lambda x: f"最近{x}小时")
        with col4:
            limit_filter = st.selectbox("显示数量", [20, 50, 100])
        
        # 获取热点数据
        params = {
            "hours": hours_filter,
            "limit": limit_filter
        }
        if platform_filter != "全部":
            params["platform"] = platform_filter
        if category_filter != "全部":
            params["category"] = category_filter
        
        # 构建查询字符串
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        topics_result = call_api(f"/api/hotspot/topics?{query_string}")
        
        if topics_result["success"]:
            topics_data = topics_result["data"]
            topics = topics_data.get("topics", [])
            
            if topics:
                st.write(f"共找到 {len(topics)} 个热点话题")
                
                # 显示热点列表
                for i, topic in enumerate(topics):
                    with st.container():
                        col1, col2, col3 = st.columns([6, 2, 2])
                        
                        with col1:
                            # 标题和描述
                            st.markdown(f"**#{topic['rank_position']} {topic['title']}**")
                            if topic.get('description'):
                                st.markdown(f"*{topic['description'][:100]}...*" if len(topic['description']) > 100 else f"*{topic['description']}*")
                            
                            # 关键词标签
                            if topic.get('keywords'):
                                keywords = topic['keywords'].split(',')[:5]  # 显示前5个关键词
                                keyword_tags = " ".join([f"`{kw.strip()}`" for kw in keywords if kw.strip()])
                                st.markdown(keyword_tags)
                        
                        with col2:
                            # 平台和分类
                            platform_emoji = {"weibo": "🐱", "zhihu": "🤔", "toutiao": "📰"}
                            st.markdown(f"{platform_emoji.get(topic['platform'], '📱')} {topic['platform']}")
                            st.markdown(f"📂 {topic['category']}")
                            
                            # 情感倾向
                            sentiment_emoji = {"positive": "😊", "negative": "😞", "neutral": "😐"}
                            st.markdown(f"{sentiment_emoji.get(topic['sentiment'], '😐')} {topic['sentiment']}")
                        
                        with col3:
                            # 热度分数
                            st.metric("热度分数", f"{topic['hot_score']:.1f}")
                            
                            # 互动数据
                            if topic.get('engagement_count', 0) > 0:
                                st.metric("互动量", f"{topic['engagement_count']:,}")
                            
                            # 时间
                            created_time = topic.get('created_at', '')
                            if created_time:
                                st.markdown(f"🕒 {format_datetime(created_time)}")
                        
                        # 操作按钮
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button(f"💡 生成创意", key=f"idea_{topic['id']}"):
                                st.session_state[f"generate_idea_{topic['id']}"] = True
                        with col_btn2:
                            if st.button(f"✍️ 创作内容", key=f"create_{topic['id']}"):
                                st.session_state[f"create_content_{topic['id']}"] = True
                        
                        # 处理生成创意
                        if st.session_state.get(f"generate_idea_{topic['id']}", False):
                            with st.spinner("AI正在分析热点并生成创意..."):
                                # 获取可用的AI模型
                                configs_result = call_api("/api/ai/configs")
                                if configs_result["success"]:
                                    active_configs = [c for c in configs_result["data"] if c["is_active"]]
                                    if active_configs:
                                        config_id = active_configs[0]["id"]  # 使用第一个活跃配置
                                        
                                        # 生成创意
                                        idea_data = {
                                            "topic": topic['title'],
                                            "platform": "通用",
                                            "style": "专业",
                                            "requirements": f"基于热点话题：{topic['title']}，生成3-5个创作角度和内容方向建议",
                                            "config_id": config_id
                                        }
                                        
                                        idea_result = call_api("/api/content/title", "POST", idea_data)
                                        if idea_result["success"]:
                                            st.success("创意生成成功！")
                                            st.markdown("### 💡 创作建议：")
                                            st.markdown(idea_result["data"]["titles"])
                                        else:
                                            st.error(f"创意生成失败: {idea_result.get('error', '未知错误')}")
                                    else:
                                        st.error("没有可用的AI模型配置")
                                else:
                                    st.error("无法获取AI模型配置")
                            
                            # 重置状态
                            st.session_state[f"generate_idea_{topic['id']}"] = False
                        
                        st.divider()
                
                # 分页（简化版本）
                if len(topics) >= limit_filter:
                    st.info(f"显示了前 {limit_filter} 个热点，调整显示数量可查看更多")
            else:
                st.info("暂无热点数据，请先执行数据抓取")
        else:
            st.error("获取热点数据失败")
    
    # 关键词分析标签页
    with tab2:
        st.subheader("🎯 热门关键词分析")
        
        # 获取关键词数据
        col1, col2 = st.columns(2)
        with col1:
            keyword_hours = st.selectbox("分析时间范围", [24, 48, 72, 168], format_func=lambda x: f"最近{x}小时", key="keyword_hours")
        with col2:
            keyword_limit = st.selectbox("关键词数量", [10, 20, 50], key="keyword_limit")
        
        keywords_result = call_api(f"/api/hotspot/keywords?hours={keyword_hours}&limit={keyword_limit}")
        
        if keywords_result["success"]:
            keywords_data = keywords_result["data"]["keywords"]
            
            if keywords_data:
                st.write(f"发现 {len(keywords_data)} 个热门关键词")
                
                # 关键词排行榜
                st.subheader("🏆 关键词排行榜")
                
                for i, kw in enumerate(keywords_data):
                    col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                    
                    with col1:
                        st.markdown(f"**#{i+1}**")
                    with col2:
                        st.markdown(f"**{kw['keyword']}**")
                    with col3:
                        st.metric("出现次数", kw['count'])
                    with col4:
                        st.metric("综合热度", f"{kw['total_score']:.1f}")
                
                # 关键词云图（使用简单的文本展示）
                st.subheader("☁️ 关键词概览")
                keyword_text = " • ".join([f"**{kw['keyword']}**({kw['count']})" for kw in keywords_data[:20]])
                st.markdown(keyword_text)
                
                # 关键词趋势图
                st.subheader("📈 关键词热度分布")
                chart_data = {kw['keyword']: kw['total_score'] for kw in keywords_data[:15]}
                st.bar_chart(chart_data)
                
            else:
                st.info("暂无关键词数据")
        else:
            st.error("获取关键词数据失败")
    
    # 数据统计标签页
    with tab3:
        st.subheader("📊 热点数据统计")
        
        # 获取统计数据
        stats_result = call_api("/api/hotspot/stats")
        
        if stats_result["success"]:
            stats = stats_result["data"]
            
            # 总体统计
            st.subheader("📈 总体概况")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("总热点数", stats["total_topics"])
            with col2:
                platform_count = len(stats["platform_stats"])
                st.metric("活跃平台", platform_count)
            with col3:
                category_count = len(stats["category_stats"])
                st.metric("涉及分类", category_count)
            with col4:
                st.metric("时间范围", stats["time_range"])
            
            # 平台统计
            if stats["platform_stats"]:
                st.subheader("📱 平台分布")
                platform_data = []
                for platform, data in stats["platform_stats"].items():
                    platform_data.append({
                        "平台": platform,
                        "热点数量": data["count"],
                        "平均热度": data["avg_score"]
                    })
                
                df_platform = pd.DataFrame(platform_data)
                st.dataframe(df_platform, use_container_width=True)
                
                # 平台热点数量图表
                platform_chart = {row["平台"]: row["热点数量"] for _, row in df_platform.iterrows()}
                st.bar_chart(platform_chart)
            
            # 分类统计
            if stats["category_stats"]:
                st.subheader("📂 分类分布")
                category_chart = stats["category_stats"]
                st.bar_chart(category_chart)
            
            # 情感分析统计
            if stats["sentiment_stats"]:
                st.subheader("😊 情感倾向分析")
                sentiment_data = []
                sentiment_names = {"positive": "正面", "negative": "负面", "neutral": "中性"}
                
                for sentiment, count in stats["sentiment_stats"].items():
                    sentiment_data.append({
                        "情感倾向": sentiment_names.get(sentiment, sentiment),
                        "数量": count,
                        "占比": f"{count/stats['total_topics']*100:.1f}%"
                    })
                
                df_sentiment = pd.DataFrame(sentiment_data)
                st.dataframe(df_sentiment, use_container_width=True)
                
        else:
            st.error("获取统计数据失败")
    
    # 抓取设置标签页
    with tab4:
        st.subheader("⚙️ 抓取设置")
        
        # 获取支持的平台
        platforms_result = call_api("/api/hotspot/platforms")
        
        if platforms_result["success"]:
            platforms = platforms_result["data"]["platforms"]
            
            # 手动抓取
            st.subheader("🔄 手动抓取")
            
            # 平台选择
            selected_platforms = []
            st.write("选择要抓取的平台：")
            
            for platform in platforms:
                if st.checkbox(f"{platform['name']} - {platform['description']}", key=f"platform_{platform['platform']}"):
                    selected_platforms.append(platform['platform'])
            
            # 抓取按钮
            if st.button("🚀 开始抓取", type="primary", key="start_crawl_btn"):
                if selected_platforms:
                    with st.spinner("正在抓取热点数据..."):
                        crawl_data = selected_platforms if selected_platforms else None
                        crawl_result = call_api("/api/hotspot/crawl", "POST", crawl_data)
                        
                        if crawl_result["success"]:
                            st.success("抓取完成！")
                            
                            # 显示抓取结果
                            st.subheader("📊 抓取结果")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("总抓取数", crawl_result["data"]["total_count"])
                            with col2:
                                error_count = len(crawl_result["data"]["errors"])
                                st.metric("错误数", error_count)
                            
                            # 平台详情
                            for platform, result in crawl_result["data"]["platforms"].items():
                                with st.expander(f"{platform} 详情"):
                                    if result["success"]:
                                        st.success(f"✅ 成功抓取 {result['crawled']} 个热点，保存 {result['saved']} 个")
                                    else:
                                        st.error(f"❌ 抓取失败: {result.get('error', '未知错误')}")
                            
                            # 错误信息
                            if crawl_result["data"]["errors"]:
                                st.subheader("⚠️ 错误信息")
                                for error in crawl_result["data"]["errors"]:
                                    st.error(error)
                        else:
                            st.error(f"抓取失败: {crawl_result.get('error', '未知错误')}")
                else:
                    st.warning("请至少选择一个平台")
            
            # 数据清理
            st.subheader("🧹 数据清理")
            
            col1, col2 = st.columns(2)
            with col1:
                cleanup_days = st.selectbox("清理天数", [3, 7, 14, 30], index=1)
            with col2:
                if st.button("🗑️ 清理旧数据", key="cleanup_data_btn"):
                    with st.spinner("正在清理数据..."):
                        cleanup_result = call_api(f"/api/hotspot/cleanup?days={cleanup_days}", "DELETE")
                        
                        if cleanup_result["success"]:
                            st.success(f"✅ {cleanup_result['data']['message']}")
                        else:
                            st.error(f"清理失败: {cleanup_result.get('error', '未知错误')}")
            
            st.info(f"将清理 {cleanup_days} 天前的热点数据")
            
        else:
            st.error("获取平台信息失败")


# 使用统计页面
elif page == "📊 使用统计":
    st.title("📊 数据分析与统计")
    
    # 标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📈 内容表现", "🔥 热点分析", "🤖 AI使用统计", "📋 综合报告"])
    
    # 内容表现分析标签页
    with tab1:
        st.subheader("📈 内容表现分析")
        
        # 筛选选项
        col1, col2 = st.columns(2)
        with col1:
            days_filter = st.selectbox("分析时间范围", [7, 15, 30, 60], index=2, format_func=lambda x: f"最近{x}天")
        with col2:
            platform_filter = st.selectbox("平台筛选", ["全部", "weibo", "wechat"], key="content_platform")
        
        # 获取内容分析数据
        params = {"days": days_filter}
        if platform_filter != "全部":
            params["platform"] = platform_filter
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        content_result = call_api(f"/api/analytics/content?{query_string}")
        
        if content_result["success"]:
            data = content_result["data"]
            
            # 总体指标
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("总发布数", data["total_posts"])
            with col2:
                st.metric("成功率", f"{data['performance_summary']['success_rate']:.1f}%")
            with col3:
                st.metric("失败率", f"{data['performance_summary']['failure_rate']:.1f}%")
            with col4:
                st.metric("日均发布", f"{data['performance_summary']['avg_daily_posts']:.1f}")
            
            # 平台表现分析
            if data["platform_analysis"]:
                st.subheader("📱 平台表现对比")
                
                platform_data = []
                for platform, stats in data["platform_analysis"].items():
                    platform_data.append({
                        "平台": platform,
                        "发布数": stats["posts"],
                        "成功率": f"{stats['success_rate']:.1f}%",
                        "平均浏览": stats["avg_views"],
                        "平均点赞": stats["avg_likes"],
                        "平均评论": stats["avg_comments"],
                        "平均转发": stats["avg_shares"],
                        "平均互动": stats["avg_engagement"]
                    })
                
                df = pd.DataFrame(platform_data)
                st.dataframe(df, use_container_width=True)
            
            # 最佳发布时间
            if data["time_analysis"]["best_hours"]:
                st.subheader("⏰ 最佳发布时间")
                
                best_hours = data["time_analysis"]["best_hours"]
                for i, hour_data in enumerate(best_hours[:3]):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**第{i+1}名：{hour_data['hour']}:00**")
                    with col2:
                        st.write(f"成功率 {hour_data['success_rate']:.1f}%")
                    with col3:
                        st.write(f"平均互动 {hour_data['avg_engagement']:.1f}")
            
            # 内容洞察
            if data["content_insights"]:
                st.subheader("💡 内容洞察")
                insights = data["content_insights"]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("成功发布", insights["total_successful_posts"])
                    st.info(f"**最佳标题长度：** {insights['best_title_length']}")
                with col2:
                    st.metric("失败发布", insights["total_failed_posts"])
                    if insights["common_failure_reasons"]:
                        failure_reasons = list(insights["common_failure_reasons"].items())
                        st.warning(f"**常见失败原因：** {failure_reasons[0][0]} ({failure_reasons[0][1]}次)")
        else:
            st.error("无法获取内容分析数据")
    
    # 热点分析标签页
    with tab2:
        st.subheader("🔥 热点趋势分析")
        
        days_filter = st.selectbox("分析时间范围", [3, 7, 14], index=1, format_func=lambda x: f"最近{x}天", key="hotspot_days")
        
        hotspot_result = call_api(f"/api/analytics/hotspot?days={days_filter}")
        
        if hotspot_result["success"]:
            data = hotspot_result["data"]
            
            if data.get("total_topics", 0) > 0:
                # 总体统计
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("热点话题数", data["total_topics"])
                with col2:
                    platform_count = len(data.get("platform_analysis", {}))
                    st.metric("覆盖平台", platform_count)
                with col3:
                    category_count = len(data.get("category_distribution", {}))
                    st.metric("话题分类", category_count)
                
                # 平台分析
                if data.get("platform_analysis"):
                    st.subheader("📱 平台热点分布")
                    
                    platform_data = []
                    for platform, stats in data["platform_analysis"].items():
                        platform_data.append({
                            "平台": platform,
                            "热点数量": stats["count"],
                            "平均热度": stats["avg_score"]
                        })
                    
                    df = pd.DataFrame(platform_data)
                    st.dataframe(df, use_container_width=True)
                
                # 分类分布
                if data.get("category_distribution"):
                    st.subheader("📂 话题分类分布")
                    category_chart = data["category_distribution"]
                    st.bar_chart(category_chart)
                
                # 热门关键词
                if data.get("top_keywords"):
                    st.subheader("🔑 热门关键词")
                    keywords = data["top_keywords"]
                    
                    # 显示前10个关键词
                    keyword_data = []
                    for keyword, count in list(keywords.items())[:10]:
                        keyword_data.append({"关键词": keyword, "出现次数": count})
                    
                    df = pd.DataFrame(keyword_data)
                    st.dataframe(df, use_container_width=True)
                
                # 创作机会
                if data.get("content_opportunities"):
                    st.subheader("💡 创作机会推荐")
                    opportunities = data["content_opportunities"]
                    
                    for opp in opportunities[:5]:
                        with st.expander(f"#{opp['rank']} {opp['topic']} (热度: {opp['hot_score']:.1f})"):
                            st.write(f"**平台：** {opp['platform']}")
                            st.write(f"**分类：** {opp['category']}")
                            st.write(f"**情感倾向：** {opp['sentiment']}")
                            if opp['keywords']:
                                keywords_str = ", ".join(opp['keywords'])
                                st.write(f"**关键词：** {keywords_str}")
                            st.write(f"**创作建议：** {opp['suggestion']}")
            else:
                st.info("暂无热点数据，建议先运行热点抓取功能")
        else:
            st.error("无法获取热点分析数据")
    
    # AI使用统计标签页
    with tab3:
        st.subheader("🤖 AI使用统计")
        
        # 获取AI使用统计
        stats_result = call_api("/api/ai/stats")
        if stats_result["success"]:
            stats = stats_result["data"]
            configs = stats.get("configs", [])
            
            # 总体统计
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("配置总数", len(configs))
            with col2:
                st.metric("活跃配置", len([c for c in configs if c["is_active"]]))
            with col3:
                st.metric("总使用次数", stats.get("total_usage", 0))
            with col4:
                st.metric("总Token消耗", stats.get("total_tokens", 0))
            
            # 配置详细统计
            if configs:
                st.subheader("📊 各模型使用情况")
                
                df_data = []
                for config in configs:
                    df_data.append({
                        "名称": config["name"],
                        "提供商": config["provider"],
                        "使用次数": config["usage_count"],
                        "Token消耗": config["total_tokens"],
                        "状态": "✅ 活跃" if config["is_active"] else "❌ 停用",
                        "默认": "⭐ 是" if config["is_default"] else ""
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
                
                # 使用量图表
                if any(config["usage_count"] > 0 for config in configs):
                    st.subheader("📈 使用分布")
                    
                    usage_data = {config["name"]: config["usage_count"] for config in configs if config["usage_count"] > 0}
                    if usage_data:
                        st.bar_chart(usage_data)
                    
                    token_data = {config["name"]: config["total_tokens"] for config in configs if config["total_tokens"] > 0}
                    if token_data:
                        st.subheader("🥧 Token消耗分布")
                        st.bar_chart(token_data)
            else:
                st.info("暂无AI模型配置数据")
        else:
            st.error("无法获取AI统计数据")
    
    # 综合报告标签页
    with tab4:
        st.subheader("📋 综合分析报告")
        
        days_filter = st.selectbox("报告时间范围", [7, 15, 30, 60], index=2, format_func=lambda x: f"最近{x}天", key="report_days")
        
        if st.button("生成综合报告", type="primary", key="generate_report_btn"):
            with st.spinner("正在生成综合报告..."):
                report_result = call_api(f"/api/analytics/report?days={days_filter}")
                
                if report_result["success"]:
                    data = report_result["data"]
                    
                    # 报告摘要
                    if data.get("summary"):
                        st.subheader("📊 报告摘要")
                        summary = data["summary"]
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("总发布数", summary.get("total_posts", 0))
                        with col2:
                            st.metric("成功率", f"{summary.get('success_rate', 0):.1f}%")
                        with col3:
                            st.metric("热点话题数", summary.get("total_hotspots", 0))
                        
                        # 关键洞察
                        if summary.get("key_insights"):
                            st.subheader("💡 关键洞察")
                            for insight in summary["key_insights"]:
                                st.info(f"• {insight}")
                    
                    # 内容创作建议
                    if data.get("recommendations"):
                        st.subheader("🎯 创作建议")
                        for rec in data["recommendations"]:
                            priority_color = {
                                "high": "🔴",
                                "medium": "🟡", 
                                "low": "🟢"
                            }
                            priority_icon = priority_color.get(rec.get("priority", "medium"), "🟡")
                            
                            st.write(f"{priority_icon} **{rec['title']}**")
                            st.write(f"   {rec['description']}")
                    
                    # 详细数据展示
                    with st.expander("📈 详细数据"):
                        st.json(data)
                else:
                    st.error("生成报告失败")
        
        # 获取内容创作建议
        st.subheader("💡 实时创作建议")
        recommendations_result = call_api("/api/analytics/recommendations")
        
        if recommendations_result["success"]:
            data = recommendations_result["data"]
            
            if data.get("recommendations"):
                for rec in data["recommendations"]:
                    priority_color = {
                        "high": "error",
                        "medium": "warning", 
                        "low": "success"
                    }
                    message_type = priority_color.get(rec.get("priority", "medium"), "info")
                    
                    if message_type == "error":
                        st.error(f"**{rec['title']}** - {rec['description']}")
                    elif message_type == "warning":
                        st.warning(f"**{rec['title']}** - {rec['description']}")
                    else:
                        st.success(f"**{rec['title']}** - {rec['description']}")
            else:
                st.info("暂无创作建议，建议增加更多发布数据")
        else:
            st.info("无法获取创作建议")

# 页面底部
st.markdown("---")
st.markdown("*自媒体运营工具 v1.0.0 - 让内容创作更智能*") 