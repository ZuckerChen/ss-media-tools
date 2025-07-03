#!/usr/bin/env python3
"""
更新默认模型配置脚本
将默认模型从OpenAI改为DeepSeek
"""
import sqlite3
import os

def update_default_model():
    """更新默认模型配置"""
    db_path = "media_tools.db"
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查看当前配置
        cursor.execute("SELECT id, name, provider, is_default FROM ai_model_configs")
        configs = cursor.fetchall()
        
        print("📋 当前配置:")
        for config in configs:
            default_mark = " (默认)" if config[3] else ""
            print(f"  ID: {config[0]}, 名称: {config[1]}, 提供商: {config[2]}{default_mark}")
        
        # 取消所有默认配置
        cursor.execute("UPDATE ai_model_configs SET is_default = 0")
        
        # 检查是否已有DeepSeek配置
        cursor.execute("SELECT id FROM ai_model_configs WHERE provider = 'deepseek'")
        deepseek_config = cursor.fetchone()
        
        if deepseek_config:
            # 如果已有DeepSeek配置，设为默认
            cursor.execute("UPDATE ai_model_configs SET is_default = 1 WHERE id = ?", (deepseek_config[0],))
            print(f"✅ 已将现有DeepSeek配置(ID: {deepseek_config[0]})设为默认")
        else:
            # 如果没有DeepSeek配置，创建一个
            cursor.execute("""
                INSERT INTO ai_model_configs 
                (name, provider, model_name, max_tokens, temperature, is_default, is_active, usage_count, total_tokens, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                "默认DeepSeek模型",
                "deepseek", 
                "deepseek-chat",
                4000,
                0.7,
                1,  # is_default
                1,  # is_active
                0,  # usage_count
                0   # total_tokens
            ))
            print("✅ 已创建新的默认DeepSeek配置")
        
        # 提交更改
        conn.commit()
        
        # 验证更改
        cursor.execute("SELECT id, name, provider, is_default FROM ai_model_configs WHERE is_default = 1")
        default_config = cursor.fetchone()
        
        if default_config:
            print(f"🎯 当前默认模型: {default_config[1]} ({default_config[2]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        return False

if __name__ == "__main__":
    print("🔧 更新默认模型配置为DeepSeek")
    print("=" * 40)
    
    success = update_default_model()
    
    if success:
        print("\n🎉 默认模型配置更新成功！")
        print("现在可以在AI模型管理页面中看到DeepSeek作为默认模型")
    else:
        print("\n⚠️ 更新失败，请检查错误信息") 