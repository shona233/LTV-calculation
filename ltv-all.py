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
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        padding: 1.5rem 0rem 1rem 0rem;
        border-bottom: 2px solid #f0f2f6;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .status-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e1e5e9;
        margin: 0.5rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .progress-item {
        padding: 0.5rem 0;
        border-bottom: 1px solid #f0f2f6;
    }
    .stButton > button {
        width: 100%;
        border-radius: 0.25rem;
        border: 1px solid #1f77b4;
        background-color: #1f77b4;
        color: white;
        font-weight: 500;
    }
    .stButton > button:hover {
        background-color: #0d5aa7;
        border-color: #0d5aa7;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    h1, h2, h3 {
        color: #2c3e50;
        font-weight: 600;
    }
    .stSelectbox label, .stMultiselect label, .stFileUploader label {
        font-weight: 500;
        color: #34495e;
    }
</style>
""", unsafe_allow_html=True)

# 主标题
st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.title("LTV Analytics Platform")
st.markdown("**用户生命周期价值分析系统**")
st.markdown('</div>', unsafe_allow_html=True)

# 侧边栏导航
st.sidebar.markdown("### 分析流程")
page = st.sidebar.selectbox(
    "选择分析模块",
    [
        "数据上传与汇总", 
        "留存率计算", 
        "LT拟合分析", 
        "ARPU计算", 
        "LTV结果报告"
    ],
    label_visibility="collapsed"
)

# 初始化session state
session_keys = [
    'channel_mapping', 'merged_data', 'retention_data', 
    'lt_results', 'arpu_data', 'ltv_results'
]
for key in session_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# ===== 数据整合功能（保留原有逻辑）=====
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

def integrate_excel_files_streamlit(uploaded_files, target_month=None):
    """Streamlit版本的Excel文件整合函数"""
    if target_month is None:
        today = datetime.datetime.now()
        first_day_of_current_month = today.replace(day=1)
        first_day_of_last_month = (first_day_of_current_month - datetime.timedelta(days=1)).replace(day=1)
        last_day_of_two_months_ago = first_day_of_last_month - datetime.timedelta(days=1)
        target_month = last_day_of_two_months_ago.strftime("%Y-%m")

    all_data = pd.DataFrame()
    processed_count = 0

    for uploaded_file in uploaded_files:
        source_name = os.path.splitext(uploaded_file.name)[0]
        
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
                        filtered_data.insert(0, '数据来源', source_name)
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
                                filtered_data.insert(0, '数据来源', source_name)
                                if retention_col:
                                    filtered_data.rename(columns={retention_col: 'date'}, inplace=True)
                                else:
                                    filtered_data['date'] = filtered_data[date_col].dt.strftime('%Y-%m-%d')
                                
                                all_data = pd.concat([all_data, filtered_data], ignore_index=True)
                                processed_count += 1
                        except:
                            # 如果日期处理失败，保留所有数据
                            file_data_copy.insert(0, '数据来源', source_name)
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

# ===== 拟合计算功能（用numpy替代scipy）=====
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
