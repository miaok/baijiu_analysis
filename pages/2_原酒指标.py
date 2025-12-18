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

# 初始化session state
if 'filter_applied' not in st.session_state:
    st.session_state.filter_applied = True  # 默认加载所有数据

# 获取筛选选项
try:
    filter_options = get_filter_options()
except Exception as e:
    st.error(f"❌ 加载筛选选项失败: {str(e)}")
    st.stop()

# 在侧边栏渲染筛选UI组件
with st.sidebar:
    filters, submit_button = render_filter_ui(filter_options, sidebar=True)

# 创建主内容区域的占位符
main_placeholder = st.empty()

# ==================== 应用筛选并加载数据 ====================
if submit_button or st.session_state.filter_applied:
    # 验证筛选条件（filters已经由render_filter_ui返回）
    validated_filters = validate_filter_conditions(filters)

    # 标记筛选已应用
    st.session_state.filter_applied = True
    
    # 加载数据
    with st.spinner("正在加载数据..."):
        try:
            df = get_liquor_output_data(validated_filters if validated_filters else None)
            
            # 使用占位符渲染内容
            with main_placeholder.container():
                if df.empty:
                    st.warning("⚠️ 没有符合条件的数据，请调整筛选条件")
                else:
                    # 数据表格展示(主区域)
                    st.markdown("---")
                    st.subheader("📊 原酒指标分析")
                    
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
                  
                    # 汇总维度和统计方法选择
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1.5])
                    
                    with col1:
                        # 主要汇总维度
                        primary_dimension = st.selectbox(
                            "主要汇总维度",
                            ["车间", "班组", "窖池", "轮次", "段次"],
                            key="primary_dimension"
                        )
                    
                    with col2:
                        # 次要汇总维度(可选) - 动态排除主要维度
                        available_secondary = ["无"] + [d for d in ["车间", "班组", "窖池", "轮次", "段次"] if d != primary_dimension]
                        secondary_dimension = st.selectbox(
                            "次要汇总维度(可选)",
                            available_secondary,
                            key="secondary_dimension"
                        )
                    
                    with col3:
                        # 统计方法（添加记录次数）
                        agg_method = st.selectbox(
                            "统计方法",
                            ["平均值", "最大值", "最小值", "中位数", "标准差", "总和", "记录次数"],
                            key="agg_method"
                        )
                    
                    with col4:
                        # 显示全部统计指标
                        show_all_stats = st.checkbox(
                            "显示全部统计指标", 
                            value=False, 
                            key="show_all_stats_liquor",
                            help="显示所有统计指标(平均值、最大值、最小值等)"
                        )
                    
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
                        "总和": "sum",
                        "记录次数": "count"
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
                            
                            # 计算己酸乙酯加权平均所需的辅助列
                            if 'quantity_kg' in df_temp.columns and 'ethyl_hexanoate' in df_temp.columns:
                                df_temp['ethyl_weighted'] = df_temp['quantity_kg'] * df_temp['ethyl_hexanoate']
                            
                            if show_all_stats:
                                # 显示全部统计指标
                                agg_dict = {
                                    'quantity_kg': ['sum', 'mean', 'max', 'min', 'median', 'std', 'count'],
                                    'ethyl_hexanoate': ['max', 'min', 'median', 'std'],
                                    'ethyl_weighted': ['sum']  # 用于计算加权平均
                                }
                                
                                agg_df = df_temp.groupby(existing_group_fields).agg(agg_dict).reset_index()
                                
                                # 扁平化多级列名
                                agg_df.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                                                 for col in agg_df.columns.values]
                                
                                # 计算加权平均己酸乙酯
                                if 'ethyl_weighted_sum' in agg_df.columns and 'quantity_kg_sum' in agg_df.columns:
                                    agg_df['ethyl_hexanoate_weighted_mean'] = (
                                        agg_df['ethyl_weighted_sum'] / agg_df['quantity_kg_sum']
                                    )
                                    # 删除辅助列
                                    agg_df.drop(columns=['ethyl_weighted_sum'], inplace=True)
                                
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
                                        if 'weighted_mean' in col:
                                            rename_dict[col] = "己酸乙酯_加权平均(g/L)"
                                        else:
                                            stat = col.split('_')[-1]
                                            stat_cn = {
                                                'max': '最大值', 'min': '最小值',
                                                'median': '中位数', 'std': '标准差'
                                            }.get(stat, stat)
                                            rename_dict[col] = f"己酸乙酯_{stat_cn}(g/L)"
                                
                                display_df = agg_df.rename(columns=rename_dict)
                                
                            else:
                                # 单一统计方法
                                selected_method = method_map[agg_method]
                                
                                # 根据选择的统计方法构建聚合字典
                                if selected_method == 'count':
                                    # 记录次数：只统计记录数
                                    agg_dict = {
                                        'production_date': 'count'
                                    }
                                elif selected_method == 'mean':
                                    # 平均值：产量用平均，己酸乙酯用加权平均
                                    agg_dict = {
                                        'quantity_kg': 'mean',
                                        'ethyl_weighted': 'sum',
                                        'quantity_kg_for_weight': 'sum'  # 用于计算加权平均的分母
                                    }
                                    # 添加一个用于加权平均分母的列
                                    df_temp['quantity_kg_for_weight'] = df_temp['quantity_kg']
                                elif selected_method in ['max', 'min', 'median', 'std']:
                                    agg_dict = {
                                        'quantity_kg': selected_method,
                                        'ethyl_hexanoate': selected_method
                                    }
                                else:  # sum
                                    # 总和：产量求和，己酸乙酯用加权平均
                                    agg_dict = {
                                        'quantity_kg': 'sum',
                                        'ethyl_weighted': 'sum'
                                    }
                                
                                agg_df = df_temp.groupby(existing_group_fields).agg(agg_dict).reset_index()
                                
                                # 如果是平均值或总和，计算加权平均己酸乙酯
                                if selected_method == 'mean':
                                    if 'ethyl_weighted' in agg_df.columns and 'quantity_kg_for_weight' in agg_df.columns:
                                        agg_df['ethyl_hexanoate'] = agg_df['ethyl_weighted'] / agg_df['quantity_kg_for_weight']
                                        agg_df.drop(columns=['ethyl_weighted', 'quantity_kg_for_weight'], inplace=True)
                                elif selected_method == 'sum':
                                    if 'ethyl_weighted' in agg_df.columns and 'quantity_kg' in agg_df.columns:
                                        agg_df['ethyl_hexanoate'] = agg_df['ethyl_weighted'] / agg_df['quantity_kg']
                                        agg_df.drop(columns=['ethyl_weighted'], inplace=True)
                                
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
                                        if selected_method in ['mean', 'sum']:
                                            rename_dict[col] = "己酸乙酯_加权平均(g/L)"
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
                                
                                # 格式化数值列：平均值和标准差保留两位小数
                                for col in display_df.columns:
                                    if ('平均值' in col or '标准差' in col or '加权平均' in col) and ('产量' in col or '己酸乙酯' in col):
                                        display_df[col] = display_df[col].round(2)
                        
                        except Exception as e:
                            st.error(f"汇总数据失败: {str(e)}")
                            display_df = pd.DataFrame()
                    
                else:  # 完整数据
                    # 数据筛选选项
                    col_filter1, col_filter2, col_filter3 = st.columns(3)
                    
                    with col_filter1:
                        # 段次筛选
                        segment_filter = st.selectbox(
                            "段次筛选",
                            ["全部", "一段", "二段"],
                            key="segment_filter",
                            help="选择要显示的段次数据"
                        )
                    
                    with col_filter2:
                        # 获取产量范围
                        if 'quantity_kg' in df.columns:
                            min_quantity = float(df['quantity_kg'].min())
                            max_quantity = float(df['quantity_kg'].max())
                            
                            # 产量范围筛选（使用滑块）
                            quantity_range = st.slider(
                                "产量范围筛选 (kg)",
                                min_value=min_quantity,
                                max_value=max_quantity,
                                value=(min_quantity, max_quantity),
                                step=1.0,
                                key="quantity_range_slider",
                                help="拖动滑块选择产量范围"
                            )
                        else:
                            quantity_range = None
                    
                    with col_filter3:
                        # 获取己酸乙酯范围
                        if 'ethyl_hexanoate' in df.columns:
                            min_ethyl = float(df['ethyl_hexanoate'].min())
                            max_ethyl = float(df['ethyl_hexanoate'].max())
                            
                            # 己酸乙酯范围筛选（使用滑块）
                            ethyl_range = st.slider(
                                "己酸乙酯范围筛选 (g/L)",
                                min_value=min_ethyl,
                                max_value=max_ethyl,
                                value=(min_ethyl, max_ethyl),
                                step=0.01,
                                key="ethyl_range_slider",
                                help="拖动滑块选择己酸乙酯范围"
                            )
                        else:
                            ethyl_range = None
                    
                    # 应用筛选条件
                    filtered_df = df.copy()
                    
                    # 应用段次筛选
                    if segment_filter != "全部":
                        if 'segment_name' in filtered_df.columns:
                            filtered_df = filtered_df[filtered_df['segment_name'] == segment_filter]
                    
                    # 应用产量范围筛选
                    if quantity_range is not None and 'quantity_kg' in filtered_df.columns:
                        filtered_df = filtered_df[
                            (filtered_df['quantity_kg'] >= quantity_range[0]) & 
                            (filtered_df['quantity_kg'] <= quantity_range[1])
                        ]
                    
                    # 应用己酸乙酯范围筛选
                    if ethyl_range is not None and 'ethyl_hexanoate' in filtered_df.columns:
                        filtered_df = filtered_df[
                            (filtered_df['ethyl_hexanoate'] >= ethyl_range[0]) & 
                            (filtered_df['ethyl_hexanoate'] <= ethyl_range[1])
                        ]
                    
                    # 核心列的英文名（调整顺序：生产日期、班组、轮次、窖池、段次、产量、己酸乙酯）
                    core_columns_en = ['production_date', 'team_name', 'round_number', 'pit_no', 'segment_name', 'quantity_kg', 'ethyl_hexanoate']
                    display_columns_en = [col for col in core_columns_en if col in filtered_df.columns]
                    
                    # 选择列并翻译
                    display_df = filtered_df[display_columns_en].copy()
                    display_df.rename(columns=column_names_cn, inplace=True)
                
                # 显示数据表格（使用中文列名）
                if not display_df.empty:
                    st.dataframe(
                        display_df,
                        use_container_width=True,
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
