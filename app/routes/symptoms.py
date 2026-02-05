from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, Symptom

symptoms_bp = Blueprint('symptoms', __name__)

def get_area_info():
    """获取区域信息"""
    return {
        'red': {'name': '红色区域', 'count': 50, 'range': '1-50'},
        'green': {'name': '绿色区域', 'count': 50, 'range': '51-100'},
        'white': {'name': '白色区域', 'count': 50, 'range': '101-150'},
        'black': {'name': '黑色区域', 'count': 50, 'range': '151-200'},
        'yellow': {'name': '黄色区域', 'count': 50, 'range': '201-250'},
        'blue': {'name': '蓝色区域', 'count': 50, 'range': '251-300'}
    }

def determine_area(symptom_id):
    """根据症状ID确定区域"""
    if 1 <= symptom_id <= 50:
        return 'red'
    elif 51 <= symptom_id <= 100:
        return 'green'
    elif 101 <= symptom_id <= 150:
        return 'white'
    elif 151 <= symptom_id <= 200:
        return 'black'
    elif 201 <= symptom_id <= 250:
        return 'yellow'
    elif 251 <= symptom_id <= 300:
        return 'blue'
    else:
        return 'unknown'

@symptoms_bp.route('', methods=['GET'])
def get_all_symptoms():
    """获取所有症状列表（前端症状勾选页面使用）"""
    # 查询参数
    area = request.args.get('area', '').strip()
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # 构建查询
    query = Symptom.query
    
    # 按区域筛选
    if area and area in ['red', 'green', 'white', 'black', 'yellow', 'blue']:
        query = query.filter(Symptom.area == area)
    
    # 排序（按ID升序，与文档顺序一致）
    query = query.order_by(Symptom.id.asc())
    
    # 分页限制
    if limit is not None and limit > 0:
        query = query.limit(limit).offset(offset)
    
    # 执行查询
    symptoms = query.all()
    
    # 构建症状数据
    symptoms_data = []
    for symptom in symptoms:
        symptoms_data.append({
            'id': symptom.id,
            'name': symptom.name,
            'area': symptom.area,
            'brief_description': symptom.get_brief_description() if hasattr(symptom, 'get_brief_description') else symptom.description[:100] + '...' if len(symptom.description) > 100 else symptom.description
        })
    
    # 获取区域信息
    area_info = get_area_info()
    
    # 如果没有指定区域，只返回相关区域信息
    filtered_area_info = {}
    if area:
        if area in area_info:
            filtered_area_info[area] = area_info[area]
    else:
        filtered_area_info = area_info
    
    return jsonify({
        'code': 200,
        'message': '成功',
        'data': {
            'symptoms': symptoms_data,
            'total': len(symptoms_data),
            'areas': filtered_area_info
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@symptoms_bp.route('/<int:symptom_id>', methods=['GET'])
def get_symptom_detail(symptom_id):
    """获取单个症状的详细信息（前端详情展示使用）"""
    # 验证症状ID范围
    if symptom_id < 1 or symptom_id > 300:
        return jsonify({
            'code': 400,
            'message': '症状ID必须在1-300范围内',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    
    # 查询症状
    symptom = Symptom.query.get(symptom_id)
    
    if not symptom:
        # 如果数据库中不存在，返回基本信息
        area = determine_area(symptom_id)
        return jsonify({
            'code': 200,
            'message': '成功',
            'data': {
                'id': symptom_id,
                'name': f'症状{symptom_id}',
                'area': area,
                'description': '症状详情待导入',
                'precautions': None,
                'contraindications': None,
                'tags': []
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    # 获取标签
    tags = [tag.tag for tag in symptom.tags]
    
    return jsonify({
        'code': 200,
        'message': '成功',
        'data': {
            'id': symptom.id,
            'name': symptom.name,
            'area': symptom.area,
            'description': symptom.description,
            'precautions': symptom.precautions,
            'contraindications': symptom.contraindications,
            'tags': tags
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200