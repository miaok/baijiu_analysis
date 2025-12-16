"""
工艺标准设置页面
用于定义理化指标的工艺标准范围
"""

import streamlit as st
import json
import os
from pathlib import Path
from typing import Dict, Any

# 页面配置
st.set_page_config(
    page_title="工艺标准设置",
    page_icon="⚙️",
    layout="wide"
)

# 侧边栏标题
with st.sidebar:
    st.markdown("# ⚙️ 工艺标准设置")
    st.markdown("---")
    st.info("💡 在此页面设置理化指标的工艺标准范围，用于后续的工艺分析和异常检测。")

# 配置文件路径
CONFIG_DIR = Path("config")
CONFIG_FILE = CONFIG_DIR / "process_standards.json"

# 确保配置目录存在
CONFIG_DIR.mkdir(exist_ok=True)

# 默认工艺标准配置
DEFAULT_STANDARDS = {
    "entry": {
        "moisture": {"min": 50.0, "max": 56.0, "enabled": True},
        "alcohol": {"min": 1.5, "max": 3.0, "enabled": True},
        "acidity": {"min": 1.8, "max": 2.5, "enabled": True},
        "starch": {"min": 10.0, "max": 15.0, "enabled": True},
        "sugar": {"min": 0.5, "max": 1.2, "enabled": True}
    },
    "exit": {
        "moisture": {"min": 58.0, "max": 62.0, "enabled": True},
        "alcohol": {"min": None, "max": None, "enabled": False},
        "acidity": {"min": 2.5, "max": 3.5, "enabled": True},
        "starch": {"min": None, "max": 5.0, "enabled": True},
        "sugar": {"min": None, "max": 1.5, "enabled": True}
    },
    "temperature": {
        "grains_entry_temp": {"min": 25.0, "max": 30.0, "enabled": True},
        "temp_rise_range": {"min": 10.0, "max": 15.0, "enabled": True},
        "distillation_temp": {"min": 30.0, "max": 35.0, "enabled": True}
    }
}

# 指标中文名称映射
INDICATOR_NAMES = {
    "moisture": "水分",
    "alcohol": "酒分",
    "acidity": "酸度",
    "starch": "淀粉",
    "sugar": "还原糖"
}

TEMPERATURE_NAMES = {
    "grains_entry_temp": "入池温度",
    "temp_rise_range": "升温幅度",
    "distillation_temp": "馏酒温度"
}


def load_standards() -> Dict[str, Any]:
    """加载工艺标准配置"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"加载配置失败: {str(e)}")
            return DEFAULT_STANDARDS.copy()
    return DEFAULT_STANDARDS.copy()


def save_standards(standards: Dict[str, Any]) -> bool:
    """保存工艺标准配置"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(standards, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"保存配置失败: {str(e)}")
        return False


# 主标题
# st.title("⚙️ 工艺标准设置")
# st.markdown("---")

# 加载当前配置
if 'standards' not in st.session_state:
    st.session_state.standards = load_standards()

standards = st.session_state.standards

# 确保温度指标存在(向后兼容)
if "temperature" not in standards:
    standards["temperature"] = DEFAULT_STANDARDS["temperature"].copy()

# 创建三列布局
col_entry, col_exit, col_temp = st.columns(3)

# ==================== 入池指标设置 ====================
with col_entry:
    st.markdown("### 📥 入池指标标准")
    st.markdown("---")
    
    for indicator_key, indicator_name in INDICATOR_NAMES.items():
        with st.expander(f"**{indicator_name}**", expanded=True):
            # 启用/禁用开关
            enabled_key = f"entry_{indicator_key}_enabled"
            enabled = st.checkbox(
                "启用此指标",
                value=standards["entry"][indicator_key]["enabled"],
                key=enabled_key
            )
            standards["entry"][indicator_key]["enabled"] = enabled
            
            if enabled:
                col1, col2 = st.columns(2)
                
                with col1:
                    min_key = f"entry_{indicator_key}_min"
                    current_min = standards["entry"][indicator_key]["min"]
                    min_val = st.number_input(
                        "最小值",
                        value=current_min if current_min is not None else 0.0,
                        format="%.2f",
                        key=min_key,
                        help="留空表示不设下限"
                    )
                    # 如果用户清空了输入,设为None
                    if st.checkbox(f"不设下限entry_{indicator_key}", value=(current_min is None)):
                        standards["entry"][indicator_key]["min"] = None
                    else:
                        standards["entry"][indicator_key]["min"] = min_val
                
                with col2:
                    max_key = f"entry_{indicator_key}_max"
                    current_max = standards["entry"][indicator_key]["max"]
                    max_val = st.number_input(
                        "最大值",
                        value=current_max if current_max is not None else 100.0,
                        format="%.2f",
                        key=max_key,
                        help="留空表示不设上限"
                    )
                    # 如果用户清空了输入,设为None
                    if st.checkbox(f"不设上限entry_{indicator_key}", value=(current_max is None)):
                        standards["entry"][indicator_key]["max"] = None
                    else:
                        standards["entry"][indicator_key]["max"] = max_val
                
                # 显示当前标准范围
                min_display = standards["entry"][indicator_key]["min"]
                max_display = standards["entry"][indicator_key]["max"]
                
                if min_display is not None and max_display is not None:
                    st.info(f"✅ 标准范围: {min_display:.2f} ~ {max_display:.2f}")
                elif min_display is not None:
                    st.info(f"✅ 标准范围: ≥ {min_display:.2f}")
                elif max_display is not None:
                    st.info(f"✅ 标准范围: ≤ {max_display:.2f}")
                else:
                    st.warning("⚠️ 未设置任何限制")

# ==================== 出池指标设置 ====================
with col_exit:
    st.markdown("### 📤 出池指标标准")
    st.markdown("---")
    
    for indicator_key, indicator_name in INDICATOR_NAMES.items():
        with st.expander(f"**{indicator_name}**", expanded=True):
            # 启用/禁用开关
            enabled_key = f"exit_{indicator_key}_enabled"
            enabled = st.checkbox(
                "启用此指标",
                value=standards["exit"][indicator_key]["enabled"],
                key=enabled_key
            )
            standards["exit"][indicator_key]["enabled"] = enabled
            
            if enabled:
                col1, col2 = st.columns(2)
                
                with col1:
                    min_key = f"exit_{indicator_key}_min"
                    current_min = standards["exit"][indicator_key]["min"]
                    min_val = st.number_input(
                        "最小值",
                        value=current_min if current_min is not None else 0.0,
                        format="%.2f",
                        key=min_key,
                        help="留空表示不设下限"
                    )
                    # 如果用户清空了输入,设为None
                    if st.checkbox(f"不设下限##exit_{indicator_key}", value=(current_min is None)):
                        standards["exit"][indicator_key]["min"] = None
                    else:
                        standards["exit"][indicator_key]["min"] = min_val
                
                with col2:
                    max_key = f"exit_{indicator_key}_max"
                    current_max = standards["exit"][indicator_key]["max"]
                    max_val = st.number_input(
                        "最大值",
                        value=current_max if current_max is not None else 100.0,
                        format="%.2f",
                        key=max_key,
                        help="留空表示不设上限"
                    )
                    # 如果用户清空了输入,设为None
                    if st.checkbox(f"不设上限##exit_{indicator_key}", value=(current_max is None)):
                        standards["exit"][indicator_key]["max"] = None
                    else:
                        standards["exit"][indicator_key]["max"] = max_val
                
                # 显示当前标准范围
                min_display = standards["exit"][indicator_key]["min"]
                max_display = standards["exit"][indicator_key]["max"]
                
                if min_display is not None and max_display is not None:
                    st.info(f"✅ 标准范围: {min_display:.2f} ~ {max_display:.2f}")
                elif min_display is not None:
                    st.info(f"✅ 标准范围: ≥ {min_display:.2f}")
                elif max_display is not None:
                    st.info(f"✅ 标准范围: ≤ {max_display:.2f}")
                else:
                    st.warning("⚠️ 未设置任何限制")

# ==================== 温度指标设置 ====================
with col_temp:
    st.markdown("### 🌡️ 温度指标标准")
    st.markdown("---")
    
    for indicator_key, indicator_name in TEMPERATURE_NAMES.items():
        with st.expander(f"**{indicator_name}**", expanded=True):
            # 启用/禁用开关
            enabled_key = f"temp_{indicator_key}_enabled"
            enabled = st.checkbox(
                "启用此指标",
                value=standards["temperature"][indicator_key]["enabled"],
                key=enabled_key
            )
            standards["temperature"][indicator_key]["enabled"] = enabled
            
            if enabled:
                col1, col2 = st.columns(2)
                
                with col1:
                    min_key = f"temp_{indicator_key}_min"
                    current_min = standards["temperature"][indicator_key]["min"]
                    min_val = st.number_input(
                        "最小值",
                        value=current_min if current_min is not None else 0.0,
                        format="%.2f",
                        key=min_key,
                        help="留空表示不设下限"
                    )
                    # 如果用户清空了输入,设为None
                    if st.checkbox(f"不设下限temp_{indicator_key}", value=(current_min is None)):
                        standards["temperature"][indicator_key]["min"] = None
                    else:
                        standards["temperature"][indicator_key]["min"] = min_val
                
                with col2:
                    max_key = f"temp_{indicator_key}_max"
                    current_max = standards["temperature"][indicator_key]["max"]
                    max_val = st.number_input(
                        "最大值",
                        value=current_max if current_max is not None else 100.0,
                        format="%.2f",
                        key=max_key,
                        help="留空表示不设上限"
                    )
                    # 如果用户清空了输入,设为None
                    if st.checkbox(f"不设上限temp_{indicator_key}", value=(current_max is None)):
                        standards["temperature"][indicator_key]["max"] = None
                    else:
                        standards["temperature"][indicator_key]["max"] = max_val
                
                # 显示当前标准范围
                min_display = standards["temperature"][indicator_key]["min"]
                max_display = standards["temperature"][indicator_key]["max"]
                
                if min_display is not None and max_display is not None:
                    st.info(f"✅ 标准范围: {min_display:.2f} ~ {max_display:.2f}")
                elif min_display is not None:
                    st.info(f"✅ 标准范围: ≥ {min_display:.2f}")
                elif max_display is not None:
                    st.info(f"✅ 标准范围: ≤ {max_display:.2f}")
                else:
                    st.warning("⚠️ 未设置任何限制")

# ==================== 操作按钮 ====================
st.markdown("---")
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])

with col_btn1:
    if st.button("💾 保存设置", type="primary", use_container_width=True):
        if save_standards(standards):
            st.session_state.standards = standards
            st.success("✅ 设置已保存!")
            st.rerun()

with col_btn2:
    if st.button("🔄 重置为默认", use_container_width=True):
        st.session_state.standards = DEFAULT_STANDARDS.copy()
        st.info("已重置为默认设置,请点击保存按钮确认")
        st.rerun()

