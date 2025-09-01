import datetime
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import date

# 创建蓝图
anniversary_bp = Blueprint('anniversary', __name__)

# 定义纪念日模型
def init_anniversary_model(db):
    class Anniversary(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(100), nullable=False)
        date = db.Column(db.Date, nullable=False)
        icon = db.Column(db.String(50), nullable=False)
        icon_color = db.Column(db.String(20), default='')
        card_color = db.Column(db.String(20), nullable=False)
        is_future = db.Column(db.Boolean, default=False)
        sort_order = db.Column(db.Integer, default=0, nullable=False)  # 添加排序字段
    
    return Anniversary

# 注册路由函数到蓝图
def register_anniversary_routes(bp, db, Anniversary):
    # 后台管理页面
    @bp.route('/admin_anniversaries')
    def admin_anniversaries():
        # 获取排序参数，默认为按排序字段排序
        sort_by = request.args.get('sort_by', 'sort_order')
        # 获取排序方向，默认为升序
        sort_order = request.args.get('sort_order', 'asc')
        
        # 根据排序参数构建查询
        if sort_by == 'date':
            if sort_order == 'asc':
                anniversaries = Anniversary.query.order_by(Anniversary.date.asc()).all()
            else:
                anniversaries = Anniversary.query.order_by(Anniversary.date.desc()).all()
        elif sort_by == 'title':
            if sort_order == 'asc':
                anniversaries = Anniversary.query.order_by(Anniversary.title.asc()).all()
            else:
                anniversaries = Anniversary.query.order_by(Anniversary.title.desc()).all()
        elif sort_by == 'id':
            if sort_order == 'asc':
                anniversaries = Anniversary.query.order_by(Anniversary.id.asc()).all()
            else:
                anniversaries = Anniversary.query.order_by(Anniversary.id.desc()).all()
        elif sort_by == 'sort_order':
            if sort_order == 'asc':
                anniversaries = Anniversary.query.order_by(Anniversary.sort_order.asc()).all()
            else:
                anniversaries = Anniversary.query.order_by(Anniversary.sort_order.desc()).all()
        else:
            # 默认按排序字段升序
            # 从数据库获取所有纪念日并按排序字段排序
            anniversaries = Anniversary.query.order_by(Anniversary.sort_order.asc()).all()
        
        message = request.args.get('message')
        message_type = request.args.get('message_type', 'success')
        
        # 将排序信息传递给模板
        return render_template('admin_anniversaries.html', 
                            anniversaries=anniversaries, 
                            message=message, 
                            message_type=message_type,
                            current_sort=sort_by,
                            current_order=sort_order)

    # 添加纪念日
    @bp.route('/admin/add', methods=['POST'])
    def add_anniversary():
        try:
            title = request.form['title']
            date_str = request.form['date']
            icon = request.form['icon']
            icon_color = request.form.get('icon_color', '')
            card_color = request.form['card_color']
            is_future = 'is_future' in request.form
            
            # 转换日期字符串为date对象
            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # 获取当前最大排序值
            max_sort_order = db.session.query(db.func.max(Anniversary.sort_order)).scalar() or 0
            
            # 创建新的纪念日记录，设置排序值为最大值+1
            new_anniversary = Anniversary(
                title=title,
                date=date_obj,
                icon=icon,
                icon_color=icon_color,
                card_color=card_color,
                is_future=is_future,
                sort_order=max_sort_order + 1  # 设置默认排序值
            )
            
            # 添加到数据库
            db.session.add(new_anniversary)
            db.session.commit()
            
            return redirect(url_for('anniversary.admin_anniversaries', message='纪念日添加成功！', message_type='success'))
        except Exception as e:
            return redirect(url_for('anniversary.admin_anniversaries', message=f'添加失败：{str(e)}', message_type='error'))

    # 获取纪念日数据（用于编辑）
    @bp.route('/admin/get/<int:id>')
    def get_anniversary(id):
        anniversary = Anniversary.query.get_or_404(id)
        return jsonify({
            'id': anniversary.id,
            'title': anniversary.title,
            'date': anniversary.date.strftime('%Y-%m-%d'),
            'icon': anniversary.icon,
            'icon_color': anniversary.icon_color,
            'card_color': anniversary.card_color,
            'is_future': anniversary.is_future,
            'sort_order': anniversary.sort_order
        })

    # 编辑纪念日
    @bp.route('/admin/edit/<int:id>', methods=['POST'])
    def edit_anniversary(id):
        try:
            anniversary = Anniversary.query.get_or_404(id)
            
            # 获取表单中的排序值
            new_sort_order = int(request.form['sort_order'])
            
            # 检查排序值是否与其他记录重复
            existing_anniversary = Anniversary.query.filter(
                Anniversary.id != id,
                Anniversary.sort_order == new_sort_order
            ).first()
            
            if existing_anniversary:
                return redirect(url_for('anniversary.admin_anniversaries', message='排序值已存在，请选择其他排序值', message_type='error'))
            
            # 检查是否是默认的"我们在一起啦"纪念日，如果是则不允许修改标题
            if anniversary.title == '我们在一起啦':
                # 标题保持不变，只更新其他字段
                date_str = request.form['date']
                anniversary.date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                anniversary.icon = request.form['icon']
                anniversary.icon_color = request.form.get('icon_color', '')
                anniversary.card_color = request.form['card_color']
                anniversary.is_future = 'is_future' in request.form
                anniversary.sort_order = new_sort_order
            else:
                # 更新所有字段
                anniversary.title = request.form['title']
                date_str = request.form['date']
                anniversary.date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                anniversary.icon = request.form['icon']
                anniversary.icon_color = request.form.get('icon_color', '')
                anniversary.card_color = request.form['card_color']
                anniversary.is_future = 'is_future' in request.form
                anniversary.sort_order = new_sort_order
            
            db.session.commit()
            
            return redirect(url_for('anniversary.admin_anniversaries', message='纪念日更新成功！', message_type='success'))
        except Exception as e:
            return redirect(url_for('anniversary.admin_anniversaries', message=f'更新失败：{str(e)}', message_type='error'))

    # 删除纪念日
    @bp.route('/admin/delete/<int:id>')
    def delete_anniversary(id):
        try:
            anniversary = Anniversary.query.get_or_404(id)
            
            # 检查是否是默认的"我们在一起啦"纪念日，如果是则不允许删除
            if anniversary.title == '我们在一起啦':
                return redirect(url_for('anniversary.admin_anniversaries', message='默认纪念日不可删除', message_type='error'))
            
            db.session.delete(anniversary)
            db.session.commit()
            return redirect(url_for('anniversary.admin_anniversaries', message='纪念日删除成功！', message_type='success'))
        except Exception as e:
            return redirect(url_for('anniversary.admin_anniversaries', message=f'删除失败：{str(e)}', message_type='error'))

    # 更新纪念日排序
    @bp.route('/admin/update_order', methods=['POST'])
    def update_order():
        try:
            # 获取排序数据
            order_data = request.json.get('order', [])
            
            # 检查排序值是否有重复
            sort_orders = [item['sort_order'] for item in order_data]
            if len(sort_orders) != len(set(sort_orders)):
                return jsonify({'success': False, 'message': '排序值有重复，请重新排序'})
            
            # 更新数据库中的排序值
            for item in order_data:
                anniversary = Anniversary.query.get_or_404(item['id'])
                anniversary.sort_order = item['sort_order']
                
            db.session.commit()
            return jsonify({'success': True, 'message': '排序更新成功！'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'排序更新失败：{str(e)}'})

    # 获取最大排序值
    @bp.route('/admin/get_max_sort_order')
    def get_max_sort_order():
        try:
            # 查询当前最大排序值
            max_sort_order = db.session.query(db.func.max(Anniversary.sort_order)).scalar()
            return jsonify({'max_sort_order': max_sort_order})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return bp