import os
from datetime import timedelta

class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'health_system.db'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # 分页配置
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # 加密密钥（用于联系方式加密）
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY') or 'encryption-key-32-bytes-need-change'
    
    # 备份配置
    BACKUP_PATH = os.environ.get('BACKUP_PATH') or 'backups'
    BACKUP_RETENTION_DAYS = 7
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'app.log'

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    DATABASE_PATH = 'health_system_dev.db'

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DATABASE_PATH = 'health_system_test.db'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    DATABASE_PATH = '/data/health_system.db'  # Zeabur持久化存储路径

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}