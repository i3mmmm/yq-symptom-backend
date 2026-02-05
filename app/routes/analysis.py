from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import db, SymptomRecord, SymptomSelection, Symptom, SymptomTag, Customer
from collections import Counter
import math

analysis_bp = Blueprint('analysis', __name__)

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

@analysis_bp.route('/summary/<int:record_id>', methods=['GET'])
@jwt_required()
def get_analysis_summary(record_id):
    """症状统计分析：按区域统计症状数量，计算占比"""
    # 查询记录
    record = SymptomRecord.query.get_or_404(record_id)
    
    # 查询症状选择
    selections = SymptomSelection.query.filter_by(record_id=record_id).all()
    
    # 统计区域分布
    area_counts = Counter()
    for selection in selections:
        # 使用症状ID确定区域（而不是selection.area字段，因为可能不正确）
        area = get_area_by_id(selection.symptom_id)
        area_counts[area] += 1
    
    total_symptoms = len(selections)
    
    # 区域信息映射
    area_info = {
        'red': {'name': '红色区域', 'description': '心、小肠'},
        'green': {'name': '绿色区域', 'description': '肝、胆'},
        'white': {'name': '白色区域', 'description': '肺、大肠'},
        'black': {'name': '黑色区域', 'description': '肾、膀胱'},
        'yellow': {'name': '黄色区域', 'description': '脾、胃'},
        'blue': {'name': '蓝色区域', 'description': '妇科病'}
    }
    
    # 构建区域统计结果
    area_statistics = []
    for area_code in ['red', 'green', 'white', 'black', 'yellow', 'blue']:
        count = area_counts.get(area_code, 0)
        percentage = round(count / total_symptoms * 100, 2) if total_symptoms > 0 else 0
        
        area_statistics.append({
            'area': area_code,
            'area_name': area_info[area_code]['name'],
            'description': area_info[area_code]['description'],
            'symptom_count': count,
            'percentage': percentage,
            'risk_level': '高危' if percentage > 20 else '中危' if percentage > 10 else '低危'
        })
    
    # 按数量排序
    area_statistics.sort(key=lambda x: x['symptom_count'], reverse=True)
    
    # 主要问题区域
    primary_areas = [area for area in area_statistics if area['symptom_count'] > 0]
    
    # 风险等级
    total_percentage_high = sum(area['percentage'] for area in area_statistics if area['percentage'] > 15)
    if total_percentage_high > 40:
        overall_risk = '高危'
    elif total_percentage_high > 20:
        overall_risk = '中危'
    else:
        overall_risk = '低危'
    
    return jsonify({
        'code': 200,
        'message': '成功',
        'data': {
            'record_id': record_id,
            'customer_id': record.customer_id,
            'total_symptoms': total_symptoms,
            'area_distribution': area_statistics,
            'primary_areas': primary_areas[:3],  # 前三个主要区域
            'overall_risk_level': overall_risk,
            'submission_time': record.submission_time.isoformat() if record.submission_time else None,
            'note': record.note
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@analysis_bp.route('/causes/<int:record_id>', methods=['GET'])
@jwt_required()
def get_causes_analysis(record_id):
    """症状原因分析：基于症状标签分析主要原因类型"""
    # 查询记录
    record = SymptomRecord.query.get_or_404(record_id)
    
    # 查询症状选择
    selections = SymptomSelection.query.filter_by(record_id=record_id).all()
    
    # 收集所有症状的标签
    tag_counts = Counter()
    area_tag_counts = {}
    
    for selection in selections:
        symptom = Symptom.query.get(selection.symptom_id)
        if not symptom:
            continue
            
        # 获取症状标签
        tags = [tag.tag for tag in symptom.tags] if hasattr(symptom, 'tags') else []
        
        # 统计全局标签
        for tag in tags:
            tag_counts[tag] += 1
        
        # 按区域统计标签
        area = get_area_by_id(symptom.id)
        if area not in area_tag_counts:
            area_tag_counts[area] = Counter()
        
        for tag in tags:
            area_tag_counts[area][tag] += 1
    
    total_symptoms = len(selections)
    
    # 标签百分比
    tag_percentages = []
    for tag, count in tag_counts.most_common():
        percentage = round(count / total_symptoms * 100, 2) if total_symptoms > 0 else 0
        tag_percentages.append({
            'tag': tag,
            'count': count,
            'percentage': percentage,
            'severity': '高' if percentage > 30 else '中' if percentage > 15 else '低'
        })
    
    # 按区域标签分析
    area_analysis = []
    for area_code in ['red', 'green', 'white', 'black', 'yellow', 'blue']:
        if area_code in area_tag_counts:
            area_tags = area_tag_counts[area_code]
            total_area_symptoms = sum(area_tags.values())
            
            top_tags = []
            for tag, count in area_tags.most_common(3):
                percentage = round(count / total_area_symptoms * 100, 2) if total_area_symptoms > 0 else 0
                top_tags.append({
                    'tag': tag,
                    'count': count,
                    'percentage': percentage
                })
            
            area_info = {
                'red': {'name': '红色区域'},
                'green': {'name': '绿色区域'},
                'white': {'name': '白色区域'},
                'black': {'name': '黑色区域'},
                'yellow': {'name': '黄色区域'},
                'blue': {'name': '蓝色区域'}
            }
            
            area_analysis.append({
                'area': area_code,
                'area_name': area_info[area_code]['name'],
                'total_symptoms': total_area_symptoms,
                'top_tags': top_tags
            })
    
    # 主要问题类型
    main_problem_types = []
    if tag_percentages:
        # 最常见的5个标签
        for tag_info in tag_percentages[:5]:
            main_problem_types.append({
                'type': tag_info['tag'],
                'description': get_tag_description(tag_info['tag']),
                'impact_score': tag_info['percentage'] / 10  # 简单评分
            })
    
    return jsonify({
        'code': 200,
        'message': '成功',
        'data': {
            'record_id': record_id,
            'total_symptoms': total_symptoms,
            'tag_distribution': tag_percentages,
            'area_tag_analysis': area_analysis,
            'main_problem_types': main_problem_types,
            'summary': generate_causes_summary(tag_counts, total_symptoms)
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@analysis_bp.route('/recommendations/<int:record_id>', methods=['GET'])
@jwt_required()
def get_recommendations(record_id):
    """健康建议生成：结合症状严重程度和原因生成个性化建议"""
    # 查询记录
    record = SymptomRecord.query.get_or_404(record_id)
    
    # 获取客户信息
    customer = Customer.query.get_or_404(record.customer_id)
    
    # 获取分析数据
    selections = SymptomSelection.query.filter_by(record_id=record_id).all()
    
    # 统计标签
    tag_counts = Counter()
    area_counts = Counter()
    
    for selection in selections:
        symptom = Symptom.query.get(selection.symptom_id)
        if not symptom:
            continue
            
        # 标签统计
        tags = [tag.tag for tag in symptom.tags] if hasattr(symptom, 'tags') else []
        for tag in tags:
            tag_counts[tag] += 1
        
        # 区域统计
        area = get_area_by_id(symptom.id)
        area_counts[area] += 1
    
    total_symptoms = len(selections)
    
    # 生成建议
    recommendations = []
    
    # 1. 基于整体风险
    if total_symptoms > 30:
        recommendations.append({
            'category': '整体健康',
            'priority': '高',
            'recommendation': '症状数量较多，建议进行全面健康评估和系统调理',
            'action_items': ['预约全面体检', '制定长期健康计划', '考虑专业健康管理服务']
        })
    elif total_symptoms > 15:
        recommendations.append({
            'category': '整体健康',
            'priority': '中',
            'recommendation': '症状数量中等，建议关注主要问题区域并进行针对性改善',
            'action_items': ['重点调理主要问题区域', '改善生活习惯', '定期复查']
        })
    else:
        recommendations.append({
            'category': '整体健康',
            'priority': '低',
            'recommendation': '症状数量较少，保持良好生活习惯，预防为主',
            'action_items': ['维持健康生活方式', '定期自我检查', '注意早期预警信号']
        })
    
    # 2. 基于主要标签
    top_tags = tag_counts.most_common(3)
    for tag, count in top_tags:
        percentage = round(count / total_symptoms * 100, 2) if total_symptoms > 0 else 0
        
        if tag == '毒素':
            recommendations.append({
                'category': '排毒调理',
                'priority': '高' if percentage > 25 else '中',
                'recommendation': f'毒素相关问题占{percentage}%，建议加强排毒功能',
                'action_items': ['增加膳食纤维摄入', '多喝水促进代谢', '适量运动排汗', '避免接触环境毒素']
            })
        elif tag == '营养':
            recommendations.append({
                'category': '营养改善',
                'priority': '高' if percentage > 25 else '中',
                'recommendation': f'营养相关问题占{percentage}%，建议优化饮食结构',
                'action_items': ['均衡膳食营养', '补充必要维生素矿物质', '定期营养评估']
            })
        elif tag == '习惯':
            recommendations.append({
                'category': '生活习惯',
                'priority': '中',
                'recommendation': f'生活习惯相关问题占{percentage}%，建议改善不良生活方式',
                'action_items': ['规律作息', '适度运动', '减少熬夜', '管理压力']
            })
    
    # 3. 基于主要区域
    top_areas = area_counts.most_common(2)
    for area_code, count in top_areas:
        percentage = round(count / total_symptoms * 100, 2) if total_symptoms > 0 else 0
        
        area_info = {
            'red': {'name': '心、小肠系统', 'focus': '心血管健康、血液循环'},
            'green': {'name': '肝、胆系统', 'focus': '解毒功能、情绪管理'},
            'white': {'name': '肺、大肠系统', 'focus': '呼吸健康、肠道功能'},
            'black': {'name': '肾、膀胱系统', 'focus': '泌尿健康、水分代谢'},
            'yellow': {'name': '脾、胃系统', 'focus': '消化吸收、免疫调节'},
            'blue': {'name': '妇科系统', 'focus': '内分泌平衡、生殖健康'}
        }
        
        if area_code in area_info:
            recommendations.append({
                'category': area_info[area_code]['name'],
                'priority': '高' if percentage > 20 else '中',
                'recommendation': f'{area_info[area_code]["name"]}症状占{percentage}%，建议重点关注{area_info[area_code]["focus"]}',
                'action_items': [f'进行{area_info[area_code]["name"]}专项检查', f'针对{area_info[area_code]["focus"]}制定调理方案']
            })
    
    # 4. 个性化建议（基于性别、年龄）
    age_group = '中青年' if 18 <= customer.age <= 45 else '中老年' if 46 <= customer.age <= 65 else '老年'
    
    if customer.gender == 'female':
        recommendations.append({
            'category': '性别专属',
            'priority': '中',
            'recommendation': f'作为{age_group}女性，建议关注妇科健康、内分泌平衡和骨骼健康',
            'action_items': ['定期妇科检查', '关注月经周期变化', '补充钙质维护骨骼']
        })
    else:
        recommendations.append({
            'category': '性别专属',
            'priority': '中',
            'recommendation': f'作为{age_group}男性，建议关注心血管健康、前列腺功能和代谢状况',
            'action_items': ['定期心血管检查', '关注前列腺健康', '控制体重和血脂']
        })
    
    # 按优先级排序
    priority_order = {'高': 3, '中': 2, '低': 1}
    recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
    
    # 生成总体建议
    overall_advice = f"基于您的症状分析，我们为您生成了{len(recommendations)}条个性化健康建议。请重点关注{recommendations[0]['category']}领域，并逐步实施相关行动项。"
    
    return jsonify({
        'code': 200,
        'message': '成功',
        'data': {
            'record_id': record_id,
            'customer_id': customer.id,
            'customer_name': customer.name,
            'customer_gender': customer.gender,
            'customer_age': customer.age,
            'total_symptoms': total_symptoms,
            'overall_advice': overall_advice,
            'recommendations': recommendations,
            'action_plan': generate_action_plan(recommendations)
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@analysis_bp.route('/compare/<int:record_id1>/<int:record_id2>', methods=['GET'])
@jwt_required()
def compare_records(record_id1, record_id2):
    """两次记录对比：对比症状变化，识别新增/减少症状"""
    # 查询两条记录
    record1 = SymptomRecord.query.get_or_404(record_id1)
    record2 = SymptomRecord.query.get_or_404(record_id2)
    
    # 验证是同一客户
    if record1.customer_id != record2.customer_id:
        return jsonify({
            'code': 400,
            'message': '不能对比不同客户的记录',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    
    # 获取客户信息
    customer = Customer.query.get_or_404(record1.customer_id)
    
    # 查询症状选择
    selections1 = SymptomSelection.query.filter_by(record_id=record_id1).all()
    selections2 = SymptomSelection.query.filter_by(record_id=record_id2).all()
    
    # 提取症状ID集合
    symptom_ids1 = set([s.symptom_id for s in selections1])
    symptom_ids2 = set([s.symptom_id for s in selections2])
    
    # 计算变化
    added_symptoms = symptom_ids2 - symptom_ids1  # 第二次新增的症状
    removed_symptoms = symptom_ids1 - symptom_ids2  # 第一次有但第二次没有的症状
    common_symptoms = symptom_ids1 & symptom_ids2  # 两次都有的症状
    
    # 获取症状详情
    def get_symptom_details(symptom_ids):
        details = []
        for symptom_id in symptom_ids:
            symptom = Symptom.query.get(symptom_id)
            if symptom:
                details.append({
                    'id': symptom.id,
                    'name': symptom.name,
                    'area': get_area_by_id(symptom.id),
                    'area_name': get_area_name(get_area_by_id(symptom.id)),
                    'description_preview': symptom.description[:100] + '...' if len(symptom.description) > 100 else symptom.description
                })
        return details
    
    added_details = get_symptom_details(added_symptoms)
    removed_details = get_symptom_details(removed_symptoms)
    common_details = get_symptom_details(common_symptoms)
    
    # 按区域统计变化
    area_changes = {}
    for area_code in ['red', 'green', 'white', 'black', 'yellow', 'blue']:
        count1 = len([s for s in selections1 if get_area_by_id(s.symptom_id) == area_code])
        count2 = len([s for s in selections2 if get_area_by_id(s.symptom_id) == area_code])
        
        change = count2 - count1
        percentage_change = round(change / count1 * 100, 2) if count1 > 0 else (100 if change > 0 else 0)
        
        area_changes[area_code] = {
            'area_name': get_area_name(area_code),
            'count1': count1,
            'count2': count2,
            'change': change,
            'percentage_change': percentage_change,
            'trend': '改善' if change < 0 else '加重' if change > 0 else '稳定'
        }
    
    # 总体趋势
    total_change = len(selections2) - len(selections1)
    overall_trend = '改善' if total_change < 0 else '加重' if total_change > 0 else '稳定'
    
    # 生成对比摘要
    comparison_summary = {
        'total_symptoms1': len(selections1),
        'total_symptoms2': len(selections2),
        'net_change': total_change,
        'overall_trend': overall_trend,
        'improvement_rate': round(len(removed_symptoms) / len(selections1) * 100, 2) if len(selections1) > 0 else 0,
        'worsening_rate': round(len(added_symptoms) / len(selections1) * 100, 2) if len(selections1) > 0 else 0
    }
    
    # 生成可视化数据（供前端图表使用）
    visualization_data = {
        'area_charts': [
            {
                'area': area_code,
                'area_name': get_area_name(area_code),
                'values': [
                    {'record': '第一次', 'count': area_changes[area_code]['count1']},
                    {'record': '第二次', 'count': area_changes[area_code]['count2']}
                ]
            }
            for area_code in ['red', 'green', 'white', 'black', 'yellow', 'blue']
        ],
        'change_chart': [
            {'type': '新增症状', 'count': len(added_symptoms)},
            {'type': '减少症状', 'count': len(removed_symptoms)},
            {'type': '共同症状', 'count': len(common_symptoms)}
        ]
    }
    
    return jsonify({
        'code': 200,
        'message': '成功',
        'data': {
            'customer_id': customer.id,
            'customer_name': customer.name,
            'record1_id': record_id1,
            'record1_time': record1.submission_time.isoformat() if record1.submission_time else None,
            'record2_id': record_id2,
            'record2_time': record2.submission_time.isoformat() if record2.submission_time else None,
            'comparison_summary': comparison_summary,
            'added_symptoms': added_details,
            'removed_symptoms': removed_details,
            'common_symptoms': common_details,
            'area_changes': area_changes,
            'visualization_data': visualization_data
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200

# 辅助函数
def get_tag_description(tag):
    """获取标签描述"""
    descriptions = {
        '营养': '营养不均衡或缺乏必要营养素',
        '排毒': '身体排毒功能不足或毒素积累',
        '毒素': '内外毒素影响身体功能',
        '习惯': '不良生活习惯导致的问题',
        '体质': '先天体质或遗传因素',
        '免疫力': '免疫系统功能异常',
        '微循环': '微循环系统障碍',
        '循环': '血液循环或淋巴循环问题',
        '内分泌': '内分泌系统失调',
        '情绪': '情绪心理因素影响',
        '寒湿': '寒湿体质或环境影响',
        '温度': '体温调节或环境温度适应问题',
        '其他': '其他未分类原因'
    }
    return descriptions.get(tag, '未知原因')

def get_area_name(area_code):
    """获取区域名称"""
    area_names = {
        'red': '红色区域（心、小肠）',
        'green': '绿色区域（肝、胆）',
        'white': '白色区域（肺、大肠）',
        'black': '黑色区域（肾、膀胱）',
        'yellow': '黄色区域（脾、胃）',
        'blue': '蓝色区域（妇科）'
    }
    return area_names.get(area_code, '未知区域')

def generate_causes_summary(tag_counts, total_symptoms):
    """生成原因分析摘要"""
    if total_symptoms == 0:
        return '暂无症状数据'
    
    top_tags = tag_counts.most_common(2)
    
    if not top_tags:
        return '症状原因不明确'
    
    tag1, count1 = top_tags[0]
    percentage1 = round(count1 / total_symptoms * 100, 2)
    
    if len(top_tags) > 1:
        tag2, count2 = top_tags[1]
        percentage2 = round(count2 / total_symptoms * 100, 2)
        return f'主要问题集中在{tag1}({percentage1}%)和{tag2}({percentage2}%)方面'
    else:
        return f'主要问题集中在{tag1}({percentage1}%)方面'

def generate_action_plan(recommendations):
    """生成行动方案"""
    high_priority = [r for r in recommendations if r['priority'] == '高']
    medium_priority = [r for r in recommendations if r['priority'] == '中']
    
    action_plan = {
        'immediate_actions': [],
        'short_term_goals': [],
        'long_term_strategies': []
    }
    
    # 高优先级建议转化为立即行动
    for rec in high_priority[:2]:  # 取前2个高优先级
        if rec['action_items']:
            action_plan['immediate_actions'].extend(rec['action_items'][:2])
    
    # 中优先级建议转化为短期目标
    for rec in medium_priority[:3]:  # 取前3个中优先级
        if rec['action_items']:
            action_plan['short_term_goals'].extend(rec['action_items'][:2])
    
    # 长期策略
    action_plan['long_term_strategies'] = [
        '建立健康生活习惯并长期坚持',
        '定期进行健康检查和评估',
        '根据身体状况调整调理方案'
    ]
    
    return action_plan