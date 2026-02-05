import pytest
import json
from datetime import datetime
from app import create_app
from models import db, Customer, Admin

@pytest.fixture
def app():
    """创建测试应用实例"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # 创建测试管理员账户
        admin = Admin(
            username='test_admin',
            name='测试管理员',
            role='operator'
        )
        admin.set_password('test_password')
        db.session.add(admin)
        db.session.commit()
        
        yield app
    
    # 清理测试数据库
    import os
    if os.path.exists('health_system_test.db'):
        os.remove('health_system_test.db')

@pytest.fixture
def client(app):
    """测试客户端"""
    return app.test_client()

@pytest.fixture
def auth_token(client):
    """获取认证token"""
    response = client.post('/api/v1/auth/login', 
                          json={'username': 'test_admin', 'password': 'test_password'})
    data = json.loads(response.data)
    return data['data']['token']

def test_health_check(client):
    """测试健康检查端点"""
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['code'] == 200
    assert data['message'] == '服务正常'
    assert 'data' in data
    assert data['data']['status'] == 'healthy'

def test_admin_login(client):
    """测试管理员登录"""
    # 正确凭据
    response = client.post('/api/v1/auth/login', 
                          json={'username': 'test_admin', 'password': 'test_password'})
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['code'] == 200
    assert data['message'] == '登录成功'
    assert 'token' in data['data']
    assert 'admin' in data['data']
    
    # 错误凭据
    response = client.post('/api/v1/auth/login', 
                          json={'username': 'test_admin', 'password': 'wrong_password'})
    assert response.status_code == 401
    
    data = json.loads(response.data)
    assert data['code'] == 401
    assert data['message'] == '用户名或密码错误'

def test_create_customer(client):
    """测试创建客户"""
    customer_data = {
        'name': '测试客户',
        'gender': 'male',
        'age': 30,
        'contact': '13800138000',
        'selected_symptoms': [1, 5, 10]
    }
    
    response = client.post('/api/v1/records', json=customer_data)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['code'] == 200
    assert data['message'] == '症状记录提交成功'
    assert 'record_id' in data['data']
    assert 'customer_id' in data['data']
    
    # 验证客户已创建
    response = client.get('/api/v1/customers', 
                         headers={'Authorization': f'Bearer {auth_token(client)}'})
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert len(data['data']['items']) > 0

def test_gender_validation(client):
    """测试性别验证逻辑"""
    # 男性用户选择妇科症状（ID 260）
    customer_data = {
        'name': '男性测试客户',
        'gender': 'male',
        'age': 35,
        'contact': '13800138001',
        'selected_symptoms': [1, 5, 260]  # 260是妇科症状
    }
    
    response = client.post('/api/v1/records', json=customer_data)
    assert response.status_code == 422
    
    data = json.loads(response.data)
    assert data['code'] == 422
    assert '男性用户不能选择妇科症状' in data['message']
    
    # 女性用户选择妇科症状应该成功
    customer_data = {
        'name': '女性测试客户',
        'gender': 'female',
        'age': 35,
        'contact': '13800138002',
        'selected_symptoms': [1, 5, 260]
    }
    
    response = client.post('/api/v1/records', json=customer_data)
    assert response.status_code == 200

def test_get_customers_list(client, auth_token):
    """测试获取客户列表"""
    # 先创建一些测试客户
    for i in range(5):
        customer_data = {
            'name': f'测试客户{i}',
            'gender': 'male' if i % 2 == 0 else 'female',
            'age': 20 + i,
            'contact': f'13800138{i:03d}',
            'selected_symptoms': [1, 2, 3]
        }
        client.post('/api/v1/records', json=customer_data)
    
    # 获取客户列表
    response = client.get('/api/v1/customers', 
                         headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['code'] == 200
    assert 'items' in data['data']
    assert 'total' in data['data']
    assert 'page' in data['data']
    assert 'size' in data['data']

def test_get_customer_detail(client, auth_token):
    """测试获取客户详情"""
    # 先创建测试客户
    customer_data = {
        'name': '详情测试客户',
        'gender': 'female',
        'age': 25,
        'contact': '13800138111',
        'selected_symptoms': [1, 2, 3]
    }
    
    response = client.post('/api/v1/records', json=customer_data)
    data = json.loads(response.data)
    customer_id = data['data']['customer_id']
    
    # 获取客户详情
    response = client.get(f'/api/v1/customers/{customer_id}', 
                         headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['code'] == 200
    assert data['data']['id'] == customer_id
    assert data['data']['name'] == '详情测试客户'
    assert 'records' in data['data']

if __name__ == '__main__':
    pytest.main(['-v', __file__])