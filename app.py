"""
自媒体运营工具 - Streamlit前端应用
"""
import streamlit as st
import requests
import json
from typing import Dict, Any, Optional, List
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
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        return {
            "success": response.status_code < 400,
            "data": response.json() if response.content else {},
            "status_code": response.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {}
        }


def format_datetime(dt_str: str) -> str:
    """格式化日期时间"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return dt_str


# 侧边栏导航
st.sidebar.title("🚀 自媒体运营工具")
page = st.sidebar.selectbox(
    "选择功能模块",
    ["🏠 首页", "🤖 AI模型管理", "✍️ 内容创作", "📝 草稿管理", "🚀 发布管理", "📊 使用统计"]
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
                provider = st.selectbox("提供商", ["openai", "baidu", "dashscope", "tencent"])
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
                    if st.button(f"🔗 测试", key=f"test_{config['id']}"):
                        with st.spinner("测试连接中..."):
                            test_result = call_api(f"/api/ai/configs/{config['id']}/test", "POST")
                            if test_result["success"] and test_result["data"]["status"] == "success":
                                st.success("连接正常！")
                            else:
                                st.error("连接失败！")
                
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
        ["🏷️ 标题生成", "📋 大纲制作", "🔄 内容改写", "💬 自由对话"],
        horizontal=True
    )
    
    if creation_type == "🏷️ 标题生成":
        st.subheader("🏷️ 智能标题生成")
        
        with st.form("title_generation"):
            col1, col2 = st.columns(2)
            
            with col1:
                topic = st.text_area("主题内容", placeholder="请输入要创作的主题内容...", height=100)
                platform = st.selectbox("目标平台", ["通用", "微信公众号", "微博", "小红书", "抖音", "知乎"])
            
            with col2:
                style = st.selectbox("标题风格", ["专业", "吸引眼球", "温馨", "幽默", "权威", "疑问式"])
                requirements = st.text_area("特殊要求", placeholder="例如：包含关键词、控制字数等...", height=100)
            
            if st.form_submit_button("🎯 生成标题"):
                if not topic:
                    st.error("请输入主题内容")
                else:
                    with st.spinner("AI正在生成标题..."):
                        data = {
                            "topic": topic,
                            "platform": platform,
                            "style": style,
                            "requirements": requirements,
                            "config_id": selected_config_id
                        }
                        
                        result = call_api("/api/content/title", "POST", data)
                        
                        if result["success"]:
                            st.success("标题生成成功！")
                            st.markdown("### 生成的标题：")
                            st.markdown(result["data"]["titles"])
                            
                            # 显示使用统计
                            if "usage" in result["data"]:
                                usage = result["data"]["usage"]
                                st.info(f"本次消耗Token: {usage.get('total_tokens', '未知')}")
                        else:
                            st.error(f"生成失败: {result.get('error', '未知错误')}")
    
    elif creation_type == "📋 大纲制作":
        st.subheader("📋 内容大纲制作")
        
        with st.form("outline_generation"):
            title = st.text_input("文章标题", placeholder="请输入文章标题...")
            
            col1, col2 = st.columns(2)
            with col1:
                platform = st.selectbox("目标平台", ["通用", "微信公众号", "微博", "小红书", "知乎", "头条号"])
                audience = st.text_input("目标受众", value="通用受众", placeholder="例如：年轻女性、科技爱好者...")
            
            with col2:
                length = st.selectbox("内容长度", ["短文", "中等长度", "长文"])
            
            if st.form_submit_button("📝 生成大纲"):
                if not title:
                    st.error("请输入文章标题")
                else:
                    with st.spinner("AI正在制作大纲..."):
                        data = {
                            "title": title,
                            "platform": platform,
                            "audience": audience,
                            "length": length,
                            "config_id": selected_config_id
                        }
                        
                        result = call_api("/api/content/outline", "POST", data)
                        
                        if result["success"]:
                            st.success("大纲生成成功！")
                            st.markdown("### 内容大纲：")
                            st.markdown(result["data"]["outline"])
                            
                            # 保存为草稿选项
                            if st.button("💾 保存为草稿"):
                                draft_data = {
                                    "title": title,
                                    "outline": result["data"]["outline"],
                                    "platform_type": platform,
                                    "category": "AI生成大纲"
                                }
                                
                                draft_result = call_api("/api/drafts", "POST", draft_data)
                                if draft_result["success"]:
                                    st.success("已保存为草稿！")
                                else:
                                    st.error("保存失败")
                        else:
                            st.error(f"生成失败: {result.get('error', '未知错误')}")
    
    elif creation_type == "🔄 内容改写":
        st.subheader("🔄 智能内容改写")
        
        with st.form("content_rewrite"):
            original_content = st.text_area("原始内容", placeholder="请输入需要改写的内容...", height=200)
            
            col1, col2 = st.columns(2)
            with col1:
                platform = st.selectbox("目标平台", ["通用", "微信公众号", "微博", "小红书", "知乎"])
            with col2:
                requirements = st.text_input("改写要求", value="改写为更吸引人的版本", placeholder="例如：更口语化、更正式...")
            
            if st.form_submit_button("✨ 开始改写"):
                if not original_content:
                    st.error("请输入原始内容")
                else:
                    with st.spinner("AI正在改写内容..."):
                        data = {
                            "original_content": original_content,
                            "requirements": requirements,
                            "platform": platform,
                            "config_id": selected_config_id
                        }
                        
                        result = call_api("/api/content/rewrite", "POST", data)
                        
                        if result["success"]:
                            st.success("内容改写成功！")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("### 原始内容：")
                                st.markdown(original_content)
                            
                            with col2:
                                st.markdown("### 改写后内容：")
                                st.markdown(result["data"]["rewritten_content"])
                        else:
                            st.error(f"改写失败: {result.get('error', '未知错误')}")
    
    elif creation_type == "💬 自由对话":
        st.subheader("💬 AI自由对话")
        
        with st.form("free_chat"):
            prompt = st.text_area("请输入你的问题或需求", placeholder="例如：帮我写一个关于健康饮食的小红书文案...", height=150)
            
            col1, col2 = st.columns(2)
            with col1:
                max_tokens = st.number_input("最大Token数", value=2000, min_value=100, max_value=4000)
            with col2:
                temperature = st.slider("创造性 (Temperature)", 0.0, 2.0, 0.7, 0.1)
            
            if st.form_submit_button("🚀 发送"):
                if not prompt:
                    st.error("请输入内容")
                else:
                    with st.spinner("AI正在思考..."):
                        data = {
                            "prompt": prompt,
                            "config_id": selected_config_id,
                            "max_tokens": max_tokens,
                            "temperature": temperature
                        }
                        
                        result = call_api("/api/content/generate", "POST", data)
                        
                        if result["success"]:
                            st.success("AI回复：")
                            st.markdown(result["data"]["content"])
                            
                            # 保存为草稿选项
                            if st.button("💾 保存回复为草稿"):
                                draft_data = {
                                    "title": prompt[:50] + "..." if len(prompt) > 50 else prompt,
                                    "content": result["data"]["content"],
                                    "category": "AI对话",
                                    "ai_generated": True
                                }
                                
                                draft_result = call_api("/api/drafts", "POST", draft_data)
                                if draft_result["success"]:
                                    st.success("已保存为草稿！")
                        else:
                            st.error(f"生成失败: {result.get('error', '未知错误')}")


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
        if st.button("📝 新建草稿"):
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
                        if st.button("❌ 关闭"):
                            del st.session_state.view_draft_id
                            st.rerun()
                    with col2:
                        if st.button("🗑️ 删除草稿"):
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
                    if st.button("🚀 开始发布", type="primary"):
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


# 使用统计页面
elif page == "📊 使用统计":
    st.title("📊 使用统计")
    
    # 获取统计数据
    stats_result = call_api("/api/ai/stats")
    
    if not stats_result["success"]:
        st.error("无法获取统计数据")
        st.stop()
    
    stats = stats_result["data"]
    configs = stats.get("configs", [])
    
    # 总体统计
    st.subheader("📈 总体统计")
    
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
        st.subheader("🤖 各模型使用情况")
        
        # 创建DataFrame用于展示
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
            st.subheader("📊 使用量分布")
            
            # 使用次数柱状图
            usage_data = {config["name"]: config["usage_count"] for config in configs if config["usage_count"] > 0}
            if usage_data:
                st.bar_chart(usage_data)
            
            # Token消耗饼图（使用Streamlit的内置图表功能的替代方案）
            token_data = {config["name"]: config["total_tokens"] for config in configs if config["total_tokens"] > 0}
            if token_data:
                st.subheader("🥧 Token消耗分布")
                st.bar_chart(token_data)
    
    else:
        st.info("暂无AI模型配置数据")

# 页面底部
st.markdown("---")
st.markdown("*自媒体运营工具 v1.0.0 - 让内容创作更智能*") 