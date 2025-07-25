from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timedelta
import calendar

app = Flask(__name__)
CORS(app)

# 数据库配置
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'efficiency.db')

def init_database():
    """初始化数据库"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 创建数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT DEFAULT '全部部门',
            commit_count INTEGER,
            bug_fix_rate REAL,
            code_quality INTEGER,
            delivery_efficiency REAL,
            record_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT DEFAULT '全部部门',
            project_name TEXT,
            developer TEXT,
            commits INTEGER,
            code_lines INTEGER,
            bugs INTEGER,
            completion_time TEXT,
            record_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS developer_rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT DEFAULT '全部部门',
            name TEXT,
            score INTEGER,
            record_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            refresh_interval INTEGER,
            email_notifications INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 插入示例数据
    current_date = datetime.now().strftime('%Y-%m')
    
    # 检查是否已有数据
    cursor.execute('SELECT COUNT(*) FROM metrics')
    if cursor.fetchone()[0] == 0:
        # 插入多部门示例数据
        departments = ['全部部门', '前端开发部', '后端开发部', '测试部', '产品部']
        
        for dept in departments:
            # 插入指标数据
            cursor.execute('''
                INSERT INTO metrics (department, commit_count, bug_fix_rate, code_quality, delivery_efficiency, record_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (dept, 1250 + hash(dept) % 500, 92.5 + (hash(dept) % 10) / 10, 85 + hash(dept) % 15, 88.3 + (hash(dept) % 20) / 10, current_date))
            
            # 插入项目详情数据
            projects = [
                (f'{dept}-项目A', '张三', 45, 2300, 3, '2024-01-15'),
                (f'{dept}-项目B', '李四', 38, 1800, 1, '2024-01-20'),
                (f'{dept}-项目C', '王五', 52, 2800, 2, '2024-01-25')
            ]
            
            for project in projects:
                cursor.execute('''
                    INSERT INTO project_details (department, project_name, developer, commits, code_lines, bugs, completion_time, record_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (dept, project[0], project[1], project[2], project[3], project[4], project[5], current_date))
            
            # 插入开发者排行数据
            developers = [
                ('张三', 95 + hash(dept + '张三') % 5),
                ('李四', 88 + hash(dept + '李四') % 7),
                ('王五', 82 + hash(dept + '王五') % 8)
            ]
            
            for dev in developers:
                cursor.execute('''
                    INSERT INTO developer_rankings (department, name, score, record_date)
                    VALUES (?, ?, ?, ?)
                ''', (dept, dev[0], dev[1], current_date))
        
        # 插入设置数据
        cursor.execute('''
            INSERT INTO settings (refresh_interval, email_notifications)
            VALUES (10, 1)
        ''')
    
    conn.commit()
    conn.close()

def get_filter_conditions(department=None, date_filter=None):
    """构建筛选条件"""
    conditions = []
    params = []
    
    if department and department != '全部部门':
        conditions.append('department = ?')
        params.append(department)
    
    if date_filter:
        conditions.append('record_date = ?')
        params.append(date_filter)
    
    where_clause = ' AND '.join(conditions) if conditions else '1=1'
    return where_clause, params

# 静态文件服务
@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('../frontend', path)

# API路由
@app.route('/api/dashboard/metrics')
def get_metrics():
    department = request.args.get('department', '全部部门')
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m'))
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    where_clause, params = get_filter_conditions(department, date_filter)
    
    if department == '全部部门':
        # 聚合所有部门数据
        query = f'''
            SELECT 
                SUM(commit_count) as total_commits,
                AVG(bug_fix_rate) as avg_bug_fix_rate,
                AVG(code_quality) as avg_code_quality,
                AVG(delivery_efficiency) as avg_delivery_efficiency
            FROM metrics 
            WHERE {where_clause.replace('department = ?', '1=1') if 'department = ?' in where_clause else where_clause}
        '''
        # 移除部门参数
        if department != '全部部门' and 'department = ?' in where_clause:
            params = [p for p in params if p != department]
    else:
        query = f'''
            SELECT commit_count, bug_fix_rate, code_quality, delivery_efficiency
            FROM metrics 
            WHERE {where_clause}
            ORDER BY created_at DESC LIMIT 1
        '''
    
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return jsonify({
            'commitCount': int(result[0]) if result[0] else 0,
            'bugFixRate': round(float(result[1]), 1) if result[1] else 0,
            'codeQuality': int(result[2]) if result[2] else 0,
            'deliveryEfficiency': round(float(result[3]), 1) if result[3] else 0
        })
    return jsonify({
        'commitCount': 0,
        'bugFixRate': 0,
        'codeQuality': 0,
        'deliveryEfficiency': 0
    })

@app.route('/api/dashboard/trends')
def get_trends():
    department = request.args.get('department', '全部部门')
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m'))
    
    # 生成趋势数据（模拟月度数据）
    year, month = map(int, date_filter.split('-'))
    days_in_month = calendar.monthrange(year, month)[1]
    
    trends = []
    for day in range(1, min(days_in_month + 1, 31)):  # 最多显示30天
        date_str = f"{year}-{month:02d}-{day:02d}"
        # 模拟趋势值，根据部门和日期生成
        base_value = 80
        if department != '全部部门':
            base_value += hash(department) % 10
        value = base_value + (day % 10) + (hash(date_str) % 15)
        trends.append({
            'date': date_str,
            'value': min(100, value)  # 限制最大值为100
        })
    
    return jsonify({'trends': trends})

@app.route('/api/dashboard/rankings')
def get_rankings():
    department = request.args.get('department', '全部部门')
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m'))
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    where_clause, params = get_filter_conditions(department, date_filter)
    
    if department == '全部部门':
        # 聚合所有部门的开发者排行
        query = f'''
            SELECT name, AVG(score) as avg_score
            FROM developer_rankings 
            WHERE {where_clause.replace('department = ?', '1=1') if 'department = ?' in where_clause else where_clause}
            GROUP BY name
            ORDER BY avg_score DESC
        '''
        if 'department = ?' in where_clause:
            params = [p for p in params if p != department]
    else:
        query = f'''
            SELECT name, score 
            FROM developer_rankings 
            WHERE {where_clause}
            ORDER BY score DESC
        '''
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    
    rankings = [{
        'name': row[0], 
        'score': int(row[1]) if isinstance(row[1], (int, float)) else int(float(row[1]))
    } for row in results]
    
    return jsonify({'rankings': rankings})

@app.route('/api/dashboard/details')
def get_details():
    department = request.args.get('department', '全部部门')
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m'))
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    where_clause, params = get_filter_conditions(department, date_filter)
    
    query = f'''
        SELECT department, project_name, developer, commits, code_lines, bugs, completion_time
        FROM project_details 
        WHERE {where_clause}
        ORDER BY created_at DESC
    '''
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    
    details = [{
        'department': row[0],
        'projectName': row[1],
        'developer': row[2],
        'commits': row[3],
        'codeLines': row[4],
        'bugs': row[5],
        'completionTime': row[6]
    } for row in results]
    
    return jsonify({'details': details})

@app.route('/api/departments')
def get_departments():
    """获取部门列表"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT DISTINCT department FROM metrics ORDER BY department')
    results = cursor.fetchall()
    conn.close()
    
    departments = [row[0] for row in results]
    # 确保"全部部门"在第一位
    if '全部部门' in departments:
        departments.remove('全部部门')
    departments.insert(0, '全部部门')
    
    return jsonify({'departments': departments})

@app.route('/api/date-range')
def get_date_range():
    """获取可用的日期范围"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT DISTINCT record_date FROM metrics ORDER BY record_date DESC')
    results = cursor.fetchall()
    conn.close()
    
    dates = [row[0] for row in results if row[0]]
    
    # 如果没有数据，返回当前月份
    if not dates:
        dates = [datetime.now().strftime('%Y-%m')]
    
    return jsonify({'dates': dates})

@app.route('/api/ai-analysis')
def get_ai_analysis():
    department = request.args.get('department', '全部部门')
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m'))
    
    # 根据筛选条件生成AI分析
    dept_text = f"针对{department}" if department != '全部部门' else "针对全部门"
    date_text = f"{date_filter}月份"
    
    analysis_result = f"""
    <h3>AI效能分析报告</h3>
    <p>{dept_text}{date_text}的数据分析，团队整体效能表现良好：</p>
    <ul>
        <li>代码质量保持在85分以上，建议继续保持</li>
        <li>Bug修复率达到92.5%，表现优秀</li>
        <li>建议关注交付效率，可通过自动化测试提升</li>
        <li>当前筛选条件：部门={department}，时间={date_filter}</li>
    </ul>
    """
    return jsonify({'analysis': analysis_result})

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    if request.method == 'GET':
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT refresh_interval, email_notifications FROM settings ORDER BY updated_at DESC LIMIT 1')
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return jsonify({
                'refreshInterval': result[0],
                'emailNotifications': bool(result[1])
            })
        return jsonify({
            'refreshInterval': 10,
            'emailNotifications': False
        })
    
    elif request.method == 'POST':
        data = request.get_json()
        refresh_interval = data.get('refreshInterval', 10)
        email_notifications = data.get('emailNotifications', False)
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO settings (refresh_interval, email_notifications, updated_at)
            VALUES (?, ?, ?)
        ''', (refresh_interval, email_notifications, datetime.now()))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})

if __name__ == '__main__':
    # 确保数据库目录存在
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)