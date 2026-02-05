from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import db, SymptomRecord, SymptomSelection, Customer
from collections import Counter

compare_bp = Blueprint('compare', __name__)

def get_area_by_id(symptom_id):
    """根据症状ID确定区域（与records.py中的determine_area函数保持一致）"""
    if 1 <= symptom_id <= 55:
        return 'red'
    elif 56 <= symptom_id <= 109:
        return 'green'
    elif 110 <= symptom_id <= 163:
        return 'white'
    elif 164 <= symptom_id <= 212:
        return 'black'
    elif 213 <= symptom_id <= 259:
        return 'yellow'
    elif 260 <= symptom_id <= 300:
        return 'blue'
    else:
        return 'unknown'

@compare_bp.route('/records/<int:record_a_id>/<int:record_b_id>', methods=['GET'])
@jwt_required()
def compare_two_records(record_a_id, record_b_id):
    """对比两次记录"""
    # 查询两条记录
    record_a = SymptomRecord.query.get_or_404(record_a_id)
    record_b = SymptomRecord.query.get_or_404(record_b_id)
    
    # 验证是同一客户
    if record_a.customer_id != record_b.customer_id:
        return jsonify({
            'code': 400,
            'message': '不能对比不同客户的记录',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    
    # 获取客户信息
    customer = Customer.query.get_or_404(record_a.customer_id)
    
    # 查询症状选择
    selections_a = SymptomSelection.query.filter_by(record_id=record_a_id).all()
    selections_b = SymptomSelection.query.filter_by(record_id=record_b_id).all()
    
    # 提取症状ID集合
    symptom_ids_a = set([s.symptom_id for s in selections_a])
    symptom_ids_b = set([s.symptom_id for s in selections_b])
    
    # 计算变化
    added_symptoms = symptom_ids_b - symptom_ids_a  # 第二次新增的症状
    removed_symptoms = symptom_ids_a - symptom_ids_b  # 第一次有但第二次没有的症状
    common_symptoms = symptom_ids_a & symptom_ids_b  # 两次都有的症状
    
    # 按区域统计变化
    area_changes = {}
    for area_code in ['red', 'green', 'white', 'black', 'yellow', 'blue']:
        count_a = len([s for s in selections_a if get_area_by_id(s.symptom_id) == area_code])
        count_b = len([s for s in selections_b if get_area_by_id(s.symptom_id) == area_code])
        
        change = count_b - count_a
        percentage_change = round(change / count_a * 100, 2) if count_a > 0 else (100 if change > 0 else 0)
        
        area_info = {
            'red': {'name': '红色区域'},
            'green': {'name': '绿色区域'},
            'white': {'name': '白色区域'},
            'black': {'name': '黑色区域'},
            'yellow': {'name': '黄色区域'},
            'blue': {'name': '蓝色区域'}
        }
        
        area_changes[area_code] = {
            'area_name': area_info[area_code]['name'],
            'count_a': count_a,
            'count_b': count_b,
            'change': change,
            'percentage_change': percentage_change,
            'trend': '改善' if change < 0 else '加重' if change > 0 else '稳定'
        }
    
    # 总体趋势
    total_change = len(selections_b) - len(selections_a)
    overall_trend = '改善' if total_change < 0 else '加重' if total_change > 0 else '稳定'
    
    return jsonify({
        'code': 200,
        'message': '成功',
        'data': {
            'customer_id': customer.id,
            'customer_name': customer.name,
            'record_a_id': record_a_id,
            'record_a_time': record_a.submission_time.isoformat() if record_a.submission_time else None,
            'record_b_id': record_b_id,
            'record_b_time': record_b.submission_time.isoformat() if record_b.submission_time else None,
            'total_symptoms_a': len(selections_a),
            'total_symptoms_b': len(selections_b),
            'net_change': total_change,
            'overall_trend': overall_trend,
            'added_count': len(added_symptoms),
            'removed_count': len(removed_symptoms),
            'common_count': len(common_symptoms),
            'area_changes': area_changes
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@compare_bp.route('/customers/<int:customer_id>/available', methods=['GET'])
@jwt_required()
def get_available_comparisons(customer_id):
    """获取可对比记录列表"""
    # 验证客户存在
    customer = Customer.query.get_or_404(customer_id)
    
    # 查询客户的所有记录，按时间倒序
    records = SymptomRecord.query.filter_by(customer_id=customer_id)\
        .order_by(SymptomRecord.submission_time.desc())\
        .all()
    
    # 构建记录列表
    record_list = []
    for record in records:
        record_list.append({
            'id': record.id,
            'submission_time': record.submission_time.isoformat() if record.submission_time else None,
            'symptom_count': record.symptom_count,
            'note': record.note,
            'created_at': record.created_at.isoformat() if record.created_at else None
        })
    
    return jsonify({
        'code': 200,
        'message': '成功',
        'data': {
            'customer_id': customer_id,
            'customer_name': customer.name,
            'records': record_list,
            'total': len(record_list)
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200