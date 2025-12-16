"""
数据汇总工具模块
提供多维度数据透视和汇总功能
"""

import pandas as pd
from typing import Dict, List, Optional, Literal


# 定义理化指标的字段映射
PHYSICOCHEMICAL_INDICATORS = {
    '水分': {
        'entry_upper': 'entry_moisture_upper',
        'entry_lower': 'entry_moisture_lower',
        'exit_upper': 'exit_moisture_upper',
        'exit_lower': 'exit_moisture_lower',
    },
    '酒分': {
        'entry_upper': 'entry_alcohol_upper',
        'entry_lower': 'entry_alcohol_lower',
        'exit_upper': 'exit_alcohol_upper',
        'exit_lower': 'exit_alcohol_lower',
    },
    '酸度': {
        'entry_upper': 'entry_acidity_upper',
        'entry_lower': 'entry_acidity_lower',
        'exit_upper': 'exit_acidity_upper',
        'exit_lower': 'exit_acidity_lower',
    },
    '淀粉': {
        'entry_upper': 'entry_starch_upper',
        'entry_lower': 'entry_starch_lower',
        'exit_upper': 'exit_starch_upper',
        'exit_lower': 'exit_starch_lower',
    },
    '还原糖': {
        'entry_upper': 'entry_sugar_upper',
        'entry_lower': 'entry_sugar_lower',
        'exit_upper': 'exit_sugar_upper',
        'exit_lower': 'exit_sugar_lower',
    }
}


def get_columns_by_dimensions(
    layer: Literal['全部', '上层', '下层'],
    direction: Literal['全部', '入池', '出池']
) -> List[str]:
    """
    根据层次和出入池维度获取需要汇总的列
    
    Args:
        layer: 层次维度 (全部/上层/下层)
        direction: 出入池维度 (全部/入池/出池)
    
    Returns:
        List[str]: 需要汇总的列名列表
    """
    columns = []
    
    for indicator_name, fields in PHYSICOCHEMICAL_INDICATORS.items():
        # 根据出入池维度筛选
        if direction == '入池':
            field_keys = ['entry_upper', 'entry_lower']
        elif direction == '出池':
            field_keys = ['exit_upper', 'exit_lower']
        else:  # 全部
            field_keys = list(fields.keys())
        
        # 根据层次维度筛选
        if layer == '上层':
            field_keys = [k for k in field_keys if 'upper' in k]
        elif layer == '下层':
            field_keys = [k for k in field_keys if 'lower' in k]
        
        # 添加对应的字段名
        for key in field_keys:
            columns.append(fields[key])
    
    return columns


def aggregate_data(
    df: pd.DataFrame,
    layer: Literal['全部', '上层', '下层'],
    direction: Literal['全部', '入池', '出池'],
    agg_method: Literal['平均值', '最大值', '最小值', '中位数', '标准差', '总和', '计数']
) -> pd.DataFrame:
    """
    对数据进行多维度汇总
    
    Args:
        df: 原始数据DataFrame
        layer: 层次维度
        direction: 出入池维度
        agg_method: 汇总方式
    
    Returns:
        pd.DataFrame: 汇总后的数据
    """
    # 获取需要汇总的列
    columns = get_columns_by_dimensions(layer, direction)
    
    # 过滤出存在的列
    existing_columns = [col for col in columns if col in df.columns]
    
    if not existing_columns:
        return pd.DataFrame()
    
    # 选择汇总方法
    agg_func_map = {
        '平均值': 'mean',
        '最大值': 'max',
        '最小值': 'min',
        '中位数': 'median',
        '标准差': 'std',
        '总和': 'sum',
        '计数': 'count'
    }
    
    agg_func = agg_func_map.get(agg_method, 'mean')
    
    # 执行汇总
    result = df[existing_columns].agg(agg_func)
    
    return result


def create_pivot_table(
    df: pd.DataFrame,
    layer: Literal['全部', '上层', '下层'],
    direction: Literal['全部', '入池', '出池'],
    agg_method: Literal['平均值', '最大值', '最小值', '中位数', '标准差', '总和', '计数'],
    group_by: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    创建数据透视表
    
    Args:
        df: 原始数据DataFrame
        layer: 层次维度
        direction: 出入池维度
        agg_method: 汇总方式
        group_by: 分组字段列表 (例如: ['round_number', 'workshop'])
    
    Returns:
        pd.DataFrame: 透视表数据
    """
    # 获取需要汇总的列
    columns = get_columns_by_dimensions(layer, direction)
    existing_columns = [col for col in columns if col in df.columns]
    
    if not existing_columns:
        return pd.DataFrame()
    
    # 选择汇总方法
    agg_func_map = {
        '平均值': 'mean',
        '最大值': 'max',
        '最小值': 'min',
        '中位数': 'median',
        '标准差': 'std',
        '总和': 'sum',
        '计数': 'count'
    }
    
    agg_func = agg_func_map.get(agg_method, 'mean')
    
    # 如果没有分组字段,返回整体汇总
    if not group_by:
        result = df[existing_columns].agg(agg_func).to_frame(name=agg_method)
        result.index.name = '指标'
        return result
    
    # 过滤出存在的分组字段
    existing_group_by = [col for col in group_by if col in df.columns]
    
    if not existing_group_by:
        # 如果分组字段都不存在,返回整体汇总
        result = df[existing_columns].agg(agg_func).to_frame(name=agg_method)
        result.index.name = '指标'
        return result
    
    # 执行分组汇总
    result = df.groupby(existing_group_by)[existing_columns].agg(agg_func)
    
    return result


def format_column_name(col_name: str) -> str:
    """
    将英文列名转换为中文显示名称
    
    Args:
        col_name: 英文列名
    
    Returns:
        str: 中文显示名称
    """
    # 分组字段映射(优先检查)
    group_field_map = {
        'pit_no': '窖池',
        'round_number': '轮次',
        'workshop': '车间',
        'team_name': '班组',
        'production_date': '生产日期',
        'work_year': '工作年度',
        'fiscal_year': '实际年份'
    }
    
    # 如果是分组字段,直接返回中文名
    if col_name in group_field_map:
        return group_field_map[col_name]
    
    # 指标名称映射
    indicator_map = {
        'moisture': '水分',
        'alcohol': '酒分',
        'acidity': '酸度',
        'starch': '淀粉',
        'sugar': '还原糖'
    }
    
    # 方向映射
    direction_map = {
        'entry': '入池',
        'exit': '出池'
    }
    
    # 层次映射
    layer_map = {
        'upper': '上层',
        'lower': '下层'
    }
    
    # 解析列名
    parts = col_name.split('_')
    
    if len(parts) >= 3:
        direction = direction_map.get(parts[0], parts[0])
        indicator = indicator_map.get(parts[1], parts[1])
        layer = layer_map.get(parts[2], parts[2])
        
        return f"{direction}{indicator}({layer})"
    
    return col_name


def get_summary_statistics(
    df: pd.DataFrame,
    layer: Literal['全部', '上层', '下层'],
    direction: Literal['全部', '入池', '出池']
) -> pd.DataFrame:
    """
    获取多种统计指标的汇总
    
    Args:
        df: 原始数据DataFrame
        layer: 层次维度
        direction: 出入池维度
    
    Returns:
        pd.DataFrame: 包含多种统计指标的汇总表(行为汇总方式,列为指标名称)
    """
    # 获取需要汇总的列
    columns = get_columns_by_dimensions(layer, direction)
    existing_columns = [col for col in columns if col in df.columns]
    
    if not existing_columns:
        return pd.DataFrame()
    
    # 计算多种统计指标 - 使用字典形式
    stats = df[existing_columns].agg(['mean', 'max', 'min', 'median', 'std', 'count'])
    
    # 重命名行索引为中文
    stats.index = ['平均值', '最大值', '最小值', '中位数', '标准差', '计数']
    
    # 格式化列名为中文
    stats.columns = [format_column_name(col) for col in stats.columns]
    
    # 设置索引名称
    stats.index.name = '汇总方式'
    
    return stats
