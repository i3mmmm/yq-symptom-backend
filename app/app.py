import os
import sys
from datetime import datetime
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.config import config
from app.models import db
from app.routes.auth import auth_bp, create_default_admin
from app.routes.customers import customers_bp
from app.routes.records import records_bp
from app.routes.symptoms import symptoms_bp
from app.routes.analysis import analysis_bp
from app.routes.compare import compare_bp
from app.routes.reports import reports_bp
from app.routes.admin import admin_bp

def create_app(config_name='default'):
    """创建Flask应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 配置数据库路径
    db_path = app.config['DATABASE_PATH']
    if db_path:
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # 初始化扩展
    db.init_app(app)
    jwt = JWTManager(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 注册错误处理器
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'code': 400,
            'message': '请求参数错误',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'code': 404,
            'message': '资源不存在',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 500
    
    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(customers_bp, url_prefix='/api/v1/customers')
    app.register_blueprint(records_bp, url_prefix='/api/v1/records')
    app.register_blueprint(symptoms_bp, url_prefix='/api/v1/symptoms')
    app.register_blueprint(analysis_bp, url_prefix='/api/v1/analysis')
    app.register_blueprint(compare_bp, url_prefix='/api/v1/compare')
    app.register_blueprint(reports_bp, url_prefix='/api/v1/reports')
    app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')
    
    # 健康检查端点
    @app.route('/api/v1/health')
    def health_check():
        return jsonify({
            'code': 200,
            'message': '服务正常',
            'data': {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat()
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        print(f"数据库已初始化，路径: {db_path}")
        
        # 创建默认管理员账户
        create_default_admin()
    
    return app

if __name__ == '__main__':
    # 设置环境变量
    if len(sys.argv) > 1:
        config_name = sys.argv[1]
    else:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = create_app(config_name)
    
    # 运行应用
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8080))
    
    print(f"启动医疗症状收集与分析系统后端...")
    print(f"环境: {config_name}")
    print(f"数据库: {app.config['DATABASE_PATH']}")
    print(f"服务地址: http://{host}:{port}")
    
    app.run(host=host, port=port, debug=app.config.get('DEBUG', False))
