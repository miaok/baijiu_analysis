"""
数据库工具模块
提供数据库连接和查询功能
"""

import sqlite3
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime

DB_FILE = 'baijiu_production.db'

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_physicochemical_data(filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    获取理化指标数据
    
    Args:
        filters: 筛选条件字典，包括：
            - start_date: 开始日期
            - end_date: 结束日期
            - months: 月份列表
            - rounds: 轮次列表
            - workshops: 车间列表
            - teams: 班组列表
            - pits: 窖池列表
            - work_years: 工作年度列表
    
    Returns:
        DataFrame: 理化指标数据
    """
    conn = get_db_connection()
    
    # 基础查询SQL
    query = """
    SELECT 
        peh.event_id,
        peh.production_date,
        peh.fiscal_year,
        peh.work_year,
        peh.round_number,
        peh.team_name,
        pm.pit_no,
        pm.workshop,
        pm.team_name as pit_team,
        ppi.map_id,
        
        -- 入池理化指标(上层)
        pc.entry_moisture_upper,
        pc.entry_alcohol_upper,
        pc.entry_acidity_upper,
        pc.entry_starch_upper,
        pc.entry_sugar_upper,
        
        -- 入池理化指标(下层)
        pc.entry_moisture_lower,
        pc.entry_alcohol_lower,
        pc.entry_acidity_lower,
        pc.entry_starch_lower,
        pc.entry_sugar_lower,
        
        -- 出池理化指标(上层)
        pc.exit_moisture_upper,
        pc.exit_alcohol_upper,
        pc.exit_acidity_upper,
        pc.exit_starch_upper,
        pc.exit_sugar_upper,
        
        -- 出池理化指标(下层)
        pc.exit_moisture_lower,
        pc.exit_alcohol_lower,
        pc.exit_acidity_lower,
        pc.exit_starch_lower,
        pc.exit_sugar_lower
        
    FROM production_event_header peh
    LEFT JOIN pit_production_map ppi ON peh.event_id = ppi.event_id
    LEFT JOIN pit_master pm ON ppi.pit_no = pm.pit_no
    LEFT JOIN physicochemical_indicators pc ON ppi.map_id = pc.map_id
    WHERE 1=1
    """
    
    params = []
    
    # 应用筛选条件
    if filters:
        # 日期范围筛选
        if filters.get('start_date'):
            query += " AND peh.production_date >= ?"
            params.append(filters['start_date'])
        
        if filters.get('end_date'):
            query += " AND peh.production_date <= ?"
            params.append(filters['end_date'])
        
        # 月份筛选（从日期中提取月份）
        if filters.get('months'):
            month_placeholders = ','.join(['?' for _ in filters['months']])
            query += f" AND CAST(strftime('%m', peh.production_date) AS INTEGER) IN ({month_placeholders})"
            params.extend(filters['months'])
        
        # 轮次筛选
        if filters.get('rounds'):
            round_placeholders = ','.join(['?' for _ in filters['rounds']])
            query += f" AND peh.round_number IN ({round_placeholders})"
            params.extend(filters['rounds'])
        
        # 工作年度筛选
        if filters.get('work_years'):
            year_placeholders = ','.join(['?' for _ in filters['work_years']])
            query += f" AND peh.work_year IN ({year_placeholders})"
            params.extend(filters['work_years'])
        
        # 实际年份筛选
        if filters.get('fiscal_years'):
            fiscal_year_placeholders = ','.join(['?' for _ in filters['fiscal_years']])
            query += f" AND peh.fiscal_year IN ({fiscal_year_placeholders})"
            params.extend(filters['fiscal_years'])

        
        # 车间筛选
        if filters.get('workshops'):
            workshop_placeholders = ','.join(['?' for _ in filters['workshops']])
            query += f" AND pm.workshop IN ({workshop_placeholders})"
            params.extend(filters['workshops'])
        
        # 班组筛选
        if filters.get('teams'):
            team_placeholders = ','.join(['?' for _ in filters['teams']])
            query += f" AND peh.team_name IN ({team_placeholders})"
            params.extend(filters['teams'])
        
        # 窖池筛选
        if filters.get('pits'):
            pit_placeholders = ','.join(['?' for _ in filters['pits']])
            query += f" AND pm.pit_no IN ({pit_placeholders})"
            params.extend(filters['pits'])
    
    query += " ORDER BY peh.production_date DESC, pm.pit_no"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df


def get_filter_options() -> Dict[str, List]:
    """
    获取所有可用的筛选选项
    
    Returns:
        Dict: 包含各维度的可选值
    """
    conn = get_db_connection()
    
    options = {}
    
    # 获取工作年度
    options['work_years'] = pd.read_sql_query(
        "SELECT DISTINCT work_year FROM production_event_header ORDER BY work_year DESC",
        conn
    )['work_year'].tolist()
    
    # 获取轮次
    options['rounds'] = pd.read_sql_query(
        "SELECT DISTINCT round_number FROM production_event_header ORDER BY round_number",
        conn
    )['round_number'].tolist()
    
    # 获取车间
    options['workshops'] = pd.read_sql_query(
        "SELECT DISTINCT workshop FROM pit_master ORDER BY workshop",
        conn
    )['workshop'].tolist()
    
    # 获取班组
    options['teams'] = pd.read_sql_query(
        "SELECT DISTINCT team_name FROM production_event_header ORDER BY team_name",
        conn
    )['team_name'].tolist()
    
    # 获取窖池
    options['pits'] = pd.read_sql_query(
        "SELECT DISTINCT pit_no FROM pit_master ORDER BY pit_no",
        conn
    )['pit_no'].tolist()
    
    # 获取日期范围
    date_range = pd.read_sql_query(
        "SELECT MIN(production_date) as min_date, MAX(production_date) as max_date FROM production_event_header",
        conn
    )
    
    if not date_range.empty:
        options['min_date'] = pd.to_datetime(date_range['min_date'][0]).date()
        options['max_date'] = pd.to_datetime(date_range['max_date'][0]).date()
    else:
        options['min_date'] = datetime.now().date()
        options['max_date'] = datetime.now().date()
    
    conn.close()
    
    return options


def get_teams_by_workshop(workshop: str) -> List[str]:
    """
    根据车间获取对应的班组列表
    
    Args:
        workshop: 车间名称
    
    Returns:
        List: 班组列表
    """
    conn = get_db_connection()
    
    query = """
    SELECT DISTINCT peh.team_name 
    FROM production_event_header peh
    JOIN pit_production_map ppi ON peh.event_id = ppi.event_id
    JOIN pit_master pm ON ppi.pit_no = pm.pit_no
    WHERE pm.workshop = ?
    ORDER BY peh.team_name
    """
    
    teams = pd.read_sql_query(query, conn, params=[workshop])['team_name'].tolist()
    conn.close()
    
    return teams


def get_pits_by_workshop_team(workshop: Optional[str] = None, team: Optional[str] = None) -> List[str]:
    """
    根据车间和班组获取窖池列表
    
    Args:
        workshop: 车间名称
        team: 班组名称
    
    Returns:
        List: 窖池列表
    """
    conn = get_db_connection()
    
    query = "SELECT DISTINCT pit_no FROM pit_master WHERE 1=1"
    params = []
    
    if workshop:
        query += " AND workshop = ?"
        params.append(workshop)
    
    if team:
        query += " AND team_name = ?"
        params.append(team)
    
    query += " ORDER BY pit_no"
    
    pits = pd.read_sql_query(query, conn, params=params)['pit_no'].tolist()
    conn.close()
    
    return pits


def get_liquor_output_data(filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    获取原酒产出数据
    
    Args:
        filters: 筛选条件字典,包括:
            - start_date: 开始日期
            - end_date: 结束日期
            - months: 月份列表
            - rounds: 轮次列表
            - workshops: 车间列表
            - teams: 班组列表
            - pits: 窖池列表
            - work_years: 工作年度列表
            - fiscal_years: 实际年份列表
    
    Returns:
        DataFrame: 原酒产出数据
    """
    conn = get_db_connection()
    
    # 基础查询SQL
    query = """
    SELECT 
        peh.event_id,
        peh.production_date,
        peh.fiscal_year,
        peh.work_year,
        peh.round_number,
        peh.team_name,
        pm.pit_no,
        pm.workshop,
        pm.team_name as pit_team,
        ppi.map_id,
        
        -- 原酒产出数据
        lor.record_id,
        lor.segment_type,
        lor.quantity_kg,
        lor.ethyl_hexanoate
        
    FROM production_event_header peh
    LEFT JOIN pit_production_map ppi ON peh.event_id = ppi.event_id
    LEFT JOIN pit_master pm ON ppi.pit_no = pm.pit_no
    LEFT JOIN liquor_output_record lor ON ppi.map_id = lor.map_id
    WHERE 1=1
    """
    
    params = []
    
    # 应用筛选条件
    if filters:
        # 日期范围筛选
        if filters.get('start_date'):
            query += " AND peh.production_date >= ?"
            params.append(filters['start_date'])
        
        if filters.get('end_date'):
            query += " AND peh.production_date <= ?"
            params.append(filters['end_date'])
        
        # 月份筛选（从日期中提取月份）
        if filters.get('months'):
            month_placeholders = ','.join(['?' for _ in filters['months']])
            query += f" AND CAST(strftime('%m', peh.production_date) AS INTEGER) IN ({month_placeholders})"
            params.extend(filters['months'])
        
        # 轮次筛选
        if filters.get('rounds'):
            round_placeholders = ','.join(['?' for _ in filters['rounds']])
            query += f" AND peh.round_number IN ({round_placeholders})"
            params.extend(filters['rounds'])
        
        # 工作年度筛选
        if filters.get('work_years'):
            year_placeholders = ','.join(['?' for _ in filters['work_years']])
            query += f" AND peh.work_year IN ({year_placeholders})"
            params.extend(filters['work_years'])
        
        # 实际年份筛选
        if filters.get('fiscal_years'):
            fiscal_year_placeholders = ','.join(['?' for _ in filters['fiscal_years']])
            query += f" AND peh.fiscal_year IN ({fiscal_year_placeholders})"
            params.extend(filters['fiscal_years'])
        
        # 车间筛选
        if filters.get('workshops'):
            workshop_placeholders = ','.join(['?' for _ in filters['workshops']])
            query += f" AND pm.workshop IN ({workshop_placeholders})"
            params.extend(filters['workshops'])
        
        # 班组筛选
        if filters.get('teams'):
            team_placeholders = ','.join(['?' for _ in filters['teams']])
            query += f" AND peh.team_name IN ({team_placeholders})"
            params.extend(filters['teams'])
        
        # 窖池筛选
        if filters.get('pits'):
            pit_placeholders = ','.join(['?' for _ in filters['pits']])
            query += f" AND pm.pit_no IN ({pit_placeholders})"
            params.extend(filters['pits'])
    
    query += " ORDER BY peh.production_date DESC, pm.pit_no, lor.segment_type"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    # 添加段次名称映射
    segment_mapping = {
        1: '一段',
        2: '二段',
        3: '三段',
        99: '其它'
    }
    df['segment_name'] = df['segment_type'].map(segment_mapping)
    
    return df


def get_temperature_data(filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    获取温度数据（包括工艺参数）
    
    Args:
        filters: 筛选条件字典,包括:
            - start_date: 开始日期
            - end_date: 结束日期
            - months: 月份列表
            - rounds: 轮次列表
            - workshops: 车间列表
            - teams: 班组列表
            - pits: 窖池列表
            - work_years: 工作年度列表
            - fiscal_years: 实际年份列表
    
    Returns:
        DataFrame: 温度数据（工艺参数）
    """
    conn = get_db_connection()
    
    # 基础查询SQL - 获取工艺参数
    query = """
    SELECT 
        peh.event_id,
        peh.production_date,
        peh.fiscal_year,
        peh.work_year,
        peh.round_number,
        peh.team_name,
        pm.pit_no,
        pm.workshop,
        pm.team_name as pit_team,
        ppi.map_id,
        
        -- 工艺参数
        pp.temp_peak,
        pp.days_to_peak,
        pp.peak_duration,
        pp.temp_rise_range,
        pp.temp_end,
        pp.starter_activation_temp,
        pp.grains_entry_temp,
        pp.distillation_temp
        
    FROM production_event_header peh
    LEFT JOIN pit_production_map ppi ON peh.event_id = ppi.event_id
    LEFT JOIN pit_master pm ON ppi.pit_no = pm.pit_no
    LEFT JOIN process_parameters pp ON ppi.map_id = pp.map_id
    WHERE 1=1
    """
    
    params = []
    
    # 应用筛选条件
    if filters:
        # 日期范围筛选
        if filters.get('start_date'):
            query += " AND peh.production_date >= ?"
            params.append(filters['start_date'])
        
        if filters.get('end_date'):
            query += " AND peh.production_date <= ?"
            params.append(filters['end_date'])
        
        # 月份筛选（从日期中提取月份）
        if filters.get('months'):
            month_placeholders = ','.join(['?' for _ in filters['months']])
            query += f" AND CAST(strftime('%m', peh.production_date) AS INTEGER) IN ({month_placeholders})"
            params.extend(filters['months'])
        
        # 轮次筛选
        if filters.get('rounds'):
            round_placeholders = ','.join(['?' for _ in filters['rounds']])
            query += f" AND peh.round_number IN ({round_placeholders})"
            params.extend(filters['rounds'])
        
        # 工作年度筛选
        if filters.get('work_years'):
            year_placeholders = ','.join(['?' for _ in filters['work_years']])
            query += f" AND peh.work_year IN ({year_placeholders})"
            params.extend(filters['work_years'])
        
        # 实际年份筛选
        if filters.get('fiscal_years'):
            fiscal_year_placeholders = ','.join(['?' for _ in filters['fiscal_years']])
            query += f" AND peh.fiscal_year IN ({fiscal_year_placeholders})"
            params.extend(filters['fiscal_years'])
        
        # 车间筛选
        if filters.get('workshops'):
            workshop_placeholders = ','.join(['?' for _ in filters['workshops']])
            query += f" AND pm.workshop IN ({workshop_placeholders})"
            params.extend(filters['workshops'])
        
        # 班组筛选
        if filters.get('teams'):
            team_placeholders = ','.join(['?' for _ in filters['teams']])
            query += f" AND peh.team_name IN ({team_placeholders})"
            params.extend(filters['teams'])
        
        # 窖池筛选
        if filters.get('pits'):
            pit_placeholders = ','.join(['?' for _ in filters['pits']])
            query += f" AND pm.pit_no IN ({pit_placeholders})"
            params.extend(filters['pits'])
    
    query += " ORDER BY peh.production_date DESC, pm.pit_no"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df


def get_temperature_readings(map_id: int) -> pd.DataFrame:
    """
    获取指定map_id的20天温度记录
    
    Args:
        map_id: 窖池任务ID
    
    Returns:
        DataFrame: 温度记录数据
    """
    conn = get_db_connection()
    
    query = """
    SELECT 
        day_number,
        temperature
    FROM temperature_readings
    WHERE map_id = ?
    ORDER BY day_number
    """
    
    df = pd.read_sql_query(query, conn, params=[map_id])
    conn.close()
    
    return df


def get_dynamic_date_range(
    work_years: Optional[List[int]] = None,
    fiscal_years: Optional[List[int]] = None,
    months: Optional[List[int]] = None,
    rounds: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    根据筛选条件动态获取日期范围
    
    Args:
        work_years: 工作年度列表
        fiscal_years: 实际年份列表
        months: 月份列表
        rounds: 轮次列表
    
    Returns:
        Dict: 包含 min_date 和 max_date 的字典
    """
    conn = get_db_connection()
    
    query = """
    SELECT 
        MIN(production_date) as min_date,
        MAX(production_date) as max_date
    FROM production_event_header
    WHERE 1=1
    """
    
    params = []
    
    # 工作年度筛选
    if work_years:
        year_placeholders = ','.join(['?' for _ in work_years])
        query += f" AND work_year IN ({year_placeholders})"
        params.extend(work_years)
    
    # 实际年份筛选
    if fiscal_years:
        fiscal_year_placeholders = ','.join(['?' for _ in fiscal_years])
        query += f" AND fiscal_year IN ({fiscal_year_placeholders})"
        params.extend(fiscal_years)
    
    # 月份筛选
    if months:
        month_placeholders = ','.join(['?' for _ in months])
        query += f" AND CAST(strftime('%m', production_date) AS INTEGER) IN ({month_placeholders})"
        params.extend(months)
    
    # 轮次筛选
    if rounds:
        round_placeholders = ','.join(['?' for _ in rounds])
        query += f" AND round_number IN ({round_placeholders})"
        params.extend(rounds)
    
    date_range = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    result = {}
    if not date_range.empty and date_range['min_date'][0] is not None:
        result['min_date'] = pd.to_datetime(date_range['min_date'][0]).date()
        result['max_date'] = pd.to_datetime(date_range['max_date'][0]).date()
    else:
        # 如果没有数据,返回默认范围
        result['min_date'] = datetime.now().date()
        result['max_date'] = datetime.now().date()
    
    return result

