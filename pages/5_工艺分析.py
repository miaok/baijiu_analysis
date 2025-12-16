"""
工艺分析页面
基于工艺标准进行异常检测和合格率分析
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from utils.db_utils import (
    get_physicochemical_data, 
    get_temperature_data,
    get_filter_options
)
from utils.filter_utils import validate_filter_conditions, build_filter_summary
from utils.filter_components import render_filter_ui
from utils.column_config import PHYSICOCHEMICAL_COLUMNS_CN
from utils.process_analysis import (
    load_process_standards,
    analyze_all_indicators,
    get_abnormal_records,
    calculate_qualification_summary,
    INDICATOR_NAMES_CN
)

# 页面配置
st.set_page_config(
    page_title="工艺分析",
    page_icon="📊",
    layout="wide"
)

# 侧边栏标题
with st.sidebar:
    st.markdown("# 📊 工艺分析")
    #st.markdown("---")

# 主标题
# st.title("📊 工艺分析")

# 检查工艺标准是否已设置
standards = load_process_standards()

if standards is None:
    st.warning("⚠️ 尚未设置工艺标准,请先前往 **工艺标准设置** 页面进行配置。")
    st.info("💡 在侧边栏选择 **⚙️ 标准设置** 页面来定义理化指标的标准范围。")
    st.stop()

# 初始化session state
if 'filter_applied' not in st.session_state:
    st.session_state.filter_applied = True

# 获取筛选选项
try:
    filter_options = get_filter_options()
except Exception as e:
    st.error(f"❌ 加载筛选选项失败: {str(e)}")
    st.stop()

# 渲染筛选UI
with st.container():
    filters, submit_button = render_filter_ui(filter_options)

# 应用筛选并加载数据
if submit_button or st.session_state.filter_applied:
    validated_filters = validate_filter_conditions(filters)
    st.session_state.filter_applied = True
    
    # 加载数据
    with st.spinner("正在加载数据..."):
        try:
            # 加载理化数据
            df_phys = get_physicochemical_data(validated_filters if validated_filters else None)
            
            # 加载温度数据
            df_temp = get_temperature_data(validated_filters if validated_filters else None)
            
            # 合并数据(基于map_id)
            if not df_phys.empty and not df_temp.empty:
                df = pd.merge(
                    df_phys, 
                    df_temp[['map_id', 'grains_entry_temp', 'temp_rise_range', 'distillation_temp']], 
                    on='map_id', 
                    how='left'
                )
            elif not df_phys.empty:
                df = df_phys
            else:
                df = pd.DataFrame()
            
            if df.empty:
                st.warning("⚠️ 没有符合条件的数据,请调整筛选条件")
            else:
                # 在侧边栏显示筛选摘要
                with st.sidebar:
                    st.markdown("### 📋 当前筛选条件")
                    filter_summary = build_filter_summary(validated_filters)
                    st.info(filter_summary)
                    
                    #st.markdown("---")
                    st.markdown("### 📈 数据概览")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("总记录数", f"{len(df):,}")
                    with col2:
                        unique_pits = df['pit_no'].nunique()
                        st.metric("窖池数", f"{unique_pits}")
                
                # ==================== 整体合格率概览 ====================
                #st.markdown("---")
                st.markdown("### 📈 整体合格率概览")
                
                summary = calculate_qualification_summary(df, standards)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "总测量次数",
                        f"{summary['total_measurements']:,}",
                        help="所有启用指标的测量总次数"
                    )
                
                with col2:
                    st.metric(
                        "合格次数",
                        f"{summary['total_qualified']:,}",
                        help="符合工艺标准的测量次数"
                    )
                
                with col3:
                    st.metric(
                        "异常次数",
                        f"{summary['total_abnormal']:,}",
                        delta=f"-{summary['total_abnormal']}",
                        delta_color="inverse",
                        help="超出工艺标准的测量次数"
                    )
                
                with col4:
                    rate = summary['overall_qualification_rate']
                    st.metric(
                        "整体合格率",
                        f"{rate:.2f}%",
                        delta=f"{rate - 100:.2f}%",
                        delta_color="normal",
                        help="所有指标的综合合格率"
                    )
                
                # ==================== 各指标合格率分析 ====================
                #st.markdown("---")
                st.markdown("### 📊 各指标合格率分析")
                
                analysis_df = analyze_all_indicators(df, standards)
                
                if not analysis_df.empty:
                    # 使用颜色标记合格率
                    def highlight_qualification_rate(val):
                        if isinstance(val, (int, float)):
                            if val >= 95:
                                return 'background-color: #d4edda'  # 绿色
                            elif val >= 85:
                                return 'background-color: #fff3cd'  # 黄色
                            else:
                                return 'background-color: #f8d7da'  # 红色
                        return ''
                    
                    styled_df = analysis_df.style.applymap(
                        highlight_qualification_rate,
                        subset=['合格率(%)']
                    ).format({
                        '合格率(%)': '{:.2f}%'
                    })
                    
                    st.dataframe(
                        styled_df,
                        use_container_width=True,
                        height=400
                    )
                    
                    # 导出分析结果
                    col_export1, col_export2, col_export3 = st.columns([1, 1, 2])
                    
                    with col_export1:
                        csv = analysis_df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📥 导出分析结果 (CSV)",
                            data=csv,
                            file_name=f"工艺分析_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    with col_export2:
                        from io import BytesIO
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            analysis_df.to_excel(writer, index=False, sheet_name='工艺分析')
                        output.seek(0)
                        
                        st.download_button(
                            label="📥 导出分析结果 (Excel)",
                            data=output,
                            file_name=f"工艺分析_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.info("ℹ️ 没有启用的指标或没有数据")
                
                # ==================== 异常记录查询 ====================
                #st.markdown("---")
                st.markdown("### 🔍 异常记录查询")
                
                # 选择器区域 - 放在expander外部
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    direction_option = st.selectbox(
                        "选择方向",
                        ["入池", "出池", "温度"],
                        key="abnormal_direction"
                    )
                    if direction_option == "温度":
                        direction_key = "temperature"
                    else:
                        direction_key = "entry" if direction_option == "入池" else "exit"
                
                with col2:
                    # 获取已启用的指标
                    if direction_key == "temperature":
                        enabled_indicators = [
                            INDICATOR_NAMES_CN[ind]
                            for ind in ["grains_entry_temp", "temp_rise_range", "distillation_temp"]
                            if "temperature" in standards and standards["temperature"][ind]["enabled"]
                        ]
                    else:
                        enabled_indicators = [
                            INDICATOR_NAMES_CN[ind]
                            for ind in ["moisture", "alcohol", "acidity", "starch", "sugar"]
                            if standards[direction_key][ind]["enabled"]
                        ]
                    
                    if enabled_indicators:
                        indicator_option = st.selectbox(
                            "选择指标",
                            enabled_indicators,
                            key="abnormal_indicator"
                        )
                    else:
                        st.warning("⚠️ 该方向没有启用的指标")
                        indicator_option = None
                
                # 查询按钮
                with col3:
                    st.write("")  # 占位,对齐按钮
                    st.write("")
                    query_button = st.button("🔍 查询异常记录", type="primary", use_container_width=True)
                
                # 结果显示区域 - 扩展至整个区域
                if indicator_option and (query_button or st.session_state.get('show_abnormal_records', False)):
                    st.session_state.show_abnormal_records = True
                    
                    # 反向查找指标key
                    indicator_key = None
                    for k, v in INDICATOR_NAMES_CN.items():
                        if v == indicator_option:
                            indicator_key = k
                            break
                    
                    if indicator_key:
                        abnormal_df = get_abnormal_records(df, direction_key, indicator_key, standards)
                        
                        #st.markdown("---")
                        
                        if not abnormal_df.empty:
                            st.markdown(f"#### 📋 异常记录: {direction_option}{indicator_option}")
                            
                            # 显示统计信息
                            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                            with col_stat1:
                                st.metric("异常记录数", f"{len(abnormal_df):,}")
                            with col_stat2:
                                unique_rounds = abnormal_df['round_number'].nunique() if 'round_number' in abnormal_df.columns else 0
                                st.metric("涉及轮次", f"{unique_rounds}")
                            with col_stat3:
                                unique_pits = abnormal_df['pit_no'].nunique() if 'pit_no' in abnormal_df.columns else 0
                                st.metric("涉及窖池", f"{unique_pits}")
                            with col_stat4:
                                # 获取标准范围
                                std = standards[direction_key][indicator_key]
                                min_val = std.get("min")
                                max_val = std.get("max")
                                if min_val is not None and max_val is not None:
                                    std_range = f"{min_val:.1f}~{max_val:.1f}"
                                elif min_val is not None:
                                    std_range = f"≥{min_val:.1f}"
                                elif max_val is not None:
                                    std_range = f"≤{max_val:.1f}"
                                else:
                                    std_range = "无限制"
                                st.metric("标准范围", std_range)
                            
                            st.markdown("")
                            
                            # 重命名列为中文
                            display_abnormal = abnormal_df.copy()
                            display_abnormal.rename(columns=PHYSICOCHEMICAL_COLUMNS_CN, inplace=True)
                            
                            # 扩展至整个区域的表格
                            st.dataframe(
                                display_abnormal,
                                use_container_width=True,
                                height=500,
                                hide_index=True
                            )
                            
                            # 导出按钮
                            col_export1, col_export2, col_export3 = st.columns([1, 1, 2])
                            with col_export1:
                                csv_abnormal = display_abnormal.to_csv(index=False, encoding='utf-8-sig')
                                st.download_button(
                                    label="📥 导出异常记录 (CSV)",
                                    data=csv_abnormal,
                                    file_name=f"异常记录_{direction_option}{indicator_option}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv"
                                )
                            
                            with col_export2:
                                from io import BytesIO
                                output = BytesIO()
                                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                    display_abnormal.to_excel(writer, index=False, sheet_name='异常记录')
                                output.seek(0)
                                
                                st.download_button(
                                    label="📥 导出异常记录 (Excel)",
                                    data=output,
                                    file_name=f"异常记录_{direction_option}{indicator_option}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                        else:
                            st.success(f"✅ {direction_option}{indicator_option} 没有异常记录!")
                
        except Exception as e:
            st.error(f"❌ 加载数据失败: {str(e)}")
            import traceback
            with st.expander("查看错误详情"):
                st.code(traceback.format_exc())
