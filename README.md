# 🚀 自媒体运营工具

一个基于AI的智能自媒体内容创作和运营管理平台，帮助内容创作者提高创作效率和内容质量。

## ✨ 功能特性

### 🤖 AI模型管理
- 支持多个AI大模型提供商（OpenAI、百度文心一言、阿里通义千问、腾讯混元）
- 统一的API配置管理
- 使用量监控和成本控制
- 连接测试和状态监控

### ✍️ 智能内容创作
- **标题生成**：根据主题智能生成多种风格的吸引力标题
- **大纲制作**：为文章自动生成结构化内容大纲
- **内容改写**：保持核心观点不变的智能改写
- **自由对话**：与AI进行开放式对话和内容创作

### 📝 草稿管理
- 内容草稿的保存和管理
- 分类存储和标签管理
- 版本控制和历史记录
- 快速搜索和筛选

### 🚀 发布管理
- 一键多平台发布（微博、微信公众号）
- 平台内容适配检查
- 定时发布功能
- 发布记录管理
- 发布统计分析

### 📊 数据统计
- AI模型使用统计
- Token消耗分析
- 创作效率监控
- 可视化图表展示

## 🛠 技术架构

- **后端**：FastAPI + SQLAlchemy + SQLite
- **前端**：Streamlit
- **AI集成**：OpenAI API + 多模型支持
- **数据库**：SQLite（轻量级本地部署）
- **部署方式**：本地Python环境

## 📦 安装和使用

### 1. 环境要求
- Python 3.8+
- Windows/macOS/Linux

### 2. 克隆项目
```bash
git clone <项目地址>
cd ss-media-tools
```

### 3. 安装依赖
```bash
# 建议使用虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖包
pip install -r requirements.txt
```

### 4. 配置环境变量
```bash
# 复制配置文件
cp env_example.txt .env

# 编辑 .env 文件，填入你的AI模型API密钥
# 至少配置一个AI模型才能正常使用
```

### 5. 启动应用
```bash
# 使用启动脚本（推荐）
python start.py

# 或者手动启动
# 后端API (终端1)
python main.py

# 前端界面 (终端2)  
streamlit run app.py
```

### 6. 访问应用
- 前端界面：http://localhost:8501
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

## 🔧 配置说明

### AI模型配置
在 `.env` 文件中配置你需要使用的AI模型API密钥：

```bash
# OpenAI (推荐)
OPENAI_API_KEY="your-openai-api-key"

# 百度文心一言
BAIDU_API_KEY="your-baidu-api-key"
BAIDU_SECRET_KEY="your-baidu-secret-key"

# 阿里通义千问
DASHSCOPE_API_KEY="your-dashscope-api-key"

# 腾讯混元
TENCENT_SECRET_ID="your-tencent-secret-id"
TENCENT_SECRET_KEY="your-tencent-secret-key"
```

### 模型推荐
- **新手推荐**：OpenAI GPT-3.5-turbo（便宜、稳定、效果好）
- **国产首选**：百度文心一言（中文理解能力强）
- **企业用户**：阿里通义千问（企业级服务）

## 📖 使用指南

### 1. 配置AI模型
1. 进入"AI模型管理"页面
2. 添加新的AI模型配置
3. 填入API密钥等信息
4. 测试连接确保配置正确

### 2. 创作内容
1. 进入"内容创作"页面
2. 选择创作类型（标题生成、大纲制作等）
3. 填入相关信息
4. 点击生成按钮获取AI创作的内容

### 3. 管理草稿
1. 在"草稿管理"页面查看所有草稿
2. 可以创建、查看、编辑、删除草稿
3. 支持分类和标签管理

### 4. 发布内容
1. 进入"发布管理"页面
2. 在"平台账号"标签页中配置发布平台的账号信息
3. 在"内容发布"标签页中选择草稿并设置发布平台
4. 系统会自动检查内容适配性并提供优化建议
5. 可选择立即发布或定时发布

### 5. 查看统计
1. 在"使用统计"页面查看AI使用情况
2. 在"发布管理-发布统计"查看发布数据
3. 监控各模型的使用次数和Token消耗
4. 优化使用策略

## 🔮 后续功能规划

- [ ] 更多平台支持（小红书、抖音、B站等）
- [ ] 热点抓取和分析
- [ ] 内容SEO优化建议
- [ ] 素材管理功能
- [ ] 团队协作功能
- [ ] 移动端支持
- [ ] 更多AI模型接入

## 📄 项目结构

```
ss-media-tools/
├── config.py          # 配置文件
├── models.py           # 数据库模型
├── ai_models.py        # AI模型管理
├── publisher.py        # 发布管理模块
├── main.py             # FastAPI后端
├── app.py              # Streamlit前端
├── start.py            # 启动脚本
├── test_basic.py       # 基础功能测试
├── test_publish.py     # 发布功能测试
├── requirements.txt    # 依赖包
├── env_example.txt     # 环境变量示例
├── README.md           # 项目说明
├── 需求文档.md         # 详细需求文档
├── 项目开发进度.md     # 开发进度跟踪
└── venv/               # 虚拟环境（自动生成）
```

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📞 支持

如果你在使用过程中遇到问题，可以：
1. 查看项目文档
2. 提交Issue
3. 查看API文档（http://localhost:8000/docs）

## 📜 许可证

本项目采用 MIT 许可证。

---

**让AI为你的内容创作赋能！** 🎯 