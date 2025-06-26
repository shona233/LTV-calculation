import streamlit as st
import os
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import datetime
import tempfile
import zipfile
import io
import matplotlib.pyplot as plt
import matplotlib as mpl
import re
from matplotlib.font_manager import FontProperties
import seaborn as sns
from scipy.optimize import curve_fit

# 忽略警告
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl.styles.stylesheet')
warnings.filterwarnings('ignore', category=UserWarning,
                        message="Could not infer format, so each element will be parsed individually")

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 设置页面配置
st.set_page_config(
    page_title="LTV Analytics Platform",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📊"
)

# 蓝色系CSS样式
st.markdown("""
<style>
    /* 全局样式 */
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 30%, #334155 100%);
        min-height: 100vh;
    }
    
    .block-container {
        padding: 1rem 1rem 3rem 1rem;
        max-width: 100%;
        background: transparent;
    }
    
    /* 主标题区域 */
    .main-header {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        padding: 1.2rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(15, 23, 42, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.18);
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    .main-title {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1e293b 0%, #475569 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    
    .main-subtitle {
        color: #64748b;
        font-size: 1.1rem;
        font-weight: 400;
    }
    
    /* 卡片样式 */
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 20px rgba(15, 23, 42, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.18);
        margin-bottom: 1rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(15, 23, 42, 0.3);
    }
    
    /* 分界线 */
    .section-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, rgba(30, 41, 59, 0.3) 50%, transparent 100%);
        margin: 1rem 0;
        border-radius: 1px;
    }
    
    /* 指标卡片 */
    .metric-card {
        background: linear-gradient(135deg, #1e40af 0%, #2563eb 50%, #3b82f6 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 12px rgba(37, 99, 235, 0.3);
        margin-bottom: 0.8rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* 状态卡片 */
    .status-card {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #2563eb;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
        margin-bottom: 0.8rem;
    }
    
    /* 导航步骤样式 */
    .nav-container {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .nav-step {
        display: flex;
        align-items: center;
        margin-bottom: 0.5rem;
        padding: 0.8rem;
        border-radius: 8px;
        transition: all 0.3s ease;
        cursor: pointer;
        border: 1px solid transparent;
    }
    
    .nav-step:hover {
        background: rgba(37, 99, 235, 0.1);
        border-color: rgba(37, 99, 235, 0.3);
        transform: translateX(3px);
    }
    
    .nav-step.active {
        background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
    }
    
    .nav-step.completed {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(5, 150, 105, 0.3);
    }
    
    .nav-step.warning {
        background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(217, 119, 6, 0.3);
    }
    
    .step-number {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 1rem;
        font-weight: 600;
        flex-shrink: 0;
    }
    
    .step-content {
        flex: 1;
    }
    
    .step-title {
        font-weight: 600;
        margin-bottom: 0.2rem;
    }
    
    /* 说明文字样式 */
    .step-explanation {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.05) 0%, rgba(59, 130, 246, 0.08) 100%);
        border-left: 4px solid #2563eb;
        padding: 1.5rem;
        margin-top: 2rem;
        border-radius: 0 12px 12px 0;
        box-shadow: 0 2px 10px rgba(37, 99, 235, 0.1);
    }
    
    .step-explanation h4 {
        color: #1e40af;
        margin-bottom: 0.8rem;
        font-size: 1.1rem;
        font-weight: 700;
    }
    
    .step-explanation ul {
        margin: 0.5rem 0;
        padding-left: 1.5rem;
        list-style-type: disc;
    }
    
    .step-explanation li {
        margin-bottom: 0.5rem;
        color: #374151;
        line-height: 1.5;
    }
    
    .step-explanation strong {
        color: #1e40af;
        font-weight: 600;
    }
    
    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%);
    }
    
    /* 侧边栏样式 */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
    }
    
    /* 数据表格样式 */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1);
    }
    
    /* 文件上传区域 */
    .uploadedfile {
        border: 2px dashed #2563eb;
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        background: rgba(37, 99, 235, 0.05);
    }
    
    /* 选择框样式 */
    .stSelectbox label, .stMultiselect label, .stFileUploader label {
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    
    /* 标题样式 - 统一小标题大小 */
    h1, h2, h3, h4 {
        color: #1e293b;
        font-weight: 600;
        font-size: 1.1rem !important;
    }
    
    /* 成功/警告/错误消息 */
    .stSuccess {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white;
        border-radius: 8px;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
        color: white;
        border-radius: 8px;
    }
    
    .stError {
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
        color: white;
        border-radius: 8px;
    }
    
    /* 隐藏默认的Streamlit元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 响应式设计 */
    @media (max-width: 768px) {
        .main-title {
            font-size: 1.5rem;
        }
        
        .glass-card {
            padding: 1rem;
        }
        
        .metric-card {
            padding: 0.8rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# 默认渠道映射数据
DEFAULT_CHANNEL_MAPPING = {
    # 总体
    '9000': '总体',
    
    # 新媒体
    '500345': '新媒体', '500346': '新媒体', '500447': '新媒体', '500449': '新媒体', 
    '500450': '新媒体', '500531': '新媒体', '500542': '新媒体',
    
    # 应用宝
    '5007XS': '应用宝', '500349': '应用宝', '500350': '应用宝',
    
    # 鼎乐系列
    '500285': '鼎乐-盛世6',
    '500286': '鼎乐-盛世7',
    
    # 酷派
    '5108': '酷派', '5528': '酷派',
    
    # 新美系列
    '500275': '新美-北京2',
    '500274': '新美-北京1',
    
    # A_深圳蛋丁2
    '500316': 'A_深圳蛋丁2',
    
    # 主流厂商
    '500297': '荣耀',
    '5057': '华为',
    '5237': 'vivo',
    '5599': '小米',
    '5115': 'OPPO',
    
    # 网易
    '500471': '网易', '500480': '网易', '500481': '网易', '500482': '网易',
    
    # 华为非商店-品众
    '500337': '华为非商店-品众', '500338': '华为非商店-品众', '500343': '华为非商店-品众',
    '500445': '华为非商店-品众', '500383': '华为非商店-品众', '500444': '华为非商店-品众',
    '500441': '华为非商店-品众',
    
    # 魅族
    '5072': '魅族',
    
    # OPPO非商店
    '500287': 'OPPO非商店', '500288': 'OPPO非商店',
    
    # vivo非商店
    '5187': 'vivo非商店',
    
    # 百度sem系列
    '500398': '百度sem--百度时代安卓', '500400': '百度sem--百度时代安卓', '500404': '百度sem--百度时代安卓',
    '500402': '百度sem--百度时代ios', '500403': '百度sem--百度时代ios', '500405': '百度sem--百度时代ios',
    
    # 百青藤
    '500377': '百青藤-安卓', '500379': '百青藤-安卓', '500435': '百青藤-安卓', '500436': '百青藤-安卓',
    '500490': '百青藤-安卓', '500491': '百青藤-安卓', '500434': '百青藤-安卓', '500492': '百青藤-安卓',
    '500437': '百青藤-ios',
    
    # 小米非商店
    '500170': '小米非商店',
    
    # 华为非商店-星火
    '500532': '华为非商店-星火', '500533': '华为非商店-星火', '500534': '华为非商店-星火',
    '500537': '华为非商店-星火', '500538': '华为非商店-星火', '500539': '华为非商店-星火',
    '500540': '华为非商店-星火', '500541': '华为非商店-星火',
    
    # 微博系列
    '500504': '微博-蜜橘', '500505': '微博-蜜橘',
    '500367': '微博-央广', '500368': '微博-央广', '500369': '微博-央广',
    
    # 广点通
    '500498': '广点通', '500497': '广点通', '500500': '广点通',
    '500501': '广点通', '500496': '广点通', '500499': '广点通',
    
    # 网易易效
    '500514': '网易易效', '500515': '网易易效', '500516': '网易易效'
}

# 计算默认目标月份（2个月前）
def get_default_target_month():
    today = datetime.datetime.now()
    if today.month <= 2:
        target_year = today.year - 1
        target_month = today.month + 10
    else:
        target_year = today.year
        target_month = today.month - 2
    
    return f"{target_year}-{target_month:02d}"

# 主标题
st.markdown("""
<div class="main-header">
    <div class="main-title">智能用户生命周期价值分析系统</div>
    <div class="main-subtitle">基于分阶段数学建模的LTV精准预测平台</div>
</div>
""", unsafe_allow_html=True)

# 初始化session state
session_keys = [
    'channel_mapping', 'merged_data', 'cleaned_data', 'retention_data', 
    'lt_results', 'arpu_data', 'ltv_results', 'current_step', 'excluded_data'
]
for key in session_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# 设置默认值
if st.session_state.channel_mapping is None:
    st.session_state.channel_mapping = DEFAULT_CHANNEL_MAPPING
if st.session_state.current_step is None:
    st.session_state.current_step = 0
if st.session_state.excluded_data is None:
    st.session_state.excluded_data = []

# 分析步骤定义
ANALYSIS_STEPS = [
    {"name": "数据上传与汇总"},
    {"name": "异常数据剔除"},
    {"name": "留存率计算"},
    {"name": "LT拟合分析"},
    {"name": "ARPU计算"},
    {"name": "LTV结果报告"}
]

# 检查步骤完成状态
def get_step_status(step_index):
    """获取步骤状态：completed, active, warning, normal"""
    if step_index == st.session_state.current_step:
        return "active"
    
    # 检查是否已完成
    if step_index == 0 and st.session_state.merged_data is not None:
        return "completed"
    elif step_index == 1 and st.session_state.cleaned_data is not None:
        return "completed"
    elif step_index == 2 and st.session_state.retention_data is not None:
        return "completed"
    elif step_index == 3 and st.session_state.lt_results is not None:
        return "completed"
    elif step_index == 4 and st.session_state.arpu_data is not None:
        return "completed"
    elif step_index == 5 and st.session_state.ltv_results is not None:
        return "completed"
    
    # 检查是否有依赖警告
    elif step_index == 1 and st.session_state.merged_data is None:
        return "warning"
    elif step_index == 2 and st.session_state.merged_data is None:
        return "warning"
    elif step_index == 3 and st.session_state.retention_data is None:
        return "warning"
    elif step_index == 4 and st.session_state.lt_results is None:
        return "warning"
    elif step_index == 5 and (st.session_state.lt_results is None or st.session_state.arpu_data is None):
        return "warning"
    
    return "normal"

# 侧边栏导航
with st.sidebar:
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    st.markdown('<h4 style="text-align: center; margin-bottom: 1rem; color: #495057;">分析流程</h4>', unsafe_allow_html=True)
    
    # 创建导航步骤
    for i, step in enumerate(ANALYSIS_STEPS):
        step_status = get_step_status(i)
        
        # 使用按钮进行导航
        if st.button(f"{i+1}. {step['name']}", key=f"nav_{i}", 
                    use_container_width=True,
                    type="primary" if step_status == "active" else "secondary"):
            st.session_state.current_step = i
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 状态信息
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    st.markdown('<h4 style="text-align: center; margin-bottom: 1rem; color: #495057;">当前状态</h4>', unsafe_allow_html=True)
    
    # 数据状态
    status_items = [
        ("原始数据", "已完成" if st.session_state.merged_data is not None else "待处理"),
        ("清理数据", "已完成" if st.session_state.cleaned_data is not None else "待处理"),
        ("留存数据", "已完成" if st.session_state.retention_data is not None else "待处理"),
        ("LT结果", "已完成" if st.session_state.lt_results is not None else "待处理"),
        ("ARPU数据", "已完成" if st.session_state.arpu_data is not None else "待处理"),
        ("LTV结果", "已完成" if st.session_state.ltv_results is not None else "待处理")
    ]
    
    for status_name, status_text in status_items:
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; padding: 0.3rem 0; border-bottom: 1px solid #e9ecef;">
            <span style="font-size: 0.9rem;">{status_name}</span>
            <span style="font-size: 0.8rem; color: {'#059669' if status_text == '已完成' else '#6b7280'};">{status_text}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# 定义数学函数（使用第二个代码的函数）
def power_function(x, a, b):
    """幂函数：y = a * x^b"""
    return a * np.power(x, b)

def exponential_function(x, c, d):
    """指数函数：y = c * exp(d * x)"""
    return c * np.exp(d * x)

# 数据整合功能（使用第三个代码的逻辑）
def standardize_output_columns(df):
    """标准化输出列结构，确保包含指定的列顺序"""
    target_columns = [
        '数据来源', 'date', '数据来源_date',
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
        '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
        '21', '22', '23', '24', '25', '26', '27', '28', '29', '30',
        '数据来源_日期', '日期', '回传新增数', 'is_target_month', 'month', 'stat_date',
        'new', 'new_retain_1', 'new_retain_2', 'new_retain_3', 'new_retain_4', 'new_retain_5',
        'new_retain_6', 'new_retain_7', 'new_retain_8', 'new_retain_9', 'new_retain_10',
        'new_retain_11', 'new_retain_12', 'new_retain_13', 'new_retain_14', 'new_retain_15',
        'new_retain_16', 'new_retain_17', 'new_retain_18', 'new_retain_19', 'new_retain_20',
        'new_retain_21', 'new_retain_22', 'new_retain_23', 'new_retain_24', 'new_retain_25',
        'new_retain_26', 'new_retain_27', 'new_retain_28', 'new_retain_29', 'new_retain_30'
    ]

    result_df = pd.DataFrame()
    
    for col_name in target_columns:
        if col_name == '数据来源':
            result_df[col_name] = df[col_name] if col_name in df.columns else ''
        elif col_name == 'date':
            if col_name in df.columns:
                result_df[col_name] = df[col_name]
            elif 'stat_date' in df.columns:
                result_df[col_name] = df['stat_date']
            else:
                result_df[col_name] = ''
        elif col_name == '数据来源_date':
            data_source = df['数据来源'] if '数据来源' in df.columns else ''
            date_col = df['date'] if 'date' in df.columns else (df['stat_date'] if 'stat_date' in df.columns else '')
            result_df[col_name] = data_source.astype(str) + date_col.astype(str)
        elif col_name == '数据来源_日期':
            data_source = df['数据来源'] if '数据来源' in df.columns else ''
            date_col = df['日期'] if '日期' in df.columns else (
                df['date'] if 'date' in df.columns else (df['stat_date'] if 'stat_date' in df.columns else ''))
            result_df[col_name] = data_source.astype(str) + date_col.astype(str)
        else:
            result_df[col_name] = df[col_name] if col_name in df.columns else ''

    for col in df.columns:
        if col not in target_columns:
            result_df[col] = df[col]

    return result_df

def integrate_excel_files_streamlit(uploaded_files, target_month=None, channel_mapping=None):
    """Streamlit版本的Excel文件整合函数，使用第三个代码的完整逻辑"""
    if target_month is None:
        target_month = get_default_target_month()

    all_data = pd.DataFrame()
    processed_count = 0
    mapping_warnings = []

    for uploaded_file in uploaded_files:
        source_name = os.path.splitext(uploaded_file.name)[0]
        
        # 渠道映射
        if channel_mapping and source_name in channel_mapping:
            mapped_source = channel_mapping[source_name]
        else:
            mapped_source = source_name
            if channel_mapping:
                mapping_warnings.append(f"文件 '{source_name}' 未在渠道映射表中找到对应项，将使用原始文件名")
        
        try:
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names

            ocpx_sheet = None
            channel_sheet = None

            for sheet in sheet_names:
                if "ocpx监测留存数" in sheet:
                    ocpx_sheet = sheet
                if "监测渠道回传量" in sheet:
                    channel_sheet = sheet

            file_data = None

            if ocpx_sheet:
                ocpx_df = pd.read_excel(uploaded_file, sheet_name=ocpx_sheet)
                
                if channel_sheet:
                    channel_df = pd.read_excel(uploaded_file, sheet_name=channel_sheet)
                    if len(channel_df.columns) >= 2:
                        last_two_cols = channel_df.iloc[:, -2:]
                        ocpx_df = ocpx_df.copy()
                        for col_name in last_two_cols.columns:
                            ocpx_df[col_name] = last_two_cols[col_name].values[:len(ocpx_df)] if len(
                                last_two_cols) >= len(ocpx_df) else last_two_cols[col_name].values.tolist() + [
                                None] * (len(ocpx_df) - len(last_two_cols))
                
                file_data = ocpx_df
            else:
                file_data = pd.read_excel(uploaded_file, sheet_name=0)

            if file_data is not None and not file_data.empty:
                file_data_copy = file_data.copy()

                # 检查是否是新格式表
                has_stat_date = 'stat_date' in file_data_copy.columns
                retain_columns = [f'new_retain_{i}' for i in range(1, 31)]
                has_retain_columns = any(col in file_data_copy.columns for col in retain_columns)

                if has_stat_date and has_retain_columns:
                    # 新格式表处理
                    standardized_data = file_data_copy.copy()

                    if 'new' in standardized_data.columns:
                        standardized_data['回传新增数'] = standardized_data['new']

                    for i in range(1, 31):
                        retain_col = f'new_retain_{i}'
                        if retain_col in standardized_data.columns:
                            standardized_data[str(i)] = standardized_data[retain_col]

                    date_col = 'stat_date'
                    standardized_data[date_col] = pd.to_datetime(standardized_data[date_col], errors='coerce')
                    standardized_data[date_col] = standardized_data[date_col].dt.strftime('%Y-%m-%d')
                    standardized_data['日期'] = standardized_data[date_col]
                    standardized_data['month'] = standardized_data[date_col].str[:7]

                    filtered_data = standardized_data[standardized_data['month'] == target_month].copy()

                    if not filtered_data.empty:
                        filtered_data.insert(0, '数据来源', mapped_source)
                        filtered_data['date'] = filtered_data['stat_date']
                        all_data = pd.concat([all_data, filtered_data], ignore_index=True)
                        processed_count += 1

                else:
                    # 旧格式表处理
                    retention_col = None
                    for col in file_data_copy.columns:
                        if '留存天数' in str(col):
                            retention_col = col
                            break

                    date_col = None
                    for col in file_data_copy.columns:
                        if '日期' in str(col):
                            date_col = col
                            break

                    # 处理回传新增数列
                    if len(file_data_copy.columns) >= 2:
                        second_col = file_data_copy.columns[1]
                        file_data_copy['回传新增数'] = file_data_copy[second_col]

                    if date_col:
                        try:
                            file_data_copy[date_col] = pd.to_datetime(file_data_copy[date_col], errors='coerce')
                            file_data_copy['month'] = file_data_copy[date_col].dt.strftime('%Y-%m')
                            filtered_data = file_data_copy[file_data_copy['month'] == target_month].copy()
                            
                            if not filtered_data.empty:
                                filtered_data.insert(0, '数据来源', mapped_source)
                                if retention_col:
                                    filtered_data.rename(columns={retention_col: 'date'}, inplace=True)
                                else:
                                    filtered_data['date'] = filtered_data[date_col].dt.strftime('%Y-%m-%d')
                                
                                all_data = pd.concat([all_data, filtered_data], ignore_index=True)
                                processed_count += 1
                        except:
                            # 出错时保留所有数据
                            file_data_copy.insert(0, '数据来源', mapped_source)
                            if retention_col:
                                file_data_copy.rename(columns={retention_col: 'date'}, inplace=True)
                            all_data = pd.concat([all_data, file_data_copy], ignore_index=True)
                            processed_count += 1
                    else:
                        # 没有日期列，保留所有数据
                        file_data_copy.insert(0, '数据来源', mapped_source)
                        if retention_col:
                            file_data_copy.rename(columns={retention_col: 'date'}, inplace=True)
                        all_data = pd.concat([all_data, file_data_copy], ignore_index=True)
                        processed_count += 1

        except Exception as e:
            st.error(f"处理文件 {uploaded_file.name} 时出错: {str(e)}")

    if not all_data.empty:
        standardized_df = standardize_output_columns(all_data)
        return standardized_df, processed_count, mapping_warnings
    else:
        return None, 0, mapping_warnings

def parse_channel_mapping(channel_df):
    """解析渠道映射表，支持新的格式：第一列为渠道名，后续列为渠道号"""
    pid_to_channel = {}
    
    for _, row in channel_df.iterrows():
        channel_name = str(row.iloc[0]).strip()
        
        if pd.isna(channel_name) or channel_name == '' or channel_name == 'nan':
            continue
            
        for col_idx in range(1, len(row)):
            pid = row.iloc[col_idx]
            
            if pd.isna(pid) or str(pid).strip() in ['', 'nan', '　', ' ']:
                continue
                
            pid_str = str(pid).strip()
            if pid_str:
                pid_to_channel[pid_str] = channel_name
    
    return pid_to_channel

# 留存率计算（改进版，更接近第二个代码的逻辑）
def calculate_retention_rates_advanced(df):
    """计算留存率数据，转换为第二个代码兼容的格式"""
    retention_results = []
    
    data_sources = df['数据来源'].unique()
    
    for source in data_sources:
        source_data = df[df['数据来源'] == source].copy()
        
        # 收集所有有效的留存数据点
        all_days = []
        all_rates = []
        
        for _, row in source_data.iterrows():
            new_users = row.get('回传新增数', 0)
            
            if pd.isna(new_users) or new_users <= 0:
                continue
            
            # 从1到30天的留存数据
            for day in range(1, 31):
                day_col = str(day)
                if day_col in row and not pd.isna(row[day_col]):
                    retain_count = row[day_col]
                    if retain_count > 0:  # 只保留有效留存数据
                        retention_rate = retain_count / new_users
                        if 0 < retention_rate <= 1.5:  # 过滤异常值
                            all_days.append(day)
                            all_rates.append(retention_rate)
        
        if all_days:
            # 按天数分组，计算平均留存率
            df_temp = pd.DataFrame({'day': all_days, 'rate': all_rates})
            df_avg = df_temp.groupby('day')['rate'].mean().reset_index()
            
            retention_data = {
                'data_source': source,
                'days': df_avg['day'].values,
                'rates': df_avg['rate'].values
            }
            retention_results.append(retention_data)
    
    return retention_results

# LT拟合分析（使用第二个代码的完整逻辑）
def calculate_lt_advanced(retention_data, channel_name, lt_years=5):
    """使用第二个代码的分阶段LT计算逻辑"""
    # 渠道规则 - 完全按照第二个代码
    CHANNEL_RULES = {
        "华为": {"stage_2": [30, 120], "stage_3_base": [120, 220]},
        "小米": {"stage_2": [30, 190], "stage_3_base": [190, 290]},
        "oppo": {"stage_2": [30, 160], "stage_3_base": [160, 260]},
        "vivo": {"stage_2": [30, 150], "stage_3_base": [150, 250]},
        "iphone": {"stage_2": [30, 150], "stage_3_base": [150, 250]},
        "其他": {"stage_2": [30, 100], "stage_3_base": [100, 200]}
    }

    # 判断渠道类型
    if re.search(r'\d+月华为$', channel_name) or re.search(r'华为', channel_name):
        rules = CHANNEL_RULES["华为"]
    elif re.search(r'\d+月小米$', channel_name) or re.search(r'小米', channel_name):
        rules = CHANNEL_RULES["小米"]
    elif re.search(r'\d+月oppo$', channel_name) or re.search(r'\d+月OPPO$', channel_name) or re.search(r'oppo|OPPO', channel_name):
        rules = CHANNEL_RULES["oppo"]
    elif re.search(r'\d+月vivo$', channel_name) or re.search(r'vivo', channel_name):
        rules = CHANNEL_RULES["vivo"]
    elif re.search(r'\d+月[iI][pP]hone$', channel_name) or re.search(r'iphone|iPhone', channel_name):
        rules = CHANNEL_RULES["iphone"]
    else:
        rules = CHANNEL_RULES["其他"]
    
    stage_2_start, stage_2_end = rules["stage_2"]
    stage_3_base_start, stage_3_base_end = rules["stage_3_base"]
    max_days = lt_years * 365

    days = retention_data['days']
    rates = retention_data['rates']

    fit_params = {}

    try:
        # 第一阶段：1-30天幂函数拟合
        popt_power, _ = curve_fit(power_function, days, rates)
        a, b = popt_power
        fit_params["power"] = {"a": a, "b": b}

        # 生成完整的 1-30 天留存率
        days_full = np.arange(1, 31)
        rates_full = power_function(days_full, a, b)
        lt1_to_30 = np.sum(rates_full)

        # 第二阶段：使用幂函数延续预测
        days_stage_2 = np.arange(stage_2_start, stage_2_end + 1)
        rates_stage_2 = power_function(days_stage_2, a, b)
        lt_stage_2 = np.sum(rates_stage_2)

        # 第三阶段：指数函数拟合长期衰减
        try:
            days_stage_3_base = np.arange(stage_3_base_start, stage_3_base_end + 1)
            rates_stage_3_base = power_function(days_stage_3_base, a, b)

            # 指数拟合
            initial_c = rates_stage_3_base[0]
            initial_d = -0.001
            popt_exp, _ = curve_fit(
                exponential_function,
                days_stage_3_base,
                rates_stage_3_base,
                p0=[initial_c, initial_d],
                bounds=([0, -np.inf], [np.inf, 0])  # 限制 d < 0
            )
            c, d = popt_exp
            fit_params["exponential"] = {"c": c, "d": d}
            
            days_stage_3 = np.arange(stage_3_base_start, max_days + 1)
            rates_stage_3 = exponential_function(days_stage_3, c, d)
            lt_stage_3 = np.sum(rates_stage_3)
            
        except Exception as e:
            # 指数拟合失败，使用幂函数
            days_stage_3 = np.arange(stage_3_base_start, max_days + 1)
            rates_stage_3 = power_function(days_stage_3, a, b)
            lt_stage_3 = np.sum(rates_stage_3)

        # 总LT计算：1 + 第一阶段 + 第二阶段 + 第三阶段
        total_lt = 1.0 + lt1_to_30 + lt_stage_2 + lt_stage_3

        # 计算拟合度
        predicted_rates = power_function(days, a, b)
        r2_score = 1 - np.sum((rates - predicted_rates) ** 2) / np.sum((rates - np.mean(rates)) ** 2)

        return {
            'lt_value': total_lt,
            'fit_params': fit_params,
            'power_r2': max(0, min(1, r2_score)),
            'success': True,
            'model_used': 'power+exponential'
        }

    except Exception as e:
        return {
            'lt_value': 30.0,  # 默认值
            'fit_params': {},
            'power_r2': 0.0,
            'success': False,
            'model_used': 'default'
        }

# 显示依赖提示
def show_dependency_warning(required_step):
    """显示依赖提示"""
    st.warning(f"⚠️ 此步骤需要先完成「{required_step}」")
    st.info("您可以点击左侧导航直接跳转到对应步骤，或者继续查看当前步骤的功能介绍。")

# 获取当前页面
current_page = ANALYSIS_STEPS[st.session_state.current_step]["name"]

# ==================== 页面内容 ====================

if current_page == "数据上传与汇总":
    # 渠道映射配置
    with st.expander("渠道映射配置", expanded=False):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("### 当前配置状态")
            if st.session_state.channel_mapping:
                st.success(f"已配置 {len(st.session_state.channel_mapping)} 个渠道映射")
                st.info("正在使用默认渠道映射表")
            else:
                st.warning("未配置渠道映射")
        
        with col2:
            if st.session_state.channel_mapping:
                st.markdown("### 渠道映射示例")
                mapping_by_channel = {}
                for pid, channel in st.session_state.channel_mapping.items():
                    if channel not in mapping_by_channel:
                        mapping_by_channel[channel] = []
                    mapping_by_channel[channel].append(pid)
                
                count = 0
                for channel, pids in list(mapping_by_channel.items())[:5]:
                    st.code(f"{channel}: {', '.join(pids[:3])}{'...' if len(pids) > 3 else ''}")
                    count += 1
                
                if len(mapping_by_channel) > 5:
                    st.text(f"... 还有 {len(mapping_by_channel) - 5} 个渠道")
        
        # 自定义渠道映射文件上传
        st.markdown("### 上传自定义渠道映射表")
        channel_file = st.file_uploader(
            "选择渠道映射文件 (可选)",
            type=['xlsx', 'xls'],
            help="第一列为渠道名，后续列为对应的渠道号。如不上传将使用默认映射表"
        )
        
        if channel_file:
            try:
                channel_df = pd.read_excel(channel_file)
                custom_mapping = parse_channel_mapping(channel_df)
                st.session_state.channel_mapping = custom_mapping
                st.success(f"自定义渠道映射已加载，共 {len(custom_mapping)} 个映射")
                st.dataframe(channel_df.head(), use_container_width=True)
            except Exception as e:
                st.error(f"渠道映射文件读取失败: {str(e)}")
    
    # 分界线
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # 数据文件上传
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("数据文件处理")
    
    uploaded_files = st.file_uploader(
        "选择Excel数据文件",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        help="支持上传多个Excel文件，系统会自动解析留存数据，支持新旧两种数据格式"
    )
    
    # 目标月份选择
    default_month = get_default_target_month()
    target_month = st.text_input(
        "目标月份 (YYYY-MM)",
        value=default_month,
        help=f"当前默认为2个月前: {default_month}"
    )
    
    # 仅在有文件时显示状态信息和处理按钮
    if uploaded_files:
        st.info(f"已选择 {len(uploaded_files)} 个文件：{', '.join([f.name for f in uploaded_files])}")
        
        if st.button("开始处理数据", type="primary", use_container_width=True):
            with st.spinner("正在处理数据文件..."):
                try:
                    merged_data, processed_count, mapping_warnings = integrate_excel_files_streamlit(
                        uploaded_files, target_month, st.session_state.channel_mapping
                    )
                    
                    if merged_data is not None and not merged_data.empty:
                        st.session_state.merged_data = merged_data
                        
                        st.success(f"数据处理完成！成功处理 {processed_count} 个文件")
                        
                        if mapping_warnings:
                            st.warning("渠道映射提示:")
                            for warning in mapping_warnings:
                                st.write(f"• {warning}")
                            st.info("这不会影响后续的留存率计算和拟合分析")
                        
                        # 显示关键指标
                        st.subheader("数据概览")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                            st.markdown(f'<div class="metric-value">{len(merged_data):,}</div>', unsafe_allow_html=True)
                            st.markdown('<div class="metric-label">总记录数</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                            st.markdown(f'<div class="metric-value">{merged_data["数据来源"].nunique()}</div>', unsafe_allow_html=True)
                            st.markdown('<div class="metric-label">数据来源</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with col3:
                            total_new_users = merged_data['回传新增数'].sum()
                            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                            st.markdown(f'<div class="metric-value">{total_new_users:,.0f}</div>', unsafe_allow_html=True)
                            st.markdown('<div class="metric-label">总新增用户</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with col4:
                            date_range = f"{merged_data['date'].min()} 至 {merged_data['date'].max()}"
                            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                            st.markdown('<div class="metric-value">日期</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="metric-label">{date_range}</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # 数据预览
                        st.subheader("数据预览")
                        st.dataframe(merged_data.head(10), use_container_width=True)
                    
                    else:
                        st.error("未找到有效数据，请检查文件格式和目标月份设置")
                
                except Exception as e:
                    st.error(f"处理过程中出现错误：{str(e)}")
    else:
        st.info("请选择Excel文件开始数据处理")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 步骤说明
    st.markdown("""
    <div class="step-explanation">
        <h4>支持的文件格式与要求</h4>
        <ul>
            <li><strong>新格式数据表：</strong>包含stat_date列作为日期字段，new列作为新增用户数，new_retain_1到new_retain_30列作为1-30天留存数据</li>
            <li><strong>旧格式数据表：</strong>包含"留存天数"和"日期"列，以及标识为1-30的留存数据列</li>
            <li><strong>工作表识别：</strong>优先读取"ocpx监测留存数"工作表，如存在"监测渠道回传量"则自动合并相关列</li>
            <li><strong>渠道映射：</strong>支持通过映射表将文件名或渠道ID转换为标准渠道名称</li>
        </ul>
        
        <h4>数据处理流程</h4>
        <ul>
            <li><strong>格式识别：</strong>自动检测数据表格式，根据关键列名判断新旧格式</li>
            <li><strong>列标准化：</strong>将不同格式的列名统一转换为标准格式，确保后续处理一致性</li>
            <li><strong>时间筛选：</strong>根据目标月份筛选相关数据，保留目标月份及前后时间范围的记录</li>
            <li><strong>数据整合：</strong>将多个文件的数据按照统一的列结构合并，添加数据来源标识</li>
            <li><strong>质量检查：</strong>验证数据完整性，识别并处理缺失值和异常值</li>
        </ul>
        
        <h4>输出数据结构</h4>
        <ul>
            <li><strong>核心字段：</strong>数据来源、日期、新增用户数、1-30天留存数据</li>
            <li><strong>辅助字段：</strong>月份标识、目标月份标记、原始日期等</li>
            <li><strong>格式统一：</strong>所有数据按照预定义的列顺序排列，便于后续分析</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

elif current_page == "异常数据剔除":
    if st.session_state.merged_data is None:
        show_dependency_warning("数据上传与汇总")
    
    # 功能介绍
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("功能说明")
    st.markdown("""
    此步骤用于识别和剔除异常数据点，提高留存率计算的准确性。异常数据可能来源于系统错误、数据采集问题或特殊事件影响。
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.merged_data is not None:
        merged_data = st.session_state.merged_data
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("数据概览")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总记录数", f"{len(merged_data):,}")
        with col2:
            st.metric("数据来源数", merged_data['数据来源'].nunique())
        with col3:
            st.metric("已剔除记录", len(st.session_state.excluded_data))
        
        # 数据预览
        st.markdown("### 数据预览")
        display_cols = ['数据来源', 'date', '回传新增数', '1', '7', '15', '30']
        available_cols = [col for col in display_cols if col in merged_data.columns]
        st.dataframe(merged_data[available_cols].head(8), use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 异常数据剔除界面
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("异常数据剔除配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 按数据来源剔除")
            
            all_sources = merged_data['数据来源'].unique().tolist()
            excluded_sources = st.multiselect(
                "选择要剔除的数据来源",
                options=all_sources,
                help="选中的数据来源将被完全排除在留存率计算之外"
            )
            
            if excluded_sources:
                excluded_by_source = merged_data[merged_data['数据来源'].isin(excluded_sources)]
                st.info(f"将剔除 {len(excluded_by_source)} 条记录")
        
        with col2:
            st.markdown("### 按日期剔除")
            
            all_dates = sorted(merged_data['date'].unique().tolist())
            excluded_dates = st.multiselect(
                "选择要剔除的日期",
                options=all_dates,
                help="选中日期的所有数据将被排除在留存率计算之外"
            )
            
            if excluded_dates:
                excluded_by_date = merged_data[merged_data['date'].isin(excluded_dates)]
                st.info(f"将剔除 {len(excluded_by_date)} 条记录")
        
        # 数值条件剔除
        st.markdown("### 按数值条件剔除")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_new_users = st.number_input(
                "最小新增用户数阈值",
                min_value=0,
                value=0,
                help="低于此值的记录将被剔除，避免小样本偏差"
            )
        
        with col2:
            max_day1_retention = st.number_input(
                "Day1最大留存率阈值",
                min_value=0.0,
                max_value=2.0,
                value=1.5,
                step=0.1,
                help="Day1留存率超过此值的记录将被剔除（通常表示数据错误）"
            )
        
        with col3:
            min_retention_days = st.number_input(
                "最少有效留存天数",
                min_value=1,
                max_value=30,
                value=7,
                help="留存数据少于此天数的记录将被剔除"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 预览将被剔除的数据
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("剔除效果预览")
        
        # 计算所有剔除条件
        exclusion_mask = pd.Series([False] * len(merged_data), index=merged_data.index)
        
        if excluded_sources:
            source_mask = merged_data['数据来源'].isin(excluded_sources)
            exclusion_mask |= source_mask
        
        if excluded_dates:
            date_mask = merged_data['date'].isin(excluded_dates)
            exclusion_mask |= date_mask
        
        if min_new_users > 0:
            users_mask = merged_data['回传新增数'] < min_new_users
            exclusion_mask |= users_mask
        
        if '1' in merged_data.columns:
            day1_retention = merged_data['1'] / merged_data['回传新增数']
            retention_mask = day1_retention > max_day1_retention
            exclusion_mask |= retention_mask
        
        retention_cols = [str(i) for i in range(1, min(31, min_retention_days + 1)) if str(i) in merged_data.columns]
        if retention_cols:
            completeness_mask = merged_data[retention_cols].isna().sum(axis=1) > (len(retention_cols) - min_retention_days)
            exclusion_mask |= completeness_mask
        
        to_exclude = merged_data[exclusion_mask]
        to_keep = merged_data[~exclusion_mask]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 将被剔除的数据")
            st.markdown(f"**数量:** {len(to_exclude)} 条")
            if len(to_exclude) > 0:
                st.dataframe(to_exclude[available_cols].head(10), use_container_width=True)
        
        with col2:
            st.markdown("### 保留的数据")
            st.markdown(f"**数量:** {len(to_keep)} 条")
            if len(to_keep) > 0:
                st.dataframe(to_keep[available_cols].head(10), use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 确认剔除
        if st.button("确认剔除异常数据", type="primary", use_container_width=True):
            if len(to_exclude) > 0:
                excluded_records = []
                for _, row in to_exclude.iterrows():
                    excluded_records.append(f"{row['数据来源']} - {row['date']}")
                
                st.session_state.excluded_data = excluded_records
                st.session_state.cleaned_data = to_keep.copy()
                
                st.success(f"成功剔除 {len(to_exclude)} 条异常数据，保留 {len(to_keep)} 条有效数据")
                
                # 显示清理后的数据统计
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{len(to_keep):,}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">有效记录数</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{to_keep["数据来源"].nunique()}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">数据来源</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{len(to_exclude):,}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">剔除记录数</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col4:
                    retention_rate = len(to_keep) / len(merged_data) * 100
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{retention_rate:.1f}%</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">数据保留率</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                st.session_state.cleaned_data = merged_data.copy()
                st.info("未发现需要剔除的异常数据，所有数据将保留")
    
    # 步骤说明
    st.markdown("""
    <div class="step-explanation">
        <h4>异常数据识别原理</h4>
        <ul>
            <li><strong>渠道级异常：</strong>某些渠道可能存在系统性数据质量问题，需要整体排除以避免影响总体分析</li>
            <li><strong>时间点异常：</strong>特定日期可能受到外部事件影响（如系统维护、营销活动），导致数据不具代表性</li>
            <li><strong>样本量异常：</strong>新增用户数过少的记录缺乏统计意义，可能产生高方差的留存率估计</li>
            <li><strong>数值逻辑异常：</strong>留存率超过100%通常表示数据采集或计算错误</li>
            <li><strong>完整性异常：</strong>留存数据缺失过多会影响后续曲线拟合的准确性和稳定性</li>
        </ul>
        
        <h4>剔除策略与原则</h4>
        <ul>
            <li><strong>保守原则：</strong>优先保留数据，只在有明确证据表明异常时才剔除</li>
            <li><strong>业务导向：</strong>结合业务知识判断异常，避免过度依赖统计规则</li>
            <li><strong>可追溯性：</strong>记录所有剔除操作，保证分析过程的透明度和可重现性</li>
            <li><strong>影响评估：</strong>实时评估剔除操作对数据集规模和结构的影响</li>
        </ul>
        
        <h4>剔除后的数据质量保证</h4>
        <ul>
            <li><strong>样本代表性：</strong>确保剔除后的数据仍能代表目标用户群体的行为特征</li>
            <li><strong>时间连续性：</strong>保持足够的时间跨度以支持趋势分析</li>
            <li><strong>渠道覆盖性：</strong>保留主要渠道的数据以支持对比分析</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

elif current_page == "留存率计算":
    # 确定使用的数据源
    if st.session_state.cleaned_data is not None:
        working_data = st.session_state.cleaned_data
        data_source_info = "使用清理后的数据"
    elif st.session_state.merged_data is not None:
        working_data = st.session_state.merged_data
        data_source_info = "使用原始数据（未进行异常数据剔除）"
    else:
        working_data = None
        data_source_info = "无可用数据"
    
    if working_data is None:
        show_dependency_warning("数据上传与汇总")
    else:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("留存率计算配置")
        st.info(data_source_info)
        
        data_sources = working_data['数据来源'].unique()
        selected_sources = st.multiselect(
            "选择要分析的数据来源",
            options=data_sources,
            default=data_sources,
            help="可以选择一个或多个数据来源进行分析"
        )
        
        if selected_sources:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("选中数据来源", len(selected_sources))
            with col2:
                filtered_count = len(working_data[working_data['数据来源'].isin(selected_sources)])
                st.metric("相关记录数", f"{filtered_count:,}")
            with col3:
                st.metric("分析维度", "1-30天留存")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("计算留存率", type="primary", use_container_width=True):
            if selected_sources:
                with st.spinner("正在计算各渠道留存率..."):
                    filtered_data = working_data[working_data['数据来源'].isin(selected_sources)]
                    retention_results = calculate_retention_rates_advanced(filtered_data)
                    st.session_state.retention_data = retention_results
                    
                    st.success("留存率计算完成！")
                    
                    # 显示结果
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    st.subheader("留存率分析结果")
                    
                    for result in retention_results:
                        with st.expander(f"{result['data_source']} - 留存率详情", expanded=True):
                            days = result['days']
                            rates = result['rates']
                            
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                if len(rates) > 0:
                                    st.markdown("### 关键指标")
                                    
                                    # Day 1留存率
                                    day1_idx = np.where(days == 1)[0]
                                    if len(day1_idx) > 0:
                                        st.metric("Day 1 留存率", f"{rates[day1_idx[0]]*100:.2f}%")
                                    else:
                                        st.metric("Day 1 留存率", "N/A")
                                    
                                    # Day 7留存率
                                    day7_idx = np.where(days == 7)[0]
                                    if len(day7_idx) > 0:
                                        st.metric("Day 7 留存率", f"{rates[day7_idx[0]]*100:.2f}%")
                                    else:
                                        st.metric("Day 7 留存率", "N/A")
                                    
                                    # Day 30留存率
                                    day30_idx = np.where(days == 30)[0]
                                    if len(day30_idx) > 0:
                                        st.metric("Day 30 留存率", f"{rates[day30_idx[0]]*100:.2f}%")
                                    else:
                                        st.metric("Day 30 留存率", "N/A")
                                    
                                    st.metric("平均留存率", f"{np.mean(rates)*100:.2f}%")
                            
                            with col2:
                                if len(days) > 0:
                                    fig, ax = plt.subplots(figsize=(12, 6))
                                    
                                    # 使用蓝色系配色
                                    colors = plt.cm.Blues(np.linspace(0.4, 1, len(days)))
                                    scatter = ax.scatter(days, rates, c=colors, s=80, alpha=0.8, 
                                                       edgecolors='navy', linewidth=2)
                                    ax.plot(days, rates, '--', color='#1e40af', linewidth=2, alpha=0.8)
                                    
                                    ax.set_xlabel('留存天数', fontsize=12, fontweight='bold')
                                    ax.set_ylabel('留存率', fontsize=12, fontweight='bold')
                                    ax.set_title(f'{result["data_source"]} 留存率曲线', fontsize=14, fontweight='bold')
                                    ax.grid(True, alpha=0.3, linestyle='--')
                                    ax.set_ylim(0, max(rates) * 1.1)
                                    
                                    # 美化图表
                                    ax.spines['top'].set_visible(False)
                                    ax.spines['right'].set_visible(False)
                                    ax.spines['left'].set_linewidth(0.8)
                                    ax.spines['bottom'].set_linewidth(0.8)
                                    ax.spines['left'].set_color('#1e293b')
                                    ax.spines['bottom'].set_color('#1e293b')
                                    
                                    plt.tight_layout()
                                    st.pyplot(fig)
                                    plt.close()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error("请选择至少一个数据来源")
    
    # 步骤说明
    st.markdown("""
    <div class="step-explanation">
        <h4>留存率计算原理</h4>
        <ul>
            <li><strong>基础定义：</strong>第N天留存率 = 第N天仍活跃的用户数 / 初始新增用户数</li>
            <li><strong>数据来源：</strong>从预处理的数据表中提取1-30天的留存数据列</li>
            <li><strong>加权平均：</strong>当单个渠道包含多日数据时，按新增用户数进行加权平均处理</li>
            <li><strong>异常过滤：</strong>自动识别并过滤留存率为0、新增用户数为0或留存率异常高的记录</li>
        </ul>
        
        <h4>计算步骤详解</h4>
        <ul>
            <li><strong>数据提取：</strong>遍历每个数据来源，提取其所有有效的留存数据记录</li>
            <li><strong>比例计算：</strong>对每条记录的每一天，计算留存率 = 留存用户数 ÷ 新增用户数</li>
            <li><strong>质量控制：</strong>剔除留存率超过150%或小于等于0的异常值</li>
            <li><strong>聚合统计：</strong>按天数分组，计算每个渠道每天的平均留存率</li>
            <li><strong>结果封装：</strong>将计算结果转换为适合后续拟合分析的数据格式</li>
        </ul>
        
        <h4>输出数据结构</h4>
        <ul>
            <li><strong>渠道维度：</strong>每个数据来源生成独立的留存率曲线</li>
            <li><strong>时间维度：</strong>包含1-30天的留存率数据点</li>
            <li><strong>数据格式：</strong>days数组存储天数，rates数组存储对应的留存率</li>
            <li><strong>后续应用：</strong>为LT拟合分析提供标准化的输入数据</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

elif current_page == "LT拟合分析":
    if st.session_state.retention_data is None:
        show_dependency_warning("留存率计算")
    else:
        retention_data = st.session_state.retention_data
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("分阶段拟合参数配置")
        
        col1, col2 = st.columns(2)
        with col1:
            lt_years = st.number_input(
                "LT计算年限",
                min_value=1,
                max_value=10,
                value=5,
                help="设置计算用户生命周期的年数，影响第三阶段的计算范围"
            )
        
        with col2:
            st.metric("待分析渠道数", len(retention_data))
            st.metric("拟合策略", "三阶段建模")
        
        # 算法说明
        st.info("系统将采用三阶段分层建模：第一阶段(1-30天)使用幂函数拟合实际数据；第二阶段根据渠道类型延续幂函数预测；第三阶段使用指数函数建模长期衰减")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("开始LT拟合分析", type="primary", use_container_width=True):
            with st.spinner("正在进行分阶段拟合计算..."):
                # 执行LT拟合分析
                lt_results = []
                
                for retention_result in retention_data:
                    channel_name = retention_result['data_source']
                    lt_result = calculate_lt_advanced(retention_result, channel_name, lt_years)
                    
                    lt_results.append({
                        'data_source': channel_name,
                        'lt_value': lt_result['lt_value'],
                        'fit_success': lt_result['success'],
                        'fit_params': lt_result['fit_params'],
                        'power_r2': lt_result['power_r2'],
                        'model_used': lt_result['model_used']
                    })
                
                st.session_state.lt_results = lt_results
                
                st.success("LT拟合分析完成！")
                
                # 显示拟合结果概览
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.subheader("拟合结果概览")
                
                # 创建结果汇总表
                summary_data = []
                for result in lt_results:
                    summary_data.append({
                        '数据来源': result['data_source'],
                        'LT值': f"{result['lt_value']:.2f}",
                        '拟合状态': '成功' if result['fit_success'] else '失败',
                        '拟合模型': result['model_used'],
                        'R²得分': f"{result['power_r2']:.4f}"
                    })
                
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # LT值对比可视化
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.subheader("LT值对比分析")
                
                if lt_results:
                    # 按LT值排序
                    sorted_results = sorted(lt_results, key=lambda x: x['lt_value'])
                    sources = [r['data_source'] for r in sorted_results]
                    lt_values = [r['lt_value'] for r in sorted_results]
                    
                    fig, ax = plt.subplots(figsize=(14, 8))
                    
                    # 使用蓝色渐变
                    colors = plt.cm.Blues(np.linspace(0.4, 1, len(sources)))
                    bars = ax.bar(sources, lt_values, color=colors, alpha=0.8, 
                                 edgecolor='#1e40af', linewidth=2)
                    
                    # 添加数值标签
                    for bar, value in zip(bars, lt_values):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                               f'{value:.1f}', ha='center', va='bottom', 
                               fontweight='bold', color='#1e40af')
                    
                    ax.set_xlabel('数据来源', fontsize=12, fontweight='bold')
                    ax.set_ylabel('LT值 (天)', fontsize=12, fontweight='bold')
                    ax.set_title(f'各渠道{lt_years}年LT值对比 (按数值从低到高排序)', fontsize=14, fontweight='bold')
                    ax.tick_params(axis='x', rotation=45)
                    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
                    
                    # 美化图表
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.spines['left'].set_color('#1e293b')
                    ax.spines['bottom'].set_color('#1e293b')
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 拟合参数详情
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.subheader("拟合参数详情")
                
                for result in lt_results:
                    if result['fit_success'] and result['fit_params']:
                        with st.expander(f"{result['data_source']} - 拟合参数", expanded=False):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("### 幂函数参数 (第一、二阶段)")
                                if 'power' in result['fit_params']:
                                    params = result['fit_params']['power']
                                    st.write(f"**a (系数):** {params['a']:.6e}")
                                    st.write(f"**b (指数):** {params['b']:.6f}")
                                    st.write(f"**R² 拟合度:** {result['power_r2']:.4f}")
                            
                            with col2:
                                st.markdown("### 指数函数参数 (第三阶段)")
                                if 'exponential' in result['fit_params']:
                                    params = result['fit_params']['exponential']
                                    st.write(f"**c (基数):** {params['c']:.6e}")
                                    st.write(f"**d (衰减率):** {params['d']:.6f}")
                                else:
                                    st.write("使用幂函数延续预测")
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    # 步骤说明
    st.markdown("""
    <div class="step-explanation">
        <h4>分阶段LT拟合算法原理</h4>
        <ul>
            <li><strong>第一阶段 (1-30天)：</strong>使用幂函数 y = a × x^b 拟合实际观测的留存率数据，建立基础衰减模型</li>
            <li><strong>第二阶段 (30-X天)：</strong>根据渠道类型设定不同的时间范围，延续第一阶段的幂函数进行中期预测</li>
            <li><strong>第三阶段 (X天-终点)：</strong>使用指数函数 y = c × e^(d×x) 建模长期衰减过程，模拟用户自然流失</li>
            <li><strong>LT总值计算：</strong>LT = 1 + Σ(第一阶段) + Σ(第二阶段) + Σ(第三阶段)</li>
        </ul>
        
        <h4>渠道差异化建模策略</h4>
        <ul>
            <li><strong>华为渠道：</strong>第二阶段30-120天，第三阶段120-220天基准，适应华为用户的长期留存特征</li>
            <li><strong>小米渠道：</strong>第二阶段30-190天，第三阶段190-290天基准，反映小米用户群体的粘性</li>
            <li><strong>OPPO渠道：</strong>第二阶段30-160天，第三阶段160-260天基准</li>
            <li><strong>vivo渠道：</strong>第二阶段30-150天，第三阶段150-250天基准</li>
            <li><strong>iPhone渠道：</strong>第二阶段30-150天，第三阶段150-250天基准，考虑iOS用户行为</li>
            <li><strong>其他渠道：</strong>第二阶段30-100天，第三阶段100-200天基准，采用保守策略</li>
        </ul>
        
        <h4>数学模型与参数含义</h4>
        <ul>
            <li><strong>幂函数模型：</strong>y = a × x^b，其中a为初始留存强度，b为衰减速度（通常为负值）</li>
            <li><strong>指数函数模型：</strong>y = c × e^(d×x)，其中c为转换基准值，d为长期衰减率</li>
            <li><strong>拟合质量评估：</strong>使用R²决定系数评估第一阶段拟合效果，指导模型可靠性判断</li>
            <li><strong>参数约束：</strong>对指数函数的d参数施加负值约束，确保长期衰减的合理性</li>
        </ul>
        
        <h4>算法优势与适用性</h4>
        <ul>
            <li><strong>分阶段建模：</strong>避免单一函数在全生命周期范围内的拟合偏差</li>
            <li><strong>渠道自适应：</strong>根据不同渠道的用户行为特征调整建模策略</li>
            <li><strong>长期预测：</strong>结合短期实际数据和长期衰减理论，提高预测准确性</li>
            <li><strong>鲁棒性设计：</strong>当某阶段拟合失败时，自动回退到备用策略</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

elif current_page == "ARPU计算":
    if st.session_state.lt_results is None:
        show_dependency_warning("LT拟合分析")
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("ARPU数据处理")
    
    # ARPU数据上传
    arpu_file = st.file_uploader(
        "选择ARPU数据文件 (Excel格式)",
        type=['xlsx', 'xls'],
        help="上传包含各渠道用户平均收入数据的Excel文件"
    )
    
    if arpu_file:
        try:
            arpu_df = pd.read_excel(arpu_file)
            st.success("ARPU文件上传成功！")
            
            # 显示文件预览
            st.subheader("数据预览")
            st.dataframe(arpu_df.head(10), use_container_width=True)
            
            # 数据列选择与映射
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("数据列映射配置")
                
                source_col = st.selectbox(
                    "数据来源列",
                    options=arpu_df.columns,
                    help="选择标识不同渠道或数据来源的列"
                )
                
                arpu_col = st.selectbox(
                    "ARPU值列",
                    options=arpu_df.columns,
                    help="选择包含ARPU数值的列"
                )
                
                date_col = st.selectbox(
                    "日期列 (可选)",
                    options=['无'] + list(arpu_df.columns),
                    help="如果需要按时间维度分析，请选择日期列"
                )
            
            with col2:
                st.subheader("数据统计信息")
                
                if arpu_col in arpu_df.columns:
                    arpu_values = pd.to_numeric(arpu_df[arpu_col], errors='coerce')
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("平均ARPU", f"{arpu_values.mean():.2f}")
                        st.metric("最小值", f"{arpu_values.min():.2f}")
                        st.metric("最大值", f"{arpu_values.max():.2f}")
                    with col_b:
                        st.metric("有效记录数", f"{arpu_values.notna().sum():,}")
                        st.metric("缺失记录数", f"{arpu_values.isna().sum():,}")
                        st.metric("标准差", f"{arpu_values.std():.2f}")
            
            # 处理ARPU数据
            if st.button("处理并保存ARPU数据", type="primary", use_container_width=True):
                try:
                    processed_arpu = arpu_df.copy()
                    processed_arpu['data_source'] = processed_arpu[source_col].astype(str).str.strip()
                    processed_arpu['arpu_value'] = pd.to_numeric(processed_arpu[arpu_col], errors='coerce')
                    
                    if date_col != '无':
                        processed_arpu['date'] = processed_arpu[date_col]
                    
                    # 过滤有效数据并按数据来源汇总
                    valid_data = processed_arpu[processed_arpu['arpu_value'].notna() & (processed_arpu['arpu_value'] > 0)]
                    arpu_summary = valid_data.groupby('data_source')['arpu_value'].agg(['mean', 'count']).reset_index()
                    arpu_summary.columns = ['data_source', 'arpu_value', 'record_count']
                    
                    st.session_state.arpu_data = arpu_summary
                    
                    st.success("ARPU数据处理完成！")
                    
                    # 显示汇总结果
                    st.subheader("ARPU数据汇总结果")
                    
                    # 格式化显示
                    display_df = arpu_summary.copy()
                    display_df['arpu_value'] = display_df['arpu_value'].round(2)
                    display_df = display_df.rename(columns={
                        'data_source': '数据来源',
                        'arpu_value': 'ARPU均值',
                        'record_count': '记录数量'
                    })
                    
                    st.dataframe(display_df, use_container_width=True)
                    
                    # 显示统计信息
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("成功处理渠道数", len(arpu_summary))
                    with col2:
                        st.metric("总有效记录数", arpu_summary['record_count'].sum())
                    with col3:
                        st.metric("整体平均ARPU", f"{arpu_summary['arpu_value'].mean():.2f}")
                    
                except Exception as e:
                    st.error(f"ARPU数据处理失败：{str(e)}")
        
        except Exception as e:
            st.error(f"文件读取失败：{str(e)}")
    
    else:
        st.info("请上传ARPU数据文件，或使用下方的手动设置功能")
        
        # 手动设置ARPU选项
        st.subheader("手动设置ARPU值")
        
        if st.session_state.lt_results:
            st.markdown("为每个数据来源设置ARPU值：")
            
            arpu_inputs = {}
            
            # 为每个LT结果创建ARPU输入框
            col1, col2 = st.columns(2)
            for i, result in enumerate(st.session_state.lt_results):
                source = result['data_source']
                
                with col1 if i % 2 == 0 else col2:
                    arpu_value = st.number_input(
                        f"{source}",
                        min_value=0.0,
                        value=10.0,
                        step=0.01,
                        format="%.2f",
                        key=f"arpu_{source}",
                        help=f"设置{source}的ARPU值"
                    )
                    arpu_inputs[source] = arpu_value
            
            if st.button("保存手动ARPU设置", type="primary", use_container_width=True):
                arpu_df = pd.DataFrame([
                    {'data_source': source, 'arpu_value': value, 'record_count': 1} 
                    for source, value in arpu_inputs.items()
                ])
                
                st.session_state.arpu_data = arpu_df
                st.success("ARPU设置已保存！")
                
                # 显示保存的设置
                display_df = arpu_df.copy()
                display_df = display_df.rename(columns={
                    'data_source': '数据来源',
                    'arpu_value': 'ARPU值',
                    'record_count': '设置方式'
                })
                display_df['设置方式'] = '手动设置'
                st.dataframe(display_df[['数据来源', 'ARPU值', '设置方式']], use_container_width=True)
        
        else:
            st.info("请先完成LT拟合分析，然后再设置ARPU")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 步骤说明
    st.markdown("""
    <div class="step-explanation">
        <h4>ARPU数据要求与格式</h4>
        <ul>
            <li><strong>文件格式：</strong>支持Excel文件(.xlsx, .xls)，包含数据来源和ARPU值等关键字段</li>
            <li><strong>数据来源列：</strong>用于标识不同渠道、用户群体或业务线的字段，应与LT分析中的数据来源保持一致</li>
            <li><strong>ARPU值列：</strong>包含具体收入数值的字段，系统支持自动数据类型转换和异常值处理</li>
            <li><strong>日期列(可选)：</strong>如需要进行时间序列分析或周期性ARPU计算，可指定日期字段</li>
        </ul>
        
        <h4>数据处理与计算逻辑</h4>
        <ul>
            <li><strong>数据清洗：</strong>自动识别并转换数值格式，过滤空值、负值和异常值</li>
            <li><strong>分组聚合：</strong>按数据来源分组，计算每个渠道的平均ARPU值，处理多记录情况</li>
            <li><strong>质量控制：</strong>统计有效记录数量，评估数据完整性和可靠性</li>
            <li><strong>一致性检查：</strong>确保ARPU数据的渠道标识与LT分析结果匹配</li>
        </ul>
        
        <h4>手动设置与文件上传的选择</h4>
        <ul>
            <li><strong>文件上传适用场景：</strong>有完整的历史ARPU数据，需要批量处理多个渠道</li>
            <li><strong>手动设置适用场景：</strong>渠道数量较少，或需要基于业务经验设定ARPU基准值</li>
            <li><strong>混合模式：</strong>可先上传部分数据，再手动补充缺失渠道的ARPU值</li>
            <li><strong>数据优先级：</strong>文件上传的数据优先于手动设置，避免重复计算</li>
        </ul>
        
        <h4>ARPU数据的业务含义</h4>
        <ul>
            <li><strong>定义：</strong>Average Revenue Per User，衡量每个用户平均贡献的收入价值</li>
            <li><strong>时间周期：</strong>通常以月为单位计算，也可根据业务需要调整为季度或年度</li>
            <li><strong>计算范围：</strong>可包含广告收入、付费收入、增值服务收入等多种收入来源</li>
            <li><strong>渠道差异：</strong>不同获客渠道的用户质量和付费意愿存在显著差异，需要差异化分析</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

elif current_page == "LTV结果报告":
    # 检查必要数据是否存在
    if st.session_state.lt_results is None:
        show_dependency_warning("LT拟合分析")
    elif st.session_state.arpu_data is None:
        show_dependency_warning("ARPU计算")
    else:
        # 计算LTV
        lt_results = st.session_state.lt_results
        arpu_data = st.session_state.arpu_data
        
        # 合并LT和ARPU数据
        ltv_results = []
        
        for lt_result in lt_results:
            source = lt_result['data_source']
            lt_value = lt_result['lt_value']
            
            # 查找对应的ARPU值
            arpu_row = arpu_data[arpu_data['data_source'] == source]
            if not arpu_row.empty:
                arpu_value = arpu_row.iloc[0]['arpu_value']
            else:
                arpu_value = 0
                st.warning(f"渠道 '{source}' 未找到对应的ARPU数据，将使用0作为默认值")
            
            # 计算LTV
            ltv_value = lt_value * arpu_value
            
            ltv_results.append({
                'data_source': source,
                'lt_value': lt_value,
                'arpu_value': arpu_value,
                'ltv_value': ltv_value,
                'fit_success': lt_result['fit_success'],
                'model_used': lt_result.get('model_used', 'unknown')
            })
        
        st.session_state.ltv_results = ltv_results
        
        # 显示LTV计算结果
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("LTV综合计算结果")
        
        # 创建结果表格
        ltv_df = pd.DataFrame(ltv_results)
        display_df = ltv_df.copy()
        display_df = display_df.rename(columns={
            'data_source': '数据来源',
            'lt_value': 'LT值',
            'arpu_value': 'ARPU',
            'ltv_value': 'LTV',
            'fit_success': '拟合状态',
            'model_used': '使用模型'
        })
        
        # 格式化显示
        display_df['LT值'] = display_df['LT值'].round(2)
        display_df['ARPU'] = display_df['ARPU'].round(2)
        display_df['LTV'] = display_df['LTV'].round(2)
        display_df['拟合状态'] = display_df['拟合状态'].map({True: '成功', False: '失败'})
        
        st.dataframe(display_df, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 关键指标展示
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("核心业务指标")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_ltv = display_df['LTV'].mean()
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{avg_ltv:.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">平均LTV</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            max_ltv = display_df['LTV'].max()
            best_source = display_df.loc[display_df['LTV'].idxmax(), '数据来源']
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{max_ltv:.2f}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-label">最高LTV<br>({best_source})</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            avg_lt = display_df['LT值'].mean()
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{avg_lt:.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">平均LT值</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            avg_arpu = display_df['ARPU'].mean()
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{avg_arpu:.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">平均ARPU</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # LTV对比分析可视化
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("LTV对比分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 各渠道LTV排名")
            # LTV条形图
            if not display_df.empty:
                # 按LTV值排序
                sorted_df = display_df.sort_values('LTV', ascending=True)
                
                fig, ax = plt.subplots(figsize=(12, 8))
                
                # 使用蓝色渐变
                colors = plt.cm.Blues(np.linspace(0.4, 1, len(sorted_df)))
                bars = ax.barh(sorted_df['数据来源'], sorted_df['LTV'], color=colors, alpha=0.8, 
                              edgecolor='#1e40af', linewidth=1.5)
                
                # 添加数值标签
                for bar, value in zip(bars, sorted_df['LTV']):
                    width = bar.get_width()
                    ax.text(width + width*0.01, bar.get_y() + bar.get_height()/2,
                           f'{value:.1f}', ha='left', va='center', 
                           fontweight='bold', color='#1e40af')
                
                ax.set_xlabel('LTV值', fontsize=12, fontweight='bold')
                ax.set_ylabel('数据来源', fontsize=12, fontweight='bold')
                ax.set_title('各渠道LTV值对比', fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.3, axis='x', linestyle='--')
                
                # 美化图表
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_color('#1e293b')
                ax.spines['bottom'].set_color('#1e293b')
                
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
        
        with col2:
            st.markdown("### LT与ARPU关系分析")
            # LT vs ARPU散点图
            if not display_df.empty:
                fig, ax = plt.subplots(figsize=(12, 8))
                scatter = ax.scatter(display_df['LT值'], display_df['ARPU'], 
                                   c=display_df['LTV'], s=200, alpha=0.8, cmap='Blues',
                                   edgecolors='#1e40af', linewidth=2)
                
                # 添加数据源标签
                for i, source in enumerate(display_df['数据来源']):
                    ax.annotate(source, (display_df['LT值'].iloc[i], display_df['ARPU'].iloc[i]),
                               xytext=(5, 5), textcoords='offset points', 
                               fontsize=9, fontweight='bold', color='#1e40af')
                
                ax.set_xlabel('LT值 (天)', fontsize=12, fontweight='bold')
                ax.set_ylabel('ARPU', fontsize=12, fontweight='bold')
                ax.set_title('LT值与ARPU关系图', fontsize=14, fontweight='bold')
                
                # 添加颜色条
                cbar = plt.colorbar(scatter)
                cbar.set_label('LTV值', fontsize=12, fontweight='bold')
                
                # 美化图表
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_color('#1e293b')
                ax.spines['bottom'].set_color('#1e293b')
                ax.grid(True, alpha=0.3, linestyle='--')
                
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 数据导出功能
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("分析结果导出")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV导出
            export_df = display_df.copy()
            csv_data = export_df.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(
                label="下载LTV分析结果 (CSV)",
                data=csv_data,
                file_name=f"LTV_Analysis_Results_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # 详细报告导出
            report_text = f"""
LTV用户生命周期价值分析报告
===========================================
生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

执行摘要
-----------
本报告基于分阶段数学建模方法，对 {len(display_df)} 个数据来源进行了用户生命周期价值分析。

核心指标汇总
-----------
• 参与分析的渠道数量: {len(display_df)}
• 平均LTV: {display_df['LTV'].mean():.2f}
• 最高LTV: {display_df['LTV'].max():.2f} ({display_df.loc[display_df['LTV'].idxmax(), '数据来源']})
• 最低LTV: {display_df['LTV'].min():.2f} ({display_df.loc[display_df['LTV'].idxmin(), '数据来源']})
• 平均LT值: {display_df['LT值'].mean():.2f} 天
• 平均ARPU: {display_df['ARPU'].mean():.2f}

各渠道详细结果
-----------"""
            
            for _, row in display_df.iterrows():
                report_text += f"""
{row['数据来源']}:
  • LT值: {row['LT值']:.2f} 天
  • ARPU: {row['ARPU']:.2f}
  • LTV: {row['LTV']:.2f}
  • 拟合状态: {row['拟合状态']}
  • 使用模型: {row['使用模型']}
"""
            
            report_text += f"""

分析方法说明
-----------
本分析采用三阶段分层建模方法：
1. 第一阶段(1-30天): 幂函数拟合实际留存数据
2. 第二阶段: 根据渠道类型延续幂函数预测
3. 第三阶段: 指数函数建模长期衰减

计算公式: LTV = LT × ARPU

报告生成: LTV智能分析平台 v2.0
"""
            
            st.download_button(
                label="下载详细分析报告 (TXT)",
                data=report_text,
                file_name=f"LTV_Detailed_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 步骤说明
    st.markdown("""
    <div class="step-explanation">
        <h4>LTV计算公式与业务含义</h4>
        <ul>
            <li><strong>基础公式：</strong>LTV = LT × ARPU，即用户生命周期价值等于生命周期天数乘以平均每用户收入</li>
            <li><strong>LT来源：</strong>通过三阶段数学拟合得到的用户生命周期预测值，单位为天</li>
            <li><strong>ARPU来源：</strong>基于历史数据计算或业务设定的平均每用户收入，反映用户价值</li>
            <li><strong>业务意义：</strong>LTV表示获取一个新用户在整个生命周期内预期能够产生的总收入价值</li>
        </ul>
        
        <h4>LTV分析的关键应用场景</h4>
        <ul>
            <li><strong>渠道价值评估：</strong>识别最具价值的用户获取渠道，优化营销预算分配</li>
            <li><strong>获客成本优化：</strong>将LTV与CAC(客户获取成本)对比，确保投入产出的合理性</li>
            <li><strong>用户分群策略：</strong>基于LTV差异制定差异化的用户运营和产品策略</li>
            <li><strong>商业模式验证：</strong>评估现有商业模式的可持续性和增长潜力</li>
        </ul>
        
        <h4>LT与ARPU的关系解读</h4>
        <ul>
            <li><strong>高LT高ARPU：</strong>理想渠道，用户既留存时间长又付费能力强</li>
            <li><strong>高LT低ARPU：</strong>潜力渠道，可通过提升变现能力进一步优化</li>
            <li><strong>低LT高ARPU：</strong>短期价值渠道，需要关注用户留存优化</li>
            <li><strong>低LT低ARPU：</strong>需要重点优化或考虑减少投入的渠道</li>
        </ul>
        
        <h4>结果应用建议</h4>
        <ul>
            <li><strong>定期更新：</strong>建议每季度更新一次LTV分析，跟踪趋势变化</li>
            <li><strong>细分分析：</strong>可按用户属性、地域、时间等维度进一步细分分析</li>
            <li><strong>预测校准：</strong>定期将预测结果与实际表现对比，校准模型参数</li>
            <li><strong>决策支持：</strong>将LTV分析结果纳入营销决策、产品规划和投资评估流程</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# 底部信息
with st.sidebar:
    st.markdown("---")
    st.markdown("""
    <div class="nav-container">
        <h4 style="text-align: center; color: #495057;">使用指南</h4>
        <p style="font-size: 0.9rem; color: #6c757d; text-align: center;">
        点击上方步骤可直接跳转，系统会自动检查依赖关系并提供相应提示。
        </p>
        <p style="font-size: 0.8rem; color: #adb5bd; text-align: center;">
        LTV智能分析平台 v2.0<br>
        基于分阶段数学建模
        </p>
    </div>
    """, unsafe_allow_html=True)
