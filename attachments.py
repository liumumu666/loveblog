from flask_sqlalchemy import SQLAlchemy
import datetime
import os
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, render_template

# 创建蓝图
attachments_bp = Blueprint('attachments', __name__)

# 文件上传配置
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 定义附件模型
def init_attachment_model(db):
    """
    初始化附件模型
    :param db: SQLAlchemy实例
    :return: Attachment模型类
    """
    class Attachment(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        filename = db.Column(db.String(255), nullable=False)
        filepath = db.Column(db.String(255), nullable=False)
        size = db.Column(db.Integer, nullable=False)  # 文件大小，以字节为单位
        upload_date = db.Column(db.DateTime, default=datetime.datetime.now)
        is_referenced = db.Column(db.Boolean, default=False)
        referenced_count = db.Column(db.Integer, default=0)
    
    return Attachment

# 检查文件类型是否允许
def allowed_file(filename):
    """
    检查文件类型是否在允许的列表中
    :param filename: 文件名
    :return: 是否允许上传
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 文件大小格式化函数
def format_size(size_bytes):
    """
    将字节大小格式化为人类可读的格式
    :param size_bytes: 文件大小（字节）
    :return: 格式化后的大小字符串
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

# 注册路由函数到蓝图
def register_attachment_routes(bp, app, db, Attachment, UserInfo=None, Anniversary=None):
    """
    注册附件管理相关路由到蓝图
    :param bp: 蓝图实例
    :param app: Flask应用实例
    :param db: SQLAlchemy实例
    :param Attachment: Attachment模型类
    :param UserInfo: UserInfo模型类（可选）
    :param Anniversary: Anniversary模型类（可选）
    :return: 已注册路由的蓝图
    """
    # 确保上传目录存在
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # 添加文件大小格式化过滤器到模板
    @app.template_filter('format_size')
    def format_size_filter(size_bytes):
        return format_size(size_bytes)
    
    # 附件管理页面
    @bp.route('/admin_attachments')
    def admin_attachments():
        """
        附件管理后台页面
        支持查询所有附件的文件名、文件路径、文件大小、上传日期和引用状态
        """
        # 获取过滤参数
        show_unreferenced_only = request.args.get('unreferenced_only') == 'true'
        
        # 构建查询
        query = Attachment.query
        
        # 如果只显示未引用的文件
        if show_unreferenced_only:
            query = query.filter_by(is_referenced=False)
        
        # 获取所有文件记录
        files = query.order_by(Attachment.upload_date.desc()).all()
        
        # 检查是否有消息参数
        message = request.args.get('message')
        message_type = request.args.get('message_type', 'success')
        
        return render_template('admin_attachments.html', 
                             files=files, 
                             message=message, 
                             message_type=message_type)
    
    # 上传附件接口
    @bp.route('/admin/upload_attachment', methods=['POST'])
    def upload_attachment():
        """
        上传附件接口
        """
        try:
            # 检查是否有文件部分
            if 'file' not in request.files:
                return jsonify({'success': False, 'message': '没有文件部分'})
            
            file = request.files['file']
            
            # 如果用户没有选择文件，浏览器也会提交一个空的文件部分
            if file.filename == '':
                return jsonify({'success': False, 'message': '没有选择文件'})
            
            # 检查文件类型
            if file and allowed_file(file.filename):
                # 生成安全的文件名
                filename = secure_filename(file.filename)
                # 添加时间戳避免文件名冲突
                timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                unique_filename = f"{timestamp}_{filename}"
                
                # 保存文件
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                
                # 获取文件大小
                file_size = os.path.getsize(filepath)
                
                # 创建附件记录
                attachment = Attachment(
                    filename=filename,
                    filepath=f"/static/uploads/{unique_filename}",
                    size=file_size,
                    upload_date=datetime.datetime.now(),
                    is_referenced=False,
                    referenced_count=0
                )
                db.session.add(attachment)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': '文件上传成功',
                    'attachment': {
                        'id': attachment.id,
                        'filename': attachment.filename,
                        'filepath': attachment.filepath,
                        'size': attachment.size,
                        'upload_date': attachment.upload_date.isoformat()
                    }
                })
            else:
                return jsonify({'success': False, 'message': '不支持的文件类型'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    
    # 删除附件接口
    @bp.route('/admin/delete_attachment/<int:attachment_id>', methods=['DELETE'])
    def delete_attachment(attachment_id):
        """
        删除附件接口
        """
        try:
            # 查找附件
            attachment = Attachment.query.get_or_404(attachment_id)
            
            # 检查文件是否存在并删除
            file_path = os.path.join(app.root_path, attachment.filepath.lstrip('/'))
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # 从数据库中删除记录
            db.session.delete(attachment)
            db.session.commit()
            
            return jsonify({'success': True, 'message': '文件删除成功'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    
    # 更新附件引用状态接口
    @bp.route('/admin/update_attachment_reference/<int:attachment_id>', methods=['POST'])
    def update_attachment_reference(attachment_id):
        """
        更新附件引用状态接口
        """
        try:
            # 查找附件
            attachment = Attachment.query.get_or_404(attachment_id)
            
            # 获取请求数据
            data = request.get_json()
            is_referenced = data.get('is_referenced', False)
            
            # 更新引用状态
            attachment.is_referenced = is_referenced
            if is_referenced:
                attachment.referenced_count += 1
            else:
                attachment.referenced_count = max(0, attachment.referenced_count - 1)
            
            db.session.commit()
            
            return jsonify({'success': True, 'message': '引用状态更新成功'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    
    # 批量删除未引用的附件
    @bp.route('/admin/batch_delete_unreferenced', methods=['POST'])
    def batch_delete_unreferenced():
        """
        批量删除未引用的附件接口
        """
        try:
            # 查找所有未引用的附件
            unreferenced_attachments = Attachment.query.filter_by(is_referenced=False).all()
            
            if not unreferenced_attachments:
                return jsonify({'success': True, 'message': '没有未引用的文件需要删除'})
            
            # 记录删除的文件数量
            deleted_count = 0
            
            # 删除每个未引用的附件
            for attachment in unreferenced_attachments:
                # 检查文件是否存在并删除
                file_path = os.path.join(app.root_path, attachment.filepath.lstrip('/'))
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_count += 1
                
                # 从数据库中删除记录
                db.session.delete(attachment)
            
            db.session.commit()
            
            return jsonify({'success': True, 'message': f'成功删除了{deleted_count}个未引用的文件'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    
    # 扫描附件引用状态
    @bp.route('/admin/scan_attachments', methods=['POST'])
    def scan_attachments():
        """
        扫描并更新附件的引用状态
        同时检查static/uploads目录下的所有文件，更新或创建数据库记录
        """
        try:
            # 1. 首先扫描static/uploads目录下的所有文件，更新或创建数据库记录
            uploads_dir = os.path.join(app.root_path, 'static', 'uploads')
            if os.path.exists(uploads_dir):
                # 获取数据库中所有附件记录
                db_attachments = {os.path.basename(a.filepath): a for a in Attachment.query.all()}
                
                # 遍历uploads目录下的所有文件
                for filename in os.listdir(uploads_dir):
                    file_path = os.path.join(uploads_dir, filename)
                    if os.path.isfile(file_path):
                        # 计算文件大小
                        file_size = os.path.getsize(file_path)
                        
                        # 构建数据库中的filepath
                        db_filepath = f"/static/uploads/{filename}"
                        
                        # 检查文件是否已在数据库中
                        if filename in db_attachments:
                            # 更新现有记录
                            attachment = db_attachments[filename]
                            attachment.size = file_size
                            # 保留现有的引用状态
                        else:
                            # 创建新记录
                            attachment = Attachment(
                                filename=filename,
                                filepath=db_filepath,
                                size=file_size,
                                upload_date=datetime.datetime.now(),
                                is_referenced=False,
                                referenced_count=0
                            )
                            db.session.add(attachment)
                
                # 2. 删除数据库中有记录但实际文件不存在的附件
                for filename, attachment in db_attachments.items():
                    file_path = os.path.join(app.root_path, attachment.filepath.lstrip('/'))
                    if not os.path.exists(file_path):
                        db.session.delete(attachment)
            
            # 3. 重置所有附件的引用状态
            Attachment.query.update({Attachment.is_referenced: False, Attachment.referenced_count: 0})
            
            # 4. 检查UserInfo模型中的引用
            if UserInfo:
                user_infos = UserInfo.query.all()
                for user_info in user_infos:
                    # 检查头像1引用
                    if user_info.avatar1 and user_info.avatar1.startswith('/static/uploads/'):
                        filename = user_info.avatar1.split('/')[-1]
                        attachment = Attachment.query.filter_by(filepath=user_info.avatar1).first()
                        if attachment:
                            attachment.is_referenced = True
                            attachment.referenced_count += 1
                    
                    # 检查头像2引用
                    if user_info.avatar2 and user_info.avatar2.startswith('/static/uploads/'):
                        filename = user_info.avatar2.split('/')[-1]
                        attachment = Attachment.query.filter_by(filepath=user_info.avatar2).first()
                        if attachment:
                            attachment.is_referenced = True
                            attachment.referenced_count += 1
                    
                    # 检查壁纸引用
                    if user_info.banner and user_info.banner.startswith('/static/uploads/'):
                        filename = user_info.banner.split('/')[-1]
                        attachment = Attachment.query.filter_by(filepath=user_info.banner).first()
                        if attachment:
                            attachment.is_referenced = True
                            attachment.referenced_count += 1
            
            db.session.commit()
            
            return jsonify({'success': True, 'message': '附件状态检测完成，已更新数据库'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    
    return bp