"""
筛选组件模块
提供可复用的数据筛选UI组件
"""

import streamlit as st
from datetime import datetime
from .filter_utils import get_month_options, format_month_label
from .db_utils import get_teams_by_workshop, get_pits_by_workshop_team, get_dynamic_date_range


def render_filter_ui(filter_options):
    """
    渲染数据筛选UI组件
    
    Args:
        filter_options: 包含可用筛选选项的字典
            - work_years: 工作年度列表
            - rounds: 轮次列表
            - workshops: 车间列表
            - teams: 班组列表
            - pits: 窖池列表
            - min_date: 最小日期
            - max_date: 最大日期
    
    Returns:
        dict: 包含用户选择的筛选条件
    """
    
    # 添加自定义CSS以减少间距
    st.markdown("""
        <style>
        /* 减少筛选区域的整体padding */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0.5rem !important;
        }
        /* 减少multiselect和其他组件的margin */
        div[data-baseweb="select"] {
            margin-bottom: 0.3rem !important;
        }
        /* 减少radio按钮组的margin */
        div[role="radiogroup"] {
            margin-bottom: 0.3rem !important;
        }
        /* 减少date_input的margin */
        div[data-testid="stDateInput"] {
            margin-bottom: 0.3rem !important;
        }
        /* 减少markdown标题的margin */
        .stMarkdown h3, .stMarkdown h4 {
            margin-top: 0.2rem !important;
            margin-bottom: 0.2rem !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
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
    
    # ========== 第一行：年度筛选 + 月份/轮次 + 时间筛选（三列平齐） ==========
    main_col1, main_col2, main_col3 = st.columns([1, 1, 1])
    
    # 第一列：年度筛选
    with main_col1:
        st.markdown("**📅 年份选择**")
        year_mode = st.radio(
            "选择年度类型",
            ["不筛选", "工作年度", "实际年份"],
            horizontal=True,
            key="year_mode",
            label_visibility="collapsed"
        )
        
        # 根据年度类型显示相应的下拉列表
        if year_mode == "工作年度":
            work_years = st.multiselect(
                "选择工作年度",
                options=filter_options.get('work_years', []),
                placeholder="请选择一个或多个工作年度",
                key="work_years_select",
                label_visibility="collapsed"
            )
        elif year_mode == "实际年份":
            # 获取实际年份选项（从工作年度推算）
            fiscal_year_options = sorted(list(set([y for y in filter_options.get('work_years', [])])))
            fiscal_years = st.multiselect(
                "选择实际年份",
                options=fiscal_year_options,
                placeholder="请选择一个或多个实际年份",
                key="fiscal_years_select",
                label_visibility="collapsed"
            )
    
    # 第二列：月份/轮次选择
    with main_col2:
        st.markdown("**⏰ 月份/轮次**")
        time_mode = st.radio(
            "筛选模式",
            ["不筛选", "按月份", "按轮次"],
            horizontal=True,
            key="time_mode",
            label_visibility="collapsed"
        )
    
    # 第三列:时间筛选(根据第二列的选择动态显示)
    with main_col3:
        st.markdown("**🕐 时间选择**")
        
        # 根据已选择的条件动态获取日期范围
        dynamic_date_range = None
        if work_years or fiscal_years or months or rounds:
            # 如果用户已经选择了年份、月份或轮次,则获取对应的日期范围
            dynamic_date_range = get_dynamic_date_range(
                work_years=work_years if work_years else None,
                fiscal_years=fiscal_years if fiscal_years else None,
                months=months if months else None,
                rounds=rounds if rounds else None
            )
        
        # 确定实际使用的日期范围
        if dynamic_date_range:
            current_min_date = dynamic_date_range['min_date']
            current_max_date = dynamic_date_range['max_date']
        else:
            current_min_date = filter_options.get('min_date', datetime.now().date())
            current_max_date = filter_options.get('max_date', datetime.now().date())
        
        if time_mode == "按月份":
            # 月份模式:直接三选项横向排列
            date_filter_type = st.radio(
                "筛选方式",
                ["月份", "日期范围", "单天"],
                horizontal=True,
                key="date_filter_type",
                label_visibility="collapsed"
            )
            
            # 根据选择显示相应的控件
            if date_filter_type == "月份":
                # 使用下拉列表选择月份
                months = st.multiselect(
                    "选择月份",
                    options=get_month_options(),
                    format_func=format_month_label,
                    placeholder="请选择一个或多个月份",
                    key="months_select",
                    label_visibility="collapsed"
                )
                
            elif date_filter_type == "单天":
                # 单个日期选择 - 使用动态日期范围
                selected_date = st.date_input(
                    "选择日期",
                    value=current_max_date,
                    min_value=current_min_date,
                    max_value=current_max_date,
                    key="single_date"
                )
                start_date = selected_date
                end_date = selected_date
                
            else:  # 日期范围
                # 日期范围选择 - 使用动态日期范围
                date_range = st.date_input(
                    "选择起始和结束日期",
                    value=(current_min_date, current_max_date),
                    min_value=current_min_date,
                    max_value=current_max_date,
                    key="date_range"
                )
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    start_date, end_date = date_range
                elif not isinstance(date_range, tuple):
                    # 只选择了一个日期
                    start_date = date_range
                    end_date = None
        
        elif time_mode == "按轮次":
            # 轮次模式:使用下拉列表选择轮次
            rounds = st.multiselect(
                "选择轮次",
                options=filter_options.get('rounds', []),
                placeholder="请选择一个或多个轮次",
                key="rounds_select",
                label_visibility="collapsed"
            )
        # 如果是"不筛选",则不显示任何控件
    
    st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)
    
    # ========== 第二行：车间、班组、窖池（层级联动） ==========
    #st.markdown("**🏭 生产单元筛选**")
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.markdown("**🏭 车间**")
        workshops = st.multiselect(
            "选择车间",
            options=filter_options.get('workshops', []),
            placeholder="不限",
            key="workshops_select",
            label_visibility="collapsed"
        )
    
    with col5:
        st.markdown("**👥 班组**")
        # 根据选择的车间动态更新班组选项
        if workshops:
            available_teams = []
            for workshop in workshops:
                workshop_teams = get_teams_by_workshop(workshop)
                available_teams.extend(workshop_teams)
            # 去重并排序
            available_teams = sorted(list(set(available_teams)))
        else:
            available_teams = filter_options.get('teams', [])
        
        teams = st.multiselect(
            "选择班组",
            options=available_teams,
            placeholder="不限",
            help="班组选项会根据所选车间自动更新",
            key="teams_select",
            label_visibility="collapsed"
        )
    
    with col6:
        st.markdown("**🏺 窖池**")
        # 根据选择的车间和班组动态更新窖池选项
        if workshops or teams:
            available_pits = []
            if workshops and not teams:
                # 仅选择了车间
                for workshop in workshops:
                    pits_in_workshop = get_pits_by_workshop_team(workshop=workshop)
                    available_pits.extend(pits_in_workshop)
            elif teams and not workshops:
                # 仅选择了班组
                for team in teams:
                    pits_in_team = get_pits_by_workshop_team(team=team)
                    available_pits.extend(pits_in_team)
            else:
                # 同时选择了车间和班组
                for workshop in workshops:
                    for team in teams:
                        pits = get_pits_by_workshop_team(workshop=workshop, team=team)
                        available_pits.extend(pits)
            
            # 去重并排序
            available_pits = sorted(list(set(available_pits)))
        else:
            available_pits = filter_options.get('pits', [])
        
        pits = st.multiselect(
            "选择窖池",
            options=available_pits,
            placeholder="不限",
            help="窖池选项会根据所选车间和班组自动更新",
            key="pits_select",
            label_visibility="collapsed"
        )
    
    # 提交按钮
    st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)
    col_left, col_center, col_right = st.columns([1, 1, 1])
    with col_center:
        submit_button = st.button("🔍 查询数据", width='stretch', type="primary")
    
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
