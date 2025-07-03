# 🔒 安全配置指南

## 📋 重要提醒

**⚠️ 请勿将真实的API密钥提交到Git仓库！**

本项目使用环境变量来管理敏感信息，确保您的API密钥安全。

## 🔧 配置步骤

### 1. 复制配置模板

```bash
cp .env.example .env
```

### 2. 编辑环境变量文件

打开 `.env` 文件，将示例值替换为您的真实API密钥：

```bash
# DeepSeek配置（必需）
DEEPSEEK_API_KEY="your_actual_deepseek_api_key_here"

# 其他AI服务配置（可选）
OPENAI_API_KEY="your_openai_api_key_here"
BAIDU_API_KEY="your_baidu_api_key_here"
# ... 其他配置
```

### 3. 验证配置

运行以下命令验证配置是否正确：

```bash
python test_basic.py
```

## 🛡️ 安全最佳实践

### ✅ 应该做的

- ✅ 使用 `.env` 文件存储API密钥
- ✅ 确保 `.env` 文件在 `.gitignore` 中
- ✅ 定期轮换API密钥
- ✅ 使用最小权限原则配置API密钥
- ✅ 在生产环境中使用环境变量或密钥管理服务

### ❌ 不应该做的

- ❌ 在代码中硬编码API密钥
- ❌ 将 `.env` 文件提交到Git
- ❌ 在日志中打印API密钥
- ❌ 在公共场所分享包含密钥的配置文件

## 🔍 检查清单

在提交代码前，请确认：

- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] 代码中没有硬编码的API密钥
- [ ] 测试文件中使用的是示例密钥
- [ ] 文档中没有包含真实密钥

## 🚨 如果密钥泄露了怎么办？

1. **立即撤销泄露的API密钥**
2. **生成新的API密钥**
3. **更新本地配置文件**
4. **检查Git历史，确保没有其他泄露**
5. **考虑使用 `git filter-branch` 清理历史记录**

## 📞 获取API密钥

### DeepSeek
- 官网：https://platform.deepseek.com/
- 注册账号后在API管理页面获取密钥

### OpenAI
- 官网：https://platform.openai.com/
- 需要绑定支付方式

### 百度文心一言
- 官网：https://cloud.baidu.com/product/wenxinworkshop
- 需要实名认证

### 阿里通义千问
- 官网：https://dashscope.aliyun.com/
- 阿里云账号登录

### 腾讯混元
- 官网：https://cloud.tencent.com/product/hunyuan
- 腾讯云账号登录

## 💡 开发建议

- 在开发环境中，可以使用免费额度较大的模型进行测试
- 建议先配置DeepSeek，它提供较好的免费额度
- 可以同时配置多个AI服务，系统会自动切换
- 定期检查API使用量，避免超出限额

---

**记住：安全第一！保护好您的API密钥就是保护您的资金安全。** 