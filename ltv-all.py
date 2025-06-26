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
        "LT简化计算", 
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

# ===== 简化的LT计算功能（不使用scipy）=====
def simple_power_regression(x, y):
    """简化的幂函数拟合，使用对数线性回归"""
    try:
        # 过滤掉非正数
        valid_idx = (x > 0) & (y > 0)
        if np.sum(valid_idx) < 2:
            return 1.0, -0.5  # 默认参数
        
        x_valid = x[valid_idx]
        y_valid = y[valid_idx]
        
        # 对数线性回归: log(y) = log(a) + b*log(x)
        log_x = np.log(x_valid)
        log_y = np.log(y_valid)
        
        # 使用最小二乘法
        n = len(log_x)
        sum_log_x = np.sum(log_x)
        sum_log_y = np.sum(log_y)
        sum_log_x_log_y = np.sum(log_x * log_y)
        sum_log_x_sq = np.sum(log_x * log_x)
        
        # 计算斜率和截距
        b = (n * sum_log_x_log_y - sum_log_x * sum_log_y) / (n * sum_log_x_sq - sum_log_x * sum_log_x)
        log_a = (sum_log_y - b * sum_log_x) / n
        a = np.exp(log_a)
        
        return a, b
    except:
        return 1.0, -0.5  # 默认参数

def simple_exponential_regression(x, y):
    """简化的指数函数拟合"""
    try:
        # 过滤掉非正数
        valid_idx = y > 0
        if np.sum(valid_idx) < 2:
            return y[0] if len(y) > 0 else 1.0, -0.001
        
        x_valid = x[valid_idx]
        y_valid = y[valid_idx]
        
        # 线性回归: log(y) = log(c) + d*x
        log_y = np.log(y_valid)
        
        # 使用最小二乘法
        n = len(x_valid)
        sum_x = np.sum(x_valid)
        sum_log_y = np.sum(log_y)
        sum_x_log_y = np.sum(x_valid * log_y)
        sum_x_sq = np.sum(x_valid * x_valid)
        
        # 计算斜率和截距
        d = (n * sum_x_log_y - sum_x * sum_log_y) / (n * sum_x_sq - sum_x * sum_x)
        log_c = (sum_log_y - d * sum_x) / n
        c = np.exp(log_c)
        
        return c, d
    except:
        return y[0] if len(y) > 0 else 1.0, -0.001

def simple_power_function(x, a, b):
    """简化的幂函数：y = a * x^b"""
    return a * np.power(np.maximum(x, 0.1), b)

def simple_exponential_function(x, c, d):
    """简化的指数函数：y = c * exp(d * x)"""
    return c * np.exp(d * x)

def calculate_lt_simple(data, channel_name, lt_years=5):
    """简化版LT计算，不依赖scipy"""
    
    # 渠道规则
    CHANNEL_RULES = {
        "华为": {"stage_2": [30, 120], "stage_3_base": [120, 220]},
        "小米": {"stage_2": [30, 190], "stage_3_base": [190, 290]},
        "oppo": {"stage_2": [30, 160], "stage_3_base": [160, 260]},
        "vivo": {"stage_2": [30, 150], "stage_3_base": [150, 250]},
        "iphone": {"stage_2": [30, 150], "stage_3_base": [150, 250]},
        "其他": {"stage_2": [30, 100], "stage_3_base": [100, 200]}
    }

    if re.search(r'\d+月华为$', channel_name):
        rules = CHANNEL_RULES["华为"]
    elif re.search(r'\d+月小米$', channel_name):
        rules = CHANNEL_RULES["小米"]
    elif re.search(r'\d+月oppo$', channel_name) or re.search(r'\d+月OPPO$', channel_name):
        rules = CHANNEL_RULES["oppo"]
    elif re.search(r'\d+月vivo$', channel_name):
        rules = CHANNEL_RULES["vivo"]
    elif re.search(r'\d+月[iI][pP]hone$', channel_name):
        rules = CHANNEL_RULES["iphone"]
    else:
        rules = CHANNEL_RULES["其他"]
    
    stage_2_start, stage_2_end = rules["stage_2"]
    stage_3_base_start, stage_3_base_end = rules["stage_3_base"]
    max_days = lt_years * 365

    days = data["留存天数"].values
    rates = data["留存率"].values

    try:
        # 第一阶段：使用简化幂函数拟合
        a, b = simple_power_regression(days, rates)
        
        # 生成1-30天完整数据
        days_full = np.arange(1, 31)
        rates_full = simple_power_function(days_full, a, b)
        rates_full = np.maximum(rates_full, 0)  # 确保非负
        lt1_to_30 = np.sum(rates_full)
        
        # 第二阶段
        days_stage_2 = np.arange(stage_2_start, stage_2_end + 1)
        rates_stage_2 = simple_power_function(days_stage_2, a, b)
        rates_stage_2 = np.maximum(rates_stage_2, 0)
        lt_stage_2 = np.sum(rates_stage_2)
        
        # 第三阶段：尝试指数拟合，失败则用幂函数
        try:
            days_stage_3_base = np.arange(stage_3_base_start, stage_3_base_end + 1)
            rates_stage_3_base = simple_power_function(days_stage_3_base, a, b)
            
            c, d = simple_exponential_regression(days_stage_3_base, rates_stage_3_base)
            
            days_stage_3 = np.arange(stage_3_base_start, max_days + 1)
            rates_stage_3 = simple_exponential_function(days_stage_3, c, d)
            rates_stage_3 = np.maximum(rates_stage_3, 0)
            lt_stage_3 = np.sum(rates_stage_3)
        except:
            # 指数拟合失败，使用幂函数
            days_stage_3 = np.arange(stage_3_base_start, max_days + 1)
            rates_stage_3 = simple_power_function(days_stage_3, a, b)
            rates_stage_3 = np.maximum(rates_stage_3, 0)
            lt_stage_3 = np.sum(rates_stage_3)
        
        total_lt = 1.0 + lt1_to_30 + lt_stage_2 + lt_stage_3
        
        return total_lt, {"a": a, "b": b}
        
    except Exception as e:
        st.error(f"{channel_name} LT计算失败：{e}")
        return 1.0, {"a": 1.0, "b": -0.5}

# ===== 页面逻辑 =====
if page == "数据上传与汇总":
    st.header("数据上传与汇总")
    st.markdown("上传渠道映射表和留存数据文件，系统将自动汇总并标准化数据格式。")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("渠道映射表")
        st.markdown("**格式要求：** 第一列为渠道名称，后续列为对应的渠道号")
        
        channel_mapping_file = st.file_uploader(
            "选择渠道映射表文件",
            type=['xlsx', 'xls'],
            key="channel_mapping"
        )
        
        if channel_mapping_file:
            try:
                channel_mapping_df = pd.read_excel(channel_mapping_file)
                st.session_state.channel_mapping = channel_mapping_df
                
                # 解析渠道映射
                pid_mapping = parse_channel_mapping(channel_mapping_df)
                
                st.success(f"渠道映射表上传成功，共解析出 {len(pid_mapping)} 个渠道号映射")
                
                with st.expander("查看映射表预览"):
                    st.dataframe(channel_mapping_df.head(10))
                    
                with st.expander("查看解析后的渠道号映射"):
                    mapping_preview = pd.DataFrame(list(pid_mapping.items()), 
                                                 columns=['渠道号', '渠道名称'])
                    st.dataframe(mapping_preview.head(20))
                    
            except Exception as e:
                st.error(f"读取渠道映射表失败：{e}")
        
        st.subheader("留存数据文件")
        st.markdown("**支持格式：** OCPX格式和HUE格式的Excel文件")
        
        retention_files = st.file_uploader(
            "选择留存数据文件（支持多文件）",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            key="retention_files"
        )
        
        target_month = st.text_input(
            "目标分析月份",
            value="",
            placeholder="YYYY-MM 格式，留空使用默认月份",
            help="指定要分析的月份，格式如：2024-02"
        )
    
    with col2:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        st.subheader("汇总设置")
        
        if retention_files:
            st.info(f"已选择 {len(retention_files)} 个文件")
            
        auto_month = datetime.datetime.now().strftime("%Y-%m")
        if not target_month:
            st.info(f"将使用默认月份：{auto_month}")
        
        process_btn = st.button("开始数据汇总", type="primary")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if process_btn:
            if retention_files:
                with st.spinner("正在汇总数据，请稍候..."):
                    try:
                        target_month_val = target_month if target_month else None
                        merged_data, processed_count = integrate_excel_files_streamlit(
                            retention_files, target_month_val
                        )
                        
                        if merged_data is not None:
                            st.session_state.merged_data = merged_data
                            st.success(f"数据汇总完成")
                            
                            # 汇总统计
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("处理文件数", processed_count)
                            with col_b:
                                st.metric("汇总记录数", len(merged_data))
                            
                            # 数据预览
                            st.subheader("数据预览")
                            st.dataframe(merged_data.head(10))
                            
                            # 提供下载
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                merged_data.to_excel(writer, sheet_name='合并数据', index=False)
                            
                            st.download_button(
                                label="下载汇总数据",
                                data=output.getvalue(),
                                file_name=f"汇总数据_{target_month or auto_month}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        else:
                            st.error("未找到符合条件的数据")
                    except Exception as e:
                        st.error(f"数据汇总失败：{e}")
            else:
                st.warning("请先上传留存数据文件")

elif page == "留存率计算":
    st.header("留存率计算")
    st.markdown("基于汇总数据计算各渠道的月均留存率。")
    
    if st.session_state.merged_data is not None:
        merged_data = st.session_state.merged_data
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"已加载汇总数据：{len(merged_data)} 条记录")
            
            # 显示渠道统计
            channel_counts = merged_data['数据来源'].value_counts()
            st.subheader("渠道数据分布")
            st.dataframe(channel_counts.to_frame('记录数').reset_index())
        
        with col2:
            st.markdown('<div class="status-card">', unsafe_allow_html=True)
            st.subheader("计算设置")
            
            if st.button("开始留存率计算", type="primary"):
                with st.spinner("正在计算留存率..."):
                    try:
                        retention_results = {}
                        
                        # 按数据来源（渠道）分组
                        for channel_name in merged_data['数据来源'].unique():
                            channel_data = merged_data[merged_data['数据来源'] == channel_name].copy()
                            
                            # 准备留存率数据
                            retention_data = []
                            
                            for _, row in channel_data.iterrows():
                                if pd.notna(row.get('回传新增数', 0)) and row.get('回传新增数', 0) > 0:
                                    new_users = float(row['回传新增数'])
                                    date_val = row.get('date', row.get('日期', ''))
                                    
                                    row_data = {'日期': date_val, '新增用户': new_users}
                                    
                                    # 计算1-30天留存率
                                    for day in range(1, 31):
                                        retention_count = row.get(str(day), 0)
                                        if pd.notna(retention_count) and retention_count > 0:
                                            retention_rate = float(retention_count) / new_users * 100
                                            row_data[str(day)] = retention_rate
                                        else:
                                            row_data[str(day)] = 0
                                    
                                    retention_data.append(row_data)
                            
                            if retention_data:
                                df = pd.DataFrame(retention_data)
                                
                                # 计算均值
                                mean_row = {'日期': '均值', '新增用户': df['新增用户'].mean()}
                                for day in range(1, 31):
                                    mean_row[str(day)] = df[str(day)].mean()
                                
                                df = pd.concat([df, pd.DataFrame([mean_row])], ignore_index=True)
                                
                                # 添加月均留存率列
                                retention_summary = []
                                for day in range(1, 31):
                                    if mean_row[str(day)] > 0:
                                        retention_summary.append({
                                            '天数': day,
                                            '月均留存率': mean_row[str(day)]
                                        })
                                
                                retention_results[channel_name] = {
                                    'detail': df,
                                    'summary': pd.DataFrame(retention_summary)
                                }
                        
                        st.session_state.retention_data = retention_results
                        st.success("留存率计算完成")
                        
                        # 结果统计
                        st.metric("成功计算渠道数", len(retention_results))
                        
                    except Exception as e:
                        st.error(f"留存率计算失败：{e}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 显示计算结果
        if st.session_state.retention_data:
            st.subheader("留存率计算结果")
            
            for channel_name, data in st.session_state.retention_data.items():
                with st.expander(f"{channel_name} - 留存率详情"):
                    
                    tab1, tab2 = st.tabs(["详细数据", "汇总统计"])
                    
                    with tab1:
                        st.dataframe(data['detail'], use_container_width=True)
                    
                    with tab2:
                        st.dataframe(data['summary'], use_container_width=True)
    else:
        st.warning("请先完成数据上传与汇总")

elif page == "LT简化计算":
    st.header("LT简化计算")
    st.markdown("使用简化算法进行生命周期价值计算，无需复杂数学库依赖。")
    
    if st.session_state.retention_data is not None:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            retention_data = st.session_state.retention_data
            st.info(f"已加载 {len(retention_data)} 个渠道的留存率数据")
            
            # 显示渠道列表
            st.subheader("待分析渠道")
            channel_list = list(retention_data.keys())
            st.write(", ".join(channel_list))
        
        with col2:
            st.markdown('<div class="status-card">', unsafe_allow_html=True)
            st.subheader("计算设置")
            
            calculate_2y = st.checkbox("计算2年LT", value=True)
            calculate_5y = st.checkbox("计算5年LT", value=True)
            
            if st.button("开始LT简化计算", type="primary"):
                with st.spinner("正在进行LT计算..."):
                    try:
                        summary_data = []
                        fit_params_data = {}
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        total_channels = len(retention_data)
                        
                        for idx, (channel_name, channel_data) in enumerate(retention_data.items()):
                            status_text.text(f"正在处理: {channel_name}")
                            progress_bar.progress((idx + 1) / total_channels)
                            
                            # 准备拟合数据
                            summary_df = channel_data['summary']
                            
                            if len(summary_df) > 0:
                                # 转换为拟合函数需要的格式
                                fit_data = pd.DataFrame({
                                    '留存天数': summary_df['天数'],
                                    '留存率': summary_df['月均留存率'] / 100  # 转换为小数
                                })
                                
                                results = {}
                                
                                if calculate_2y:
                                    lt_2_years, fit_params = calculate_lt_simple(
                                        fit_data, channel_name, lt_years=2
                                    )
                                    results['2年LT'] = lt_2_years
                                    fit_params_data[channel_name] = fit_params
                                
                                if calculate_5y:
                                    lt_5_years, _ = calculate_lt_simple(
                                        fit_data, channel_name, lt_years=5
                                    )
                                    results['5年LT'] = lt_5_years
                                
                                summary_row = {"渠道名称": channel_name}
                                summary_row.update(results)
                                summary_data.append(summary_row)
                        
                        # 清理进度显示
                        progress_bar.empty()
                        status_text.empty()
                        
                        # 保存结果
                        lt_results = {
                            'summary': pd.DataFrame(summary_data),
                            'fit_params': fit_params_data
                        }
                        
                        st.session_state.lt_results = lt_results
                        st.success("LT简化计算完成")
                        
                    except Exception as e:
                        st.error(f"LT计算失败：{e}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 显示分析结果
        if st.session_state.lt_results:
            st.subheader("LT计算结果")
            
            tab1, tab2 = st.tabs(["计算结果", "拟合参数"])
            
            with tab1:
                st.dataframe(st.session_state.lt_results['summary'], use_container_width=True)
            
            with tab2:
                if st.session_state.lt_results['fit_params']:
                    fit_params_list = []
                    for channel_name, params in st.session_state.lt_results['fit_params'].items():
                        row = {"渠道名称": channel_name}
                        row["幂函数_a"] = f"{params['a']:.6f}"
                        row["幂函数_b"] = f"{params['b']:.6f}"
                        fit_params_list.append(row)
                    
                    fit_params_df = pd.DataFrame(fit_params_list)
                    st.dataframe(fit_params_df, use_container_width=True)
                else:
                    st.info("无拟合参数数据")
            
            # 提供结果下载
            if st.button("下载分析报告"):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    st.session_state.lt_results['summary'].to_excel(writer, sheet_name='LT总结', index=False)
                    if fit_params_list:
                        fit_params_df.to_excel(writer, sheet_name='拟合参数', index=False)
                
                st.download_button(
                    label="下载LT分析报告",
                    data=output.getvalue(),
                    file_name="LT分析报告.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    else:
        st.warning("请先完成留存率计算")

elif page == "ARPU计算":
    st.header("ARPU计算")
    st.markdown("上传收入数据，计算各渠道的平均每用户收入。")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("ARPU数据文件")
        st.markdown("**必需字段：** 月份、pid、stat_date、instl_user_cnt、ad_all_rven_1d_m")
        
        arpu_file = st.file_uploader(
            "选择ARPU数据文件",
            type=['xlsx', 'xls'],
            key="arpu_file"
        )
        
        if arpu_file:
            try:
                arpu_df = pd.read_excel(arpu_file)
                st.success("ARPU数据文件上传成功")
                
                # 检查必要的列
                required_cols = ['月份', 'pid', 'stat_date', 'instl_user_cnt', 'ad_all_rven_1d_m']
                missing_cols = [col for col in required_cols if col not in arpu_df.columns]
                
                if missing_cols:
                    st.error(f"缺少必要的列：{', '.join(missing_cols)}")
                else:
                    st.success("数据格式验证通过")
                    
                    with st.expander("数据预览"):
                        st.dataframe(arpu_df.head(10))
                    
                    # 月份筛选
                    available_months = sorted(arpu_df['月份'].unique())
                    st.subheader("分析月份选择")
                    
                    # 默认选择最新一年的数据
                    current_year = datetime.datetime.now().year
                    default_months = [m for m in available_months if str(current_year) in str(m)]
                    
                    selected_months = st.multiselect(
                        "选择要分析的月份",
                        available_months,
                        default=default_months[-12:] if len(default_months) >= 12 else default_months
                    )
                    
                    st.info(f"已选择 {len(selected_months)} 个月份进行分析")
                    
            except Exception as e:
                st.error(f"读取ARPU文件失败：{e}")
    
    with col2:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        st.subheader("计算设置")
        
        if 'arpu_df' in locals() and 'selected_months' in locals() and selected_months:
            if st.session_state.channel_mapping is not None:
                
                if st.button("开始ARPU计算", type="primary"):
                    with st.spinner("正在计算ARPU..."):
                        try:
                            # 筛选数据
                            filtered_arpu = arpu_df[arpu_df['月份'].isin(selected_months)].copy()
                            
                            # 数据清洗
                            filtered_arpu['instl_user_cnt'] = pd.to_numeric(filtered_arpu['instl_user_cnt'], errors='coerce')
                            filtered_arpu['ad_all_rven_1d_m'] = pd.to_numeric(filtered_arpu['ad_all_rven_1d_m'], errors='coerce')
                            
                            # 删除无效数据
                            filtered_arpu = filtered_arpu.dropna(subset=['instl_user_cnt', 'ad_all_rven_1d_m'])
                            
                            # 使用改进的渠道匹配函数
                            pid_to_channel = parse_channel_mapping(st.session_state.channel_mapping)
                            
                            # 添加渠道名列
                            filtered_arpu['渠道名称'] = filtered_arpu['pid'].astype(str).map(pid_to_channel)
                            
                            # 过滤掉无法匹配的渠道号
                            matched_data = filtered_arpu[filtered_arpu['渠道名称'].notna()].copy()
                            
                            if len(matched_data) == 0:
                                st.error("没有找到匹配的渠道数据，请检查渠道映射表和数据文件")
                            else:
                                # 按渠道汇总
                                arpu_summary = matched_data.groupby('渠道名称').agg({
                                    'instl_user_cnt': 'sum',
                                    'ad_all_rven_1d_m': 'sum'
                                }).reset_index()
                                
                                # 计算ARPU
                                arpu_summary['ARPU'] = arpu_summary['ad_all_rven_1d_m'] / arpu_summary['instl_user_cnt']
                                
                                # 处理无效值
                                arpu_summary['ARPU'] = arpu_summary['ARPU'].fillna(0)
                                
                                st.session_state.arpu_data = arpu_summary
                                st.success("ARPU计算完成")
                                
                                # 统计信息
                                st.metric("匹配渠道数", len(arpu_summary))
                                st.metric("总用户数", f"{arpu_summary['instl_user_cnt'].sum():,.0f}")
                                st.metric("总收入", f"{arpu_summary['ad_all_rven_1d_m'].sum():,.2f}")
                                
                        except Exception as e:
                            st.error(f"ARPU计算失败：{e}")
            else:
                st.warning("请先上传渠道映射表")
        else:
            st.info("请先上传ARPU数据文件并选择分析月份")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 显示ARPU计算结果
    if st.session_state.arpu_data is not None:
        st.subheader("ARPU计算结果")
        
        arpu_summary = st.session_state.arpu_data
        
        # 结果展示
        col_a, col_b = st.columns([2, 1])
        
        with col_a:
            st.dataframe(arpu_summary, use_container_width=True)
        
        with col_b:
            # ARPU排行榜
            st.subheader("ARPU排行榜")
            top_arpu = arpu_summary.nlargest(5, 'ARPU')[['渠道名称', 'ARPU']]
            for idx, row in top_arpu.iterrows():
                st.metric(row['渠道名称'], f"{row['ARPU']:.2f}")
        
        # 提供下载
        if st.button("下载ARPU计算结果"):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                arpu_summary.to_excel(writer, sheet_name='ARPU计算结果', index=False)
            
            st.download_button(
                label="下载ARPU报告",
                data=output.getvalue(),
                file_name="ARPU计算结果.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

elif page == "LTV结果报告":
    st.header("LTV结果报告")
    st.markdown("整合LT分析和ARPU计算结果，生成最终的用户生命周期价值报告。")
    
    if st.session_state.lt_results is not None and st.session_state.arpu_data is not None:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.success("数据完整性检查通过")
            
            # 数据概览
            lt_summary = st.session_state.lt_results['summary']
            arpu_summary = st.session_state.arpu_data
            
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.metric("LT分析渠道数", len(lt_summary))
            with col_info2:
                st.metric("ARPU计算渠道数", len(arpu_summary))
        
        with col2:
            st.markdown('<div class="status-card">', unsafe_allow_html=True)
            st.subheader("生成报告")
            
            if st.button("生成LTV结果报告", type="primary"):
                with st.spinner("正在生成最终报告..."):
                    try:
                        # 合并LT和ARPU数据
                        ltv_results = lt_summary.merge(
                            arpu_summary[['渠道名称', 'ARPU']], 
                            on='渠道名称', 
                            how='left'
                        )
                        
                        # 计算LTV
                        if '2年LT' in ltv_results.columns:
                            ltv_results['2年LTV'] = ltv_results['2年LT'] * ltv_results['ARPU']
                        
                        if '5年LT' in ltv_results.columns:
                            ltv_results['5年LTV'] = ltv_results['5年LT'] * ltv_results['ARPU']
                        
                        # 重新排列列顺序
                        column_order = ['渠道名称']
                        if '5年LT' in ltv_results.columns:
                            column_order.extend(['5年LT', 'ARPU', '5年LTV'])
                        if '2年LT' in ltv_results.columns:
                            column_order.extend(['2年LT', '2年LTV'])
                        
                        # 添加其他列
                        for col in ltv_results.columns:
                            if col not in column_order:
                                column_order.append(col)
                        
                        ltv_results = ltv_results[column_order]
                        
                        st.session_state.ltv_results = ltv_results
                        st.success("LTV结果报告生成完成")
                        
                    except Exception as e:
                        st.error(f"生成LTV结果失败：{e}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 显示最终结果
        if st.session_state.ltv_results is not None:
            st.subheader("最终LTV分析结果")
            
            ltv_results = st.session_state.ltv_results
            
            # 主要结果表格
            st.dataframe(ltv_results, use_container_width=True)
            
            # 分析洞察
            col_insight1, col_insight2 = st.columns(2)
            
            with col_insight1:
                if '5年LTV' in ltv_results.columns:
                    st.subheader("5年LTV表现")
                    top_5y_ltv = ltv_results.nlargest(5, '5年LTV')[['渠道名称', '5年LTV']]
                    
                    for idx, row in top_5y_ltv.iterrows():
                        st.metric(
                            row['渠道名称'], 
                            f"{row['5年LTV']:.2f}",
                            help="5年期用户生命周期价值"
                        )
            
            with col_insight2:
                if '2年LTV' in ltv_results.columns:
                    st.subheader("2年LTV表现")
                    top_2y_ltv = ltv_results.nlargest(5, '2年LTV')[['渠道名称', '2年LTV']]
                    
                    for idx, row in top_2y_ltv.iterrows():
                        st.metric(
                            row['渠道名称'], 
                            f"{row['2年LTV']:.2f}",
                            help="2年期用户生命周期价值"
                        )
            
            # 综合分析报告下载
            st.subheader("下载完整报告")
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # 保存最终结果
                ltv_results.to_excel(writer, sheet_name='LTV最终结果', index=False)
                
                # 保存其他相关数据
                st.session_state.arpu_data.to_excel(writer, sheet_name='ARPU计算结果', index=False)
                st.session_state.lt_results['summary'].to_excel(writer, sheet_name='LT分析结果', index=False)
            
            st.download_button(
                label="下载完整LTV分析报告",
                data=output.getvalue(),
                file_name=f"LTV分析报告_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    elif st.session_state.lt_results is None:
        st.warning("请先完成LT简化计算")
    elif st.session_state.arpu_data is None:
        st.warning("请先完成ARPU计算")
    
    # 如果已经有最终结果，直接显示
    if st.session_state.ltv_results is not None:
        st.subheader("当前LTV分析结果")
        st.dataframe(st.session_state.ltv_results, use_container_width=True)

# 侧边栏进度状态
st.sidebar.markdown("---")
st.sidebar.markdown("### 分析进度")

progress_items = [
    ("渠道映射表", st.session_state.channel_mapping is not None),
    ("数据汇总", st.session_state.merged_data is not None),
    ("留存率计算", st.session_state.retention_data is not None),
    ("LT简化计算", st.session_state.lt_results is not None),
    ("ARPU计算", st.session_state.arpu_data is not None),
    ("LTV结果报告", st.session_state.ltv_results is not None)
]

for item_name, is_completed in progress_items:
    status_class = "✓" if is_completed else "○"
    status_color = "#28a745" if is_completed else "#6c757d"
    
    st.sidebar.markdown(
        f'<div class="progress-item" style="color: {status_color};">'
        f'{status_class} {item_name}'
        f'</div>',
        unsafe_allow_html=True
    )

# 底部信息
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #6c757d; font-size: 0.9rem;'>
        <p><strong>LTV Analytics Platform</strong></p>
        <p>用户生命周期价值分析系统 | 支持数据汇总、留存率计算、LT拟合、ARPU计算和LTV分析</p>
    </div>
    """, 
    unsafe_allow_html=True
)
