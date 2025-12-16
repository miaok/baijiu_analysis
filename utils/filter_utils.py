"""
筛选工具模块
提供筛选条件处理和层级联动逻辑
"""

from typing import Dict, Any, List, Optional
import streamlit as st


def validate_filter_conditions(filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证和处理筛选条件
    确保月份和轮次互斥
    
    Args:
        filters: 原始筛选条件
    
    Returns:
        Dict: 处理后的筛选条件
    """
    validated_filters = filters.copy()
    
    # 月份和轮次互斥逻辑
    if filters.get('months') and filters.get('rounds'):
        st.warning("⚠️ 月份和轮次是互斥条件，系统将优先使用轮次筛选")
        validated_filters.pop('months', None)
    
    return validated_filters


def build_filter_summary(filters: Dict[str, Any]) -> str:
    """
    构建筛选条件摘要文本
    
    Args:
        filters: 筛选条件字典
    
    Returns:
        str: 摘要文本
    """
    summary_parts = []
    
    # 年度筛选
    if filters.get('work_years'):
        summary_parts.append(f"工作年度: {', '.join(map(str, filters['work_years']))}")
    
    if filters.get('fiscal_years'):
        summary_parts.append(f"实际年份: {', '.join(map(str, filters['fiscal_years']))}")
    
    # 日期范围
    if filters.get('start_date') or filters.get('end_date'):
        date_text = "日期范围: "
        if filters.get('start_date'):
            date_text += f"{filters['start_date']}"
        else:
            date_text += "不限"
        date_text += " 至 "
        if filters.get('end_date'):
            date_text += f"{filters['end_date']}"
        else:
            date_text += "不限"
        summary_parts.append(date_text)
    
    # 月份
    if filters.get('months'):
        summary_parts.append(f"月份: {', '.join(map(str, filters['months']))}月")
    
    # 轮次
    if filters.get('rounds'):
        summary_parts.append(f"轮次: {', '.join(map(str, filters['rounds']))}")
    
    # 车间
    if filters.get('workshops'):
        summary_parts.append(f"车间: {', '.join(filters['workshops'])}")
    
    # 班组
    if filters.get('teams'):
        summary_parts.append(f"班组: {', '.join(filters['teams'])}")
    
    # 窖池
    if filters.get('pits'):
        pit_count = len(filters['pits'])
        if pit_count <= 3:
            summary_parts.append(f"窖池: {', '.join(filters['pits'])}")
        else:
            summary_parts.append(f"窖池: 已选{pit_count}个")
    
    if not summary_parts:
        return "无筛选条件（显示全部数据）"
    
    return " | ".join(summary_parts)



def get_month_options() -> List[int]:
    """获取月份选项（1-12月）"""
    return list(range(1, 13))


def format_month_label(month: int) -> str:
    """格式化月份标签"""
    return f"{month}月"


def update_cascading_filters(workshop_selected: List[str], available_teams: List[str]) -> List[str]:
    """
    更新层级联动筛选
    当车间改变时，更新可选的班组
    
    Args:
        workshop_selected: 已选择的车间列表
        available_teams: 当前可用的班组列表
    
    Returns:
        List: 更新后的班组列表
    """
    # 这里的逻辑会在页面中实现
    # 此函数主要作为接口定义
    return available_teams
