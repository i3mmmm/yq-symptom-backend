from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
from models import db, Customer, SymptomRecord
import re

customers_bp = Blueprint('customers', __name__)

def validate_contact(contact):
    """验证联系方式（电话或邮箱）"""
    # 电话格式：1开头的11位数字
    phone_pattern = r'^1[3-9]\d{9}$'
    # 邮箱格式
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(phone_pattern, contact):
        return True
    if re.match(email_pattern, contact):
        return True
    
    return False

@customers_bp.route('', methods=['POST'])
def create_customer():
    """创建新客户"""
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['name', 'gender', 'age', 'contact']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({
                'code': 400,
                'message': f'缺少必要参数: {field}',
                'data': None,
                'timestamp': datetime.utcnow().isoformat()
            }), 400
    
    # 验证性别
    if data['gender'] not in ['male', 'female']:
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
    
    # 创建客户
    customer = Customer(
        name=data['name'].strip(),
        gender=data['gender'],
        age=age,
        contact=data['contact'].strip()
    )
    
    try:
        db.session.add(customer)
        db.session.commit()
        
        return jsonify({
            'code': 201,
            'message': '客户创建成功',
            'data': customer.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'创建客户失败: {str(e)}',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@customers_bp.route('', methods=['GET'])
@jwt_required()
def get_customers():
    """获取客户列表（分页+搜索）"""
    # 分页参数
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    
    # 限制每页大小
    if size > 100:
        size = 100
    
    # 搜索参数
    keyword = request.args.get('keyword', '').strip()
    gender = request.args.get('gender', '').strip()
    min_age = request.args.get('min_age', type=int)
    max_age = request.args.get('max_age', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    order_by = request.args.get('order_by', 'created_at')
    order = request.args.get('order', 'desc')
    
    # 构建查询
    query = Customer.query
    
    # 关键词搜索（姓名或联系方式）
    if keyword:
        query = query.filter(
            db.or_(
                Customer.name.ilike(f'%{keyword}%'),
                Customer.contact.ilike(f'%{keyword}%')
            )
        )
    
    # 性别筛选
    if gender in ['male', 'female']:
        query = query.filter(Customer.gender == gender)
    
    # 年龄筛选
    if min_age is not None:
        query = query.filter(Customer.age >= min_age)
    if max_age is not None:
        query = query.filter(Customer.age <= max_age)
    
    # 日期筛选
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Customer.created_at >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Customer.created_at <= end_dt)
        except ValueError:
            pass
    
    # 排序
    order_column = None
    if order_by == 'name':
        order_column = Customer.name
    elif order_by == 'age':
        order_column = Customer.age
    else:  # created_at
        order_column = Customer.created_at
    
    if order == 'asc':
        query = query.order_by(order_column.asc())
    else:
        query = query.order_by(order_column.desc())
    
    # 分页查询
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    # 构建响应数据
    items = []
    for customer in pagination.items:
        customer_dict = customer.to_dict()
        customer_dict['record_count'] = customer.get_record_count()
        customer_dict['last_submission'] = customer.get_last_submission()
        items.append(customer_dict)
    
    return jsonify({
        'code': 200,
        'message': '成功',
        'data': {
            'items': items,
            'total': pagination.total,
            'page': pagination.page,
            'size': pagination.per_page,
            'pages': pagination.pages
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@customers_bp.route('/<int:customer_id>', methods=['GET'])
@jwt_required()
def get_customer_detail(customer_id):
    """获取客户详情"""
    customer = Customer.query.get(customer_id)
    
    if not customer:
        return jsonify({
            'code': 404,
            'message': '客户不存在',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    # 获取客户的症状记录概览
    records = []
    for record in customer.symptom_records.order_by(SymptomRecord.submission_time.desc()).limit(10):
        records.append({
            'id': record.id,
            'submission_time': record.submission_time.isoformat() if record.submission_time else None,
            'symptom_count': record.symptom_count,
            'note': record.note
        })
    
    # 统计总症状数
    total_symptoms = sum(record.symptom_count for record in customer.symptom_records)
    
    customer_data = customer.to_dict()
    customer_data['records'] = records
    customer_data['total_records'] = customer.get_record_count()
    customer_data['total_symptoms'] = total_symptoms
    
    return jsonify({
        'code': 200,
        'message': '成功',
        'data': customer_data,
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@customers_bp.route('/<int:customer_id>', methods=['PUT'])
@jwt_required()
def update_customer(customer_id):
    """更新客户信息"""
    customer = Customer.query.get(customer_id)
    
    if not customer:
        return jsonify({
            'code': 404,
            'message': '客户不存在',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    data = request.get_json()
    
    # 更新字段
    if 'name' in data and data['name']:
        customer.name = data['name'].strip()
    
    if 'gender' in data:
        if data['gender'] not in ['male', 'female']:
            return jsonify({
                'code': 422,
                'message': '性别必须为 male 或 female',
                'data': None,
                'timestamp': datetime.utcnow().isoformat()
            }), 422
        customer.gender = data['gender']
    
    if 'age' in data:
        try:
            age = int(data['age'])
            if age < 1 or age > 120:
                return jsonify({
                    'code': 422,
                    'message': '年龄必须在1-120之间',
                    'data': None,
                    'timestamp': datetime.utcnow().isoformat()
                }), 422
            customer.age = age
        except ValueError:
            return jsonify({
                'code': 422,
                'message': '年龄必须是有效的整数',
                'data': None,
                'timestamp': datetime.utcnow().isoformat()
            }), 422
    
    if 'contact' in data and data['contact']:
        if not validate_contact(str(data['contact'])):
            return jsonify({
                'code': 422,
                'message': '联系方式必须是有效的手机号或邮箱',
                'data': None,
                'timestamp': datetime.utcnow().isoformat()
            }), 422
        customer.contact = data['contact'].strip()
    
    try:
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '客户信息更新成功',
            'data': customer.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'更新客户信息失败: {str(e)}',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
@jwt_required()
def delete_customer(customer_id):
    """删除客户（级联删除所有相关记录）"""
    # 确认删除头
    confirm_header = request.headers.get('X-Confirm-Delete')
    if confirm_header != 'true':
        return jsonify({
            'code': 400,
            'message': '需要确认删除，请在请求头中添加 X-Confirm-Delete: true',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    
    customer = Customer.query.get(customer_id)
    
    if not customer:
        return jsonify({
            'code': 404,
            'message': '客户不存在',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    # 获取删除前的统计信息
    record_count = customer.get_record_count()
    
    # 获取总症状选择数
    total_selections = 0
    for record in customer.symptom_records:
        total_selections += record.symptom_count
    
    try:
        # 删除客户（级联删除会自动删除相关记录）
        db.session.delete(customer)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '客户删除成功',
            'data': {
                'deleted_customer': True,
                'deleted_records': record_count,
                'deleted_selections': total_selections
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'删除客户失败: {str(e)}',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 500