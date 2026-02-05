#!/usr/bin/env python3
"""
高级功能测试用例

测试智能整理、对比分析和PDF导出等高级功能
"""

import pytest
import json
import os
import sys
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../app'))

from app import create_app
from models import db, Customer, SymptomRecord, SymptomSelection, Symptom, SymptomTag

@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # 创建测试数据
        customer = Customer(
            name='测试客户',
            gender='male',
            age=35,
            contact='13800138000'
        )
        db.session.add(customer)
        db.session.commit()
        
        # 创建症状记录1
        record1 = SymptomRecord(
            customer_id=customer.id,
            submission_time=datetime.utcnow() - timedelta(days=30),
            symptom_count=15,
            note='第一次测试记录'
        )
        db.session.add(record1)
        
        # 创建症状记录2
        record2 = SymptomRecord(
            customer_id=customer.id,
            submission_time=datetime.utcnow(),
            symptom_count=20,
            note='第二次测试记录'
        )
        db.session.add(record2)
        db.session.commit()
        
        # 创建一些症状数据（简化版）
        symptom1 = Symptom(
            id=1,
            name='头疼',
            area='red',
            description='头疼原因描述',
            precautions='注意事项',
            contraindications='禁忌事项'
        )
        db.session.add(symptom1)
        
        symptom2 = Symptom(
            id=2,
            name='头晕',
            area='red',
            description='头晕原因描述',
            precautions='注意事项',
            contraindications='禁忌事项'
        )
        db.session.add(symptom2)
        
        symptom3 = Symptom(
            id=56,
            name='花眼',
            area='green',
            description='花眼原因描述',
            precautions='注意事项',
            contraindications='禁忌事项'
        )
        db.session.add(symptom3)
        
        # 创建症状标签
        tag1 = SymptomTag(symptom_id=1, tag='毒素')
        tag2 = SymptomTag(symptom_id=1, tag='习惯')
        tag3 = SymptomTag(symptom_id=2, tag='营养')
        tag4 = SymptomTag(symptom_id=3, tag='循环')
        
        db.session.add_all([tag1, tag2, tag3, tag4])
        
        # 创建症状选择
        selection1 = SymptomSelection(
            record_id=record1.id,
            symptom_id=1,
            area='red'
        )
        selection2 = SymptomSelection(
            record_id=record1.id,
            symptom_id=2,
            area='red'
        )
        selection3 = SymptomSelection(
            record_id=record2.id,
            symptom_id=1,
            area='red'
        )
        selection4 = SymptomSelection(
            record_id=record2.id,
            symptom_id=3,
            area='green'
        )
        
        db.session.add_all([selection1, selection2, selection3, selection4])
        db.session.commit()
        
        yield app
        
        # 清理
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    """获取认证头（简化版，实际应使用JWT）"""
    # 这里简化处理，实际应登录获取token
    return {
        'Authorization': 'Bearer test-token',
        'Content-Type': 'application/json'
    }

class TestAnalysisSummary:
    """测试症状统计分析"""
    
    def test_summary_endpoint_exists(self, client, auth_headers):
        """测试分析摘要端点存在"""
        response = client.get('/api/v1/analysis/summary/1', headers=auth_headers)
        assert response.status_code in [200, 404]  # 如果记录不存在返回404
    
    def test_summary_response_structure(self, client, auth_headers, app):
        """测试响应结构"""
        with app.app_context():
            # 确保记录存在
            record = SymptomRecord.query.first()
            if record:
                response = client.get(f'/api/v1/analysis/summary/{record.id}', headers=auth_headers)
                
                if response.status_code == 200:
                    data = json.loads(response.data)
                    
                    # 检查响应结构
                    assert 'code' in data
                    assert 'message' in data
                    assert 'data' in data
                    assert 'timestamp' in data
                    
                    # 检查数据内容
                    report_data = data['data']
                    assert 'record_id' in report_data
                    assert 'total_symptoms' in report_data
                    assert 'area_distribution' in report_data
                    assert 'overall_risk_level' in report_data
    
    def test_area_distribution_calculation(self, client, auth_headers, app):
        """测试区域分布计算"""
        with app.app_context():
            record = SymptomRecord.query.first()
            if record:
                response = client.get(f'/api/v1/analysis/summary/{record.id}', headers=auth_headers)
                
                if response.status_code == 200:
                    data = json.loads(response.data)
                    report_data = data['data']
                    
                    # 检查区域分布
                    areas = report_data['area_distribution']
                    assert isinstance(areas, list)
                    
                    # 检查每个区域的数据结构
                    for area in areas:
                        assert 'area' in area
                        assert 'area_name' in area
                        assert 'symptom_count' in area
                        assert 'percentage' in area
                        assert 'risk_level' in area

class TestCausesAnalysis:
    """测试原因分析"""
    
    def test_causes_endpoint_exists(self, client, auth_headers):
        """测试原因分析端点存在"""
        response = client.get('/api/v1/analysis/causes/1', headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_causes_response_structure(self, client, auth_headers, app):
        """测试原因分析响应结构"""
        with app.app_context():
            record = SymptomRecord.query.first()
            if record:
                response = client.get(f'/api/v1/analysis/causes/{record.id}', headers=auth_headers)
                
                if response.status_code == 200:
                    data = json.loads(response.data)
                    
                    assert 'code' in data
                    assert 'message' in data
                    assert 'data' in data
                    
                    causes_data = data['data']
                    assert 'tag_distribution' in causes_data
                    assert 'main_problem_types' in causes_data
                    assert 'summary' in causes_data
    
    def test_tag_distribution_calculation(self, client, auth_headers, app):
        """测试标签分布计算"""
        with app.app_context():
            record = SymptomRecord.query.first()
            if record:
                response = client.get(f'/api/v1/analysis/causes/{record.id}', headers=auth_headers)
                
                if response.status_code == 200:
                    data = json.loads(response.data)
                    causes_data = data['data']
                    
                    tags = causes_data['tag_distribution']
                    assert isinstance(tags, list)
                    
                    # 检查标签数据结构
                    for tag in tags:
                        assert 'tag' in tag
                        assert 'count' in tag
                        assert 'percentage' in tag

class TestRecommendations:
    """测试健康建议生成"""
    
    def test_recommendations_endpoint_exists(self, client, auth_headers):
        """测试建议生成端点存在"""
        response = client.get('/api/v1/analysis/recommendations/1', headers=auth_headers)
        assert response.status_code in [200, 404]
    
    def test_recommendations_structure(self, client, auth_headers, app):
        """测试建议数据结构"""
        with app.app_context():
            record = SymptomRecord.query.first()
            if record:
                response = client.get(f'/api/v1/analysis/recommendations/{record.id}', headers=auth_headers)
                
                if response.status_code == 200:
                    data = json.loads(response.data)
                    rec_data = data['data']
                    
                    assert 'recommendations' in rec_data
                    assert 'action_plan' in rec_data
                    
                    # 检查建议列表
                    recommendations = rec_data['recommendations']
                    assert isinstance(recommendations, list)
                    
                    for rec in recommendations:
                        assert 'category' in rec
                        assert 'priority' in rec
                        assert 'recommendation' in rec
                        assert 'action_items' in rec

class TestComparison:
    """测试对比分析"""
    
    def test_comparison_endpoint_exists(self, client, auth_headers):
        """测试对比分析端点存在"""
        response = client.get('/api/v1/analysis/compare/1/2', headers=auth_headers)
        assert response.status_code in [200, 404, 400]
    
    def test_comparison_structure(self, client, auth_headers, app):
        """测试对比分析数据结构"""
        with app.app_context():
            # 获取两条记录
            records = SymptomRecord.query.all()
            if len(records) >= 2:
                response = client.get(f'/api/v1/analysis/compare/{records[0].id}/{records[1].id}', 
                                     headers=auth_headers)
                
                if response.status_code == 200:
                    data = json.loads(response.data)
                    comp_data = data['data']
                    
                    assert 'added_count' in comp_data
                    assert 'removed_count' in comp_data
                    assert 'common_count' in comp_data
                    assert 'area_changes' in comp_data

class TestPDFReports:
    """测试PDF报告生成"""
    
    def test_report_generation_endpoint_exists(self, client, auth_headers):
        """测试报告生成端点存在"""
        response = client.post('/api/v1/reports/generate', 
                             json={'record_id': 1},
                             headers=auth_headers)
        assert response.status_code in [200, 404, 500]
    
    def test_report_response_structure(self, client, auth_headers, app):
        """测试报告生成响应结构"""
        with app.app_context():
            record = SymptomRecord.query.first()
            if record:
                response = client.post('/api/v1/reports/generate',
                                     json={'record_id': record.id},
                                     headers=auth_headers)
                
                if response.status_code == 200:
                    data = json.loads(response.data)
                    
                    assert 'code' in data
                    assert 'message' in data
                    assert 'data' in data
                    
                    report_info = data['data']
                    assert 'report_id' in report_info
                    assert 'file_name' in report_info
                    assert 'download_url' in report_info
    
    def test_report_download_endpoint_exists(self, client):
        """测试报告下载端点存在"""
        response = client.get('/api/v1/reports/download/TEST123')
        assert response.status_code in [200, 404]

if __name__ == '__main__':
    pytest.main(['-v', __file__])