import os
import shutil
from datetime import date  # 导入date类
from app import app, db, Anniversary, UserInfo, Attachment, Moment

# 确保在应用上下文内运行
with app.app_context():
    # 检查并创建所有数据表（如果表不存在）
    print("正在检查数据库表...")
    db.create_all()
    
    print("清空所有表中的数据...")
    # 清空所有表的数据，但保留表结构
    db.session.execute(db.text('DELETE FROM anniversary;'))
    db.session.execute(db.text('DELETE FROM user_info;'))
    db.session.execute(db.text('DELETE FROM attachment;'))
    db.session.execute(db.text('DELETE FROM moment;'))
    
    db.session.commit()
    
    print("添加基础记录'我们在一起啦'...")
    # 添加"我们在一起啦"记录，使用Python的date对象
    anniversary = Anniversary(
        title="我们在一起啦",
        date=date(1949, 10, 1),  # 使用date对象设置为1949-10-01
        icon="heart",
        icon_color="text-danger",
        card_color="card-red",
        sort_order=1,
        is_future=False
    )
    
    db.session.add(anniversary)
    db.session.commit()
    
    print("清空uploads目录下的文件...")
    # 清空uploads目录下的所有文件
    uploads_dirs = [
        os.path.join(app.root_path, 'static', 'uploads'),
        os.path.join(app.root_path, 'static', 'uploads', 'basic_info'),
        os.path.join(app.root_path, 'static', 'uploads', 'moments')
    ]
    
    for dir_path in uploads_dirs:
        if os.path.exists(dir_path):
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            print(f"已清空目录: {dir_path}")

print("数据库初始化完成，已清空所有表数据（保留表结构），只保留'我们在一起啦'记录，并清空uploads目录")