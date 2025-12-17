"""
筛选组件模块
提供可复用的数据筛选UI组件（侧边栏版本）
支持跨页面保持筛选条件
"""

import streamlit as st
from datetime import datetime
from .filter_utils import get_month_options, format_month_label
from .db_utils import get_dynamic_date_range


def render_filter_ui(filter_options, sidebar=True):
    """
    渲染数据筛选UI组件（侧边栏版本）
    
    Args:
        filter_options: 包含可用筛选选项的字典
            - work_years: 生产年度列表
            - rounds: 轮次列表
            - workshops: 车间列表
            - teams: 班组列表
            - pits: 窖池列表
            - min_date: 最小日期
            - max_date: 最大日期
        sidebar: 是否在侧边栏中渲染（默认True，仅支持侧边栏模式）
    
    Returns:
        tuple: (filters dict, submit_button)
    """
    
    # 添加自定义CSS - 增加侧边栏宽度
    st.markdown("""
        <style>
        /* 增加侧边栏宽度 */
        [data-testid="stSidebar"] {
            min-width: 340px !important;
            max-width: 420px !important;
        }
        /* 减少筛选区域的整体padding */
        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
        }
        /* 减少multiselect和其他组件的margin */
        div[data-baseweb="select"] {
            margin-bottom: 0.5rem !important;
        }
        /* 减少radio按钮组的margin */
        div[role="radiogroup"] {
            margin-bottom: 0.5rem !important;
        }
        /* 减少date_input的margin */
        div[data-testid="stDateInput"] {
            margin-bottom: 0.5rem !important;
        }
        /* 减少markdown标题的margin */
        .stMarkdown h3, .stMarkdown h4 {
            margin-top: 0.3rem !important;
            margin-bottom: 0.3rem !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 初始化session_state中的筛选条件（跨页面保持）
    if 'global_year_mode' not in st.session_state:
        st.session_state.global_year_mode = "所有"
    if 'global_work_years' not in st.session_state:
        st.session_state.global_work_years = []
    if 'global_fiscal_years' not in st.session_state:
        st.session_state.global_fiscal_years = []
    if 'global_time_detail_mode' not in st.session_state:
        st.session_state.global_time_detail_mode = "不筛选"
    if 'global_months' not in st.session_state:
        st.session_state.global_months = []
    if 'global_rounds' not in st.session_state:
        st.session_state.global_rounds = []
    if 'global_unit_type' not in st.session_state:
        st.session_state.global_unit_type = "所有"
    if 'global_workshops' not in st.session_state:
        st.session_state.global_workshops = []
    if 'global_teams' not in st.session_state:
        st.session_state.global_teams = []
    if 'global_pits' not in st.session_state:
        st.session_state.global_pits = []
    
    # 初始化所有筛选变量
    start_date = None
    end_date = None
    months = []
    rounds = []
    work_years = []
    fiscal_years = []
    workshops = []
    teams = []
    pits = []
    
    # ========== 时间筛选 ==========
    st.markdown("**📅 时间筛选**")
    
    # 第一级：年份选择模式
    year_mode_options = ["所有", "年度", "年份", "范围"]
    year_mode_index = year_mode_options.index(st.session_state.global_year_mode) if st.session_state.global_year_mode in year_mode_options else 0
    
    year_mode = st.radio(
        "选择时间类型",
        year_mode_options,
        index=year_mode_index,
        horizontal=True,
        key="year_mode",
        label_visibility="collapsed"
    )
    
    # 更新session_state
    st.session_state.global_year_mode = year_mode
    
    # 根据年度类型显示相应的选项
    if year_mode == "年度":
        work_years = st.multiselect(
            "选择年度",
            options=filter_options.get('work_years', []),
            default=st.session_state.global_work_years,
            placeholder="请选择一个或多个生产年度",
            key="work_years_select",
            label_visibility="collapsed"
        )
        st.session_state.global_work_years = work_years
        
        # 第二级：细化时间筛选
        if work_years:
            st.markdown("**🕐 细化时间**")
            
            time_detail_options = ["不筛选", "月份", "轮次", "单天"]
            time_detail_index = time_detail_options.index(st.session_state.global_time_detail_mode) if st.session_state.global_time_detail_mode in time_detail_options else 0
            
            time_detail_mode = st.radio(
                "细化筛选",
                time_detail_options,
                index=time_detail_index,
                horizontal=True,
                key="time_detail_mode",
                label_visibility="collapsed"
            )
            st.session_state.global_time_detail_mode = time_detail_mode
            
            # 根据已选择的条件动态获取范围
            dynamic_date_range = get_dynamic_date_range(
                work_years=work_years,
                fiscal_years=None,
                months=None,
                rounds=None
            )
            
            if dynamic_date_range:
                current_min_date = dynamic_date_range['min_date']
                current_max_date = dynamic_date_range['max_date']
            else:
                current_min_date = filter_options.get('min_date', datetime.now().date())
                current_max_date = filter_options.get('max_date', datetime.now().date())
            
            if time_detail_mode == "月份":
                months = st.multiselect(
                    "选择月份",
                    options=get_month_options(),
                    default=st.session_state.global_months,
                    format_func=format_month_label,
                    placeholder="请选择一个或多个月份",
                    key="months_select",
                    label_visibility="collapsed"
                )
                st.session_state.global_months = months
            elif time_detail_mode == "轮次":
                rounds = st.multiselect(
                    "选择轮次",
                    options=filter_options.get('rounds', []),
                    default=st.session_state.global_rounds,
                    placeholder="请选择一个或多个轮次",
                    key="rounds_select",
                    label_visibility="collapsed"
                )
                st.session_state.global_rounds = rounds
            elif time_detail_mode == "单天":
                selected_date = st.date_input(
                    "选择日期",
                    value=current_max_date,
                    min_value=current_min_date,
                    max_value=current_max_date,
                    key="single_date",
                    label_visibility="collapsed"
                )
                start_date = selected_date
                end_date = selected_date
    
    elif year_mode == "年份":
        # 获取实际年份选项（从生产年度推算）
        fiscal_year_options = sorted(list(set([y for y in filter_options.get('work_years', [])])))
        fiscal_years = st.multiselect(
            "选择实际年份",
            options=fiscal_year_options,
            default=st.session_state.global_fiscal_years,
            placeholder="请选择一个或多个实际年份",
            key="fiscal_years_select",
            label_visibility="collapsed"
        )
        st.session_state.global_fiscal_years = fiscal_years
        
        # 第二级：细化时间筛选
        if fiscal_years:
            st.markdown("**🕐 细化时间**")
            
            time_detail_options = ["所有", "月份", "轮次", "单天"]
            time_detail_index = time_detail_options.index(st.session_state.global_time_detail_mode) if st.session_state.global_time_detail_mode in time_detail_options else 0
            
            time_detail_mode = st.radio(
                "细化筛选",
                time_detail_options,
                index=time_detail_index,
                horizontal=True,
                key="time_detail_mode",
                label_visibility="collapsed"
            )
            st.session_state.global_time_detail_mode = time_detail_mode
            
            # 根据已选择的条件动态获取范围
            dynamic_date_range = get_dynamic_date_range(
                work_years=None,
                fiscal_years=fiscal_years,
                months=None,
                rounds=None
            )
            
            if dynamic_date_range:
                current_min_date = dynamic_date_range['min_date']
                current_max_date = dynamic_date_range['max_date']
            else:
                current_min_date = filter_options.get('min_date', datetime.now().date())
                current_max_date = filter_options.get('max_date', datetime.now().date())
            
            if time_detail_mode == "月份":
                months = st.multiselect(
                    "选择月份",
                    options=get_month_options(),
                    default=st.session_state.global_months,
                    format_func=format_month_label,
                    placeholder="请选择一个或多个月份",
                    key="months_select",
                    label_visibility="collapsed"
                )
                st.session_state.global_months = months
            elif time_detail_mode == "轮次":
                rounds = st.multiselect(
                    "选择轮次",
                    options=filter_options.get('rounds', []),
                    default=st.session_state.global_rounds,
                    placeholder="请选择一个或多个轮次",
                    key="rounds_select",
                    label_visibility="collapsed"
                )
                st.session_state.global_rounds = rounds
            elif time_detail_mode == "单天":
                selected_date = st.date_input(
                    "选择日期",
                    value=current_max_date,
                    min_value=current_min_date,
                    max_value=current_max_date,
                    key="single_date",
                    label_visibility="collapsed"
                )
                start_date = selected_date
                end_date = selected_date
    
    elif year_mode == "范围":
        # 直接显示范围选择器
        current_min_date = filter_options.get('min_date', datetime.now().date())
        current_max_date = filter_options.get('max_date', datetime.now().date())
        
        st.markdown("**🕐 选择范围**")
        date_range = st.date_input(
            "选择起始和结束日期",
            value=(current_min_date, current_max_date),
            min_value=current_min_date,
            max_value=current_max_date,
            key="date_range",
            label_visibility="collapsed"
        )
        
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        elif not isinstance(date_range, tuple):
            # 只选择了一个日期
            start_date = date_range
            end_date = None
    
    st.markdown("<hr style='margin: 0.8rem 0;'>", unsafe_allow_html=True)
    
    # ========== 空间筛选 ==========
    st.markdown("**🏭 空间筛选**")
    
    # 单选按钮选择筛选类型
    unit_type_options = ["所有", "车间", "班组", "窖池"]
    unit_type_index = unit_type_options.index(st.session_state.global_unit_type) if st.session_state.global_unit_type in unit_type_options else 0
    
    unit_type = st.radio(
        "筛选类型",
        unit_type_options,
        index=unit_type_index,
        horizontal=True,
        key="unit_type",
        label_visibility="collapsed"
    )
    st.session_state.global_unit_type = unit_type
    
    # 根据选择的类型显示相应的下拉列表
    if unit_type == "车间":
        workshops = st.multiselect(
            "选择车间",
            options=filter_options.get('workshops', []),
            default=st.session_state.global_workshops,
            placeholder="请选择一个或多个车间",
            key="workshops_select",
            label_visibility="collapsed"
        )
        st.session_state.global_workshops = workshops
    elif unit_type == "班组":
        teams = st.multiselect(
            "选择班组",
            options=filter_options.get('teams', []),
            default=st.session_state.global_teams,
            placeholder="请选择一个或多个班组",
            key="teams_select",
            label_visibility="collapsed"
        )
        st.session_state.global_teams = teams
    elif unit_type == "窖池":
        pits = st.multiselect(
            "选择窖池",
            options=filter_options.get('pits', []),
            default=st.session_state.global_pits,
            placeholder="请选择一个或多个窖池",
            key="pits_select",
            label_visibility="collapsed"
        )
        st.session_state.global_pits = pits
    
    # 提交按钮
    st.markdown("<hr style='margin: 0.8rem 0;'>", unsafe_allow_html=True)
    submit_button = st.button("🔍 查询数据", use_container_width=True, type="primary")
    
    # 构建筛选条件字典
    filters = {}
    
    if start_date:
        filters['start_date'] = str(start_date)
    if end_date:
        filters['end_date'] = str(end_date)
    if work_years:
        filters['work_years'] = work_years
    if fiscal_years:
        filters['fiscal_years'] = fiscal_years
    if months:
        filters['months'] = months
    if rounds:
        filters['rounds'] = rounds
    if workshops:
        filters['workshops'] = workshops
    if teams:
        filters['teams'] = teams
    if pits:
        filters['pits'] = pits
    
    return filters, submit_button
