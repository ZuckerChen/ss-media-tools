#!/usr/bin/env python3
"""
自媒体运营工具启动脚本
"""
import sys
import subprocess
import os
from pathlib import Path

def check_requirements():
    """检查依赖包是否安装"""
    try:
        import fastapi
        import streamlit
        import sqlalchemy
        import requests
        import pandas
        print("✅ 依赖包检查通过")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        print("请先运行: pip install -r requirements.txt")
        return False

def init_database():
    """初始化数据库"""
    try:
        from models import init_db
        init_db()
        print("✅ 数据库初始化完成")
        return True
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False

def check_env_file():
    """检查环境变量文件"""
    if not os.path.exists('.env'):
        print("⚠️  未找到 .env 文件")
        print("请将 env_example.txt 复制为 .env 并配置API密钥")
        return False
    print("✅ 环境配置文件存在")
    return True

def start_backend():
    """启动后端API服务"""
    print("🚀 启动后端API服务...")
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ])

def start_frontend():
    """启动前端界面"""
    print("🚀 启动前端界面...")
    subprocess.run([
        sys.executable, "-m", "streamlit", 
        "run", "app.py", 
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ])

def main():
    print("🎯 自媒体运营工具启动器")
    print("=" * 50)
    
    # 检查依赖
    if not check_requirements():
        return
    
    # 检查环境配置
    if not check_env_file():
        print("\n🔧 配置步骤:")
        print("1. 将 env_example.txt 复制为 .env")
        print("2. 编辑 .env 文件，填入AI模型API密钥")
        print("3. 重新运行此脚本")
        return
    
    # 初始化数据库
    if not init_database():
        return
    
    # 选择启动模式
    print("\n请选择启动模式:")
    print("1. 启动后端API服务 (端口: 8000)")
    print("2. 启动前端界面 (端口: 8501)")
    print("3. 同时启动前后端 (推荐)")
    print("4. 退出")
    
    try:
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            start_backend()
        elif choice == "2":
            start_frontend()
        elif choice == "3":
            # 同时启动需要多进程
            import threading
            import time
            
            # 启动后端
            backend_thread = threading.Thread(target=start_backend)
            backend_thread.daemon = True
            backend_thread.start()
            
            # 等待后端启动
            print("⏳ 等待后端服务启动...")
            time.sleep(3)
            
            # 启动前端
            start_frontend()
            
        elif choice == "4":
            print("👋 再见!")
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main() 