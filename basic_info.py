from flask import Blueprint, render_template, request, redirect, url_for, jsonify  # 添加Blueprint导入
from flask_sqlalchemy import SQLAlchemy
import datetime
import os
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify

# 创建蓝图
basic_info_bp = Blueprint('basic_info', __name__)

# 修改文件上传配置
UPLOAD_FOLDER = 'static/uploads/basic_info'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 定义用户信息模型
def init_basic_info_model(db):
    class UserInfo(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username1 = db.Column(db.String(50), default='木木')  # 第一个用户昵称
        username2 = db.Column(db.String(50), default='毛毛')  # 第二个用户昵称
        avatar1 = db.Column(db.String(255), default='https://via.placeholder.com/100')  # 第一个用户头像
        avatar2 = db.Column(db.String(255), default='https://via.placeholder.com/100')  # 第二个用户头像
        banner = db.Column(db.String(255), default='https://via.placeholder.com/1200x300')  # 首页壁纸
    
    return UserInfo

# 检查文件类型是否允许
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 注册路由函数到蓝图
def register_basic_info_routes(bp, app, db, UserInfo, Attachment):
    # 确保上传目录存在
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        
    # 获取基础信息
    @bp.route('/admin/get_basic_info')
    def get_basic_info():
        user_info = UserInfo.query.first() or UserInfo()
        return jsonify({
            'username1': user_info.username1,
            'username2': user_info.username2,
            'avatar1': user_info.avatar1,
            'avatar2': user_info.avatar2,
            'banner': user_info.banner
        })

    # 更新基础信息
    @bp.route('/admin/update_basic_info', methods=['POST'])
    def update_basic_info():
        try:
            # 获取现有的用户信息记录，如果没有则创建
            user_info = UserInfo.query.first()
            if not user_info:
                user_info = UserInfo()
                db.session.add(user_info)
            
            # 更新昵称
            user_info.username1 = request.form.get('username1', user_info.username1)
            user_info.username2 = request.form.get('username2', user_info.username2)
            
            # 处理头像1上传
            if 'avatar1' in request.files and request.files['avatar1'].filename:
                file = request.files['avatar1']
                if file and allowed_file(file.filename):
                    # 生成安全的文件名
                    original_filename = secure_filename(file.filename)
                    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                    unique_filename = f"avatar1_{timestamp}_{original_filename}"
                    
                    # 保存文件
                    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                    file.save(filepath)
                    
                    # 获取文件大小
                    file_size = os.path.getsize(filepath)
                    
                    # 先创建附件记录
                    attachment = Attachment(
                        filename=original_filename,
                        filepath=f"/static/uploads/basic_info/{unique_filename}",
                        size=file_size,
                        upload_date=datetime.datetime.now(),
                        is_referenced=True,  # 标记为已引用
                        referenced_count=1
                    )
                    db.session.add(attachment)
                    db.session.flush()  # 确保attachment.id已生成
                    
                    # 再更新用户信息
                    user_info.avatar1 = f"/static/uploads/basic_info/{unique_filename}"
            
            # 处理头像2上传
            if 'avatar2' in request.files and request.files['avatar2'].filename:
                file = request.files['avatar2']
                if file and allowed_file(file.filename):
                    original_filename = secure_filename(file.filename)
                    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                    unique_filename = f"avatar2_{timestamp}_{original_filename}"
                    
                    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                    file.save(filepath)
                    
                    file_size = os.path.getsize(filepath)
                    
                    # 先创建附件记录
                    attachment = Attachment(
                        filename=original_filename,
                        filepath=f"/static/uploads/basic_info/{unique_filename}",
                        size=file_size,
                        upload_date=datetime.datetime.now(),
                        is_referenced=True,  # 标记为已引用
                        referenced_count=1
                    )
                    db.session.add(attachment)
                    db.session.flush()
                    
                    # 再更新用户信息
                    user_info.avatar2 = f"/static/uploads/basic_info/{unique_filename}"
            
            # 处理壁纸上传
            if 'banner' in request.files and request.files['banner'].filename:
                file = request.files['banner']
                if file and allowed_file(file.filename):
                    original_filename = secure_filename(file.filename)
                    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                    unique_filename = f"banner_{timestamp}_{original_filename}"
                    
                    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                    file.save(filepath)
                    
                    file_size = os.path.getsize(filepath)
                    
                    # 先创建附件记录
                    attachment = Attachment(
                        filename=original_filename,
                        filepath=f"/static/uploads/basic_info/{unique_filename}",
                        size=file_size,
                        upload_date=datetime.datetime.now(),
                        is_referenced=True,  # 标记为已引用
                        referenced_count=1
                    )
                    db.session.add(attachment)
                    db.session.flush()
                    
                    # 再更新用户信息
                    user_info.banner = f"/static/uploads/basic_info/{unique_filename}"
            
            # 提交更改到数据库
            db.session.commit()
            
            return jsonify({'success': True, 'message': '基础信息更新成功！'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

    # 基础信息管理页面路由
    @bp.route('/admin_basic_info')
    def admin_basic_info():
        message = request.args.get('message')
        message_type = request.args.get('message_type', 'success')
        
        # 不再需要传递anniversaries数据，因为这个页面只关注基础信息
        return render_template('admin_basic_info.html', 
                              message=message,
                              message_type=message_type)

    return bp