from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event, DDL
import json

db = SQLAlchemy()

class Customer(db.Model):
    """客户表模型"""
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # 'male' or 'female'
    age = db.Column(db.Integer, nullable=False)
    contact = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    symptom_records = db.relationship('SymptomRecord', backref='customer', cascade='all, delete-orphan', lazy='dynamic')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'age': self.age,
            'contact': self.contact,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_record_count(self):
        """获取记录数量"""
        return self.symptom_records.count()
    
    def get_last_submission(self):
        """获取最后提交时间"""
        last_record = self.symptom_records.order_by(SymptomRecord.submission_time.desc()).first()
        return last_record.submission_time if last_record else None

class SymptomRecord(db.Model):
    """症状提交记录表模型"""
    __tablename__ = 'symptom_records'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    submission_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    symptom_count = db.Column(db.Integer, nullable=False, default=0)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # 关系
    symptom_selections = db.relationship('SymptomSelection', backref='symptom_record', cascade='all, delete-orphan', lazy='dynamic')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'submission_time': self.submission_time.isoformat() if self.submission_time else None,
            'symptom_count': self.symptom_count,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_area_distribution(self):
        """获取区域分布"""
        from collections import Counter
        areas = [selection.area for selection in self.symptom_selections]
        return dict(Counter(areas))
    
    def get_symptoms(self):
        """获取关联的症状"""
        return [selection.symptom for selection in self.symptom_selections]

class SymptomSelection(db.Model):
    """症状勾选关系表模型"""
    __tablename__ = 'symptom_selections'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    record_id = db.Column(db.Integer, db.ForeignKey('symptom_records.id', ondelete='CASCADE'), nullable=False)
    symptom_id = db.Column(db.Integer, nullable=False)
    area = db.Column(db.String(20), nullable=False)  # 'red', 'green', 'white', 'black', 'yellow', 'blue'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # 关系
    symptom = db.relationship('Symptom', primaryjoin='SymptomSelection.symptom_id == Symptom.id', viewonly=True)
    
    __table_args__ = (
        db.UniqueConstraint('record_id', 'symptom_id', name='idx_selections_record_symptom'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'record_id': self.record_id,
            'symptom_id': self.symptom_id,
            'area': self.area,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Symptom(db.Model):
    """症状主表模型"""
    __tablename__ = 'symptoms'
    
    id = db.Column(db.Integer, primary_key=True)  # 1-300，与文档序号一致
    name = db.Column(db.String(50), nullable=False)
    area = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False)
    precautions = db.Column(db.Text, nullable=True)
    contraindications = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    tags = db.relationship('SymptomTag', backref='symptom', cascade='all, delete-orphan', lazy='dynamic')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'area': self.area,
            'description': self.description,
            'precautions': self.precautions,
            'contraindications': self.contraindications,
            'tags': [tag.tag for tag in self.tags]
        }
    
    def get_brief_description(self):
        """获取简要描述（前100字符）"""
        return self.description[:100] + '...' if len(self.description) > 100 else self.description

class SymptomTag(db.Model):
    """症状原因标签表模型"""
    __tablename__ = 'symptom_tags'
    
    symptom_id = db.Column(db.Integer, db.ForeignKey('symptoms.id', ondelete='CASCADE'), primary_key=True)
    tag = db.Column(db.String(20), primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'symptom_id': self.symptom_id,
            'tag': self.tag,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Admin(db.Model):
    """管理员表模型"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='operator')  # 'super_admin' or 'operator'
    last_login_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'role': self.role,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# 创建索引的DDL语句
create_indexes = DDL("""
-- customers表索引
CREATE INDEX IF NOT EXISTS idx_customers_created_at ON customers(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_customers_gender_age ON customers(gender, age);
CREATE INDEX IF NOT EXISTS idx_customers_contact ON customers(contact);

-- symptom_records表索引
CREATE INDEX IF NOT EXISTS idx_records_customer_id ON symptom_records(customer_id);
CREATE INDEX IF NOT EXISTS idx_records_submission_time ON symptom_records(submission_time DESC);
CREATE INDEX IF NOT EXISTS idx_records_customer_time ON symptom_records(customer_id, submission_time);

-- symptom_selections表索引
CREATE INDEX IF NOT EXISTS idx_selections_record_id ON symptom_selections(record_id);
CREATE INDEX IF NOT EXISTS idx_selections_symptom_id ON symptom_selections(symptom_id);
CREATE INDEX IF NOT EXISTS idx_selections_area ON symptom_selections(area);

-- symptoms表索引
CREATE INDEX IF NOT EXISTS idx_symptoms_area ON symptoms(area);
CREATE INDEX IF NOT EXISTS idx_symptoms_name ON symptoms(name);

-- symptom_tags表索引
CREATE INDEX IF NOT EXISTS idx_tags_tag ON symptom_tags(tag);
CREATE INDEX IF NOT EXISTS idx_tags_symptom_id ON symptom_tags(symptom_id);

-- admins表索引
CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username);
""")

# 注册事件，在表创建后创建索引
event.listen(Customer.__table__, 'after_create', create_indexes)
event.listen(SymptomRecord.__table__, 'after_create', create_indexes)
event.listen(SymptomSelection.__table__, 'after_create', create_indexes)
event.listen(Symptom.__table__, 'after_create', create_indexes)
event.listen(SymptomTag.__table__, 'after_create', create_indexes)
event.listen(Admin.__table__, 'after_create', create_indexes)