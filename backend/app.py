from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timedelta
import calendar
import io
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.lib.colors import HexColor
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import numpy as np
import uuid
import threading
import time

# Import AI analysis services
from services.config_manager import ConfigManager
from services.file_handler import FileUploadHandler
from services.content_extractor import ContentExtractor
from services.siliconflow_client import SiliconFlowClient
from services.report_generator import ReportGenerator

app = Flask(__name__)
CORS(app)

# 数据库配置
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'efficiency.db')

# Initialize AI analysis services
config_manager = ConfigManager()
file_handler = FileUploadHandler(config_manager)
content_extractor = ContentExtractor()
report_generator = ReportGenerator()

# Initialize SiliconFlow client
try:
    siliconflow_config = config_manager.get_siliconflow_config()
    siliconflow_client = SiliconFlowClient(
        api_key=siliconflow_config['api_key'],
        base_url=siliconflow_config['base_url'],
        model=siliconflow_config['model'],
        max_tokens=siliconflow_config.get('max_tokens', 2000),
        temperature=siliconflow_config.get('temperature', 0.7),
        timeout=siliconflow_config.get('timeout', 120)
    )
except Exception as e:
    print(f"Warning: Failed to initialize SiliconFlow client: {e}")
    siliconflow_client = None

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
    
    # 检查project_details表是否存在旧结构，如果是则重建
    cursor.execute("PRAGMA table_info(project_details)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'person_name' not in columns:
        # 删除旧表并重建
        cursor.execute('DROP TABLE IF EXISTS project_details')
    
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
    
    # AI Analysis Module Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_analysis_files (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'uploaded'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_analysis_results (
            id TEXT PRIMARY KEY,
            file_id TEXT NOT NULL,
            analysis_text TEXT NOT NULL,
            prompt_used TEXT,
            processing_time REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES ai_analysis_files (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_config (
            id INTEGER PRIMARY KEY,
            api_key TEXT NOT NULL,
            custom_prompt TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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

def create_chart_image(chart_type, data, title, width=400, height=300):
    """创建图表图片"""
    plt.figure(figsize=(width/100, height/100))
    plt.style.use('default')
    
    if chart_type == 'bar':
        labels = [item['name'] for item in data]
        values = [item['value'] for item in data]
        bars = plt.bar(labels, values, color=['#007AFF', '#30D158', '#FF9500', '#FF3B30', '#5856D6'])
        plt.xticks(rotation=45, ha='right')
        
        # 在柱子上添加数值标签
        for bar, value in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01,
                    str(value), ha='center', va='bottom', fontsize=10)
    
    elif chart_type == 'line':
        x_data = list(range(len(data)))
        y_data = [item['value'] for item in data]
        plt.plot(x_data, y_data, marker='o', linewidth=2, markersize=6, color='#007AFF')
        plt.xticks(x_data, [item['name'] for item in data], rotation=45, ha='right')
        plt.grid(True, alpha=0.3)
    
    plt.title(title, fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    
    # 保存到内存中的字节流
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer

def generate_pdf_report(department, date_filter):
    """生成PDF报告"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
    
    # 获取样式
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1,  # 居中
        textColor=colors.HexColor('#007AFF')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#333333')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12
    )
    
    story = []
    
    # 标题
    dept_text = department if department != '全部部门' else '全部部门'
    title = f"研发效能管理平台报告<br/>{dept_text} - {date_filter}"
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 20))
    
    # 生成时间
    story.append(Paragraph(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    story.append(Spacer(1, 30))
    
    # 1. 数据指标部分
    story.append(Paragraph("1. 数据指标", heading_style))
    
    # 获取指标数据
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    where_clause, params = get_filter_conditions(department, date_filter)
    
    if department == '全部部门':
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
    metrics_result = cursor.fetchone()
    
    if metrics_result:
        # 创建指标表格
        metrics_data = [
            ['指标类别', '指标名称', '数值'],
            ['交付效率', '需求吞吐率', str(int(metrics_result[0]) if metrics_result[0] else 0)],
            ['', '本月非事务型交付需求数量', str(int(metrics_result[1]) if metrics_result[1] else 0)],
            ['', '本月新增需求数量', str(int(metrics_result[2]) if metrics_result[2] else 0)],
            ['交付速度', '需求交付周期（P75分位）', f"{metrics_result[3]:.1f}天" if metrics_result[3] else "0天"],
            ['交付质量', '线上缺陷数量', str(int(metrics_result[4]) if metrics_result[4] else 0)],
            ['', 'Reopen率', f"{metrics_result[5]:.1f}%" if metrics_result[5] else "0%"],
            ['', '紧急上线次数', str(int(metrics_result[6]) if metrics_result[6] else 0)],
            ['', '故障数', str(int(metrics_result[7]) if metrics_result[7] else 0)],
            ['工作量', '工作饱和度', f"{metrics_result[8]:.1f}%" if metrics_result[8] else "0%"],
            ['', '代码当量', str(int(metrics_result[9]) if metrics_result[9] else 0)]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2*inch, 3*inch, 1.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007AFF')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 30))
    
    # 2. 排行榜部分
    story.append(Paragraph("2. 排行榜", heading_style))
    
    # 获取排行榜数据
    ranking_types = [
        ('saturation', '工作饱和度排行榜', 'work_saturation'),
        ('code', '代码当量排行榜', 'code_equivalent'),
        ('defects', '缺陷数量排行榜', 'defect_count')
    ]
    
    for ranking_type, ranking_title, field in ranking_types:
        story.append(Paragraph(f"2.{ranking_types.index((ranking_type, ranking_title, field)) + 1} {ranking_title}", normal_style))
        
        order_direction = 'ASC' if ranking_type == 'defects' else 'DESC'
        
        if department == '全部部门':
            query = f'''
                SELECT name, AVG({field}) as avg_value
                FROM developer_rankings 
                WHERE {where_clause.replace('department = ?', '1=1') if 'department = ?' in where_clause else where_clause}
                GROUP BY name
                ORDER BY avg_value {order_direction}
                LIMIT 10
            '''
            query_params = [p for p in params if p != department] if 'department = ?' in where_clause else params
        else:
            query = f'''
                SELECT name, {field} as value
                FROM developer_rankings 
                WHERE {where_clause}
                ORDER BY value {order_direction}
                LIMIT 10
            '''
            query_params = params
        
        cursor.execute(query, query_params)
        ranking_results = cursor.fetchall()
        
        if ranking_results:
            ranking_data = [['排名', '姓名', '数值']]
            for i, (name, value) in enumerate(ranking_results, 1):
                if ranking_type == 'saturation':
                    value_str = f"{value:.1f}%"
                elif ranking_type == 'code':
                    value_str = str(int(value))
                else:  # defects
                    value_str = f"{int(value)}个"
                ranking_data.append([str(i), name, value_str])
            
            ranking_table = Table(ranking_data, colWidths=[1*inch, 2*inch, 1.5*inch])
            ranking_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#30D158')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            
            story.append(ranking_table)
            story.append(Spacer(1, 20))
    
    # 3. 明细数据部分
    story.append(PageBreak())
    story.append(Paragraph("3. 明细数据", heading_style))
    
    # 获取明细数据
    query = f'''
        SELECT person_name, position_name, project_name, saturation, code_equivalent, delivered_requirements, total_hours, ai_usage_days
        FROM project_details 
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT 20
    '''
    
    cursor.execute(query, params)
    details_results = cursor.fetchall()
    
    if details_results:
        details_data = [['人员名称', '职位名称', '项目名称', '饱和度(%)', '代码当量', '交付需求数', '总工时(h)', 'AI使用人天']]
        for row in details_results:
            details_data.append([
                row[0],  # person_name
                row[1],  # position_name
                row[2],  # project_name
                f"{row[3]:.1f}" if row[3] else "0",  # saturation
                str(int(row[4]) if row[4] else 0),  # code_equivalent
                str(int(row[5]) if row[5] else 0),  # delivered_requirements
                f"{row[6]:.1f}" if row[6] else "0",  # total_hours
                f"{row[7]:.1f}" if row[7] else "0"   # ai_usage_days
            ])
        
        details_table = Table(details_data, colWidths=[0.8*inch, 0.8*inch, 1.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF9500')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(details_table)
    
    conn.close()
    
    # 构建PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

@app.route('/api/download/report')
def download_report():
    """下载PDF报告"""
    try:
        department = request.args.get('department', '全部部门')
        date_filter = request.args.get('date', datetime.now().strftime('%Y-%m'))
        
        # 生成PDF
        pdf_buffer = generate_pdf_report(department, date_filter)
        
        # 生成文件名
        dept_name = department if department != '全部部门' else '全部部门'
        filename = f"研发效能报告_{dept_name}_{date_filter}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"生成PDF报告失败: {str(e)}")
        return jsonify({'error': '生成PDF报告失败'}), 500

@app.route('/api/ai-analysis/upload', methods=['POST'])
def upload_and_analyze():
    """上传文件并进行AI分析"""
    if not siliconflow_client:
        return jsonify({'error': 'AI分析服务未初始化'}), 500
    
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        # 获取自定义提示词（可选）
        custom_prompt = request.form.get('custom_prompt', '').strip()
        if not custom_prompt:
            custom_prompt = config_manager.get_effective_prompt()
        
        # 1. 验证文件
        validation_result = file_handler.validate_file(file)
        if not validation_result.is_valid:
            return jsonify({'error': validation_result.error_message}), 400
        
        # 2. 保存临时文件
        file_id, temp_file_path = file_handler.save_temp_file(file)
        
        try:
            # 3. 提取文件内容
            extraction_result = content_extractor.extract_content(
                temp_file_path, 
                validation_result.file_type
            )
            
            if not extraction_result.success:
                return jsonify({'error': f'文件内容提取失败: {extraction_result.error_message}'}), 422
            
            # 4. AI分析
            analysis_result = siliconflow_client.analyze_content(
                extraction_result.content, 
                custom_prompt
            )
            
            if not analysis_result.success:
                return jsonify({'error': f'AI分析失败: {analysis_result.error_message}'}), 500
            
            # 5. 生成分析ID并保存到数据库
            analysis_id = str(uuid.uuid4())
            
            # 保存文件信息到数据库
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO ai_analysis_files (id, filename, file_type, file_size, upload_timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (file_id, file.filename, validation_result.file_type, 
                  validation_result.file_size, datetime.now(), 'completed'))
            
            # 保存分析结果到数据库
            cursor.execute('''
                INSERT INTO ai_analysis_results (id, file_id, analysis_text, prompt_used, processing_time, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (analysis_id, file_id, analysis_result.content, custom_prompt,
                  analysis_result.processing_time, datetime.now()))
            
            conn.commit()
            conn.close()
            
            # 6. 生成报告
            file_metadata = {
                'filename': file.filename,
                'file_type': validation_result.file_type,
                'file_size': validation_result.file_size,
                'upload_time': datetime.now().isoformat(),
                'prompt_used': custom_prompt,
                'extraction_metadata': extraction_result.metadata
            }
            
            report = report_generator.generate_report(
                analysis_result, 
                file_metadata, 
                analysis_id
            )
            
            # 7. 清理临时文件
            file_handler.cleanup_temp_file(temp_file_path)
            
            # 8. 返回结果
            return jsonify({
                'success': True,
                'file_id': file_id,
                'analysis_id': analysis_id,
                'status': 'completed',
                'report': report_generator.format_json_report(report)
            })
            
        finally:
            # 确保清理临时文件
            file_handler.cleanup_temp_file(temp_file_path)
            
    except Exception as e:
        print(f"AI分析失败: {str(e)}")
        return jsonify({'error': f'AI分析失败: {str(e)}'}), 500


@app.route('/api/ai-analysis/results/<analysis_id>')
def get_analysis_result(analysis_id):
    """获取分析结果"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 获取分析结果和文件信息
        cursor.execute('''
            SELECT r.id, r.file_id, r.analysis_text, r.prompt_used, r.processing_time, r.created_at,
                   f.filename, f.file_type, f.file_size, f.upload_timestamp
            FROM ai_analysis_results r
            JOIN ai_analysis_files f ON r.file_id = f.id
            WHERE r.id = ?
        ''', (analysis_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': '分析结果不存在'}), 404
        
        # 构建响应数据
        response_data = {
            'id': result[0],
            'file_info': {
                'filename': result[6],
                'file_type': result[7],
                'file_size': result[8],
                'upload_time': result[9]
            },
            'analysis': {
                'content': result[2],
                'prompt_used': result[3],
                'processing_time': result[4],
                'created_at': result[5]
            },
            'status': 'completed'
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"获取分析结果失败: {str(e)}")
        return jsonify({'error': f'获取分析结果失败: {str(e)}'}), 500


@app.route('/api/ai-analysis/history')
def get_analysis_history():
    """获取分析历史"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 获取总数
        cursor.execute('SELECT COUNT(*) FROM ai_analysis_results')
        total = cursor.fetchone()[0]
        
        # 获取分页数据
        cursor.execute('''
            SELECT r.id, r.file_id, r.processing_time, r.created_at,
                   f.filename, f.file_type, f.file_size
            FROM ai_analysis_results r
            JOIN ai_analysis_files f ON r.file_id = f.id
            ORDER BY r.created_at DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        
        results = cursor.fetchall()
        conn.close()
        
        # 构建响应数据
        history_items = []
        for result in results:
            history_items.append({
                'id': result[0],
                'file_id': result[1],
                'filename': result[4],
                'file_type': result[5],
                'file_size': result[6],
                'processing_time': result[2],
                'created_at': result[3]
            })
        
        return jsonify({
            'items': history_items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        print(f"获取分析历史失败: {str(e)}")
        return jsonify({'error': f'获取分析历史失败: {str(e)}'}), 500


@app.route('/api/ai-analysis/results/<analysis_id>', methods=['DELETE'])
def delete_analysis_result(analysis_id):
    """删除分析结果"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 检查分析结果是否存在
        cursor.execute('SELECT file_id FROM ai_analysis_results WHERE id = ?', (analysis_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({'error': '分析结果不存在'}), 404
        
        file_id = result[0]
        
        # 删除分析结果
        cursor.execute('DELETE FROM ai_analysis_results WHERE id = ?', (analysis_id,))
        
        # 检查是否还有其他分析结果使用同一个文件
        cursor.execute('SELECT COUNT(*) FROM ai_analysis_results WHERE file_id = ?', (file_id,))
        count = cursor.fetchone()[0]
        
        # 如果没有其他分析结果使用该文件，则删除文件记录
        if count == 0:
            cursor.execute('DELETE FROM ai_analysis_files WHERE id = ?', (file_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '分析结果已删除'})
        
    except Exception as e:
        print(f"删除分析结果失败: {str(e)}")
        return jsonify({'error': f'删除分析结果失败: {str(e)}'}), 500


@app.route('/api/ai-analysis/config', methods=['GET'])
def get_ai_config():
    """获取AI分析配置"""
    try:
        # 获取当前配置
        config_data = {
            'siliconflow': {
                'model': config_manager.get_siliconflow_config().get('model', 'Qwen/Qwen2.5-7B-Instruct'),
                'max_tokens': config_manager.get_siliconflow_config().get('max_tokens', 2000),
                'temperature': config_manager.get_siliconflow_config().get('temperature', 0.7),
                'timeout': config_manager.get_siliconflow_config().get('timeout', 120),
                'base_url': config_manager.get_siliconflow_config().get('base_url', 'https://api.siliconflow.cn/v1')
            },
            'file_processing': {
                'max_file_size': config_manager.get_max_file_size(),
                'supported_formats': config_manager.get_supported_formats()
            },
            'prompts': {
                'default': config_manager.get_default_prompt(),
                'custom': config_manager.get_custom_prompt()
            }
        }
        
        return jsonify({
            'success': True,
            'config': config_data
        })
        
    except Exception as e:
        print(f"获取配置失败: {str(e)}")
        return jsonify({'error': f'获取配置失败: {str(e)}'}), 500


@app.route('/api/ai-analysis/config', methods=['POST'])
def update_ai_config():
    """更新AI分析配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '没有提供配置数据'}), 400
        
        # 目前只支持更新自定义提示词
        if 'custom_prompt' in data:
            custom_prompt = data['custom_prompt']
            if custom_prompt:
                config_manager.set_custom_prompt(custom_prompt)
            else:
                config_manager.clear_custom_prompt()
        
        return jsonify({
            'success': True,
            'message': '配置更新成功'
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"更新配置失败: {str(e)}")
        return jsonify({'error': f'更新配置失败: {str(e)}'}), 500


@app.route('/api/ai-analysis/config/prompt', methods=['PUT'])
def update_custom_prompt():
    """更新自定义提示词"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '没有提供数据'}), 400
        
        custom_prompt = data.get('prompt', '').strip()
        
        if custom_prompt:
            config_manager.set_custom_prompt(custom_prompt)
            message = '自定义提示词设置成功'
        else:
            config_manager.clear_custom_prompt()
            message = '自定义提示词已清除，将使用默认提示词'
        
        return jsonify({
            'success': True,
            'message': message,
            'effective_prompt': config_manager.get_effective_prompt()
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"更新提示词失败: {str(e)}")
        return jsonify({'error': f'更新提示词失败: {str(e)}'}), 500


@app.route('/api/ai-analysis/config/test', methods=['POST'])
def test_ai_connection():
    """测试AI服务连接"""
    try:
        if not siliconflow_client:
            return jsonify({
                'success': False,
                'error': 'AI客户端未初始化'
            }), 500
        
        # 测试连接
        test_result = siliconflow_client.test_connection()
        
        return jsonify({
            'success': test_result['success'],
            'test_result': test_result
        })
        
    except Exception as e:
        print(f"测试连接失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'测试连接失败: {str(e)}'
        }), 500


@app.route('/api/ai-analysis/config/validate', methods=['GET'])
def validate_ai_config():
    """验证AI分析配置"""
    try:
        validation_result = config_manager.validate_configuration()
        
        return jsonify({
            'success': True,
            'validation': validation_result
        })
        
    except Exception as e:
        print(f"配置验证失败: {str(e)}")
        return jsonify({'error': f'配置验证失败: {str(e)}'}), 500


@app.route('/api/ai-analysis/files')
def get_analysis_files():
    """获取分析文件列表"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        file_type = request.args.get('file_type', '')
        offset = (page - 1) * per_page
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 构建查询条件
        where_clause = "1=1"
        params = []
        
        if file_type:
            where_clause += " AND file_type = ?"
            params.append(file_type)
        
        # 获取总数
        cursor.execute(f'SELECT COUNT(*) FROM ai_analysis_files WHERE {where_clause}', params)
        total = cursor.fetchone()[0]
        
        # 获取分页数据
        cursor.execute(f'''
            SELECT id, filename, file_type, file_size, upload_timestamp, status
            FROM ai_analysis_files 
            WHERE {where_clause}
            ORDER BY upload_timestamp DESC
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])
        
        results = cursor.fetchall()
        conn.close()
        
        # 构建响应数据
        files = []
        for result in results:
            files.append({
                'id': result[0],
                'filename': result[1],
                'file_type': result[2],
                'file_size': result[3],
                'upload_timestamp': result[4],
                'status': result[5]
            })
        
        return jsonify({
            'files': files,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        print(f"获取文件列表失败: {str(e)}")
        return jsonify({'error': f'获取文件列表失败: {str(e)}'}), 500


@app.route('/api/ai-analysis/files/<file_id>', methods=['DELETE'])
def delete_analysis_file(file_id):
    """删除分析文件及其相关的所有分析结果"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 检查文件是否存在
        cursor.execute('SELECT filename FROM ai_analysis_files WHERE id = ?', (file_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({'error': '文件不存在'}), 404
        
        filename = result[0]
        
        # 删除相关的分析结果
        cursor.execute('DELETE FROM ai_analysis_results WHERE file_id = ?', (file_id,))
        deleted_results = cursor.rowcount
        
        # 删除文件记录
        cursor.execute('DELETE FROM ai_analysis_files WHERE id = ?', (file_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'文件 "{filename}" 及其 {deleted_results} 个分析结果已删除'
        })
        
    except Exception as e:
        print(f"删除文件失败: {str(e)}")
        return jsonify({'error': f'删除文件失败: {str(e)}'}), 500


@app.route('/api/ai-analysis/stats')
def get_analysis_stats():
    """获取分析统计信息"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 总文件数
        cursor.execute('SELECT COUNT(*) FROM ai_analysis_files')
        total_files = cursor.fetchone()[0]
        
        # 总分析数
        cursor.execute('SELECT COUNT(*) FROM ai_analysis_results')
        total_analyses = cursor.fetchone()[0]
        
        # 按文件类型统计
        cursor.execute('''
            SELECT file_type, COUNT(*) 
            FROM ai_analysis_files 
            GROUP BY file_type 
            ORDER BY COUNT(*) DESC
        ''')
        file_type_stats = [{'type': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # 最近7天的分析数量
        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM ai_analysis_results 
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        ''')
        recent_analyses = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # 平均处理时间
        cursor.execute('SELECT AVG(processing_time) FROM ai_analysis_results WHERE processing_time IS NOT NULL')
        avg_processing_time = cursor.fetchone()[0] or 0
        
        # 成功率（假设所有记录都是成功的，因为失败的不会保存到数据库）
        success_rate = 100.0 if total_analyses > 0 else 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_files': total_files,
                'total_analyses': total_analyses,
                'file_type_distribution': file_type_stats,
                'recent_analyses': recent_analyses,
                'average_processing_time': round(avg_processing_time, 2),
                'success_rate': success_rate
            }
        })
        
    except Exception as e:
        print(f"获取统计信息失败: {str(e)}")
        return jsonify({'error': f'获取统计信息失败: {str(e)}'}), 500


@app.route('/api/ai-analysis/export/<analysis_id>')
def export_analysis_report(analysis_id):
    """导出分析报告"""
    try:
        format_type = request.args.get('format', 'html')  # html, json, summary
        
        if format_type not in ['html', 'json', 'summary']:
            return jsonify({'error': '不支持的导出格式'}), 400
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 获取分析结果和文件信息
        cursor.execute('''
            SELECT r.id, r.file_id, r.analysis_text, r.prompt_used, r.processing_time, r.created_at,
                   f.filename, f.file_type, f.file_size, f.upload_timestamp
            FROM ai_analysis_results r
            JOIN ai_analysis_files f ON r.file_id = f.id
            WHERE r.id = ?
        ''', (analysis_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': '分析结果不存在'}), 404
        
        # 构建分析结果对象
        from services.siliconflow_client import AnalysisResult
        analysis_result = AnalysisResult(
            success=True,
            content=result[2],
            processing_time=result[4]
        )
        
        # 构建文件元数据
        file_metadata = {
            'filename': result[6],
            'file_type': result[7],
            'file_size': result[8],
            'upload_time': result[9],
            'prompt_used': result[3]
        }
        
        # 生成报告
        report = report_generator.generate_report(
            analysis_result, 
            file_metadata, 
            analysis_id
        )
        
        # 导出报告
        exported_content = report_generator.export_report(report, format_type)
        
        # 设置响应头
        if format_type == 'html':
            response = app.response_class(
                exported_content,
                mimetype='text/html',
                headers={'Content-Disposition': f'attachment; filename=analysis_report_{analysis_id}.html'}
            )
        else:  # json or summary
            response = app.response_class(
                exported_content,
                mimetype='application/json',
                headers={'Content-Disposition': f'attachment; filename=analysis_report_{analysis_id}.json'}
            )
        
        return response
        
    except Exception as e:
        print(f"导出报告失败: {str(e)}")
        return jsonify({'error': f'导出报告失败: {str(e)}'}), 500


if __name__ == '__main__':
    # 确保数据库目录存在
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)