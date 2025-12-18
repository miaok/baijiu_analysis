"""
可视化分析工具模块
提供灵活的数据可视化配置和图表生成功能
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional, Literal, Tuple
import numpy as np


# ==================== 维度定义 ====================

# 分类维度 - 可以作为X轴、分组、颜色等
CATEGORICAL_DIMENSIONS = {
    '生产日期': 'production_date',
    '实际年份': 'fiscal_year',
    '工作年度': 'work_year',
    '月份': 'month',
    '车间': 'workshop',
    '班组': 'team_name',
    '轮次': 'round_number',
    '窖池': 'pit_no',
}

# 数值维度 - 理化指标
NUMERIC_DIMENSIONS = {
    # 入池指标 - 上层
    '入池水分(上层)': 'entry_moisture_upper',
    '入池酒分(上层)': 'entry_alcohol_upper',
    '入池酸度(上层)': 'entry_acidity_upper',
    '入池淀粉(上层)': 'entry_starch_upper',
    '入池还原糖(上层)': 'entry_sugar_upper',
    # 入池指标 - 下层
    '入池水分(下层)': 'entry_moisture_lower',
    '入池酒分(下层)': 'entry_alcohol_lower',
    '入池酸度(下层)': 'entry_acidity_lower',
    '入池淀粉(下层)': 'entry_starch_lower',
    '入池还原糖(下层)': 'entry_sugar_lower',
    # 出池指标 - 上层
    '出池水分(上层)': 'exit_moisture_upper',
    '出池酒分(上层)': 'exit_alcohol_upper',
    '出池酸度(上层)': 'exit_acidity_upper',
    '出池淀粉(上层)': 'exit_starch_upper',
    '出池还原糖(上层)': 'exit_sugar_upper',
    # 出池指标 - 下层
    '出池水分(下层)': 'exit_moisture_lower',
    '出池酒分(下层)': 'exit_alcohol_lower',
    '出池酸度(下层)': 'exit_acidity_lower',
    '出池淀粉(下层)': 'exit_starch_lower',
    '出池还原糖(下层)': 'exit_sugar_lower',
}

# 聚合方式映射
AGGREGATION_METHODS = {
    '无（原始数据）': None,
    '平均值': 'mean',
    '最大值': 'max',
    '最小值': 'min',
    '中位数': 'median',
    '总和': 'sum',
    '计数': 'count',
    '标准差': 'std',
}

# 图表类型定义
CHART_TYPES = {
    '折线图': 'line',
    '柱状图': 'bar',
    '散点图': 'scatter',
    '箱线图': 'box',
    '小提琴图': 'violin',
    '面积图': 'area',
    '热力图': 'heatmap',
}


# ==================== 数据预处理 ====================

def prepare_visualization_data(
    df: pd.DataFrame,
    x_dimension: str,
    y_dimension: str,
    x_agg: Optional[str] = None,
    y_agg: Optional[str] = None,
    color_dimension: Optional[str] = None
) -> pd.DataFrame:
    """
    准备可视化数据
    
    Args:
        df: 原始数据
        x_dimension: X轴维度（英文字段名）
        y_dimension: Y轴维度（英文字段名）
        x_agg: X轴聚合方式
        y_agg: Y轴聚合方式
        color_dimension: 颜色/分组维度（英文字段名）
    
    Returns:
        准备好的数据DataFrame
    """
    # 检查必需字段是否存在
    required_cols = [x_dimension, y_dimension]
    if color_dimension:
        required_cols.append(color_dimension)
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"数据中缺少以下字段: {', '.join(missing_cols)}")
    
    # 如果不需要聚合，直接返回选择的列
    if x_agg is None and y_agg is None:
        select_cols = required_cols.copy()
        return df[select_cols].dropna()
    
    # 需要聚合的情况
    # 确定分组键
    group_keys = []
    
    # X轴需要聚合时，使用color_dimension作为分组
    # Y轴需要聚合时，使用X轴作为分组
    if y_agg is not None:
        group_keys.append(x_dimension)
        if color_dimension:
            group_keys.append(color_dimension)
    elif x_agg is not None and color_dimension:
        group_keys.append(color_dimension)
    
    if not group_keys:
        # 如果没有分组键，返回整体聚合
        result_data = {}
        if x_agg:
            result_data[x_dimension] = df[x_dimension].agg(x_agg)
        else:
            result_data[x_dimension] = df[x_dimension].iloc[0] if len(df) > 0 else None
        
        if y_agg:
            result_data[y_dimension] = df[y_dimension].agg(y_agg)
        else:
            result_data[y_dimension] = df[y_dimension].iloc[0] if len(df) > 0 else None
        
        return pd.DataFrame([result_data])
    
    # 执行分组聚合
    agg_dict = {}
    if y_agg:
        agg_dict[y_dimension] = y_agg
    
    if x_agg and x_dimension not in group_keys:
        agg_dict[x_dimension] = x_agg
    
    result = df.groupby(group_keys).agg(agg_dict).reset_index()
    
    return result.dropna()


def get_available_dimensions(df: pd.DataFrame) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    获取数据中可用的维度
    
    Args:
        df: 数据DataFrame
    
    Returns:
        (分类维度字典, 数值维度字典)
    """
    available_categorical = {}
    available_numeric = {}
    
    # 检查分类维度
    for cn_name, en_name in CATEGORICAL_DIMENSIONS.items():
        if en_name in df.columns:
            available_categorical[cn_name] = en_name
    
    # 检查数值维度
    for cn_name, en_name in NUMERIC_DIMENSIONS.items():
        if en_name in df.columns:
            available_numeric[cn_name] = en_name
    
    return available_categorical, available_numeric


# ==================== 图表推荐 ====================

def recommend_chart_type(
    x_is_categorical: bool,
    y_is_categorical: bool,
    has_aggregation: bool
) -> List[str]:
    """
    根据维度类型推荐合适的图表类型
    
    Args:
        x_is_categorical: X轴是否为分类数据
        y_is_categorical: Y轴是否为分类数据
        has_aggregation: 是否有聚合操作
    
    Returns:
        推荐的图表类型列表（中文名称）
    """
    if x_is_categorical and not y_is_categorical:
        # X分类，Y数值 - 最常见的情况
        return ['柱状图', '折线图', '箱线图', '小提琴图']
    
    elif not x_is_categorical and not y_is_categorical:
        # X数值，Y数值 - 相关性分析
        if has_aggregation:
            return ['散点图', '折线图']
        else:
            return ['散点图', '箱线图']
    
    elif x_is_categorical and y_is_categorical:
        # X分类，Y分类 - 热力图
        return ['热力图']
    
    else:
        # 其他情况
        return ['柱状图', '折线图', '散点图']


# ==================== 图表生成 ====================

def create_line_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    x_label: str,
    y_label: str,
    color_col: Optional[str] = None,
    color_label: Optional[str] = None,
    title: str = ""
) -> go.Figure:
    """创建折线图"""
    fig = px.line(
        data,
        x=x_col,
        y=y_col,
        color=color_col,
        labels={x_col: x_label, y_col: y_label, color_col: color_label} if color_col else {x_col: x_label, y_col: y_label},
        title=title,
        markers=True
    )
    
    fig.update_layout(
        hovermode='x unified',
        template='plotly_white',
        height=600
    )
    
    return fig


def create_bar_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    x_label: str,
    y_label: str,
    color_col: Optional[str] = None,
    color_label: Optional[str] = None,
    title: str = ""
) -> go.Figure:
    """创建柱状图"""
    fig = px.bar(
        data,
        x=x_col,
        y=y_col,
        color=color_col,
        labels={x_col: x_label, y_col: y_label, color_col: color_label} if color_col else {x_col: x_label, y_col: y_label},
        title=title,
        barmode='group'  # 分组显示
    )
    
    fig.update_layout(
        hovermode='x unified',
        template='plotly_white',
        height=600
    )
    
    return fig


def create_scatter_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    x_label: str,
    y_label: str,
    color_col: Optional[str] = None,
    color_label: Optional[str] = None,
    title: str = ""
) -> go.Figure:
    """创建散点图"""
    fig = px.scatter(
        data,
        x=x_col,
        y=y_col,
        color=color_col,
        labels={x_col: x_label, y_col: y_label, color_col: color_label} if color_col else {x_col: x_label, y_col: y_label},
        title=title,
        trendline="ols" if color_col is None else None  # 添加趋势线（仅当没有分组时）
    )
    
    fig.update_layout(
        hovermode='closest',
        template='plotly_white',
        height=600
    )
    
    return fig


def create_box_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    x_label: str,
    y_label: str,
    color_col: Optional[str] = None,
    color_label: Optional[str] = None,
    title: str = ""
) -> go.Figure:
    """创建箱线图"""
    fig = px.box(
        data,
        x=x_col,
        y=y_col,
        color=color_col,
        labels={x_col: x_label, y_col: y_label, color_col: color_label} if color_col else {x_col: x_label, y_col: y_label},
        title=title,
        points='outliers'  # 显示异常值
    )
    
    fig.update_layout(
        hovermode='x unified',
        template='plotly_white',
        height=600
    )
    
    return fig


def create_violin_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    x_label: str,
    y_label: str,
    color_col: Optional[str] = None,
    color_label: Optional[str] = None,
    title: str = ""
) -> go.Figure:
    """创建小提琴图"""
    fig = px.violin(
        data,
        x=x_col,
        y=y_col,
        color=color_col,
        labels={x_col: x_label, y_col: y_label, color_col: color_label} if color_col else {x_col: x_label, y_col: y_label},
        title=title,
        box=True,  # 显示箱线图
        points='outliers'  # 显示异常值
    )
    
    fig.update_layout(
        hovermode='x unified',
        template='plotly_white',
        height=600
    )
    
    return fig


def create_area_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    x_label: str,
    y_label: str,
    color_col: Optional[str] = None,
    color_label: Optional[str] = None,
    title: str = ""
) -> go.Figure:
    """创建面积图"""
    fig = px.area(
        data,
        x=x_col,
        y=y_col,
        color=color_col,
        labels={x_col: x_label, y_col: y_label, color_col: color_label} if color_col else {x_col: x_label, y_col: y_label},
        title=title
    )
    
    fig.update_layout(
        hovermode='x unified',
        template='plotly_white',
        height=600
    )
    
    return fig


def create_heatmap(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    x_label: str,
    y_label: str,
    value_col: Optional[str] = None,
    title: str = ""
) -> go.Figure:
    """创建热力图"""
    # 如果没有指定值列，需要进行数据透视
    if value_col is None:
        # 统计每个组合的出现次数
        pivot_data = data.groupby([y_col, x_col]).size().unstack(fill_value=0)
    else:
        pivot_data = data.pivot_table(
            index=y_col,
            columns=x_col,
            values=value_col,
            aggfunc='mean'
        )
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='RdYlBu_r',
        hoverongaps=False
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        template='plotly_white',
        height=600
    )
    
    return fig


def create_chart(
    chart_type: str,
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    x_label: str,
    y_label: str,
    color_col: Optional[str] = None,
    color_label: Optional[str] = None,
    title: str = ""
) -> go.Figure:
    """
    根据类型创建图表
    
    Args:
        chart_type: 图表类型（使用CHART_TYPES中的英文键）
        data: 数据DataFrame
        x_col: X轴列名（英文）
        y_col: Y轴列名（英文）
        x_label: X轴标签（中文）
        y_label: Y轴标签（中文）
        color_col: 颜色/分组列名（英文）
        color_label: 颜色/分组标签（中文）
        title: 图表标题
    
    Returns:
        Plotly图表对象
    """
    chart_funcs = {
        'line': create_line_chart,
        'bar': create_bar_chart,
        'scatter': create_scatter_chart,
        'box': create_box_chart,
        'violin': create_violin_chart,
        'area': create_area_chart,
        'heatmap': create_heatmap,
    }
    
    func = chart_funcs.get(chart_type)
    if func is None:
        raise ValueError(f"不支持的图表类型: {chart_type}")
    
    return func(data, x_col, y_col, x_label, y_label, color_col, color_label, title)


# ==================== 辅助函数 ====================

def validate_chart_config(
    chart_type: str,
    x_dimension: str,
    y_dimension: str,
    x_agg: Optional[str],
    y_agg: Optional[str]
) -> Tuple[bool, str]:
    """
    验证图表配置是否合理
    
    Returns:
        (是否有效, 错误信息)
    """
    # 热力图需要两个分类维度
    if chart_type == 'heatmap':
        x_is_categorical = x_dimension in CATEGORICAL_DIMENSIONS.values()
        y_is_categorical = y_dimension in CATEGORICAL_DIMENSIONS.values()
        
        if not (x_is_categorical and y_is_categorical):
            return False, "热力图需要X轴和Y轴都为分类维度"
    
    # 散点图通常不需要聚合
    if chart_type == 'scatter' and (x_agg or y_agg):
        return True, "注意: 散点图通常使用原始数据，聚合可能会影响分析结果"
    
    return True, ""
