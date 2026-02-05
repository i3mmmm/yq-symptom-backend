from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_system_stats():
    """获取系统统计（暂未实现完整逻辑）"""
    return jsonify({
        'code': 200,
        'message': '统计功能开发中',
        'data': {
            'period': datetime.utcnow().strftime('%Y-%m-%d'),
            'customer_stats': {
                'total': 0,
                'new_today': 0,
                'new_this_week': 0,
                'gender_distribution': {'male': 0, 'female': 0}
            }
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200