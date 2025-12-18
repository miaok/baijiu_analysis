"""
理化指标分析页面
提供多维度筛选和数据展示功能
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from utils.db_utils import (
    get_physicochemical_data, 
    get_filter_options
)
from utils.filter_utils import (
    validate_filter_conditions,
    build_filter_summary
)
from utils.filter_components import render_filter_ui
from utils.column_config import (
    PHYSICOCHEMICAL_COLUMNS_CN,
    DEFAULT_HIDDEN_COLUMNS,
    CORE_DISPLAY_COLUMNS
)
from utils.aggregation_utils import (
    get_summary_statistics,
    create_pivot_table,
    format_column_name
)
from utils.visualization_utils import (
    CATEGORICAL_DIMENSIONS,
    NUMERIC_DIMENSIONS,
    AGGREGATION_METHODS,
    CHART_TYPES,
    get_available_dimensions,
    prepare_visualization_data,
    create_chart,
    validate_chart_config,
    recommend_chart_type
)


# 页面配置
st.set_page_config(
    page_title="理化指标分析",
    page_icon="🧪",
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
            df = get_physicochemical_data(validated_filters if validated_filters else None)
            
            # 使用占位符渲染内容
            with main_placeholder.container():
                if df.empty:
                    st.warning("⚠️ 没有符合条件的数据，请调整筛选条件")
                else:
                    # 数据表格展示（主区域）
                    st.markdown("---")
                    st.subheader("🧪 理化指标分析")
                    
                    # 选择显示模式
                    display_mode = st.radio(
                        "选择显示模式",
                        ["完整数据", "数据汇总", "可视化分析"],
                        horizontal=True,
                        label_visibility="collapsed"
                    )
                
                # ==================== 数据汇总模式 ====================
                if display_mode == "数据汇总":
                    # st.markdown("### 📊 数据透视汇总")
                    # st.markdown("---")
                    
                    # 维度选择区域
                    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                    
                    with col1:
                        layer_option = st.selectbox(
                            "层次",
                            ["全部", "上层", "下层"],
                            key="layer_dimension",
                            help="选择要汇总的层次数据"
                        )
                    
                    with col2:
                        direction_option = st.selectbox(
                            "出入池",
                            ["全部", "入池", "出池"],
                            key="direction_dimension",
                            help="选择要汇总的出入池数据"
                        )
                    
                    with col3:
                        agg_method = st.selectbox(
                            "汇总方式",
                            ["平均值", "最大值", "最小值", "中位数", "标准差", "总和", "计数"],
                            key="agg_method",
                            help="选择数据汇总的计算方式"
                        )
                    
                    with col4:
                        show_all_stats = st.checkbox(
                            "显示全部统计",
                            value=False,
                            key="show_all_stats",
                            help="显示所有统计指标(平均值、最大值、最小值等)"
                        )
                    
                    # 分组选项
                    with st.expander("🔧 高级选项 - 分组汇总", expanded=False):
                                                
                        group_col1, group_col2, group_col3, group_col4 = st.columns(4)
                        
                        with group_col1:
                            group_by_round = st.checkbox("按轮次分组", value=False)
                        with group_col2:
                            group_by_workshop = st.checkbox("按车间分组", value=False)
                        with group_col3:
                            group_by_team = st.checkbox("按班组分组", value=False)
                        with group_col4:
                            group_by_pit = st.checkbox("按窖池分组", value=False)
                        
                        # 构建分组字段列表
                        group_by_fields = []
                        if group_by_round:
                            group_by_fields.append('round_number')
                        if group_by_workshop:
                            group_by_fields.append('workshop')
                        if group_by_team:
                            group_by_fields.append('team_name')
                        if group_by_pit:
                            group_by_fields.append('pit_no')
                    
                    # 执行汇总
                    try:
                        summary_df = pd.DataFrame() # Initialize to avoid UnboundLocalError
                        pivot_df_display = pd.DataFrame() # Initialize to avoid UnboundLocalError

                        if show_all_stats:
                            # 显示全部统计指标
                            summary_df = get_summary_statistics(df, layer_option, direction_option)
                            
                            if not summary_df.empty:
                                st.markdown("#### � 全部统计指标")
                                
                                st.dataframe(
                                    summary_df.style.format("{:.2f}"),
                                    use_container_width=True,
                                    height=400
                                )
                            else:
                                st.warning("⚠️ 没有可汇总的数据")
                        else:
                            if group_by_fields:
                                # 分组汇总
                                pivot_df = create_pivot_table(
                                    df, 
                                    layer_option, 
                                    direction_option, 
                                    agg_method,
                                    group_by=group_by_fields
                                )
                                
                                if not pivot_df.empty:
                                    st.markdown(f"#### 📊 {agg_method} - 分组汇总")
                                    
                                    # 格式化列名
                                    pivot_df_display = pivot_df.copy()
                                    pivot_df_display.columns = [format_column_name(col) for col in pivot_df_display.columns]
                                    
                                    st.dataframe(
                                        pivot_df_display.style.format("{:.2f}"),
                                        use_container_width=True,
                                        height=400
                                    )
                                else:
                                    st.warning("⚠️ 没有可汇总的数据")
                            else:
                                # 整体汇总
                                pivot_df = create_pivot_table(
                                    df, 
                                    layer_option, 
                                    direction_option, 
                                    agg_method,
                                    group_by=None
                                )
                                
                                if not pivot_df.empty:
                                    st.markdown(f"#### 📊 {agg_method} - 整体汇总")
                                    
                                    # 转置表格:原来是指标为行,现在转为汇总方式为行
                                    pivot_df_display = pivot_df.T
                                    
                                    # 格式化列名(原来的索引,现在是列)
                                    pivot_df_display.columns = [format_column_name(col) for col in pivot_df_display.columns]
                                    
                                    # 设置索引名称
                                    pivot_df_display.index.name = '汇总方式'
                                    
                                    st.dataframe(
                                        pivot_df_display.style.format("{:.2f}"),
                                        use_container_width=True,
                                        height=400
                                    )
                                else:
                                    st.warning("⚠️ 没有可汇总的数据")
                        
                        # 导出功能
                        export_df = None
                        if show_all_stats and not summary_df.empty:
                            export_df = summary_df
                        elif not show_all_stats and not pivot_df_display.empty:
                            export_df = pivot_df_display
                        
                        if export_df is not None and not export_df.empty:
                            st.markdown("---")
                            col_export1, col_export2, col_export3 = st.columns([1, 1, 2])
                            
                            with col_export1:
                                csv = export_df.to_csv(encoding='utf-8-sig')
                                st.download_button(
                                    label="📥 导出为 CSV",
                                    data=csv,
                                    file_name=f"理化指标汇总_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv"
                                )
                            
                            with col_export2:
                                from io import BytesIO
                                output = BytesIO()
                                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                    export_df.to_excel(writer, sheet_name='理化指标汇总')
                                output.seek(0)
                                
                                st.download_button(
                                    label="📥 导出为 Excel",
                                    data=output,
                                    file_name=f"理化指标汇总_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                    
                    except Exception as e:
                        st.error(f"❌ 汇总数据失败: {str(e)}")
                        import traceback
                        with st.expander("查看错误详情"):
                            st.code(traceback.format_exc())
                
                # ==================== 完整数据模式 ====================
                elif display_mode == "完整数据":
                    # 使用配置文件中的列名映射
                    column_names_cn = PHYSICOCHEMICAL_COLUMNS_CN
                    
                    # 数据筛选选项 - 与数据汇总保持一致的UI
                    col_filter1, col_filter2 = st.columns(2)
                    
                    with col_filter1:
                        # 层次筛选
                        layer_filter = st.selectbox(
                            "层次",
                            ["全部", "上层", "下层"],
                            key="complete_layer_filter",
                            help="选择要显示的层次数据"
                        )
                    
                    with col_filter2:
                        # 出入池筛选
                        direction_filter = st.selectbox(
                            "出入池",
                            ["全部", "入池", "出池"],
                            key="complete_direction_filter",
                            help="选择要显示的出入池数据"
                        )
                    
                    # 根据筛选条件构建显示列
                    display_columns = ['production_date', 'team_name', 'round_number', 'pit_no']
                    
                    # 指标列表
                    indicators = ['moisture', 'alcohol', 'acidity', 'starch', 'sugar']
                    
                    # 确定要显示的方向
                    if direction_filter == "全部":
                        directions = ["入池", "出池"]
                    else:
                        directions = [direction_filter]
                    
                    # 确定要显示的层次
                    if layer_filter == "全部":
                        layers = ["上层", "下层"]
                    else:
                        layers = [layer_filter]
                    
                    # 根据筛选条件添加列
                    for direction in directions:
                        direction_prefix = 'entry' if direction == '入池' else 'exit'
                        for layer in layers:
                            layer_suffix = 'upper' if layer == '上层' else 'lower'
                            for indicator in indicators:
                                col_name = f"{direction_prefix}_{indicator}_{layer_suffix}"
                                if col_name in df.columns:
                                    display_columns.append(col_name)
                    
                    # 筛选现有列
                    display_df = df[[col for col in display_columns if col in df.columns]].copy()
                    
                    # 在完整数据模式下,提供额外列的显示选项
                    optional_columns_cn = DEFAULT_HIDDEN_COLUMNS['physicochemical']
                    # 找出实际存在的可选列
                    available_optional = [col for col in optional_columns_cn if col in df.columns]
                        
                    if available_optional:
                        # 添加列显示控制选项
                        with st.expander("⚙️ 显示额外列", expanded=False):
                            show_extra_cols = st.multiselect(
                                "选择要显示的额外列",
                                options=[column_names_cn.get(col, col) for col in available_optional], # Display CN names
                                default=[],  # 默认不显示任何额外列
                                help="这些列默认隐藏，可根据需要选择显示"
                            )
                        
                        # Map selected CN names back to original column names
                        selected_original_cols = []
                        for cn_col in show_extra_cols:
                            for original_col, mapped_cn_col in column_names_cn.items():
                                if mapped_cn_col == cn_col:
                                    selected_original_cols.append(original_col)
                                    break
                        
                        # Add selected optional columns to display_df
                        for col in selected_original_cols:
                            if col not in display_df.columns and col in df.columns:
                                display_df[col] = df[col]

                    # 重命名列为中文
                    display_df.rename(columns=column_names_cn, inplace=True)

                    # 配置列固定
                    column_config = {
                        '生产日期': st.column_config.TextColumn(
                            '生产日期',
                            pinned=True
                        ),
                        '班组': st.column_config.TextColumn(
                            '班组',
                            pinned=True
                        ),
                        '轮次': st.column_config.NumberColumn(
                            '轮次',
                            pinned=True
                        ),
                        '窖池': st.column_config.TextColumn(
                            '窖池',
                            pinned=True
                        ),
                    }
                    
                    # 显示数据表格（使用中文列名）
                    st.dataframe(
                        display_df,
                        column_config=column_config,
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
                            file_name=f"理化指标_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            width='stretch'
                        )
                    
                    with col_export2:
                        # 导出为Excel（使用中文列名）
                        from io import BytesIO
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            display_df.to_excel(writer, index=False, sheet_name='理化指标')
                        output.seek(0)
                        
                        st.download_button(
                            label="📥 导出为 Excel",
                            data=output,
                            file_name=f"理化指标_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            width='stretch'
                        )

                # ==================== 可视化分析模式 ====================
                elif display_mode == "可视化分析":
                    st.markdown("### 📊 可视化分析")
                    
                    # 获取可用维度
                    available_categorical, available_numeric = get_available_dimensions(df)
                    
                    if not available_categorical and not available_numeric:
                        st.warning("⚠️ 当前数据中没有可用于可视化的维度")
                    else:
                        # 创建左右分栏布局
                        config_col, chart_col = st.columns([3, 7])
                        
                        with config_col:
                            st.markdown("#### ⚙️ 图表配置")
                            
                            # 图表类型选择
                            chart_type_cn = st.selectbox(
                                "图表类型",
                                list(CHART_TYPES.keys()),
                                help="选择要生成的图表类型"
                            )
                            chart_type = CHART_TYPES[chart_type_cn]
                            
                            st.markdown("---")
                            
                            # X轴配置
                            st.markdown("**X轴配置**")
                            
                            # 合并分类和数值维度供X轴选择
                            all_x_dimensions = {**available_categorical, **available_numeric}
                            x_dimension_cn = st.selectbox(
                                "X轴维度",
                                list(all_x_dimensions.keys()),
                                help="选择X轴显示的维度"
                            )
                            x_dimension = all_x_dimensions[x_dimension_cn]
                            
                            # 判断X轴是否为分类维度
                            x_is_categorical = x_dimension in CATEGORICAL_DIMENSIONS.values()
                            
                            # X轴聚合方式（仅数值维度可选）
                            if not x_is_categorical:
                                x_agg_cn = st.selectbox(
                                    "X轴聚合方式",
                                    list(AGGREGATION_METHODS.keys()),
                                    help="对X轴数值进行聚合计算"
                                )
                                x_agg = AGGREGATION_METHODS[x_agg_cn]
                            else:
                                x_agg = None
                                st.info("ℹ️ X轴为分类维度，无需聚合")
                            
                            st.markdown("---")
                            
                            # Y轴配置
                            st.markdown("**Y轴配置**")
                            
                            # Y轴通常选择数值维度（但也允许分类维度用于热力图等）
                            all_y_dimensions = {**available_numeric, **available_categorical}
                            y_dimension_cn = st.selectbox(
                                "Y轴维度",
                                list(all_y_dimensions.keys()),
                                help="选择Y轴显示的维度"
                            )
                            y_dimension = all_y_dimensions[y_dimension_cn]
                            
                            # 判断Y轴是否为分类维度
                            y_is_categorical = y_dimension in CATEGORICAL_DIMENSIONS.values()
                            
                            # Y轴聚合方式
                            if not y_is_categorical:
                                y_agg_cn = st.selectbox(
                                    "Y轴聚合方式",
                                    list(AGGREGATION_METHODS.keys()),
                                    index=1,  # 默认选择"平均值"
                                    help="对Y轴数值进行聚合计算"
                                )
                                y_agg = AGGREGATION_METHODS[y_agg_cn]
                            else:
                                y_agg = None
                                st.info("ℹ️ Y轴为分类维度，无需聚合")
                            
                            st.markdown("---")
                            
                            # 分组/颜色维度（可选）
                            st.markdown("**分组配置（可选）**")
                            use_color = st.checkbox("启用分组/着色", value=False)
                            
                            if use_color:
                                # 分组维度通常选择分类维度
                                color_dimension_cn = st.selectbox(
                                    "分组维度",
                                    ["无"] + list(available_categorical.keys()),
                                    help="按此维度进行分组显示"
                                )
                                
                                if color_dimension_cn != "无":
                                    color_dimension = available_categorical[color_dimension_cn]
                                else:
                                    color_dimension = None
                            else:
                                color_dimension = None
                                color_dimension_cn = None
                            
                            st.markdown("---")
                            
                            # 生成按钮
                            generate_button = st.button("🎨 生成图表", type="primary", use_container_width=True)
                        
                        with chart_col:
                            if generate_button:
                                # 验证配置
                                is_valid, error_msg = validate_chart_config(
                                    chart_type,
                                    x_dimension,
                                    y_dimension,
                                    x_agg,
                                    y_agg
                                )
                                
                                if not is_valid:
                                    st.error(f"❌ 配置错误: {error_msg}")
                                else:
                                    if error_msg:  # 有警告信息
                                        st.warning(f"⚠️ {error_msg}")
                                    
                                    try:
                                        # 准备数据
                                        viz_data = prepare_visualization_data(
                                            df,
                                            x_dimension,
                                            y_dimension,
                                            x_agg,
                                            y_agg,
                                            color_dimension
                                        )
                                        
                                        if viz_data.empty:
                                            st.warning("⚠️ 没有可用于绘图的数据，请检查筛选条件或维度选择")
                                        else:
                                            # 构建图表标题
                                            title_parts = []
                                            if y_agg:
                                                title_parts.append(f"{y_dimension_cn}的{y_agg_cn}")
                                            else:
                                                title_parts.append(y_dimension_cn)
                                            
                                            if x_agg:
                                                title_parts.append(f"vs {x_dimension_cn}的{x_agg_cn}")
                                            else:
                                                title_parts.append(f"vs {x_dimension_cn}")
                                            
                                            chart_title = " ".join(title_parts)
                                            
                                            # 创建图表
                                            fig = create_chart(
                                                chart_type,
                                                viz_data,
                                                x_dimension,
                                                y_dimension,
                                                x_dimension_cn,
                                                y_dimension_cn,
                                                color_dimension,
                                                color_dimension_cn,
                                                chart_title
                                            )
                                            
                                            # 显示图表
                                            st.plotly_chart(fig, use_container_width=True)
                                            
                                            # 显示数据预览
                                            with st.expander("📋 查看图表数据", expanded=False):
                                                # 准备显示用的列名映射
                                                display_data = viz_data.copy()
                                                
                                                # 重命名列为中文
                                                rename_map = {}
                                                if x_dimension in display_data.columns:
                                                    rename_map[x_dimension] = x_dimension_cn
                                                if y_dimension in display_data.columns:
                                                    rename_map[y_dimension] = y_dimension_cn
                                                if color_dimension and color_dimension in display_data.columns:
                                                    rename_map[color_dimension] = color_dimension_cn
                                                
                                                display_data.rename(columns=rename_map, inplace=True)
                                                
                                                st.dataframe(
                                                    display_data,
                                                    use_container_width=True,
                                                    hide_index=True
                                                )
                                            
                                            # 图表导出
                                            st.markdown("---")
                                            export_col1, export_col2 = st.columns(2)
                                            
                                            with export_col1:
                                                # 导出图表为HTML
                                                html_buffer = fig.to_html(include_plotlyjs='cdn')
                                                st.download_button(
                                                    label="📥 导出图表 (HTML)",
                                                    data=html_buffer,
                                                    file_name=f"理化指标可视化_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                                                    mime="text/html"
                                                )
                                            
                                            with export_col2:
                                                # 导出数据为CSV
                                                csv = viz_data.to_csv(index=False, encoding='utf-8-sig')
                                                st.download_button(
                                                    label="📥 导出数据 (CSV)",
                                                    data=csv,
                                                    file_name=f"理化指标可视化数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                                    mime="text/csv"
                                                )
                                    
                                    except Exception as e:
                                        st.error(f"❌ 生成图表失败: {str(e)}")
                                        import traceback
                                        with st.expander("查看错误详情"):
                                            st.code(traceback.format_exc())
                            else:
                                # 显示提示信息
                                st.info("👈 请在左侧配置图表参数,然后点击【生成图表】按钮")
                                
                                # 显示推荐的图表类型
                                has_agg = (x_agg is not None) or (y_agg is not None)
                                recommended = recommend_chart_type(x_is_categorical, y_is_categorical, has_agg)
                                
                                if recommended:
                                    st.markdown("**💡 推荐的图表类型：**")
                                    st.write("、".join(recommended))

                
        except Exception as e:
            st.error(f"❌ 加载数据失败: {str(e)}")
            import traceback
            with st.expander("查看错误详情"):
                st.code(traceback.format_exc())

