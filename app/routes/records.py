from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
from models import db, Customer, SymptomRecord, SymptomSelection, Symptom
import re

records_bp = Blueprint('records', __name__)

def validate_contact(contact):
    """验证联系方式（电话或邮箱）"""
    phone_pattern = r'^1[3-9]\d{9}$'
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(phone_pattern, contact):
        return True
    if re.match(email_pattern, contact):
        return True
    
    return False

def determine_area(symptom_id):
    """根据症状ID确定区域（基于实际数据划分）"""
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

def validate_gender_symptoms(gender, symptom_ids):
    """验证性别与症状的兼容性"""
    if gender == 'male':
        # 男性不能选择妇科症状（症状ID 260-300）
        gynecological_symptoms = [sid for sid in symptom_ids if 260 <= sid <= 300]
        if gynecological_symptoms:
            return False, gynecological_symptoms
    return True, []

@records_bp.route('', methods=['POST'])
def submit_symptom_record():
    """提交症状记录（前端用户使用）"""
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['name', 'gender', 'age', 'contact', 'selected_symptoms']
    for field in required_fields:
        if field not in data or data[field] is None:
            return jsonify({
                'code': 400,
                'message': f'缺少必要参数: {field}',
                'data': None,
                'timestamp': datetime.utcnow().isoformat()
            }), 400
    
    # 验证性别
    gender = data['gender']
    if gender not in ['male', 'female']:
        return jsonify({
            'code': 422,
            'message': '性别必须为 male 或 female',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 422
    
    # 验证年龄
    try:
        age = int(data['age'])
        if age < 1 or age > 120:
            return jsonify({
                'code': 422,
                'message': '年龄必须在1-120之间',
                'data': None,
                'timestamp': datetime.utcnow().isoformat()
            }), 422
    except ValueError:
        return jsonify({
            'code': 422,
            'message': '年龄必须是有效的整数',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 422
    
    # 验证联系方式
    if not validate_contact(str(data['contact'])):
        return jsonify({
            'code': 422,
            'message': '联系方式必须是有效的手机号或邮箱',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 422
    
    # 验证症状列表
    selected_symptoms = data['selected_symptoms']
    if not isinstance(selected_symptoms, list) or len(selected_symptoms) == 0:
        return jsonify({
            'code': 422,
            'message': '至少选择一个症状',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 422
    
    # 验证症状ID范围
    invalid_symptoms = [sid for sid in selected_symptoms if not isinstance(sid, int) or sid < 1 or sid > 300]
    if invalid_symptoms:
        return jsonify({
            'code': 422,
            'message': f'症状ID必须在1-300范围内，无效的ID: {invalid_symptoms}',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 422
    
    # 验证性别与症状兼容性
    is_valid, invalid_gynecological = validate_gender_symptoms(gender, selected_symptoms)
    if not is_valid:
        return jsonify({
            'code': 422,
            'message': f'男性用户不能选择妇科症状（症状ID 260-300），无效的ID: {invalid_gynecological}',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 422
    
    # 备注字段（可选）
    note = data.get('note', '').strip() if 'note' in data else ''
    
    # 开始事务
    try:
        # 查找或创建客户
        customer = Customer.query.filter_by(
            contact=data['contact'].strip()
        ).first()
        
        if not customer:
            customer = Customer(
                name=data['name'].strip(),
                gender=gender,
                age=age,
                contact=data['contact'].strip()
            )
            db.session.add(customer)
            db.session.flush()  # 获取customer ID
        
        # 创建症状记录
        record = SymptomRecord(
            customer_id=customer.id,
            symptom_count=len(selected_symptoms),
            note=note
        )
        db.session.add(record)
        db.session.flush()  # 获取record ID
        
        # 创建症状选择关系
        for symptom_id in selected_symptoms:
            area = determine_area(symptom_id)
            selection = SymptomSelection(
                record_id=record.id,
                symptom_id=symptom_id,
                area=area
            )
            db.session.add(selection)
        
        # 提交事务
        db.session.commit()
        
        # 生成区域分布摘要
        area_names = {
            'red': '红色区域',
            'green': '绿色区域',
            'white': '白色区域',
            'black': '黑色区域',
            'yellow': '黄色区域',
            'blue': '蓝色区域'
        }
        
        area_counts = {}
        for symptom_id in selected_symptoms:
            area = determine_area(symptom_id)
            area_counts[area] = area_counts.get(area, 0) + 1
        
        # 找出主要区域
        primary_areas = []
        if area_counts:
            max_count = max(area_counts.values())
            primary_areas = [area for area, count in area_counts.items() if count == max_count]
        
        summary = f"您提交了{len(selected_symptoms)}个症状"
        if primary_areas:
            area_desc = '、'.join([area_names.get(area, area) for area in primary_areas])
            summary += f"，主要分布在{area_desc}"
        
        return jsonify({
            'code': 200,
            'message': '症状记录提交成功',
            'data': {
                'record_id': record.id,
                'customer_id': customer.id,
                'submission_time': record.submission_time.isoformat() if record.submission_time else None,
                'symptom_count': record.symptom_count,
                'summary': summary
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'提交症状记录失败: {str(e)}',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@records_bp.route('/<int:record_id>', methods=['GET'])
@jwt_required()
def get_record_detail(record_id):
    """获取症状记录详情（管理员使用）"""
    record = SymptomRecord.query.get(record_id)
    
    if not record:
        return jsonify({
            'code': 404,
            'message': '记录不存在',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    # 获取客户信息
    customer = Customer.query.get(record.customer_id)
    
    # 获取症状详情
    symptoms_data = []
    area_distribution = {}
    
    for selection in record.symptom_selections:
        # 区域统计
        area = selection.area
        area_distribution[area] = area_distribution.get(area, 0) + 1
        
        # 症状详情（如果症状表中存在）
        symptom = Symptom.query.get(selection.symptom_id)
        if symptom:
            symptoms_data.append(symptom.to_dict())
        else:
            # 如果症状表中不存在，返回基本信息
            symptoms_data.append({
                'id': selection.symptom_id,
                'name': f'症状{selection.symptom_id}',
                'area': area,
                'description': '症状详情待完善',
                'precautions': None,
                'contraindications': None,
                'tags': []
            })
    
    # 区域名称映射
    area_names = {
        'red': '红色区域',
        'green': '绿色区域',
        'white': '白色区域',
        'black': '黑色区域',
        'yellow': '黄色区域',
        'blue': '蓝色区域'
    }
    
    # 格式化区域分布
    formatted_area_distribution = {}
    for area, count in area_distribution.items():
        formatted_area_distribution[area] = {
            'count': count,
            'percentage': round(count / record.symptom_count * 100, 1) if record.symptom_count > 0 else 0,
            'name': area_names.get(area, area)
        }
    
    return jsonify({
        'code': 200,
        'message': '成功',
        'data': {
            'id': record.id,
            'customer_id': record.customer_id,
            'customer_name': customer.name if customer else '未知',
            'submission_time': record.submission_time.isoformat() if record.submission_time else None,
            'symptom_count': record.symptom_count,
            'note': record.note,
            'symptoms': symptoms_data,
            'area_distribution': formatted_area_distribution
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@records_bp.route('/<int:record_id>', methods=['DELETE'])
@jwt_required()
def delete_record(record_id):
    """删除症状记录（管理员使用）"""
    record = SymptomRecord.query.get(record_id)
    
    if not record:
        return jsonify({
            'code': 404,
            'message': '记录不存在',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    # 获取删除前的统计信息
    symptom_count = record.symptom_count
    
    try:
        # 删除记录（级联删除会自动删除相关选择）
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '记录删除成功',
            'data': {
                'deleted_record': True,
                'deleted_selections': symptom_count
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'删除记录失败: {str(e)}',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 500