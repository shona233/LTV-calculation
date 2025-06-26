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
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.18);
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1e293b 0%, #475569 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
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
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px rgba(15, 23, 42, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.18);
        margin-bottom: 1.5rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(15, 23, 42, 0.4);
    }
    
    /* 指标卡片 */
    .metric-card {
        background: linear-gradient(135deg, #1e40af 0%, #2563eb 50%, #3b82f6 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(37, 99, 235, 0.3);
        margin-bottom: 1rem;
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
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 4px solid #2563eb;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);
        margin-bottom: 1rem;
    }
    
    /* 进度指示器 */
    .progress-container {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    .progress-step {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        padding: 0.5rem;
        border-radius: 8px;
        transition: background-color 0.3s ease;
    }
    
    .progress-step.active {
        background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%);
        color: white;
    }
    
    .progress-step.completed {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white;
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
    
    /* 标题样式 */
    h1, h2, h3 {
        color: #1e293b;
        font-weight: 600;
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
            font-size: 2rem;
        }
        
        .glass-card {
            padding: 1rem;
        }
        
        .metric-card {
            padding: 1rem;
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
    # 计算2个月前
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
    <div class="main-title" style="font-size: 1.8rem;">智能用户生命周期价值分析系统</div>
</div>
""", unsafe_allow_html=True)

# 初始化session state
session_keys = [
    'channel_mapping', 'merged_data', 'retention_data', 
    'lt_results', 'arpu_data', 'ltv_results', 'current_step'
]
for key in session_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# 设置默认值
if st.session_state.channel_mapping is None:
    st.session_state.channel_mapping = DEFAULT_CHANNEL_MAPPING
if st.session_state.current_step is None:
    st.session_state.current_step = 0

# 分析步骤定义
ANALYSIS_STEPS = [
    {"name": "数据上传与汇总", "icon": "01", "desc": "上传原始数据文件"},
    {"name": "留存率计算", "icon": "02", "desc": "计算用户留存率"},
    {"name": "LT拟合分析", "icon": "03", "desc": "拟合生命周期曲线"},
    {"name": "ARPU计算", "icon": "04", "desc": "设置/计算用户价值"},
    {"name": "LTV结果报告", "icon": "05", "desc": "生成最终报告"}
]

# 侧边栏导航
with st.sidebar:
    st.markdown("""
    <div class="progress-container">
        <h3 style="text-align: center; margin-bottom: 1.5rem; color: #495057;">分析流程</h3>
    """, unsafe_allow_html=True)
    
    # 进度指示器
    for i, step in enumerate(ANALYSIS_STEPS):
        step_class = ""
        if i < st.session_state.current_step:
            step_class = "completed"
        elif i == st.session_state.current_step:
            step_class = "active"
        
        st.markdown(f"""
        <div class="progress-step {step_class}">
            <div class="step-number">{step['icon']}</div>
            <div>
                <strong>{step['name']}</strong><br>
                <small>{step['desc']}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 页面选择
    page = st.selectbox(
        "选择分析模块",
        [step["name"] for step in ANALYSIS_STEPS],
        index=st.session_state.current_step,
        label_visibility="collapsed"
    )
    
    # 更新当前步骤
    st.session_state.current_step = [step["name"] for step in ANALYSIS_STEPS].index(page)

# 数据整合功能（保留原有逻辑）
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
    """Streamlit版本的Excel文件整合函数"""
    if target_month is None:
        target_month = get_default_target_month()

    all_data = pd.DataFrame()
    processed_count = 0

    for uploaded_file in uploaded_files:
        source_name = os.path.splitext(uploaded_file.name)[0]
        
        # 如果有渠道映射，尝试根据文件名映射渠道
        if channel_mapping and source_name in channel_mapping:
            mapped_source = channel_mapping[source_name]
        else:
            mapped_source = source_name
        
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
                    # 处理旧格式表的逻辑（简化版）
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
                            # 如果日期处理失败，保留所有数据
                            file_data_copy.insert(0, '数据来源', mapped_source)
                            if retention_col:
                                file_data_copy.rename(columns={retention_col: 'date'}, inplace=True)
                            all_data = pd.concat([all_data, file_data_copy], ignore_index=True)
                            processed_count += 1

        except Exception as e:
            st.error(f"处理文件 {uploaded_file.name} 时出错: {str(e)}")

    if not all_data.empty:
        standardized_df = standardize_output_columns(all_data)
        return standardized_df, processed_count
    else:
        return None, 0

def parse_channel_mapping(channel_df):
    """解析渠道映射表，支持新的格式：第一列为渠道名，后续列为渠道号"""
    pid_to_channel = {}
    
    for _, row in channel_df.iterrows():
        channel_name = str(row.iloc[0]).strip()  # 第一列是渠道名
        
        # 跳过空行或无效的渠道名
        if pd.isna(channel_name) or channel_name == '' or channel_name == 'nan':
            continue
            
        # 处理后续列的渠道号
        for col_idx in range(1, len(row)):
            pid = row.iloc[col_idx]
            
            # 处理各种可能的空值表示
            if pd.isna(pid) or str(pid).strip() in ['', 'nan', '　', ' ']:
                continue
                
            pid_str = str(pid).strip()
            if pid_str:
                pid_to_channel[pid_str] = channel_name
    
    return pid_to_channel

# 拟合计算功能（用numpy替代scipy）
def numpy_curve_fit_power(x, y, max_iter=1000, tolerance=1e-8):
    """
    使用numpy实现幂函数拟合：y = a * x^b
    通过对数线性回归：log(y) = log(a) + b*log(x)
    """
    try:
        # 过滤掉非正数据
        valid_mask = (x > 0) & (y > 0) & np.isfinite(x) & np.isfinite(y)
        if np.sum(valid_mask) < 2:
            return [1.0, -0.5], True  # 默认参数
        
        x_valid = x[valid_mask]
        y_valid = y[valid_mask]
        
        # 对数变换
        log_x = np.log(x_valid)
        log_y = np.log(y_valid)
        
        # 线性回归: log_y = log_a + b * log_x
        # 构建设计矩阵
        X = np.column_stack([np.ones(len(log_x)), log_x])
        
        # 最小二乘解
        coeffs = np.linalg.lstsq(X, log_y, rcond=None)[0]
        log_a, b = coeffs
        a = np.exp(log_a)
        
        return [a, b], True
        
    except Exception as e:
        print(f"幂函数拟合失败: {e}")
        return [1.0, -0.5], False

def numpy_curve_fit_exponential(x, y, initial_c=None, initial_d=-0.001, max_iter=1000):
    """
    使用numpy实现指数函数拟合：y = c * exp(d * x)
    通过对数线性回归：log(y) = log(c) + d*x
    """
    try:
        # 过滤掉非正数据
        valid_mask = (y > 0) & np.isfinite(x) & np.isfinite(y)
        if np.sum(valid_mask) < 2:
            return [initial_c or 1.0, initial_d], True
        
        x_valid = x[valid_mask]
        y_valid = y[valid_mask]
        
        # 对数变换
        log_y = np.log(y_valid)
        
        # 线性回归: log_y = log_c + d * x
        # 构建设计矩阵
        X = np.column_stack([np.ones(len(x_valid)), x_valid])
        
        # 最小二乘解
        coeffs = np.linalg.lstsq(X, log_y, rcond=None)[0]
        log_c, d = coeffs
        c = np.exp(log_c)
        
        # 检查d是否为负数（指数衰减）
        if d > 0:
            d = -abs(d)  # 强制为负数，确保衰减
        
        return [c, d], True
        
    except Exception as e:
        print(f"指数函数拟合失败: {e}")
        return [initial_c or 1.0, initial_d], False

def calculate_r_squared(y_true, y_pred):
    """计算R²值"""
    try:
        # 过滤掉无效值
        valid_mask = np.isfinite(y_true) & np.isfinite(y_pred)
        if np.sum(valid_mask) < 2:
            return 0.0
        
        y_true_valid = y_true[valid_mask]
        y_pred_valid = y_pred[valid_mask]
        
        # 计算总平方和
        ss_tot = np.sum((y_true_valid - np.mean(y_true_valid)) ** 2)
        
        # 计算残差平方和
        ss_res = np.sum((y_true_valid - y_pred_valid) ** 2)
        
        # 计算R²
        if ss_tot == 0:
            return 1.0 if ss_res == 0 else 0.0
        
        r_squared = 1 - (ss_res / ss_tot)
        return max(0.0, min(1.0, r_squared))  # 确保在[0,1]范围内
        
    except Exception as e:
        print(f"计算R²失败: {e}")
        return 0.0

def calculate_retention_rates(df):
    """计算留存率数据"""
    retention_results = []
    
    # 获取数据来源列表
    data_sources = df['数据来源'].unique()
    
    for source in data_sources:
        source_data = df[df['数据来源'] == source].copy()
        
        # 按日期分组计算加权平均留存率
        daily_retention = {}
        
        for _, row in source_data.iterrows():
            date = row['date']
            new_users = row.get('回传新增数', 0)
            
            if pd.isna(new_users) or new_users <= 0:
                continue
            
            for day in range(1, 31):
                day_col = str(day)
                if day_col in row and not pd.isna(row[day_col]):
                    retain_count = row[day_col]
                    retention_rate = retain_count / new_users if new_users > 0 else 0
                    
                    if date not in daily_retention:
                        daily_retention[date] = {}
                    
                    daily_retention[date][day] = {
                        'rate': retention_rate,
                        'weight': new_users,
                        'retain_count': retain_count,
                        'new_users': new_users
                    }
        
        # 计算整体加权平均留存率
        overall_retention = {}
        for day in range(1, 31):
            total_weighted_rate = 0
            total_weight = 0
            
            for date in daily_retention:
                if day in daily_retention[date]:
                    rate = daily_retention[date][day]['rate']
                    weight = daily_retention[date][day]['weight']
                    total_weighted_rate += rate * weight
                    total_weight += weight
            
            if total_weight > 0:
                overall_retention[day] = total_weighted_rate / total_weight
            else:
                overall_retention[day] = 0
        
        retention_results.append({
            'data_source': source,
            'retention_rates': overall_retention,
            'daily_data': daily_retention
        })
    
    return retention_results

def fit_retention_curves(retention_results):
    """对留存率进行曲线拟合"""
    fitting_results = []
    
    for result in retention_results:
        source = result['data_source']
        retention_rates = result['retention_rates']
        
        # 准备拟合数据
        days = []
        rates = []
        
        for day in range(1, 31):
            if day in retention_rates and retention_rates[day] > 0:
                days.append(day)
                rates.append(retention_rates[day])
        
        if len(days) < 3:
            # 数据点太少，跳过拟合
            fitting_results.append({
                'data_source': source,
                'power_params': [1.0, -0.5],
                'power_r2': 0.0,
                'exp_params': [1.0, -0.1],
                'exp_r2': 0.0,
                'best_model': 'power',
                'days': days,
                'rates': rates
            })
            continue
        
        days_array = np.array(days)
        rates_array = np.array(rates)
        
        # 幂函数拟合
        power_params, power_success = numpy_curve_fit_power(days_array, rates_array)
        if power_success:
            power_pred = power_params[0] * (days_array ** power_params[1])
            power_r2 = calculate_r_squared(rates_array, power_pred)
        else:
            power_r2 = 0.0
        
        # 指数函数拟合
        exp_params, exp_success = numpy_curve_fit_exponential(days_array, rates_array)
        if exp_success:
            exp_pred = exp_params[0] * np.exp(exp_params[1] * days_array)
            exp_r2 = calculate_r_squared(rates_array, exp_pred)
        else:
            exp_r2 = 0.0
        
        # 选择最佳模型
        best_model = 'power' if power_r2 >= exp_r2 else 'exponential'
        
        fitting_results.append({
            'data_source': source,
            'power_params': power_params,
            'power_r2': power_r2,
            'exp_params': exp_params,
            'exp_r2': exp_r2,
            'best_model': best_model,
            'days': days,
            'rates': rates
        })
    
    return fitting_results

def calculate_lt_values(fitting_results, max_days=365):
    """计算LT值"""
    lt_results = []
    
    for result in fitting_results:
        source = result['data_source']
        best_model = result['best_model']
        
        if best_model == 'power':
            params = result['power_params']
            a, b = params
            
            # 幂函数积分：∫(a * x^b)dx from 1 to max_days
            if b != -1:
                lt_value = (a / (b + 1)) * (max_days**(b + 1) - 1)
            else:
                # 当b=-1时，积分是对数函数
                lt_value = a * np.log(max_days)
        else:
            params = result['exp_params']
            c, d = params
            
            # 指数函数积分：∫(c * e^(d*x))dx from 1 to max_days
            if d != 0:
                lt_value = (c / d) * (np.exp(d * max_days) - np.exp(d))
            else:
                lt_value = c * (max_days - 1)
        
        # 确保LT值为正数且合理
        lt_value = max(0, min(lt_value, max_days))
        
        lt_results.append({
            'data_source': source,
            'lt_value': lt_value,
            'model_used': best_model,
            'model_params': result[f'{best_model}_params'],
            'r2_score': result[f'{best_model}_r2']
        })
    
    return lt_results

# 设置matplotlib的现代化样式
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# 页面内容
if page == "数据上传与汇总":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("📁 数据上传与汇总")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 渠道映射配置
    with st.expander("🔧 渠道映射配置", expanded=False):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown('<div class="status-card">', unsafe_allow_html=True)
            st.markdown("### 当前配置状态")
            if st.session_state.channel_mapping:
                st.success(f"✅ 已配置 {len(st.session_state.channel_mapping)} 个渠道映射")
                st.info("📋 正在使用默认渠道映射表")
            else:
                st.warning("⚠️ 未配置渠道映射")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            if st.session_state.channel_mapping:
                st.markdown("### 📋 渠道映射示例")
                # 按渠道名分组显示
                mapping_by_channel = {}
                for pid, channel in st.session_state.channel_mapping.items():
                    if channel not in mapping_by_channel:
                        mapping_by_channel[channel] = []
                    mapping_by_channel[channel].append(pid)
                
                # 显示前5个渠道映射
                count = 0
                for channel, pids in list(mapping_by_channel.items())[:5]:
                    st.code(f"{channel}: {', '.join(pids[:3])}{'...' if len(pids) > 3 else ''}")
                    count += 1
                
                if len(mapping_by_channel) > 5:
                    st.text(f"... 还有 {len(mapping_by_channel) - 5} 个渠道")
        
        # 自定义渠道映射文件上传
        st.markdown("### 📤 上传自定义渠道映射表")
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
                st.success(f"✅ 自定义渠道映射已加载，共 {len(custom_mapping)} 个映射")
                st.dataframe(channel_df.head(), use_container_width=True)
            except Exception as e:
                st.error(f"❌ 渠道映射文件读取失败: {str(e)}")
    
    # 数据文件上传
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📊 数据文件处理")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_files = st.file_uploader(
            "选择Excel数据文件",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            help="🔹 支持上传多个Excel文件\n🔹 系统会自动解析留存数据\n🔹 支持新旧两种数据格式"
        )
        
        # 目标月份选择
        default_month = get_default_target_month()
        target_month = st.text_input(
            "🗓️ 目标月份 (YYYY-MM)",
            value=default_month,
            help=f"当前默认为2个月前: {default_month}"
        )
    
    with col2:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        st.markdown("### 📋 处理状态")
        
        if uploaded_files:
            st.markdown(f"**✅ 已选择 {len(uploaded_files)} 个文件**")
            for file in uploaded_files:
                st.markdown(f"• {file.name}")
        else:
            st.info("📁 未选择数据文件")
        
        st.markdown(f"**📅 目标月份:** {target_month}")
        st.markdown(f"**🔗 渠道映射:** {len(st.session_state.channel_mapping)} 个")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 处理按钮
    if st.button("🚀 开始处理数据", type="primary", use_container_width=True):
        if uploaded_files:
            with st.spinner("⏳ 正在处理数据文件..."):
                try:
                    # 处理数据文件
                    merged_data, processed_count = integrate_excel_files_streamlit(
                        uploaded_files, target_month, st.session_state.channel_mapping
                    )
                    
                    if merged_data is not None and not merged_data.empty:
                        st.session_state.merged_data = merged_data
                        
                        st.success(f"🎉 数据处理完成！成功处理 {processed_count} 个文件")
                        
                        # 显示关键指标
                        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                        st.subheader("📊 数据概览")
                        
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
                            st.markdown('<div class="metric-value">📅</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="metric-label">{date_range}</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # 数据预览
                        st.subheader("🔍 数据预览")
                        st.dataframe(merged_data.head(10), use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    else:
                        st.error("❌ 未找到有效数据，请检查文件格式和目标月份设置")
                
                except Exception as e:
                    st.error(f"❌ 处理过程中出现错误：{str(e)}")
        else:
            st.error("⚠️ 请先选择要处理的文件")

elif page == "留存率计算":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("📈 留存率计算")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.merged_data is None:
        st.warning("⚠️ 请先在「数据上传与汇总」页面处理数据")
        if st.button("🔙 返回数据上传页面"):
            st.rerun()
    else:
        merged_data = st.session_state.merged_data
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("⚙️ 留存率分析配置")
            
            # 数据来源选择
            data_sources = merged_data['数据来源'].unique()
            selected_sources = st.multiselect(
                "选择要分析的数据来源",
                options=data_sources,
                default=data_sources,
                help="可以选择一个或多个数据来源进行分析"
            )
        
        with col2:
            st.markdown('<div class="status-card">', unsafe_allow_html=True)
            st.markdown("### 📊 分析范围")
            st.markdown(f"**数据来源:** {len(selected_sources)}")
            st.markdown(f"**总记录数:** {len(merged_data):,}")
            st.markdown(f"**分析天数:** 1-30天")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("🔄 计算留存率", type="primary", use_container_width=True):
            if selected_sources:
                with st.spinner("⏳ 正在计算留存率..."):
                    # 过滤选中的数据来源
                    filtered_data = merged_data[merged_data['数据来源'].isin(selected_sources)]
                    
                    # 计算留存率
                    retention_results = calculate_retention_rates(filtered_data)
                    st.session_state.retention_data = retention_results
                    
                    st.success("🎉 留存率计算完成！")
                    
                    # 显示结果
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    st.subheader("📊 留存率结果")
                    
                    for result in retention_results:
                        with st.expander(f"📈 {result['data_source']} - 留存率详情", expanded=True):
                            retention_rates = result['retention_rates']
                            
                            # 创建留存率表格
                            days = list(range(1, 31))
                            rates = [retention_rates.get(day, 0) for day in days]
                            
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                # 显示关键指标
                                valid_rates = [r for r in rates if r > 0]
                                if valid_rates:
                                    st.markdown("### 📊 关键指标")
                                    st.metric("Day 1 留存率", f"{rates[0]*100:.2f}%")
                                    st.metric("Day 7 留存率", f"{rates[6]*100:.2f}%" if len(rates) > 6 else "N/A")
                                    st.metric("Day 30 留存率", f"{rates[29]*100:.2f}%" if len(rates) > 29 else "N/A")
                                    st.metric("平均留存率", f"{np.mean(valid_rates)*100:.2f}%")
                            
                            with col2:
                                # 绘制留存率曲线
                                valid_days = [d for d, r in zip(days, rates) if r > 0]
                                valid_rates = [r for r in rates if r > 0]
                                
                                if valid_days:
                                    fig, ax = plt.subplots(figsize=(12, 6))
                                    
                                    # 使用渐变色
                                    colors = plt.cm.viridis(np.linspace(0, 1, len(valid_days)))
                                    scatter = ax.scatter(valid_days, valid_rates, 
                                                       c=colors, s=80, alpha=0.8, edgecolors='white', linewidth=2)
                                    ax.plot(valid_days, valid_rates, '--', color='#667eea', linewidth=2, alpha=0.7)
                                    
                                    ax.set_xlabel('天数', fontsize=12, fontweight='bold')
                                    ax.set_ylabel('留存率', fontsize=12, fontweight='bold')
                                    ax.set_title(f'{result["data_source"]} 留存率曲线', fontsize=14, fontweight='bold')
                                    ax.grid(True, alpha=0.3, linestyle='--')
                                    ax.set_ylim(0, max(valid_rates) * 1.1)
                                    
                                    # 美化图表
                                    ax.spines['top'].set_visible(False)
                                    ax.spines['right'].set_visible(False)
                                    ax.spines['left'].set_linewidth(0.5)
                                    ax.spines['bottom'].set_linewidth(0.5)
                                    
                                    plt.tight_layout()
                                    st.pyplot(fig)
                                    plt.close()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error("⚠️ 请选择至少一个数据来源")

elif page == "LT拟合分析":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("🔄 LT拟合分析")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.retention_data is None:
        st.warning("⚠️ 请先在「留存率计算」页面计算留存率")
        if st.button("🔙 返回留存率计算页面"):
            st.rerun()
    else:
        retention_data = st.session_state.retention_data
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("⚙️ 曲线拟合参数设置")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🎯 拟合方法选择")
            fit_methods = st.multiselect(
                "选择拟合方法",
                options=["幂函数 (Power)", "指数函数 (Exponential)"],
                default=["幂函数 (Power)", "指数函数 (Exponential)"],
                help="系统会自动选择拟合度最好的方法"
            )
            
            max_days = st.number_input(
                "📅 LT计算天数范围",
                min_value=30,
                max_value=1000,
                value=365,
                help="设置计算用户生命周期的天数范围"
            )
        
        with col2:
            st.markdown('<div class="status-card">', unsafe_allow_html=True)
            st.markdown("### 📊 拟合设置")
            st.markdown(f"**数据来源:** {len(retention_data)}")
            st.markdown(f"**拟合方法:** {len(fit_methods)}")
            st.markdown(f"**LT天数:** {max_days}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("🚀 开始拟合分析", type="primary", use_container_width=True):
            with st.spinner("⏳ 正在进行曲线拟合..."):
                # 执行拟合分析
                fitting_results = fit_retention_curves(retention_data)
                
                # 计算LT值
                lt_results = calculate_lt_values(fitting_results, max_days)
                st.session_state.lt_results = lt_results
                
                st.success("🎉 拟合分析完成！")
                
                # 显示拟合结果
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.subheader("📊 拟合结果")
                
                for i, result in enumerate(fitting_results):
                    source = result['data_source']
                    
                    with st.expander(f"🔄 {source} - 拟合分析详情", expanded=True):
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            # 显示拟合参数
                            st.markdown("### 📊 拟合参数")
                            
                            # 幂函数结果
                            power_params = result['power_params']
                            power_r2 = result['power_r2']
                            st.markdown(f"**🔹 幂函数:** y = {power_params[0]:.4f} × x^{power_params[1]:.4f}")
                            st.markdown(f"**R² = {power_r2:.4f}**")
                            
                            # 指数函数结果
                            exp_params = result['exp_params']
                            exp_r2 = result['exp_r2']
                            st.markdown(f"**🔹 指数函数:** y = {exp_params[0]:.4f} × e^({exp_params[1]:.4f}x)")
                            st.markdown(f"**R² = {exp_r2:.4f}**")
                            
                            # 最佳模型
                            best_model = result['best_model']
                            if best_model == 'power':
                                st.success(f"✅ **最佳模型:** 幂函数")
                            else:
                                st.success(f"✅ **最佳模型:** 指数函数")
                            
                            # LT值
                            lt_value = lt_results[i]['lt_value']
                            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                            st.markdown(f'<div class="metric-value">{lt_value:.2f}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="metric-label">LT值 (基于{max_days}天)</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with col2:
                            # 绘制拟合曲线
                            days = np.array(result['days'])
                            rates = np.array(result['rates'])
                            
                            if len(days) > 0:
                                fig, ax = plt.subplots(figsize=(12, 8))
                                
                                # 原始数据点
                                ax.scatter(days, rates, color='#ff6b6b', s=100, alpha=0.8, 
                                         label='实际数据', zorder=5, edgecolors='white', linewidth=2)
                                
                                # 拟合曲线
                                x_fit = np.linspace(1, 30, 100)
                                
                                # 幂函数拟合曲线
                                y_power = power_params[0] * (x_fit ** power_params[1])
                                ax.plot(x_fit, y_power, '--', color='#667eea', linewidth=3, 
                                       label=f'幂函数 (R²={power_r2:.3f})', alpha=0.8)
                                
                                # 指数函数拟合曲线
                                y_exp = exp_params[0] * np.exp(exp_params[1] * x_fit)
                                ax.plot(x_fit, y_exp, '--', color='#764ba2', linewidth=3, 
                                       label=f'指数函数 (R²={exp_r2:.3f})', alpha=0.8)
                                
                                # 突出显示最佳拟合
                                if best_model == 'power':
                                    ax.plot(x_fit, y_power, '-', color='#667eea', linewidth=4, 
                                           label='最佳拟合', alpha=1.0, zorder=4)
                                else:
                                    ax.plot(x_fit, y_exp, '-', color='#764ba2', linewidth=4, 
                                           label='最佳拟合', alpha=1.0, zorder=4)
                                
                                ax.set_xlabel('天数', fontsize=12, fontweight='bold')
                                ax.set_ylabel('留存率', fontsize=12, fontweight='bold')
                                ax.set_title(f'{source} - 留存率拟合曲线', fontsize=14, fontweight='bold')
                                ax.legend(fontsize=10)
                                ax.grid(True, alpha=0.3, linestyle='--')
                                ax.set_xlim(0, 31)
                                ax.set_ylim(0, max(rates) * 1.1)
                                
                                # 美化图表
                                ax.spines['top'].set_visible(False)
                                ax.spines['right'].set_visible(False)
                                ax.spines['left'].set_linewidth(0.5)
                                ax.spines['bottom'].set_linewidth(0.5)
                                
                                plt.tight_layout()
                                st.pyplot(fig)
                                plt.close()
                
                st.markdown('</div>', unsafe_allow_html=True)

elif page == "ARPU计算":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("💰 ARPU计算")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📤 上传ARPU数据")
    
    # ARPU数据上传
    arpu_file = st.file_uploader(
        "选择ARPU数据文件",
        type=['xlsx', 'xls'],
        help="📊 上传包含用户付费数据的Excel文件"
    )
    
    if arpu_file:
        try:
            # 读取ARPU文件
            arpu_df = pd.read_excel(arpu_file)
            st.success("✅ ARPU文件上传成功！")
            
            # 显示文件预览
            st.subheader("🔍 数据预览")
            st.dataframe(arpu_df.head(10), use_container_width=True)
            
            # 数据列选择
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🔗 数据列映射")
                
                # 让用户选择关键列
                source_col = st.selectbox(
                    "数据来源列",
                    options=arpu_df.columns,
                    help="选择标识数据来源的列"
                )
                
                arpu_col = st.selectbox(
                    "ARPU值列",
                    options=arpu_df.columns,
                    help="选择包含ARPU值的列"
                )
                
                date_col = st.selectbox(
                    "日期列 (可选)",
                    options=['无'] + list(arpu_df.columns),
                    help="如果有日期列，请选择"
                )
            
            with col2:
                st.subheader("📊 数据统计")
                
                # 显示基本统计
                if arpu_col in arpu_df.columns:
                    arpu_values = pd.to_numeric(arpu_df[arpu_col], errors='coerce')
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("💵 平均ARPU", f"{arpu_values.mean():.2f}")
                        st.metric("📉 最小值", f"{arpu_values.min():.2f}")
                    with col_b:
                        st.metric("📈 最大值", f"{arpu_values.max():.2f}")
                        st.metric("✅ 有效记录", f"{arpu_values.notna().sum():,}")
            
            # 处理ARPU数据
            if st.button("💾 保存ARPU数据", type="primary", use_container_width=True):
                try:
                    # 标准化ARPU数据
                    processed_arpu = arpu_df.copy()
                    processed_arpu['data_source'] = processed_arpu[source_col]
                    processed_arpu['arpu_value'] = pd.to_numeric(processed_arpu[arpu_col], errors='coerce')
                    
                    if date_col != '无':
                        processed_arpu['date'] = processed_arpu[date_col]
                    
                    # 按数据来源汇总ARPU
                    arpu_summary = processed_arpu.groupby('data_source')['arpu_value'].mean().reset_index()
                    
                    st.session_state.arpu_data = arpu_summary
                    
                    st.success("🎉 ARPU数据处理完成！")
                    
                    # 显示汇总结果
                    st.subheader("📊 ARPU汇总结果")
                    st.dataframe(arpu_summary, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"❌ ARPU数据处理失败：{str(e)}")
        
        except Exception as e:
            st.error(f"❌ 文件读取失败：{str(e)}")
    
    else:
        st.info("📁 请上传ARPU数据文件")
        
        # 如果没有ARPU数据，提供手动输入选项
        st.subheader("✏️ 手动设置ARPU")
        
        if st.session_state.lt_results:
            # 基于已有的LT结果创建ARPU输入
            st.write("为每个数据来源设置ARPU值：")
            
            arpu_inputs = {}
            for result in st.session_state.lt_results:
                source = result['data_source']
                arpu_value = st.number_input(
                    f"💰 {source} ARPU",
                    min_value=0.0,
                    value=10.0,
                    step=0.01,
                    format="%.2f"
                )
                arpu_inputs[source] = arpu_value
            
            if st.button("💾 保存手动ARPU设置", type="primary", use_container_width=True):
                # 创建ARPU数据框
                arpu_df = pd.DataFrame([
                    {'data_source': source, 'arpu_value': value} 
                    for source, value in arpu_inputs.items()
                ])
                
                st.session_state.arpu_data = arpu_df
                st.success("🎉 ARPU设置已保存！")
                st.dataframe(arpu_df, use_container_width=True)
        
        else:
            st.warning("⚠️ 请先完成LT拟合分析，然后再设置ARPU")
    
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "LTV结果报告":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("📊 LTV结果报告")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 检查必要数据是否存在
    if st.session_state.lt_results is None:
        st.warning("⚠️ 请先完成LT拟合分析")
        if st.button("🔄 跳转到LT拟合分析"):
            st.rerun()
    elif st.session_state.arpu_data is None:
        st.warning("⚠️ 请先完成ARPU计算")
        if st.button("💰 跳转到ARPU计算"):
            st.rerun()
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
                arpu_value = 0  # 如果找不到ARPU，设为0
            
            # 计算LTV
            ltv_value = lt_value * arpu_value
            
            ltv_results.append({
                'data_source': source,
                'lt_value': lt_value,
                'arpu_value': arpu_value,
                'ltv_value': ltv_value,
                'model_used': lt_result['model_used'],
                'r2_score': lt_result['r2_score']
            })
        
        st.session_state.ltv_results = ltv_results
        
        # 显示LTV结果
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🎯 LTV计算结果")
        
        # 创建结果表格
        ltv_df = pd.DataFrame(ltv_results)
        ltv_df = ltv_df.rename(columns={
            'data_source': '数据来源',
            'lt_value': 'LT值',
            'arpu_value': 'ARPU',
            'ltv_value': 'LTV',
            'model_used': '拟合模型',
            'r2_score': 'R²得分'
        })
        
        # 格式化显示
        ltv_df['LT值'] = ltv_df['LT值'].round(2)
        ltv_df['ARPU'] = ltv_df['ARPU'].round(2)
        ltv_df['LTV'] = ltv_df['LTV'].round(2)
        ltv_df['R²得分'] = ltv_df['R²得分'].round(4)
        
        st.dataframe(ltv_df, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 关键指标展示
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("📊 关键指标")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_ltv = ltv_df['LTV'].mean()
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{avg_ltv:.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">平均LTV</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            max_ltv = ltv_df['LTV'].max()
            best_source = ltv_df.loc[ltv_df['LTV'].idxmax(), '数据来源']
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{max_ltv:.2f}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-label">最高LTV<br>({best_source})</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            avg_lt = ltv_df['LT值'].mean()
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{avg_lt:.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">平均LT</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            avg_arpu = ltv_df['ARPU'].mean()
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{avg_arpu:.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">平均ARPU</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # LTV对比图表
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("📈 LTV对比分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # LTV条形图
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # 使用渐变色
            colors = plt.cm.viridis(np.linspace(0, 1, len(ltv_df)))
            bars = ax.bar(ltv_df['数据来源'], ltv_df['LTV'], color=colors, alpha=0.8, edgecolor='white', linewidth=2)
            
            ax.set_xlabel('数据来源', fontsize=12, fontweight='bold')
            ax.set_ylabel('LTV值', fontsize=12, fontweight='bold')
            ax.set_title('各渠道LTV对比', fontsize=14, fontweight='bold')
            ax.tick_params(axis='x', rotation=45)
            
            # 在条形图上显示数值
            for bar, value in zip(bars, ltv_df['LTV']):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
            
            # 美化图表
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(True, alpha=0.3, linestyle='--', axis='y')
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
        
        with col2:
            # LT vs ARPU散点图
            fig, ax = plt.subplots(figsize=(12, 8))
            scatter = ax.scatter(ltv_df['LT值'], ltv_df['ARPU'], 
                               c=ltv_df['LTV'], s=200, alpha=0.8, cmap='viridis',
                               edgecolors='white', linewidth=2)
            
            # 添加数据源标签
            for i, source in enumerate(ltv_df['数据来源']):
                ax.annotate(source, (ltv_df['LT值'].iloc[i], ltv_df['ARPU'].iloc[i]),
                           xytext=(5, 5), textcoords='offset points', fontsize=10, fontweight='bold')
            
            ax.set_xlabel('LT值', fontsize=12, fontweight='bold')
            ax.set_ylabel('ARPU', fontsize=12, fontweight='bold')
            ax.set_title('LT vs ARPU 关系图', fontsize=14, fontweight='bold')
            
            # 添加颜色条
            cbar = plt.colorbar(scatter)
            cbar.set_label('LTV值', fontsize=12, fontweight='bold')
            
            # 美化图表
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(True, alpha=0.3, linestyle='--')
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 模型质量分析
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🎯 模型质量分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # R²得分分布
            fig, ax = plt.subplots(figsize=(10, 6))
            colors = ['#ff6b6b' if r < 0.6 else '#ffa726' if r < 0.8 else '#66bb6a' for r in ltv_df['R²得分']]
            bars = ax.bar(ltv_df['数据来源'], ltv_df['R²得分'], color=colors, alpha=0.8, edgecolor='white', linewidth=2)
            
            ax.set_xlabel('数据来源', fontsize=12, fontweight='bold')
            ax.set_ylabel('R²得分', fontsize=12, fontweight='bold')
            ax.set_title('模型拟合质量 (R²得分)', fontsize=14, fontweight='bold')
            ax.tick_params(axis='x', rotation=45)
            ax.set_ylim(0, 1)
            
            # 添加质量评价线
            ax.axhline(y=0.8, color='#66bb6a', linestyle='--', alpha=0.7, linewidth=2, label='优秀 (0.8+)')
            ax.axhline(y=0.6, color='#ffa726', linestyle='--', alpha=0.7, linewidth=2, label='良好 (0.6+)')
            ax.axhline(y=0.4, color='#ff6b6b', linestyle='--', alpha=0.7, linewidth=2, label='一般 (0.4+)')
            ax.legend(fontsize=10)
            
            # 美化图表
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(True, alpha=0.3, linestyle='--', axis='y')
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
        
        with col2:
            # 模型使用统计
            model_counts = ltv_df['拟合模型'].value_counts()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            colors = ['#667eea', '#764ba2']
            wedges, texts, autotexts = ax.pie(model_counts.values, labels=model_counts.index, 
                                             autopct='%1.1f%%', colors=colors, startangle=90,
                                             textprops={'fontsize': 12, 'fontweight': 'bold'})
            ax.set_title('拟合模型使用分布', fontsize=14, fontweight='bold')
            
            st.pyplot(fig)
            plt.close()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 导出功能
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("📤 结果导出")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 准备导出数据
            export_df = ltv_df.copy()
            
            # 转换为CSV
            csv_data = export_df.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(
                label="📊 下载LTV结果 (CSV)",
                data=csv_data,
                file_name=f"LTV_Results_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # 创建详细报告
            report_text = f"""
📊 LTV分析报告
=================================
生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🎯 总体指标
---------------------------------
参与分析的数据源数量: {len(ltv_df)}
平均LTV: {avg_ltv:.2f}
最高LTV: {max_ltv:.2f} ({ltv_df.loc[ltv_df['LTV'].idxmax(), '数据来源']})
平均LT: {avg_lt:.2f}
平均ARPU: {avg_arpu:.2f}

📈 详细结果
---------------------------------
"""
            
            for _, row in ltv_df.iterrows():
                report_text += f"""
{row['数据来源']}:
  LT值: {row['LT值']:.2f}
  ARPU: {row['ARPU']:.2f}
  LTV: {row['LTV']:.2f}
  拟合模型: {row['拟合模型']}
  R²得分: {row['R²得分']:.4f}
"""
            
            st.download_button(
                label="📄 下载详细报告 (TXT)",
                data=report_text,
                file_name=f"LTV_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)

# 底部信息
with st.sidebar:
    st.markdown("---")
    st.markdown("""
    <div class="progress-container">
        <h3 style="text-align: center; color: #495057;">💡 使用提示</h3>
        <p style="font-size: 0.9rem; color: #6c757d; text-align: center;">
        请按照流程顺序完成各个步骤，每一步的结果都会保存在当前会话中。
        </p>
        <p style="font-size: 0.8rem; color: #adb5bd; text-align: center;">
        Powered by Streamlit & Advanced Analytics
        </p>
    </div>
    """, unsafe_allow_html=True)
