"""
温度数据分析页面
提供多维度筛选、温度曲线图和工艺参数展示功能
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
from io import BytesIO
import plotly.graph_objects as go

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from utils.db_utils import (
    get_temperature_data,
    get_temperature_readings,
    get_filter_options
)
from utils.filter_utils import (
    validate_filter_conditions,
    build_filter_summary
)
from utils.filter_components import render_filter_ui
from utils.column_config import (
    TEMPERATURE_COLUMNS_CN,
    DEFAULT_HIDDEN_COLUMNS,
    CORE_DISPLAY_COLUMNS
)


# 页面配置
st.set_page_config(
    page_title="温度数据分析",
    page_icon="🌡️",
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
            df = get_temperature_data(validated_filters if validated_filters else None)
            
            # 使用占位符渲染内容
            with main_placeholder.container():
                if df.empty:
                    st.warning("⚠️ 没有符合条件的数据，请调整筛选条件")
                else:
                    # 数据展示（主区域）
                    st.markdown("---")
                    st.subheader("🌡️ 温度参数分析")
                    
                    # 选择显示模式
                    display_mode = st.radio(
                        "选择显示模式",
                        ["工艺参数", "数据汇总", "温度曲线"],
                        horizontal=True,
                        label_visibility="collapsed"
                    )
                
                # 使用配置文件中的列名映射
                column_names_cn = TEMPERATURE_COLUMNS_CN
                
                # 根据显示模式处理数据
                if display_mode == "数据汇总":
                    # ==================== 数据汇总模式 ====================
                  
                    # 汇总维度和统计方法选择
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1.5])
                    
                    with col1:
                        # 主要汇总维度
                        primary_dimension = st.selectbox(
                            "主要汇总维度",
                            ["车间", "班组", "窖池", "轮次"],
                            key="temp_primary_dimension"
                        )
                    
                    with col2:
                        # 次要汇总维度(可选) - 动态排除主要维度
                        available_secondary = ["无"] + [d for d in ["车间", "班组", "窖池", "轮次"] if d != primary_dimension]
                        secondary_dimension = st.selectbox(
                            "次要汇总维度(可选)",
                            available_secondary,
                            key="temp_secondary_dimension"
                        )
                    
                    with col3:
                        # 统计方法（添加记录次数）
                        agg_method = st.selectbox(
                            "统计方法",
                            ["平均值", "最大值", "最小值", "中位数", "标准差", "总和", "记录次数"],
                            key="temp_agg_method"
                        )
                    
                    with col4:
                        # 显示全部统计指标
                        show_all_stats = st.checkbox(
                            "显示全部统计指标", 
                            value=False, 
                            key="show_all_stats_temp",
                            help="显示所有统计指标(平均值、最大值、最小值等)"
                        )
                    
                    # 维度映射
                    dimension_map = {
                        "车间": "workshop",
                        "班组": "team_name",
                        "窖池": "pit_no",
                        "轮次": "round_number"
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
                            
                            # 定义需要汇总的温度指标字段
                            temp_indicator_fields = [
                                'temp_peak', 'days_to_peak', 'peak_duration', 
                                'temp_rise_range', 'temp_end',
                                'starter_activation_temp', 'grains_entry_temp', 'distillation_temp'
                            ]
                            
                            # 过滤出存在的指标字段
                            existing_indicator_fields = [f for f in temp_indicator_fields if f in df_temp.columns]
                            
                            if show_all_stats:
                                # 显示全部统计指标
                                agg_dict = {}
                                for field in existing_indicator_fields:
                                    agg_dict[field] = ['mean', 'max', 'min', 'median', 'std', 'count']
                                
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
                                    else:
                                        # 指标列 - 格式: field_stat
                                        parts = col.rsplit('_', 1)
                                        if len(parts) == 2:
                                            field_name, stat = parts
                                            # 获取中文字段名
                                            field_cn = column_names_cn.get(field_name, field_name)
                                            # 获取中文统计方法名
                                            stat_cn = {
                                                'mean': '平均值', 'max': '最大值', 'min': '最小值',
                                                'median': '中位数', 'std': '标准差', 'count': '次数'
                                            }.get(stat, stat)
                                            rename_dict[col] = f"{field_cn}_{stat_cn}"
                                
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
                                else:
                                    agg_dict = {field: selected_method for field in existing_indicator_fields}
                                
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
                                    elif col == 'production_date':
                                        rename_dict[col] = "记录次数"
                                    elif col in existing_indicator_fields:
                                        field_cn = column_names_cn.get(col, col)
                                        rename_dict[col] = f"{field_cn}_{agg_method}"
                                
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
                                    if ('平均值' in col or '标准差' in col or '中位数' in col) and display_df[col].dtype in ['float64', 'float32']:
                                        display_df[col] = display_df[col].round(2)
                        
                        except Exception as e:
                            st.error(f"汇总数据失败: {str(e)}")
                            display_df = pd.DataFrame()
                
                elif display_mode == "工艺参数":
                    # 表格模式：显示工艺参数
                    
                    # 核心列的英文名（调整顺序：生产日期、班组、轮次、窖池、工艺参数）
                    core_columns_en = [
                        'production_date', 'team_name', 'round_number', 'pit_no',
                        'temp_peak', 'days_to_peak', 'peak_duration', 'temp_rise_range', 'temp_end',
                        'starter_activation_temp', 'grains_entry_temp', 'distillation_temp'
                    ]
                    display_columns_en = [col for col in core_columns_en if col in df.columns]
                    
                    # 选择列并翻译
                    display_df = df[display_columns_en].copy()
                    display_df.rename(columns=column_names_cn, inplace=True)
                
                else:  # 温度曲线模式
                    # st.markdown("### 🌡️ 发酵温度曲线")
                    # st.info("💡 从列表中选择一个或多个窖池任务，查看其20天发酵温度曲线")
                    
                    # 创建任务选项列表(包含日期、轮次、窖池信息)
                    task_options = []
                    task_map = {}  # 用于映射显示文本到map_id
                    
                    for _, row in df.iterrows():
                        if pd.notna(row['map_id']):
                            task_label = f"{row['pit_no']}-{row['round_number']}轮-{row['production_date']}"
                            task_options.append(task_label)
                            task_map[task_label] = int(row['map_id'])
                    
                    if not task_options:
                        st.warning("⚠️ 当前筛选条件下没有可用的温度曲线数据")
                    else:
                        # 初始化session state
                        if 'temp_default_selection' not in st.session_state:
                            st.session_state.temp_default_selection = task_options[:min(5, len(task_options))]
                        if 'temp_widget_key' not in st.session_state:
                            st.session_state.temp_widget_key = 0
                        
                        # 验证并过滤默认选择，确保所有默认选项都在当前可用选项中
                        valid_default_selection = [
                            task for task in st.session_state.temp_default_selection 
                            if task in task_options
                        ]
                        
                        # 如果过滤后没有有效选项，使用前5个可用选项
                        if not valid_default_selection:
                            valid_default_selection = task_options[:min(5, len(task_options))]
                        
                        # 更新session state为有效的默认选择
                        st.session_state.temp_default_selection = valid_default_selection
                        
                        # 选择器和随机按钮布局
                        col_select, col_random = st.columns([4, 1])
                        
                        with col_random:
                            st.write("")  # 占位对齐
                            st.write("")
                            if st.button("🎲 随机5条", use_container_width=True):
                                import random
                                random_count = min(5, len(task_options))
                                # 更新默认选择为当前可用选项中的随机5条
                                st.session_state.temp_default_selection = random.sample(task_options, random_count)
                                # 更新widget key以强制重新渲染
                                st.session_state.temp_widget_key += 1
                                st.rerun()
                        
                        with col_select:
                            # 让用户选择要查看的任务,使用动态key
                            selected_tasks = st.multiselect(
                                "选择/搜索要查看的窖池",
                                options=task_options,
                                default=st.session_state.temp_default_selection,
                                key=f"selected_temp_tasks_{st.session_state.temp_widget_key}"
                            )
                            
                            # 更新默认选择为当前选择(用户手动修改后保持)
                            if selected_tasks != st.session_state.temp_default_selection:
                                st.session_state.temp_default_selection = selected_tasks
                        
                        if selected_tasks:
                            # 创建折线图
                            fig = go.Figure()
                            
                            # 定义颜色方案
                            colors = [
                                '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
                            ]
                            
                            for idx, task_label in enumerate(selected_tasks):
                                map_id = task_map[task_label]
                                
                                # 获取该任务的温度记录
                                temp_readings = get_temperature_readings(map_id)
                                
                                if not temp_readings.empty:
                                    color = colors[idx % len(colors)]
                                    
                                    # 添加折线
                                    fig.add_trace(go.Scatter(
                                        x=temp_readings['day_number'],
                                        y=temp_readings['temperature'],
                                        mode='lines+markers',
                                        name=task_label,
                                        line=dict(
                                            width=3,
                                            color=color
                                        ),
                                        marker=dict(
                                            size=8,
                                            color=color,
                                            line=dict(
                                                width=2,
                                                color='white'
                                            )
                                        ),
                                        hovertemplate='<b>%{fullData.name}</b><br>' +
                                                      '第%{x}天<br>' +
                                                      '温度: %{y:.1f}℃<br>' +
                                                      '<extra></extra>',
                                        # 添加自定义数据用于悬停效果
                                        customdata=[task_label] * len(temp_readings)
                                    ))
                            
                            # 设置图表样式和交互
                            fig.update_layout(
                                title={
                                    'text': "🌡️ 发酵温度曲线对比",
                                    'x': 0.5,
                                    'xanchor': 'center',
                                    'font': {'size': 20, 'color': '#2c3e50'}
                                },
                                xaxis=dict(
                                    title="发酵天数",
                                    showgrid=True,
                                    gridwidth=1,
                                    gridcolor='#ecf0f1',
                                    dtick=1,  # 每天一个刻度
                                    range=[0.5, 20.5]  # 设置x轴范围
                                ),
                                yaxis=dict(
                                    title="温度 (℃)",
                                    showgrid=True,
                                    gridwidth=1,
                                    gridcolor='#ecf0f1'
                                ),
                                hovermode='closest',  # 改为closest以支持单线高亮
                                legend=dict(
                                    orientation="v",
                                    yanchor="top",
                                    y=1,
                                    xanchor="left",
                                    x=1.02,
                                    bgcolor='rgba(255, 255, 255, 0.8)',
                                    bordercolor='#bdc3c7',
                                    borderwidth=1
                                ),
                                height=650,
                                template="plotly_white",
                                plot_bgcolor='#fafafa',
                                # 添加悬停时的交互配置
                                hoverlabel=dict(
                                    bgcolor="white",
                                    font_size=13,
                                    font_family="Arial"
                                ),
                                # 启用动画
                                transition={
                                    'duration': 300,
                                    'easing': 'cubic-in-out'
                                }
                            )
                            
                            # 更新所有trace的悬停行为
                            fig.update_traces(
                                # 鼠标悬停时高亮当前线,其他线变淡
                                hoverlabel=dict(namelength=-1),
                                # 添加平滑过渡
                                line_shape='spline',  # 使用样条曲线使线条更平滑
                            )
                            
                            # 添加配置选项
                            config = {
                                'displayModeBar': True,
                                'displaylogo': False,
                                'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                                'toImageButtonOptions': {
                                    'format': 'png',
                                    'filename': f'温度曲线_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                                    'height': 650,
                                    'width': 1200,
                                    'scale': 2
                                }
                            }
                            
                            # 显示图表
                            st.plotly_chart(fig, use_container_width=True, config=config)
                            
                            # 添加说明
                            st.caption("💡 **交互提示**: 鼠标悬停在曲线上可查看详细数据 | 点击图例可隐藏/显示对应曲线 | 双击图例可单独显示某条曲线")
                            
                            # 显示温度数据表格
                            with st.expander("📋 查看温度详细数据", expanded=False):
                                for task_label in selected_tasks:
                                    map_id = task_map[task_label]
                                    temp_readings = get_temperature_readings(map_id)
                                    
                                    if not temp_readings.empty:
                                        st.markdown(f"**{task_label}**")
                                        
                                        # 转置数据:天数作为列,温度作为值
                                        temp_pivot = temp_readings.set_index('day_number').T
                                        temp_pivot.columns = [f'第{int(d)}天' for d in temp_pivot.columns]
                                        
                                        st.dataframe(
                                            temp_pivot,
                                            use_container_width=True,
                                            hide_index=True
                                        )
                                        st.markdown("---")
                        else:
                            st.info("请至少选择一个窖池任务")
                
                # ==================== 数据展示和导出（工艺参数和数据汇总模式） ====================
                if display_mode in ["工艺参数", "数据汇总"]:
                    # 显示数据表格（使用中文列名）
                    if 'display_df' in locals() and not display_df.empty:
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
                                file_name=f"温度数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        
                        with col_export2:
                            # 导出为Excel（使用中文列名）
                            output = BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                display_df.to_excel(writer, index=False, sheet_name='温度数据')
                            output.seek(0)
                            
                            st.download_button(
                                label="📥 导出为 Excel",
                                data=output,
                                file_name=f"温度数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                
        except Exception as e:
            st.error(f"❌ 加载数据失败: {str(e)}")
            import traceback
            with st.expander("查看错误详情"):
                st.code(traceback.format_exc())
