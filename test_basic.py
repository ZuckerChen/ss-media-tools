#!/usr/bin/env python3
"""
基础功能测试脚本
验证自媒体运营工具的核心功能
"""
import os
import sys
from sqlalchemy.orm import Session

def test_imports():
    """测试模块导入"""
    print("🧪 测试模块导入...")
    try:
        import config
        import models
        import ai_models
        print("✅ 所有模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_database():
    """测试数据库连接和初始化"""
    print("🧪 测试数据库...")
    try:
        from models import init_db, SessionLocal, AIModelConfig
        
        # 初始化数据库
        init_db()
        
        # 测试数据库连接
        db = SessionLocal()
        configs = db.query(AIModelConfig).all()
        db.close()
        
        print(f"✅ 数据库连接成功，现有配置: {len(configs)}个")
        return True
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def test_ai_model_manager():
    """测试AI模型管理器"""
    print("🧪 测试AI模型管理器...")
    try:
        from models import SessionLocal
        from ai_models import AIModelManager
        
        db = SessionLocal()
        manager = AIModelManager(db)
        
        # 测试获取配置列表
        configs = manager.list_configs()
        
        # 测试使用统计
        stats = manager.get_usage_stats()
        
        db.close()
        
        print(f"✅ AI模型管理器正常，配置数量: {len(configs)}")
        return True
    except Exception as e:
        print(f"❌ AI模型管理器测试失败: {e}")
        return False

def test_prompt_templates():
    """测试提示词模板"""
    print("🧪 测试提示词模板...")
    try:
        from ai_models import PromptTemplates
        
        # 测试标题生成模板
        prompt = PromptTemplates.TITLE_GENERATION.format(
            topic="人工智能",
            platform="微信公众号",
            style="专业",
            requirements="包含关键词"
        )
        
        if len(prompt) > 100:  # 基本验证模板是否正常
            print("✅ 提示词模板正常")
            return True
        else:
            print("❌ 提示词模板异常")
            return False
    except Exception as e:
        print(f"❌ 提示词模板测试失败: {e}")
        return False

def test_config():
    """测试配置文件"""
    print("🧪 测试配置文件...")
    try:
        from config import settings, AI_MODEL_CONFIGS, PLATFORM_CONFIGS
        
        # 测试基本配置
        assert settings.APP_NAME is not None
        assert len(AI_MODEL_CONFIGS) > 0
        assert len(PLATFORM_CONFIGS) > 0
        
        print("✅ 配置文件正常")
        return True
    except Exception as e:
        print(f"❌ 配置文件测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("🎯 自媒体运营工具 - 基础功能测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("配置文件", test_config),
        ("数据库", test_database),
        ("AI模型管理器", test_ai_model_manager),
        ("提示词模板", test_prompt_templates),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_func():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统准备就绪")
        print("\n📋 下一步操作:")
        print("1. 配置 .env 文件（复制 env_example.txt）")
        print("2. 添加至少一个AI模型API密钥")
        print("3. 运行 python start.py 启动应用")
    else:
        print("⚠️  部分测试失败，请检查错误信息并修复")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 