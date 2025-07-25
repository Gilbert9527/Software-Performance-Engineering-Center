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

# 静态文件服务
@app.route('/')
def index():
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    return send_from_directory(frontend_path, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    return send_from_directory(frontend_path, filename)

# 在数据库初始化中添加新的字段
def init_database():
    """初始化数据库"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 创建数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT DEFAULT '全部部门',
            requirement_throughput INTEGER,
            monthly_delivered_requirements INTEGER,
            monthly_new_requirements INTEGER,
            delivery_cycle_p75 REAL,
            online_defects INTEGER,
            reopen_rate REAL,
            emergency_releases INTEGER,
            incident_count INTEGER,
            work_saturation REAL,
            code_equivalent INTEGER,
            record_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT DEFAULT '全部部门',
            person_name TEXT,
            position_name TEXT,
            project_name TEXT,
            saturation REAL,
            code_equivalent INTEGER,
            delivered_requirements INTEGER,
            total_hours REAL,
            ai_usage_days REAL,
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
            work_saturation REAL,
            code_equivalent INTEGER,
            defect_count INTEGER,
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
                INSERT INTO metrics (department, requirement_throughput, monthly_delivered_requirements, 
                monthly_new_requirements, delivery_cycle_p75, online_defects, reopen_rate, 
                emergency_releases, incident_count, work_saturation, code_equivalent, record_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (dept, 
                  120 + hash(dept + 'throughput') % 50,      # 需求吞吐率
                  85 + hash(dept + 'delivered') % 30,        # 本月非事务型交付需求数量
                  95 + hash(dept + 'new') % 40,              # 本月新增需求数量
                  7.5 + (hash(dept + 'cycle') % 50) / 10,    # 需求交付周期P75分位
                  12 + hash(dept + 'defects') % 20,          # 线上缺陷数量
                  3.2 + (hash(dept + 'reopen') % 30) / 10,   # Reopen率
                  2 + hash(dept + 'emergency') % 8,          # 紧急上线次数
                  1 + hash(dept + 'incident') % 5,           # 故障数
                  85.5 + (hash(dept + 'saturation') % 30) / 10,  # 工作饱和度
                  1200 + hash(dept + 'equivalent') % 800,    # 代码当量
                  current_date))
            
            # 插入项目详情数据
            projects = [
                ('张三', '高级开发工程师', f'{dept}-项目A', 85.5, 1200, 15, 160.5, 2.5),
                ('李四', '开发工程师', f'{dept}-项目B', 78.2, 980, 12, 145.0, 1.8),
                ('王五', '资深开发工程师', f'{dept}-项目C', 92.1, 1450, 18, 175.5, 3.2),
                ('赵六', '开发工程师', f'{dept}-项目D', 76.8, 850, 10, 132.0, 1.5),
                ('钱七', '高级开发工程师', f'{dept}-项目E', 88.9, 1350, 16, 168.0, 2.8)
            ]
            
            for project in projects:
                cursor.execute('''
                    INSERT INTO project_details (department, person_name, position_name, project_name, saturation, code_equivalent, delivered_requirements, total_hours, ai_usage_days, record_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (dept, project[0], project[1], project[2], project[3], project[4], project[5], project[6], project[7], current_date))
            
            # 插入开发者排行数据
            developers = [
                ('张三', 95 + hash(dept + '张三') % 5),
                ('李四', 88 + hash(dept + '李四') % 7),
                ('王五', 82 + hash(dept + '王五') % 8)
            ]
            
            for dev in developers:
                cursor.execute('''
                    INSERT INTO developer_rankings (department, name, score, work_saturation, code_equivalent, defect_count, record_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (dept, dev[0], dev[1], 
                      85.5 + (hash(dept + dev[0] + 'sat') % 30) / 10,  # 工作饱和度
                      1200 + hash(dept + dev[0] + 'code') % 800,        # 代码当量
                      hash(dept + dev[0] + 'defect') % 10,             # 缺陷数量
                      current_date))
    
    conn.commit()
    conn.close()

def get_filter_conditions(department, date_filter):
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

@app.route('/api/dashboard/metrics')
def get_metrics():
    """获取指标数据"""
    department = request.args.get('department', '全部部门')
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m'))
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    where_clause, params = get_filter_conditions(department, date_filter)
    
    if department == '全部部门':
        # 聚合所有部门的数据
        query = f'''
            SELECT 
                AVG(requirement_throughput) as requirement_throughput,
                AVG(monthly_delivered_requirements) as monthly_delivered_requirements,
                AVG(monthly_new_requirements) as monthly_new_requirements,
                AVG(delivery_cycle_p75) as delivery_cycle_p75,
                AVG(online_defects) as online_defects,
                AVG(reopen_rate) as reopen_rate,
                AVG(emergency_releases) as emergency_releases,
                AVG(incident_count) as incident_count,
                AVG(work_saturation) as work_saturation,
                AVG(code_equivalent) as code_equivalent
            FROM metrics 
            WHERE {where_clause.replace('department = ?', '1=1') if 'department = ?' in where_clause else where_clause}
        '''
        if 'department = ?' in where_clause:
            params = [p for p in params if p != department]
    else:
        query = f'''
            SELECT 
                requirement_throughput,
                monthly_delivered_requirements,
                monthly_new_requirements,
                delivery_cycle_p75,
                online_defects,
                reopen_rate,
                emergency_releases,
                incident_count,
                work_saturation,
                code_equivalent
            FROM metrics 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT 1
        '''
    
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return jsonify({
            'requirementThroughput': int(result[0]) if result[0] else 0,
            'monthlyDeliveredRequirements': int(result[1]) if result[1] else 0,
            'monthlyNewRequirements': int(result[2]) if result[2] else 0,
            'deliveryCycleP75': f"{result[3]:.1f}天" if result[3] else "0天",
            'onlineDefects': int(result[4]) if result[4] else 0,
            'reopenRate': round(result[5], 1) if result[5] else 0,
            'emergencyReleases': int(result[6]) if result[6] else 0,
            'incidentCount': int(result[7]) if result[7] else 0,
            'workSaturation': round(result[8], 1) if result[8] else 0,
            'codeEquivalent': int(result[9]) if result[9] else 0
        })
    
    return jsonify({
        'requirementThroughput': 0,
        'monthlyDeliveredRequirements': 0,
        'monthlyNewRequirements': 0,
        'deliveryCycleP75': "0天",
        'onlineDefects': 0,
        'reopenRate': 0,
        'emergencyReleases': 0,
        'incidentCount': 0,
        'workSaturation': 0,
        'codeEquivalent': 0
    })

@app.route('/api/dashboard/trends')
def get_trends():
    """获取趋势数据"""
    department = request.args.get('department', '全部部门')
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m'))
    
    # 这里可以返回趋势图表数据
    # 暂时返回空数据，实际应用中需要根据时间序列查询数据
    return jsonify({
        'trends': {
            'throughput': [],
            'deliveredRequirements': [],
            'newRequirements': [],
            'deliveryCycle': [],
            'onlineDefects': [],
            'reopenRate': [],
            'codeEquivalent': []
        }
    })

# 更新排行榜API
@app.route('/api/dashboard/rankings')
def get_rankings():
    department = request.args.get('department', '全部部门')
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m'))
    ranking_type = request.args.get('type', 'score')
    sort_order = request.args.get('sort', 'desc')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    where_clause, params = get_filter_conditions(department, date_filter)
    
    # 根据排行榜类型选择字段（去掉综合评分）
    field_mapping = {
        'saturation': 'work_saturation',
        'code': 'code_equivalent',
        'defects': 'defect_count'
    }
    
    field = field_mapping.get(ranking_type, 'score')
    order_direction = 'ASC' if sort_order == 'asc' else 'DESC'
    
    # 对于缺陷数量，默认升序（缺陷越少越好）
    if ranking_type == 'defects' and sort_order == 'desc':
        order_direction = 'ASC'
    elif ranking_type == 'defects' and sort_order == 'asc':
        order_direction = 'DESC'
    
    if department == '全部部门':
        # 聚合所有部门的数据
        query = f'''
            SELECT name, AVG({field}) as avg_value
            FROM developer_rankings 
            WHERE {where_clause.replace('department = ?', '1=1') if 'department = ?' in where_clause else where_clause}
            GROUP BY name
            ORDER BY avg_value {order_direction}
        '''
        if 'department = ?' in where_clause:
            params = [p for p in params if p != department]
    else:
        query = f'''
            SELECT name, {field} as value
            FROM developer_rankings 
            WHERE {where_clause}
            ORDER BY value {order_direction}
        '''
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    
    rankings = []
    for row in results:
        value = row[1]
        if ranking_type == 'saturation':
            value = round(float(value), 1)
        elif ranking_type in ['score', 'code', 'defects']:
            value = int(value) if value is not None else 0
            
        rankings.append({
            'name': row[0],
            'value': value
        })
    
    return jsonify({'rankings': rankings})

@app.route('/api/dashboard/details')
def get_details():
    department = request.args.get('department', '全部部门')
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m'))
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    where_clause, params = get_filter_conditions(department, date_filter)
    
    query = f'''
        SELECT person_name, position_name, project_name, saturation, code_equivalent, delivered_requirements, total_hours, ai_usage_days
        FROM project_details 
        WHERE {where_clause}
        ORDER BY created_at DESC
    '''
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    
    details = [{
        'personName': row[0],
        'positionName': row[1],
        'projectName': row[2],
        'saturation': round(row[3], 1) if row[3] else 0,
        'codeEquivalent': int(row[4]) if row[4] else 0,
        'deliveredRequirements': int(row[5]) if row[5] else 0,
        'totalHours': round(row[6], 1) if row[6] else 0,
        'aiUsageDays': round(row[7], 1) if row[7] else 0
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