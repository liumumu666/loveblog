# 修改文件开头的导入部分
import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import date
import os
from werkzeug.utils import secure_filename
from flask import Blueprint  # 添加这行导入

# 导入纪念日管理模块
from anniversaries import anniversary_bp, init_anniversary_model, register_anniversary_routes
# 导入基础信息管理模块
from basic_info import basic_info_bp, init_basic_info_model, register_basic_info_routes
# 导入附件管理模块
from attachments import attachments_bp, init_attachment_model, register_attachment_routes
# 导入点滴瞬间模块
from moments import moments_bp, init_moment_model, register_moment_routes

# 导入备份模块
from backup import backup_bp, register_backup_routes

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

# 确保点滴瞬间图片目录存在
if not os.path.exists(os.path.join(UPLOAD_FOLDER, 'moments')):
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'moments'))
    
# 确保基础信息图片目录存在
if not os.path.exists(os.path.join(UPLOAD_FOLDER, 'basic_info')):
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'basic_info'))

# 初始化数据库
# 确保这里使用正确的方式初始化数据库
# 注意：这里需要确保先有db对象才能初始化模型
# 因此，我们先创建db对象
from flask_sqlalchemy import SQLAlchemy

# 创建数据库对象
from flask_sqlalchemy import SQLAlchemy

# 创建db对象
# 确保这是在Flask应用创建之后，但在模型初始化之前
# 在实际应用中，应该避免重复导入，这里只是为了确保代码的完整性
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)

# 初始化纪念日模型
Anniversary = init_anniversary_model(db)

# 注册纪念日相关路由到蓝图并注册蓝图到应用
anniversary_bp = register_anniversary_routes(anniversary_bp, db, Anniversary)
app.register_blueprint(anniversary_bp)

# 初始化基础信息模型
UserInfo = init_basic_info_model(db)

# 初始化附件模型
Attachment = init_attachment_model(db)

# 初始化点滴瞬间模型
Moment = init_moment_model(db)

# 注册基础信息相关路由到蓝图并注册蓝图到应用
basic_info_bp = register_basic_info_routes(basic_info_bp, app, db, UserInfo, Attachment)
app.register_blueprint(basic_info_bp)

# 注册附件相关路由到蓝图并注册蓝图到应用
attachments_bp = register_attachment_routes(attachments_bp, app, db, Attachment, UserInfo, Anniversary)
app.register_blueprint(attachments_bp)

# 注册点滴瞬间相关路由到蓝图并注册蓝图到应用
moments_bp = register_moment_routes(moments_bp, app, db, Moment, Attachment)
app.register_blueprint(moments_bp)

# 注册备份相关路由到蓝图并注册蓝图到应用
backup_bp = register_backup_routes(backup_bp, app, db)
app.register_blueprint(backup_bp)

# 更新首页路由，安全地获取UserInfo数据
@app.route('/')
def home():
    # 从数据库中读取title为"我们在一起啦"的纪念日日期
    relationship_start = Anniversary.query.filter_by(title='我们在一起啦').first()
    
    if relationship_start:
        # 如果找到记录，使用该记录的日期
        start_date = datetime.datetime.combine(relationship_start.date, datetime.time.min)
    else:
        # 如果没有找到记录，使用默认日期作为后备方案
        start_date = datetime.datetime(2020, 1, 30)
    
    now = datetime.datetime.now()
    
    # 使用.days获取天数差
    love_days = (now - start_date).days
    hours = now.hour
    minutes = now.minute
    seconds = now.second
    
    # 计算开始日期的时间戳并转换为毫秒
    start_timestamp = int(start_date.timestamp() * 1000)
    
    # 安全地获取用户信息
    user_info = None
    try:
        user_info = UserInfo.query.first()
    except Exception:
        pass
    
    # 如果没有用户信息，使用默认值
    if not user_info:
        user_info = UserInfo()
    
    # 从数据库获取所有纪念日
    anniversaries = Anniversary.query.order_by(Anniversary.sort_order.asc()).all()
    
    # 计算每个纪念日距离今天的天数
    today = date.today()
    for anniv in anniversaries:
        if anniv.is_future:
            # 未来日期
            days_diff = (anniv.date - today).days
            anniv.days_text = f"还有{days_diff}天"
        else:
            # 过去日期
            days_diff = (today - anniv.date).days
            anniv.days_text = f"过了{days_diff}天"
    
    return render_template('index.html',
                          love_days=love_days,
                          hours=hours,
                          minutes=minutes,
                          seconds=seconds,
                          start_timestamp=start_timestamp,
                          anniversaries=anniversaries,
                          user_info=user_info)  # 保留用户信息传递
                          
# 后台管理主页
@app.route('/admin')
def admin():
    # 直接渲染admin页面，不再重定向
    return render_template('admin.html')

if __name__ == '__main__':
    # 创建数据库表
    with app.app_context():
        db.create_all()
        
        # 检查是否已经存在"我们在一起啦"的纪念日
        relationship_anniversary = Anniversary.query.filter_by(title='我们在一起啦').first()
        
        # 如果不存在，则添加默认的"我们在一起啦"纪念日
        if not relationship_anniversary:
            # 使用默认日期：2020-01-30（与首页逻辑保持一致）
            default_date = datetime.date(2020, 1, 30)
            
            # 创建默认纪念日记录
            new_relationship_anniversary = Anniversary(
                title='我们在一起啦',
                date=default_date,
                icon='heart',  # 使用心形图标
                icon_color='red',  # 红色图标
                card_color='#FFCCCC',  # 浅红色卡片背景
                is_future=False,  # 这是过去的日期
                sort_order=0  # 设置为最高优先级
            )
            
            # 添加到数据库并提交
            db.session.add(new_relationship_anniversary)
            db.session.commit()
            print("已添加默认的'我们在一起啦'纪念日数据")
    # 重要：使用0.0.0.0作为主机，使容器外部可以访问
    app.run(host='0.0.0.0', port=1314, debug=True)
