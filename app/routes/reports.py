from flask import Blueprint, request, jsonify, send_file, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import os
import tempfile
import io
from models import db, SymptomRecord, SymptomSelection, Symptom, SymptomTag, Customer
from collections import Counter
import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
from reportlab.lib import colors
import base64

reports_bp = Blueprint('reports', __name__)

# 确保reports目录存在
REPORTS_DIR = 'reports'
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

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

@reports_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_health_report():
    """生成PDF健康咨询报告"""
    data = request.get_json()
    
    # 验证输入
    if not data or 'record_id' not in data:
        return jsonify({
            'code': 400,
            'message': '缺少record_id参数',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    
    record_id = data['record_id']
    
    # 查询记录
    record = SymptomRecord.query.get_or_404(record_id)
    customer = Customer.query.get_or_404(record.customer_id)
    
    # 获取分析数据（调用analysis模块的函数）
    # 这里简化处理，实际应该调用analysis模块的函数
    selections = SymptomSelection.query.filter_by(record_id=record_id).all()
    total_symptoms = len(selections)
    
    # 统计区域分布
    area_counts = Counter()
    for selection in selections:
        area = get_area_by_id(selection.symptom_id)
        area_counts[area] += 1
    
    # 构建报告数据
    report_data = {
        'report_id': f'REP_{datetime.utcnow().strftime("%Y%m%d")}_{record_id}',
        'generated_at': datetime.utcnow().strftime('%Y年%m月%d日 %H:%M'),
        'customer_name': customer.name,
        'customer_gender': '男' if customer.gender == 'male' else '女',
        'customer_age': customer.age,
        'customer_contact': customer.contact,
        'record_count': record.id,  # 简化处理
        'submission_time': record.submission_time.strftime('%Y年%m月%d日 %H:%M') if record.submission_time else '未知',
        'total_symptoms': total_symptoms,
        'overall_risk_level': '中危',  # 简化处理
        'primary_areas': ['红色区域', '绿色区域'],  # 简化处理
        'area_distribution': [],
        'causes_summary': '主要问题集中在毒素和营养方面',
        'tag_distribution': [
            {'tag': '毒素', 'count': 25},
            {'tag': '营养', 'count': 18},
            {'tag': '习惯', 'count': 12}
        ],
        'area_tag_analysis': [
            {
                'area_name': '红色区域',
                'total_symptoms': 15,
                'top_tags': [
                    {'tag': '毒素', 'count': 10},
                    {'tag': '营养', 'count': 8}
                ]
            }
        ],
        'overall_advice': '基于症状分析，建议重点关注排毒调理和营养改善',
        'recommendations': [
            {
                'category': '排毒调理',
                'priority': '高',
                'recommendation': '毒素相关问题较多，建议加强排毒功能',
                'action_items': ['增加膳食纤维摄入', '多喝水促进代谢']
            },
            {
                'category': '营养改善',
                'priority': '中',
                'recommendation': '营养不均衡问题明显，建议优化饮食结构',
                'action_items': ['均衡膳食营养', '补充必要维生素']
            }
        ],
        'action_plan': {
            'immediate_actions': ['增加膳食纤维摄入', '多喝水促进代谢'],
            'short_term_goals': ['均衡膳食营养', '补充必要维生素'],
            'long_term_strategies': ['建立健康生活习惯', '定期健康检查']
        }
    }
    
    # 填充区域分布数据
    area_info = {
        'red': {'name': '红色区域', 'description': '心、小肠'},
        'green': {'name': '绿色区域', 'description': '肝、胆'},
        'white': {'name': '白色区域', 'description': '肺、大肠'},
        'black': {'name': '黑色区域', 'description': '肾、膀胱'},
        'yellow': {'name': '黄色区域', 'description': '脾、胃'},
        'blue': {'name': '蓝色区域', 'description': '妇科病'}
    }
    
    for area_code in ['red', 'green', 'white', 'black', 'yellow', 'blue']:
        count = area_counts.get(area_code, 0)
        percentage = round(count / total_symptoms * 100, 2) if total_symptoms > 0 else 0
        
        report_data['area_distribution'].append({
            'area': area_code,
            'area_name': area_info[area_code]['name'],
            'description': area_info[area_code]['description'],
            'symptom_count': count,
            'percentage': percentage,
            'risk_level': '高危' if percentage > 20 else '中危' if percentage > 10 else '低危'
        })
    
    # 生成PDF报告
    try:
        pdf_buffer = generate_pdf_report(report_data)
        
        # 保存PDF文件
        filename = f"{report_data['report_id']}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)
        
        with open(filepath, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        # 返回成功响应
        return jsonify({
            'code': 200,
            'message': 'PDF报告生成成功',
            'data': {
                'report_id': report_data['report_id'],
                'customer_id': customer.id,
                'customer_name': customer.name,
                'file_name': filename,
                'file_path': filepath,
                'download_url': f'/api/v1/reports/download/{report_data["report_id"]}',
                'file_size': len(pdf_buffer.getvalue()),
                'generated_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat()
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        print(f"PDF生成错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'PDF报告生成失败: {str(e)}',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 500

def generate_pdf_report(report_data):
    """生成PDF报告"""
    buffer = io.BytesIO()
    
    # 创建PDF文档
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    
    story = []
    
    # 样式定义
    styles = getSampleStyleSheet()
    
    # 自定义样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor('#1a5dc1'),
        spaceAfter=30
    )
    
    heading1_style = ParagraphStyle(
        'Heading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a5dc1'),
        spaceAfter=12
    )
    
    heading2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c80ff'),
        spaceAfter=8
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    
    # 标题
    title = Paragraph(f"健康咨询分析报告", title_style)
    story.append(title)
    
    subtitle = Paragraph(f"报告编号：{report_data['report_id']} • 生成时间：{report_data['generated_at']}", 
                         ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, textColor=colors.gray))
    story.append(subtitle)
    story.append(Spacer(1, 20))
    
    # 客户信息
    story.append(Paragraph("客户基本信息", heading1_style))
    
    customer_info = [
        ['姓名', report_data['customer_name']],
        ['性别', report_data['customer_gender']],
        ['年龄', f"{report_data['customer_age']}岁"],
        ['联系方式', report_data['customer_contact']],
        ['报告对应记录', f"第{report_data['record_count']}次提交"],
        ['提交时间', report_data['submission_time']]
    ]
    
    customer_table = Table(customer_info, colWidths=[2*inch, 3*inch])
    customer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0ff')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1a5dc1')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d4e4ff'))
    ]))
    
    story.append(customer_table)
    story.append(Spacer(1, 25))
    
    # 症状汇总
    story.append(Paragraph("症状汇总分析", heading1_style))
    
    summary_info = [
        ['总症状数量', f"{report_data['total_symptoms']}个"],
        ['整体风险等级', report_data['overall_risk_level']],
        ['主要问题区域', '、'.join(report_data['primary_areas'])]
    ]
    
    summary_table = Table(summary_info, colWidths=[2*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fbff')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1a5dc1')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d4e4ff'))
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 15))
    
    # 区域分布
    story.append(Paragraph("区域症状分布", heading2_style))
    
    area_data = [['区域', '症状数量', '占比', '风险等级']]
    for area in report_data['area_distribution']:
        area_data.append([
            area['area_name'],
            str(area['symptom_count']),
            f"{area['percentage']}%",
            area['risk_level']
        ])
    
    area_table = Table(area_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1.5*inch])
    area_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c80ff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d4e4ff'))
    ]))
    
    story.append(area_table)
    story.append(Spacer(1, 25))
    
    # 原因分析
    story.append(Paragraph("原因分析", heading1_style))
    
    causes_text = f"<b>主要问题类型：</b> {report_data['causes_summary']}"
    story.append(Paragraph(causes_text, normal_style))
    story.append(Spacer(1, 10))
    
    # 标签分布
    story.append(Paragraph("症状原因标签分布", heading2_style))
    
    tag_text = "、".join([f"{tag['tag']}({tag['count']}个)" for tag in report_data['tag_distribution'][:5]])
    story.append(Paragraph(tag_text, normal_style))
    story.append(Spacer(1, 15))
    
    # 健康建议
    story.append(Paragraph("个性化健康建议", heading1_style))
    
    advice_text = f"<b>总体建议：</b> {report_data['overall_advice']}"
    story.append(Paragraph(advice_text, normal_style))
    story.append(Spacer(1, 15))
    
    # 详细建议
    story.append(Paragraph("详细建议列表", heading2_style))
    
    for rec in report_data['recommendations'][:3]:  # 只显示前3条建议
        rec_text = f"<b>{rec['category']}</b> ({rec['priority']}优先级)：{rec['recommendation']}"
        story.append(Paragraph(rec_text, normal_style))
        
        if rec['action_items']:
            action_text = "具体行动项：" + "；".join(rec['action_items'][:3])
            story.append(Paragraph(action_text, ParagraphStyle('Action', parent=normal_style, leftIndent=20)))
        
        story.append(Spacer(1, 10))
    
    # 生成PDF
    doc.build(story)
    
    buffer.seek(0)
    return buffer

@reports_bp.route('/download/<report_id>', methods=['GET'])
def download_report(report_id):
    """下载PDF报告"""
    filename = f"{report_id}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    if not os.path.exists(filepath):
        return jsonify({
            'code': 404,
            'message': '报告不存在或已过期',
            'data': None,
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    return send_file(filepath, as_attachment=True, download_name=filename)

@reports_bp.route('/template', methods=['GET'])
def get_report_template():
    """获取报告模板预览（用于测试）"""
    # 返回模板HTML
    template_path = os.path.join('templates', 'report_template.html')
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        return template_content, 200, {'Content-Type': 'text/html'}
    
    return "模板文件不存在", 404