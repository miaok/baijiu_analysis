import streamlit as st

# 页面配置
st.set_page_config(
    page_title="白酒生产数据分析平台",
    page_icon="🍶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 主页标题
st.title("🍶 白酒生产数据分析平台")

st.markdown("""
### 欢迎使用白酒生产数据分析系统

请从左侧菜单选择分析页面：

- **理化指标** - 查看和分析入池/出池理化指标数据
- **原酒指标** - 分析原酒产量和质量指标
- **温度监控** - 监控发酵温度变化趋势及工艺参数

---

#### 系统说明
本系统基于白酒生产数据库，提供多维度数据筛选、可视化分析和报表导出功能。
""")

# 添加侧边栏说明
with st.sidebar:
    st.markdown("### 📊 数据分析导航")
    st.info("请从上方菜单中选择要分析的数据类型")
