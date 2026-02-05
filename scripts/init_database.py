#!/usr/bin/env python3
"""
医疗症状收集与分析系统 - 数据库初始化脚本
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../app'))

from app import create_app
from routes.auth import create_default_admin
from models import db

def init_database(config_name='development'):
    """初始化数据库"""
    print("=== 医疗症状收集与分析系统数据库初始化 ===")
    
    # 创建应用实例
    app = create_app(config_name)
    
    with app.app_context():
        # 创建所有表
        print("创建数据库表...")
        db.create_all()
        print(f"数据库表创建完成，路径: {app.config['DATABASE_PATH']}")
        
        # 创建默认管理员账户
        print("创建默认管理员账户...")
        admin = create_default_admin()
        print(f"默认管理员账户: {admin.username}")
        
        print("数据库初始化完成！")
        
        # 显示数据库信息
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"\n数据库包含 {len(tables)} 个表:")
        for table in tables:
            columns = inspector.get_columns(table)
            print(f"  - {table} ({len(columns)} 列)")

if __name__ == '__main__':
    # 支持命令行参数指定配置环境
    if len(sys.argv) > 1:
        config_name = sys.argv[1]
    else:
        config_name = 'development'
    
    init_database(config_name)