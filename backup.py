import os
import shutil
import json
import datetime
import zipfile
from flask import Blueprint, send_file, request, redirect, url_for, current_app, render_template
from flask_sqlalchemy import SQLAlchemy
import tempfile
import sqlite3

# 创建备份蓝图
backup_bp = Blueprint('backup', __name__)

# 初始化备份模块
# 这里不需要创建模型，因为我们只需要操作现有的数据库

def register_backup_routes(bp, app, db):
    # 备份功能 - 简化和完善数据库路径处理
    @bp.route('/admin/backup')
    @bp.route('/backup/backup')
    def backup():
        try:
            # 添加调试日志，记录请求已接收
            app.logger.info('接收到备份请求，开始备份过程...')
            
            # 创建临时目录用于存储备份文件
            with tempfile.TemporaryDirectory() as temp_dir:
                # 生成备份文件名，包含当前时间戳
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_filename = f'loveblog_backup_{timestamp}.zip'
                backup_filepath = os.path.join(temp_dir, backup_filename)
                
                # 创建zip文件
                with zipfile.ZipFile(backup_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # 1. 备份数据库
                    db_name = "anniversaries.db"
                    
                    # 直接指定instance目录中的数据库文件
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    app.logger.info(f'当前文件目录: {current_dir}')
                    
                    instance_dir = os.path.join(current_dir, 'instance')
                    db_path = os.path.join(instance_dir, db_name)
                    
                    # 添加详细的调试日志
                    app.logger.info(f'构建的数据库路径: {db_path}')
                    app.logger.info(f'当前工作目录: {os.getcwd()}')
                    app.logger.info(f'instance目录是否存在: {os.path.exists(instance_dir)}')
                    app.logger.info(f'数据库文件是否存在: {os.path.exists(db_path)}')
                    
                    # 检查数据库文件是否存在
                    if not os.path.exists(db_path):
                        raise FileNotFoundError(f"数据库文件不存在: {db_path}")
                    
                    # 复制数据库文件到临时目录
                    temp_db_path = os.path.join(temp_dir, f'db_backup_{timestamp}.sqlite')
                    shutil.copy2(db_path, temp_db_path)
                    app.logger.info(f'数据库文件已复制到临时目录: {temp_db_path}')
                    
                    # 将数据库文件添加到zip文件
                    zipf.write(temp_db_path, f'database/{db_name}')
                    app.logger.info(f'数据库文件已添加到zip文件: database/{db_name}')
                    
                    # 2. 备份附件文件
                    upload_folder = app.config['UPLOAD_FOLDER']
                    if os.path.exists(upload_folder):
                        for root, dirs, files in os.walk(upload_folder):
                            for file in files:
                                file_path = os.path.join(root, file)
                                # 计算相对路径，以便在zip中保持目录结构
                                rel_path = os.path.relpath(file_path, upload_folder)
                                zipf.write(file_path, f'attachments/{rel_path}')
                    
                    # 3. 添加备份信息文件
                    backup_info = {
                        'backup_time': datetime.datetime.now().isoformat(),
                        'app_name': 'Love Blog',
                        'backup_version': '1.0',
                        'database_path': db_path,
                        'upload_folder': upload_folder
                    }
                    
                    # 将备份信息写入文件并添加到zip
                    info_file_path = os.path.join(temp_dir, 'backup_info.json')
                    with open(info_file_path, 'w', encoding='utf-8') as f:
                        json.dump(backup_info, f, ensure_ascii=False, indent=4)
                    
                    zipf.write(info_file_path, 'backup_info.json')
                
                # 发送生成的备份文件给用户下载
                return send_file(backup_filepath, as_attachment=True, download_name=backup_filename)
                
        except Exception as e:
            # 记录错误并返回错误消息
            app.logger.error(f'备份过程中发生错误: {str(e)}')
            return redirect(url_for('admin', message=f'备份失败: {str(e)}', message_type='error'))
    
    # 恢复功能
    @bp.route('/admin/restore', methods=['POST'])
    @bp.route('/backup/restore', methods=['POST'])
    def restore():
        try:
            # 检查是否有文件部分
            if 'backup_file' not in request.files:
                return redirect(url_for('admin', message='请选择备份文件', message_type='error'))
            
            backup_file = request.files['backup_file']
            
            # 如果用户没有选择文件，浏览器也会提交一个空的文件部分
            if backup_file.filename == '':
                return redirect(url_for('admin', message='没有选择文件', message_type='error'))
            
            # 检查文件类型是否为zip
            if not backup_file.filename.endswith('.zip'):
                return redirect(url_for('admin', message='请选择有效的备份文件(.zip)', message_type='error'))
            
            # 创建临时目录用于解压备份文件
            with tempfile.TemporaryDirectory() as temp_dir:
                # 保存上传的备份文件
                backup_file_path = os.path.join(temp_dir, 'temp_backup.zip')
                backup_file.save(backup_file_path)
                
                # 解压备份文件
                extract_dir = os.path.join(temp_dir, 'extracted')
                os.makedirs(extract_dir)
                
                with zipfile.ZipFile(backup_file_path, 'r') as zipf:
                    zipf.extractall(extract_dir)
                
                # 1. 恢复数据库
                # 确定数据库文件路径 - 在Flask应用中，数据库通常位于instance目录
                db_name = "anniversaries.db"
                # 确保instance目录存在
                instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
                os.makedirs(instance_dir, exist_ok=True)
                # 设置数据库路径为instance目录下的anniversaries.db
                db_path = os.path.join(instance_dir, db_name)
                
                db_filename = db_name
                
                # 数据库备份文件路径
                backup_db_path = os.path.join(extract_dir, 'database', db_filename)
                
                if not os.path.exists(backup_db_path):
                    return redirect(url_for('admin', message='备份文件中未找到数据库', message_type='error'))
                
                # 关闭数据库连接
                db.session.close()
                
                # 复制备份的数据库文件到原位置
                shutil.copy2(backup_db_path, db_path)
                
                # 2. 恢复附件文件
                upload_folder = app.config['UPLOAD_FOLDER']
                backup_attachments_dir = os.path.join(extract_dir, 'attachments')
                
                # 如果上传目录不存在，则创建
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                else:
                    # 清空现有附件目录
                    for root, dirs, files in os.walk(upload_folder):
                        for file in files:
                            os.remove(os.path.join(root, file))
                
                # 复制备份的附件文件
                if os.path.exists(backup_attachments_dir):
                    for root, dirs, files in os.walk(backup_attachments_dir):
                        for dir in dirs:
                            # 确保目标目录存在
                            os.makedirs(os.path.join(upload_folder, dir), exist_ok=True)
                        for file in files:
                            source_path = os.path.join(root, file)
                            # 计算目标路径
                            rel_path = os.path.relpath(source_path, backup_attachments_dir)
                            target_path = os.path.join(upload_folder, rel_path)
                            # 复制文件
                            shutil.copy2(source_path, target_path)
                
                # 重新打开数据库连接
                with app.app_context():
                    db.create_all()
                
                return redirect(url_for('admin', message='数据恢复成功', message_type='success'))
                
        except Exception as e:
            # 记录错误并返回错误消息
            app.logger.error(f'恢复过程中发生错误: {str(e)}')
            return redirect(url_for('admin', message=f'恢复失败: {str(e)}', message_type='error'))
    
    # 备份管理页面
    @bp.route('/admin_backup')
    def admin_backup():
        message = request.args.get('message')
        message_type = request.args.get('message_type', 'success')
        
        return render_template('admin_backup.html', 
                              message=message, 
                              message_type=message_type)
    
    return bp