#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
用于创建所有表结构并插入初始测试数据
适用于Docker镜像打包使用
"""

import datetime
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta

# 创建Flask应用实例
app = Flask(__name__)

# 配置SQLite数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///anniversaries.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 文件上传配置
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 确保上传目录存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 初始化数据库
db = SQLAlchemy(app)

# 定义纪念日模型
class Anniversary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    icon = db.Column(db.String(50), nullable=False)
    icon_color = db.Column(db.String(20), default='')
    card_color = db.Column(db.String(20), nullable=False)
    is_future = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)

# 定义用户信息模型
class UserInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username1 = db.Column(db.String(50), default='木木')
    username2 = db.Column(db.String(50), default='毛毛')
    avatar1 = db.Column(db.String(255), default='https://via.placeholder.com/100')
    avatar2 = db.Column(db.String(255), default='https://via.placeholder.com/100')
    banner = db.Column(db.String(255), default='https://via.placeholder.com/1200x300')

# 定义附件模型
class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.datetime.now)
    is_referenced = db.Column(db.Boolean, default=False)
    referenced_count = db.Column(db.Integer, default=0)

# 创建测试图片文件的函数
def create_test_image(file_path):
    """创建一个简单的测试图片文件"""
    # 最小的PNG文件（1x1透明像素）
    minimal_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0aIDATx\x9cc\x00\x00\x00\x02\x00\x01\xe5\xb1\xc0\xff\x00\x00\x00\x00IEND\xaeB`\x82'
    with open(file_path, 'wb') as f:
        f.write(minimal_png)
    return len(minimal_png)

# 初始化数据库并插入测试数据
def init_database():
    """初始化数据库，创建表并插入测试数据"""
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        print("创建表结构成功")
        
        # 插入纪念日测试数据
        anniversaries = [
            Anniversary(
                title='我们在一起啦',
                date=date(2020, 1, 30),
                icon='heart',
                icon_color='red',
                card_color='#FFB6C1',
                is_future=False,
                sort_order=1
            ),
            Anniversary(
                title='中华人民共和国成立',
                date=date(1949, 10, 1),
                icon='coffee',
                icon_color='brown',
                card_color='#DEB887',
                is_future=False,
                sort_order=2
            ),
            Anniversary(
                title='一周年纪念日',
                date=date(2021, 1, 30),
                icon='gift',
                icon_color='gold',
                card_color='#FFD700',
                is_future=False,
                sort_order=3
            ),
            Anniversary(
                title='生日 - 木木',
                date=date(date.today().year, 5, 20),
                icon='cake',
                icon_color='pink',
                card_color='#FFC0CB',
                is_future=date(date.today().year, 5, 20) > date.today(),
                sort_order=4
            ),
            Anniversary(
                title='生日 - 毛毛',
                date=date(date.today().year, 8, 15),
                icon='cake',
                icon_color='blue',
                card_color='#87CEEB',
                is_future=date(date.today().year, 8, 15) > date.today(),
                sort_order=5
            )
        ]
        
        db.session.add_all(anniversaries)
        db.session.commit()
        
        print(f"插入了{len(anniversaries)}条纪念日测试数据")
        
        # 创建测试图片文件并插入附件数据
        attachments = []
        
        # 创建头像1
        avatar1_filename = f"avatar1_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_test.png"
        avatar1_path = os.path.join(UPLOAD_FOLDER, avatar1_filename)
        avatar1_size = create_test_image(avatar1_path)
        avatar1_attachment = Attachment(
            filename='avatar1_test.png',
            filepath=f"/static/uploads/{avatar1_filename}",
            size=avatar1_size,
            upload_date=datetime.datetime.now(),
            is_referenced=True,
            referenced_count=1
        )
        attachments.append(avatar1_attachment)
        
        # 创建头像2
        avatar2_filename = f"avatar2_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_test.png"
        avatar2_path = os.path.join(UPLOAD_FOLDER, avatar2_filename)
        avatar2_size = create_test_image(avatar2_path)
        avatar2_attachment = Attachment(
            filename='avatar2_test.png',
            filepath=f"/static/uploads/{avatar2_filename}",
            size=avatar2_size,
            upload_date=datetime.datetime.now(),
            is_referenced=True,
            referenced_count=1
        )
        attachments.append(avatar2_attachment)
        
        # 创建壁纸
        banner_filename = f"banner_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_test.png"
        banner_path = os.path.join(UPLOAD_FOLDER, banner_filename)
        banner_size = create_test_image(banner_path)
        banner_attachment = Attachment(
            filename='banner_test.png',
            filepath=f"/static/uploads/{banner_filename}",
            size=banner_size,
            upload_date=datetime.datetime.now(),
            is_referenced=True,
            referenced_count=1
        )
        attachments.append(banner_attachment)
        
        # 添加一些未引用的测试附件
        for i in range(3):
            test_filename = f"test_file_{i}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            test_path = os.path.join(UPLOAD_FOLDER, test_filename)
            test_size = create_test_image(test_path)
            test_attachment = Attachment(
                filename=f"test_file_{i}.png",
                filepath=f"/static/uploads/{test_filename}",
                size=test_size,
                upload_date=datetime.datetime.now(),
                is_referenced=False,
                referenced_count=0
            )
            attachments.append(test_attachment)
        
        db.session.add_all(attachments)
        db.session.commit()
        
        print(f"插入了{len(attachments)}条附件测试数据")
        
        # 插入用户信息测试数据
        user_info = UserInfo(
            username1='木木',
            username2='毛毛',
            avatar1=f"/static/uploads/{avatar1_filename}",
            avatar2=f"/static/uploads/{avatar2_filename}",
            banner=f"/static/uploads/{banner_filename}"
        )
        
        db.session.add(user_info)
        db.session.commit()
        
        print("插入了用户信息测试数据")
        print("数据库初始化完成！")

if __name__ == '__main__':
    # 检查数据库是否已存在
    db_path = os.path.join(app.root_path, 'instance', 'anniversaries.db')
    if os.path.exists(db_path):
        print(f"数据库文件{db_path}已存在，正在删除...")
        os.remove(db_path)
    
    # 初始化数据库
    init_database()