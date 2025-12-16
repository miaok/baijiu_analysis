"""
原酒指标分析页面
提供多维度筛选和数据展示功能
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
from io import BytesIO

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from utils.db_utils import (
    get_liquor_output_data, 
    get_filter_options
)
from utils.filter_utils import (
    validate_filter_conditions,
    build_filter_summary
)
from utils.filter_components import render_filter_ui
from utils.column_config import (
    LIQUOR_OUTPUT_COLUMNS_CN,
    DEFAULT_HIDDEN_COLUMNS,
    CORE_DISPLAY_COLUMNS
)


# 页面配置
st.set_page_config(
    page_title="原酒指标分析",
    page_icon="🍶",
    layout="wide"
)

# 侧边栏标题
with st.sidebar:
    st.markdown("# 🍶 原酒指标分析")
    st.markdown("---")

# 初始化session state
if 'liquor_filter_applied' not in st.session_state:
    st.session_state.liquor_filter_applied = True  # 默认加载所有数据

# 获取筛选选项
try:
    filter_options = get_filter_options()
except Exception as e:
    st.error(f"❌ 加载筛选选项失败: {str(e)}")
    st.stop()

with st.container():
    # 渲染筛选UI组件并获取筛选条件
    filters, submit_button = render_filter_ui(filter_options)

# ==================== 应用筛选并加载数据 ====================
if submit_button or st.session_state.liquor_filter_applied:
    # 验证筛选条件（filters已经由render_filter_ui返回）
    validated_filters = validate_filter_conditions(filters)

    # 标记筛选已应用
    st.session_state.liquor_filter_applied = True
    
    # 加载数据
    with st.spinner("正在加载数据..."):
        try:
            df = get_liquor_output_data(validated_filters if validated_filters else None)
            
            if df.empty:
                st.warning("⚠️ 没有符合条件的数据，请调整筛选条件")
            else:
                # 在侧边栏显示筛选摘要和数据概览
                with st.sidebar:
                    st.markdown("### 📋 当前筛选条件")
                    filter_summary = build_filter_summary(validated_filters)
                    st.info(filter_summary)
                    
                    st.markdown("---")
                    st.markdown("### 📈 数据概览")
                    
                    # 2x2 布局显示数据概览
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("总记录数", f"{len(df):,}")
                    with col2:
                        unique_rounds = df['round_number'].nunique()
                        st.metric("轮次", f"{unique_rounds}")
                    
                    col3, col4 = st.columns(2)
                    with col3:
                        unique_pits = df['pit_no'].nunique()
                        st.metric("窖池", f"{unique_pits}")
                    with col4:
                        unique_dates = df['production_date'].nunique()
                        st.metric("日期", f"{unique_dates}")
                    
                    # 统计数据
                    st.markdown("---")
                    st.markdown("### 📊 统计信息")
                    
                    # 总产量统计
                    total_quantity = df['quantity_kg'].sum()
                    st.metric("总产量(Kg)", f"{total_quantity:,.0f}" if pd.notna(total_quantity) else "无数据")
                    
                    # 加权平均己酸乙酯
                    weighted_sum = (df['quantity_kg'] * df['ethyl_hexanoate']).sum()
                    total_qty = df['quantity_kg'].sum()
                    avg_ethyl = weighted_sum / total_qty if total_qty > 0 else 0
                    st.metric("平均己酸乙酯(g/L)", f"{avg_ethyl:.2f}" if pd.notna(avg_ethyl) and avg_ethyl > 0 else "无数据")


                
                # 数据表格展示(主区域)
                st.markdown("---")
                st.subheader("📊 原酒产出数据")
                
                # 选择显示模式
                display_mode = st.radio(
                    "选择显示模式",
                    ["完整数据", "数据汇总"],
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                # 使用配置文件中的列名映射
                column_names_cn = LIQUOR_OUTPUT_COLUMNS_CN
                
                # 根据显示模式处理数据
                if display_mode == "数据汇总":
                    # ==================== 数据汇总模式 ====================
                    st.markdown("### 📊 数据汇总分析")
                    
                    # 汇总维度和统计方法选择
                    col1, col2, col3 = st.columns([2, 2, 2])
                    
                    with col1:
                        # 主要汇总维度
                        primary_dimension = st.selectbox(
                            "主要汇总维度",
                            ["车间", "班组", "窖池", "轮次", "段次"],
                            key="primary_dimension"
                        )
                    
                    with col2:
                        # 次要汇总维度(可选)
                        secondary_dimension = st.selectbox(
                            "次要汇总维度(可选)",
                            ["无", "车间", "班组", "窖池", "轮次", "段次"],
                            key="secondary_dimension"
                        )
                    
                    with col3:
                        # 统计方法
                        agg_method = st.selectbox(
                            "统计方法",
                            ["平均值", "最大值", "最小值", "中位数", "标准差", "总和"],
                            key="agg_method"
                        )
                    
                    # 高级选项
                    with st.expander("🔧 高级选项", expanded=False):
                        show_count = st.checkbox("显示记录次数", value=True, key="show_count")
                        show_all_stats = st.checkbox("显示全部统计指标", value=False, key="show_all_stats_liquor")
                    
                    # 维度映射
                    dimension_map = {
                        "车间": "workshop",
                        "班组": "team_name",
                        "窖池": "pit_no",
                        "轮次": "round_number",
                        "段次": "segment_name"
                    }
                    
                    # 统计方法映射
                    method_map = {
                        "平均值": "mean",
                        "最大值": "max",
                        "最小值": "min",
                        "中位数": "median",
                        "标准差": "std",
                        "总和": "sum"
                    }
                    
                    # 构建分组字段列表
                    group_by_fields = [dimension_map[primary_dimension]]
                    if secondary_dimension != "无":
                        group_by_fields.append(dimension_map[secondary_dimension])
                    
                    # 检查字段是否存在
                    existing_group_fields = [f for f in group_by_fields if f in df.columns]
                    
                    if not existing_group_fields:
                        st.warning("⚠️ 选择的汇总维度在当前数据中不存在")
                        display_df = pd.DataFrame()
                    else:
                        try:
                            # 准备数据
                            df_temp = df.copy()
                            
                            # 对于产量,总是使用sum
                            # 对于己酸乙酯,使用加权平均
                            if show_all_stats:
                                # 显示全部统计指标
                                agg_dict = {
                                    'quantity_kg': ['sum', 'mean', 'max', 'min', 'median', 'std', 'count'],
                                    'ethyl_hexanoate': ['mean', 'max', 'min', 'median', 'std']
                                }
                                
                                agg_df = df_temp.groupby(existing_group_fields).agg(agg_dict).reset_index()
                                
                                # 扁平化多级列名
                                agg_df.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                                                 for col in agg_df.columns.values]
                                
                                # 重命名列为中文
                                rename_dict = {}
                                for col in agg_df.columns:
                                    if col in existing_group_fields:
                                        # 维度列
                                        for cn, en in dimension_map.items():
                                            if en == col:
                                                rename_dict[col] = cn
                                                break
                                    elif 'quantity_kg' in col:
                                        stat = col.split('_')[-1]
                                        stat_cn = {
                                            'sum': '总和', 'mean': '平均值', 'max': '最大值',
                                            'min': '最小值', 'median': '中位数', 'std': '标准差', 'count': '次数'
                                        }.get(stat, stat)
                                        rename_dict[col] = f"产量_{stat_cn}(Kg)"
                                    elif 'ethyl_hexanoate' in col:
                                        stat = col.split('_')[-1]
                                        stat_cn = {
                                            'mean': '平均值', 'max': '最大值', 'min': '最小值',
                                            'median': '中位数', 'std': '标准差'
                                        }.get(stat, stat)
                                        rename_dict[col] = f"己酸乙酯_{stat_cn}(g/L)"
                                
                                display_df = agg_df.rename(columns=rename_dict)
                                
                            else:
                                # 单一统计方法
                                selected_method = method_map[agg_method]
                                
                                # 对于产量,特殊处理
                                if selected_method in ['mean', 'max', 'min', 'median', 'std']:
                                    agg_dict = {
                                        'quantity_kg': selected_method,
                                        'ethyl_hexanoate': selected_method
                                    }
                                else:  # sum
                                    agg_dict = {
                                        'quantity_kg': 'sum',
                                        'ethyl_hexanoate': 'mean'  # 己酸乙酯用平均值
                                    }
                                
                                if show_count:
                                    agg_dict['production_date'] = 'count'
                                
                                agg_df = df_temp.groupby(existing_group_fields).agg(agg_dict).reset_index()
                                
                                # 重命名列
                                rename_dict = {}
                                for col in agg_df.columns:
                                    if col in existing_group_fields:
                                        # 维度列
                                        for cn, en in dimension_map.items():
                                            if en == col:
                                                rename_dict[col] = cn
                                                break
                                    elif col == 'quantity_kg':
                                        rename_dict[col] = f"产量_{agg_method}(Kg)"
                                    elif col == 'ethyl_hexanoate':
                                        if selected_method == 'sum':
                                            rename_dict[col] = "己酸乙酯_平均值(g/L)"
                                        else:
                                            rename_dict[col] = f"己酸乙酯_{agg_method}(g/L)"
                                    elif col == 'production_date':
                                        rename_dict[col] = "记录次数"
                                
                                display_df = agg_df.rename(columns=rename_dict)
                            
                            # 排序
                            if not display_df.empty:
                                # 按第一个维度排序
                                first_dim_cn = None
                                for cn, en in dimension_map.items():
                                    if en == existing_group_fields[0]:
                                        first_dim_cn = cn
                                        break
                                if first_dim_cn and first_dim_cn in display_df.columns:
                                    display_df = display_df.sort_values(first_dim_cn)
                        
                        except Exception as e:
                            st.error(f"汇总数据失败: {str(e)}")
                            display_df = pd.DataFrame()
                    
                else:  # 完整数据
                    # 在完整数据模式下，提供额外列的显示选项
                    optional_columns_en = ['fiscal_year', 'work_year', 'workshop', 'team_name']
                    optional_columns_cn = [column_names_cn.get(col, col) for col in optional_columns_en if col in df.columns]
                    
                    show_extra_cols = []
                    if optional_columns_cn:
                        # 添加列显示控制选项
                        with st.expander("⚙️ 显示额外列", expanded=False):
                            show_extra_cols = st.multiselect(
                                "选择要显示的额外列",
                                options=optional_columns_cn,
                                default=[],  # 默认不显示任何额外列
                                help="这些列默认隐藏，可根据需要选择显示",
                                key="complete_extra_cols"
                            )
                    
                    # 先确定要显示的英文列名
                    # 核心列的英文名
                    core_columns_en = ['production_date', 'round_number', 'pit_no', 'segment_name', 'quantity_kg', 'ethyl_hexanoate']
                    display_columns_en = [col for col in core_columns_en if col in df.columns]
                    
                    # 添加用户选择的可选列（转换回英文）
                    if show_extra_cols:
                        cn_to_en = {v: k for k, v in column_names_cn.items()}
                        for cn_col in show_extra_cols:
                            en_col = cn_to_en.get(cn_col)
                            if en_col and en_col in df.columns and en_col not in display_columns_en:
                                display_columns_en.append(en_col)
                    
                    # 选择列并翻译
                    display_df = df[display_columns_en].copy()
                    display_df.rename(columns=column_names_cn, inplace=True)

                
                # 显示数据表格（使用中文列名）
                if not display_df.empty:
                    st.dataframe(
                        display_df,
                        width='stretch',
                        height=500,
                        hide_index=True
                    )
                    
                    # 数据导出
                    st.markdown("---")
                    col_export1, col_export2, col_export3 = st.columns([1, 1, 2])
                    
                    with col_export1:
                        # 导出为CSV（使用中文列名）
                        csv = display_df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📥 导出为 CSV",
                            data=csv,
                            file_name=f"原酒指标_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            width='stretch'
                        )
                    
                    with col_export2:
                        # 导出为Excel（使用中文列名）
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            display_df.to_excel(writer, index=False, sheet_name='原酒指标')
                        output.seek(0)
                        
                        st.download_button(
                            label="📥 导出为 Excel",
                            data=output,
                            file_name=f"原酒指标_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            width='stretch'
                        )
                
        except Exception as e:
            st.error(f"❌ 加载数据失败: {str(e)}")
            import traceback
            with st.expander("查看错误详情"):
                st.code(traceback.format_exc())
