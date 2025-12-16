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

# 侧边栏标题
with st.sidebar:
    st.markdown("# 🌡️ 温度数据分析")
    st.markdown("---")

# 初始化session state
if 'temp_filter_applied' not in st.session_state:
    st.session_state.temp_filter_applied = True  # 默认加载所有数据

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
if submit_button or st.session_state.temp_filter_applied:
    # 验证筛选条件（filters已经由render_filter_ui返回）
    validated_filters = validate_filter_conditions(filters)

    # 标记筛选已应用
    st.session_state.temp_filter_applied = True
    
    # 加载数据
    with st.spinner("正在加载数据..."):
        try:
            df = get_temperature_data(validated_filters if validated_filters else None)
            
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
                    
                    # 平均顶温
                    avg_peak = df['temp_peak'].mean()
                    st.metric("平均顶温(℃)", f"{avg_peak:.1f}" if pd.notna(avg_peak) else "无数据")
                    
                    # 平均达到顶温天数
                    avg_days = df['days_to_peak'].mean()
                    st.metric("平均达顶天数", f"{avg_days:.1f}" if pd.notna(avg_days) else "无数据")

                
                # 数据展示（主区域）
                st.markdown("---")
                st.subheader("📊 温度数据")
                
                # 选择显示模式
                display_mode = st.radio(
                    "选择显示模式",
                    ["温度参数", "温度曲线"],
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                # 使用配置文件中的列名映射
                column_names_cn = TEMPERATURE_COLUMNS_CN
                
                if display_mode == "温度参数":
                    # 表格模式：显示工艺参数
                    
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
                                key="temp_extra_cols"
                            )
                    
                    # 先确定要显示的英文列名
                    # 核心列的英文名
                    core_columns_en = [
                        'production_date', 'round_number', 'pit_no',
                        'temp_peak', 'days_to_peak', 'peak_duration', 'temp_rise_range', 'temp_end',
                        'starter_activation_temp', 'grains_entry_temp', 'distillation_temp'
                    ]
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
                            file_name=f"温度数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            width='stretch'
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
                            width='stretch'
                        )
                
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
                        
                        # 选择器和随机按钮布局
                        col_select, col_random = st.columns([4, 1])
                        
                        with col_random:
                            st.write("")  # 占位对齐
                            st.write("")
                            if st.button("🎲 随机5条", use_container_width=True, help="随机选择5条温度曲线"):
                                import random
                                random_count = min(5, len(task_options))
                                # 更新默认选择
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
                
        except Exception as e:
            st.error(f"❌ 加载数据失败: {str(e)}")
            import traceback
            with st.expander("查看错误详情"):
                st.code(traceback.format_exc())
