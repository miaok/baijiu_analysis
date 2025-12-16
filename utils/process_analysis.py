"""
工艺分析工具模块
提供异常检测和合格率分析功能
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List


# 配置文件路径
CONFIG_FILE = Path("config/process_standards.json")

# 指标字段映射
INDICATOR_FIELDS = {
    "entry": {
        "moisture": ["entry_moisture_upper", "entry_moisture_lower"],
        "alcohol": ["entry_alcohol_upper", "entry_alcohol_lower"],
        "acidity": ["entry_acidity_upper", "entry_acidity_lower"],
        "starch": ["entry_starch_upper", "entry_starch_lower"],
        "sugar": ["entry_sugar_upper", "entry_sugar_lower"]
    },
    "exit": {
        "moisture": ["exit_moisture_upper", "exit_moisture_lower"],
        "alcohol": ["exit_alcohol_upper", "exit_alcohol_lower"],
        "acidity": ["exit_acidity_upper", "exit_acidity_lower"],
        "starch": ["exit_starch_upper", "exit_starch_lower"],
        "sugar": ["exit_sugar_upper", "exit_sugar_lower"]
    },
    "temperature": {
        "grains_entry_temp": ["grains_entry_temp"],
        "temp_rise_range": ["temp_rise_range"],
        "distillation_temp": ["distillation_temp"]
    }
}

# 指标中文名称
INDICATOR_NAMES_CN = {
    "moisture": "水分",
    "alcohol": "酒分",
    "acidity": "酸度",
    "starch": "淀粉",
    "sugar": "还原糖",
    "grains_entry_temp": "入池温度",
    "temp_rise_range": "升温幅度",
    "distillation_temp": "馏酒温度"
}


def load_process_standards() -> Dict[str, Any]:
    """加载工艺标准配置"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    return None


def check_value_in_range(value: float, min_val: float = None, max_val: float = None) -> bool:
    """
    检查值是否在标准范围内
    
    Args:
        value: 待检查的值
        min_val: 最小值(None表示无下限)
        max_val: 最大值(None表示无上限)
    
    Returns:
        bool: True表示合格,False表示异常
    """
    if pd.isna(value):
        return True  # 空值视为合格(未测量)
    
    if min_val is not None and value < min_val:
        return False
    
    if max_val is not None and value > max_val:
        return False
    
    return True


def analyze_single_indicator(
    df: pd.DataFrame,
    direction: str,
    indicator: str,
    standards: Dict[str, Any]
) -> Dict[str, Any]:
    """
    分析单个指标的合格率
    
    Args:
        df: 数据DataFrame
        direction: 方向 (entry/exit)
        indicator: 指标名称 (moisture/alcohol/acidity/starch/sugar)
        standards: 工艺标准配置
    
    Returns:
        Dict: 包含分析结果的字典
    """
    # 获取该指标的标准
    std = standards[direction][indicator]
    
    if not std["enabled"]:
        return {
            "enabled": False,
            "total_count": 0,
            "qualified_count": 0,
            "abnormal_count": 0,
            "qualification_rate": 0.0
        }
    
    min_val = std["min"]
    max_val = std["max"]
    
    # 获取该指标对应的字段(上层和下层)
    fields = INDICATOR_FIELDS[direction][indicator]
    
    # 合并上下层数据进行分析
    all_values = []
    for field in fields:
        if field in df.columns:
            all_values.extend(df[field].dropna().tolist())
    
    if not all_values:
        return {
            "enabled": True,
            "total_count": 0,
            "qualified_count": 0,
            "abnormal_count": 0,
            "qualification_rate": 0.0,
            "min_standard": min_val,
            "max_standard": max_val
        }
    
    # 检查每个值是否合格
    total_count = len(all_values)
    qualified_count = sum(1 for v in all_values if check_value_in_range(v, min_val, max_val))
    abnormal_count = total_count - qualified_count
    qualification_rate = (qualified_count / total_count * 100) if total_count > 0 else 0.0
    
    return {
        "enabled": True,
        "total_count": total_count,
        "qualified_count": qualified_count,
        "abnormal_count": abnormal_count,
        "qualification_rate": qualification_rate,
        "min_standard": min_val,
        "max_standard": max_val
    }


def analyze_all_indicators(df: pd.DataFrame, standards: Dict[str, Any]) -> pd.DataFrame:
    """
    分析所有指标的合格率
    
    Args:
        df: 数据DataFrame
        standards: 工艺标准配置
    
    Returns:
        pd.DataFrame: 分析结果表格
    """
    results = []
    
    # 分析入池和出池指标
    for direction in ["entry", "exit"]:
        direction_name = "入池" if direction == "entry" else "出池"
        
        for indicator in ["moisture", "alcohol", "acidity", "starch", "sugar"]:
            indicator_name = INDICATOR_NAMES_CN[indicator]
            
            analysis = analyze_single_indicator(df, direction, indicator, standards)
            
            if analysis["enabled"]:
                # 格式化标准范围
                min_std = analysis.get("min_standard")
                max_std = analysis.get("max_standard")
                
                if min_std is not None and max_std is not None:
                    std_range = f"{min_std:.2f} ~ {max_std:.2f}"
                elif min_std is not None:
                    std_range = f"≥ {min_std:.2f}"
                elif max_std is not None:
                    std_range = f"≤ {max_std:.2f}"
                else:
                    std_range = "无限制"
                
                results.append({
                    "方向": direction_name,
                    "指标": indicator_name,
                    "标准范围": std_range,
                    "总测量次数": analysis["total_count"],
                    "合格次数": analysis["qualified_count"],
                    "异常次数": analysis["abnormal_count"],
                    "合格率(%)": round(analysis["qualification_rate"], 2)
                })
    
    # 分析温度指标
    if "temperature" in standards:
        for indicator in ["grains_entry_temp", "temp_rise_range", "distillation_temp"]:
            indicator_name = INDICATOR_NAMES_CN[indicator]
            
            analysis = analyze_single_indicator(df, "temperature", indicator, standards)
            
            if analysis["enabled"]:
                # 格式化标准范围
                min_std = analysis.get("min_standard")
                max_std = analysis.get("max_standard")
                
                if min_std is not None and max_std is not None:
                    std_range = f"{min_std:.2f} ~ {max_std:.2f}"
                elif min_std is not None:
                    std_range = f"≥ {min_std:.2f}"
                elif max_std is not None:
                    std_range = f"≤ {max_std:.2f}"
                else:
                    std_range = "无限制"
                
                results.append({
                    "方向": "温度",
                    "指标": indicator_name,
                    "标准范围": std_range,
                    "总测量次数": analysis["total_count"],
                    "合格次数": analysis["qualified_count"],
                    "异常次数": analysis["abnormal_count"],
                    "合格率(%)": round(analysis["qualification_rate"], 2)
                })
    
    return pd.DataFrame(results)


def get_abnormal_records(
    df: pd.DataFrame,
    direction: str,
    indicator: str,
    standards: Dict[str, Any]
) -> pd.DataFrame:
    """
    获取指定指标的异常记录
    
    Args:
        df: 数据DataFrame
        direction: 方向 (entry/exit)
        indicator: 指标名称
        standards: 工艺标准配置
    
    Returns:
        pd.DataFrame: 异常记录
    """
    std = standards[direction][indicator]
    
    if not std["enabled"]:
        return pd.DataFrame()
    
    min_val = std["min"]
    max_val = std["max"]
    
    # 获取该指标对应的字段
    fields = INDICATOR_FIELDS[direction][indicator]
    
    # 筛选异常记录
    abnormal_mask = pd.Series([False] * len(df))
    
    for field in fields:
        if field in df.columns:
            field_abnormal = ~df[field].apply(lambda x: check_value_in_range(x, min_val, max_val))
            abnormal_mask = abnormal_mask | field_abnormal
    
    abnormal_df = df[abnormal_mask].copy()
    
    # 只保留相关列
    keep_columns = ['production_date', 'round_number', 'pit_no', 'workshop', 'team_name']
    keep_columns.extend([f for f in fields if f in df.columns])
    
    existing_columns = [col for col in keep_columns if col in abnormal_df.columns]
    
    return abnormal_df[existing_columns]


def calculate_qualification_summary(df: pd.DataFrame, standards: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算整体合格率汇总
    
    Args:
        df: 数据DataFrame
        standards: 工艺标准配置
    
    Returns:
        Dict: 汇总统计
    """
    total_measurements = 0
    total_qualified = 0
    total_abnormal = 0
    
    # 统计入池和出池指标
    for direction in ["entry", "exit"]:
        for indicator in ["moisture", "alcohol", "acidity", "starch", "sugar"]:
            analysis = analyze_single_indicator(df, direction, indicator, standards)
            
            if analysis["enabled"]:
                total_measurements += analysis["total_count"]
                total_qualified += analysis["qualified_count"]
                total_abnormal += analysis["abnormal_count"]
    
    # 统计温度指标
    if "temperature" in standards:
        for indicator in ["grains_entry_temp", "temp_rise_range", "distillation_temp"]:
            analysis = analyze_single_indicator(df, "temperature", indicator, standards)
            
            if analysis["enabled"]:
                total_measurements += analysis["total_count"]
                total_qualified += analysis["qualified_count"]
                total_abnormal += analysis["abnormal_count"]
    
    overall_rate = (total_qualified / total_measurements * 100) if total_measurements > 0 else 0.0
    
    return {
        "total_measurements": total_measurements,
        "total_qualified": total_qualified,
        "total_abnormal": total_abnormal,
        "overall_qualification_rate": round(overall_rate, 2)
    }
