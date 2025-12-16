"""
数据列名中文映射配置
用于将数据库字段名翻译为中文显示名称
"""

# 理化指标表列名映射
PHYSICOCHEMICAL_COLUMNS_CN = {
    # 基础信息
    'production_date': '生产日期',
    'fiscal_year': '实际年份',
    'work_year': '工作年度',
    'round_number': '轮次',
    'team_name': '班组',
    'pit_no': '窖池',
    'workshop': '车间',
    
    # 入池上层理化指标
    'entry_moisture_upper': '入池上层水分',
    'entry_alcohol_upper': '入池上层酒分',
    'entry_acidity_upper': '入池上层酸度',
    'entry_starch_upper': '入池上层淀粉',
    'entry_sugar_upper': '入池上层还原糖',
    
    # 入池下层理化指标
    'entry_moisture_lower': '入池下层水分',
    'entry_alcohol_lower': '入池下层酒分',
    'entry_acidity_lower': '入池下层酸度',
    'entry_starch_lower': '入池下层淀粉',
    'entry_sugar_lower': '入池下层还原糖',
    
    # 出池上层理化指标
    'exit_moisture_upper': '出池上层水分',
    'exit_alcohol_upper': '出池上层酒分',
    'exit_acidity_upper': '出池上层酸度',
    'exit_starch_upper': '出池上层淀粉',
    'exit_sugar_upper': '出池上层还原糖',
    
    # 出池下层理化指标
    'exit_moisture_lower': '出池下层水分',
    'exit_alcohol_lower': '出池下层酒分',
    'exit_acidity_lower': '出池下层酸度',
    'exit_starch_lower': '出池下层淀粉',
    'exit_sugar_lower': '出池下层还原糖',
}

# 原酒指标表列名映射
LIQUOR_OUTPUT_COLUMNS_CN = {
    # 基础信息
    'production_date': '生产日期',
    'fiscal_year': '实际年份',
    'work_year': '工作年度',
    'round_number': '轮次',
    'team_name': '班组',
    'pit_no': '窖池',
    'workshop': '车间',
    
    # 段次类型
    'segment_type': '段次',
    'segment_name': '段次名称',
    
    # 原酒指标
    'quantity_kg': '原酒产量(Kg)',
    'ethyl_hexanoate': '己酸乙酯(g/L)',
}

# 温度数据表列名映射
TEMPERATURE_COLUMNS_CN = {
    # 基础信息
    'production_date': '生产日期',
    'fiscal_year': '实际年份',
    'work_year': '工作年度',
    'round_number': '轮次',
    'team_name': '班组',
    'pit_no': '窖池',
    'workshop': '车间',
    
    # 发酵特征值
    'temp_peak': '顶温(℃)',
    'days_to_peak': '达到顶温天数',
    'peak_duration': '顶温持续天数',
    'temp_rise_range': '升温幅度(℃)',
    'temp_end': '终止温度(℃)',
    
    # 工艺操作温度
    'starter_activation_temp': '酒曲活化温度(℃)',
    'grains_entry_temp': '酒醅入池温度(℃)',
    'distillation_temp': '馏酒温度(℃)',
    
    # 温度记录
    'day_number': '发酵天数',
    'temperature': '温度(℃)',
}

# 获取指定表的列名映射
def get_column_names_cn(table_name):
    """
    根据表名获取对应的列名中文映射
    
    Args:
        table_name: 表名

    Returns:
        dict: 列名中文映射字典
    """
    mapping = {
        'physicochemical': PHYSICOCHEMICAL_COLUMNS_CN,
        'liquor_output': LIQUOR_OUTPUT_COLUMNS_CN,
        'temperature': TEMPERATURE_COLUMNS_CN,
    }
    return mapping.get(table_name, {})


# 默认隐藏的列（用于完整数据模式）
DEFAULT_HIDDEN_COLUMNS = {
    'physicochemical': ['实际年份', '工作年度', '车间', '班组'],
    'liquor_output': ['实际年份', '工作年度', '车间', '班组'],
    'temperature': ['实际年份', '工作年度', '车间', '班组'],
}


# 核心显示列
CORE_DISPLAY_COLUMNS = {
    'physicochemical': [
        '生产日期', '轮次', '窖池',
        '入池上层水分', '入池下层水分',
        '入池上层酒分', '入池下层酒分',
        '入池上层酸度', '入池下层酸度',
        '入池上层淀粉', '入池下层淀粉',
        '入池上层还原糖', '入池下层还原糖',
        '出池上层水分', '出池下层水分',
        '出池上层酒分', '出池下层酒分',
        '出池上层酸度', '出池下层酸度',
        '出池上层淀粉', '出池下层淀粉',
        '出池上层还原糖', '出池下层还原糖'
    ],
    'liquor_output': [
        '生产日期', '轮次', '窖池', '段次名称', '原酒产量(Kg)', '己酸乙酯(g/L)'
    ],
    'temperature': [
        '生产日期', '轮次', '窖池', 
        '顶温(℃)', '达到顶温天数', '顶温持续天数', '升温幅度(℃)', '终止温度(℃)',
        '酒曲活化温度(℃)', '酒醅入池温度(℃)', '馏酒温度(℃)'
    ]
}
