from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime
import os
from werkzeug.utils import secure_filename

# 创建蓝图
moments_bp = Blueprint('moments', __name__)

# 文件上传配置
UPLOAD_FOLDER = 'static/uploads/moments'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 定义点滴瞬间模型
def init_moment_model(db):
    class Moment(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        content = db.Column(db.Text, nullable=False)  # 文字内容
        created_at = db.Column(db.DateTime, default=datetime.datetime.now)
        updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
        image_paths = db.Column(db.Text, default='[]')  # 存储图片路径的JSON字符串
    
    return Moment

# 检查文件类型是否允许
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 注册路由函数到蓝图
# 修改register_moment_routes函数定义，添加Attachment参数
def register_moment_routes(bp, app, db, Moment, Attachment):
    # 确保上传目录存在
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # 点滴瞬间管理页面
    @bp.route('/admin_moments')
    def admin_moments():
        # 获取所有点滴瞬间记录，按创建时间倒序排列
        moments = Moment.query.order_by(Moment.created_at.desc()).all()
        
        # 将图片路径的JSON字符串转换为列表
        for moment in moments:
            moment.images = eval(moment.image_paths)
        
        message = request.args.get('message')
        message_type = request.args.get('message_type', 'success')
        
        return render_template('admin_moments.html', 
                               moments=moments, 
                               message=message, 
                               message_type=message_type)
    
    # 添加新的点滴瞬间
    @bp.route('/admin/add_moment', methods=['POST'])
    def add_moment():
        try:
            content = request.form['content']
            
            # 处理文件上传
            image_paths = []
            files = request.files.getlist('images[]')
            
            for file in files:
                if file and allowed_file(file.filename):
                    original_filename = secure_filename(file.filename)
                    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                    unique_filename = f"moment_{timestamp}_{original_filename}"
                    
                    # 保存文件
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'moments', unique_filename)
                    file.save(filepath)
                    
                    # 获取文件大小
                    file_size = os.path.getsize(filepath)
                    
                    # 先在附件表中创建记录
                    new_attachment = Attachment(
                        filename=original_filename,
                        filepath=f"/static/uploads/moments/{unique_filename}",
                        size=file_size,
                        is_referenced=True,
                        referenced_count=1
                    )
                    db.session.add(new_attachment)
                    
                    # 保存相对路径到moment记录
                    image_paths.append(f"/static/uploads/moments/{unique_filename}")
            
            # 创建新的点滴瞬间记录
            new_moment = Moment(
                content=content,
                image_paths=str(image_paths)
            )
            
            # 添加到数据库
            db.session.add(new_moment)
            db.session.commit()
            
            # 重定向回管理页面，显示成功消息
            return redirect(url_for('moments.admin_moments', message='点滴瞬间添加成功！', message_type='success'))
        except Exception as e:
            # 出错时回滚事务
            db.session.rollback()
            return redirect(url_for('moments.admin_moments', message=f'添加失败: {str(e)}', message_type='error'))
    
    # 删除点滴瞬间
    @bp.route('/admin/delete_moment/<int:moment_id>', methods=['POST'])
    def delete_moment(moment_id):
        try:
            # 查找要删除的点滴瞬间
            moment = Moment.query.get_or_404(moment_id)
            
            # 处理图片删除
            if moment.image_paths and moment.image_paths != '[]':
                # 解析图片路径列表
                image_paths = eval(moment.image_paths)
                
                for image_path in image_paths:
                    # 构建完整的文件路径
                    full_path = os.path.join(app.root_path, image_path.lstrip('/'))
                    
                    # 检查文件是否存在，如果存在则删除
                    if os.path.exists(full_path):
                        os.remove(full_path)
                    
                    # 更新附件表中的引用计数和引用状态
                    attachment = Attachment.query.filter_by(filepath=image_path).first()
                    if attachment:
                        attachment.referenced_count -= 1
                        if attachment.referenced_count <= 0:
                            attachment.is_referenced = False
            
            # 从数据库中删除点滴瞬间记录
            db.session.delete(moment)
            db.session.commit()
            
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    
    # 前端查看点滴瞬间列表
    @bp.route('/moments')
    def moments_list():
        # 获取所有点滴瞬间记录，按创建时间倒序排列
        moments = Moment.query.order_by(Moment.created_at.desc()).all()
        
        # 将图片路径的JSON字符串转换为列表
        for moment in moments:
            moment.images = eval(moment.image_paths)
            # 格式化日期
            moment.formatted_date = moment.created_at.strftime('%Y-%m-%d %H:%M')
        
        return render_template('moments.html', moments=moments)
    
    # 获取点滴瞬间API
    @bp.route('/api/moments')
    def get_moments_api():
        moments = Moment.query.order_by(Moment.created_at.desc()).all()
        moments_data = []
        
        for moment in moments:
            images = eval(moment.image_paths)
            moments_data.append({
                'id': moment.id,
                'content': moment.content,
                'created_at': moment.created_at.isoformat(),
                'images': images
            })
        
        return jsonify(moments_data)
    
    return bp