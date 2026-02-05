from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import datetime
from models import db, Admin

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """管理员登录"""
    data = request.get_json()
    
    # 验证请求数据
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({
            'code': 400,
            'message': '缺少用户名或密码',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    
    username = data['username'].strip()
    password = data['password'].strip()
    
    # 查询管理员
    admin = Admin.query.filter_by(username=username).first()
    
    if not admin or not admin.check_password(password):
        return jsonify({
            'code': 401,
            'message': '用户名或密码错误',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 401
    
    # 更新最后登录时间
    admin.last_login_at = datetime.utcnow()
    db.session.commit()
    
    # 生成访问令牌
    access_token = create_access_token(identity={
        'id': admin.id,
        'username': admin.username,
        'role': admin.role
    })
    
    refresh_token = create_refresh_token(identity={
        'id': admin.id,
        'username': admin.username,
        'role': admin.role
    })
    
    return jsonify({
        'code': 200,
        'message': '登录成功',
        'data': {
            'token': access_token,
            'token_type': 'Bearer',
            'expires_in': 86400,  # 24小时
            'admin': admin.to_dict()
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    current_user = get_jwt_identity()
    
    access_token = create_access_token(identity=current_user)
    
    return jsonify({
        'code': 200,
        'message': '令牌刷新成功',
        'data': {
            'token': access_token,
            'token_type': 'Bearer',
            'expires_in': 86400
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """登出（客户端应删除本地存储的token）"""
    # 在真实场景中，可能需要将token加入黑名单
    # 这里简化处理，仅返回成功消息
    return jsonify({
        'code': 200,
        'message': '登出成功',
        'data': None,
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_admin():
    """获取当前管理员信息"""
    current_user = get_jwt_identity()
    
    admin = Admin.query.get(current_user['id'])
    
    if not admin:
        return jsonify({
            'code': 404,
            'message': '管理员不存在',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    return jsonify({
        'code': 200,
        'message': '成功',
        'data': admin.to_dict(),
        'timestamp': datetime.utcnow().isoformat()
    }), 200

def create_default_admin():
    """创建默认管理员账户"""
    default_username = '931'
    default_password = 'z123456'
    
    # 检查是否已存在默认管理员
    admin = Admin.query.filter_by(username=default_username).first()
    
    if not admin:
        admin = Admin(
            username=default_username,
            name='系统管理员',
            role='super_admin'
        )
        admin.set_password(default_password)
        db.session.add(admin)
        db.session.commit()
        print(f"已创建默认管理员账户: {default_username}")
    
    return admin