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

# ==================== 基础配置 ====================
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

# ==================== CSS 样式定义 ====================
# 简洁CSS样式
st.markdown("""
<style>
    /* 全局样式 */
    .main {
        background: #f8f9fa;
        min-height: 100vh;
    }

    .block-container {
        padding: 1rem 1rem 3rem 1rem;
        max-width: 100%;
        background: transparent;
    }

    /* 主标题区域 */
    .main-header {
        background: white;
        padding: 1.2rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
        margin-bottom: 1.5rem;
        text-align: center;
    }

    .main-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 0.3rem;
    }

    .main-subtitle {
        color: #6c757d;
        font-size: 1.1rem;
        font-weight: 400;
    }

    /* 卡片样式 */
    .glass-card {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
    }

    /* 分界线 */
    .section-divider {
        height: 1px;
        background: #dee2e6;
        margin: 1rem 0;
    }

    /* 指标卡片 */
    .metric-card {
        background: #f8f9fa;
        color: #495057;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #dee2e6;
        margin-bottom: 0.8rem;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #2c3e50;
    }

    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
    }

    /* 状态卡片 */
    .status-card {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #28a745;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 0.8rem;
    }

    /* 导航步骤样式 */
    .nav-container {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #e9ecef;
    }

    /* 按钮样式 */
    .stButton > button {
        background: #28a745;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background: #218838;
        transform: translateY(-1px);
    }

    /* 选择框样式 */
    .stSelectbox label, .stMultiselect label, .stFileUploader label {
        font-weight: 600;
        color: #495057;
        margin-bottom: 0.5rem;
    }

    /* 标题样式 */
    h1, h2, h3, h4 {
        color: #2c3e50;
        font-weight: 600;
        font-size: 1.1rem !important;
    }

    /* 说明文字样式 */
    .step-explanation {
        background: #f8f9fa;
        border-left: 4px solid #28a745;
        padding: 1.5rem;
        margin-top: 2rem;
        border-radius: 0 8px 8px 0;
    }

    .step-explanation h4 {
        color: #2c3e50;
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
        color: #495057;
        line-height: 1.5;
    }

    .step-explanation strong {
        color: #2c3e50;
        font-weight: 600;
    }

    /* 隐藏默认的Streamlit元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==================== 默认配置数据 ====================
# 默认渠道映射数据
DEFAULT_CHANNEL_MAPPING = {
    '9000': '总体',
    '500345': '新媒体', '500346': '新媒体', '500447': '新媒体', '500449': '新媒体',
    '500450': '新媒体', '500531': '新媒体', '500542': '新媒体',
    '5007XS': '应用宝', '500349': '应用宝', '500350': '应用宝',
    '500285': '鼎乐-盛世6', '500286': '鼎乐-盛世7',
    '5108': '酷派', '5528': '酷派',
    '500275': '新美-北京2', '500274': '新美-北京1',
    '500316': 'A_深圳蛋丁2',
    '500297': '荣耀', '5057': '华为', '5237': 'vivo', '5599': '小米', '5115': 'OPPO',
    '500471': '网易', '500480': '网易', '500481': '网易', '500482': '网易',
    '500337': '华为非商店-品众', '500338': '华为非商店-品众', '500343': '华为非商店-品众', 
    '500445': '华为非商店-品众', '500383': '华为非商店-品众', '500444': '华为非商店-品众', '500441': '华为非商店-品众',
    '5072': '魅族',
    '500287': 'OPPO非商店', '500288': 'OPPO非商店',
    '5187': 'vivo非商店',
    '500398': '百度sem--百度时代安卓', '500400': '百度sem--百度时代安卓', '500404': '百度sem--百度时代安卓',
    '500402': '百度sem--百度时代ios', '500403': '百度sem--百度时代ios', '500405': '百度sem--百度时代ios',
    '500377': '百青藤-安卓', '500379': '百青藤-安卓', '500435': '百青藤-安卓', '500436': '百青藤-安卓', 
    '500490': '百青藤-安卓', '500491': '百青藤-安卓', '500434': '百青藤-安卓', '500492': '百青藤-安卓',
    '500437': '百青藤-ios',
    '500170': '小米非商店',
    '500532': '华为非商店-星火', '500533': '华为非商店-星火', '500534': '华为非商店-星火', '500537': '华为非商店-星火',
    '500538': '华为非商店-星火', '500539': '华为非商店-星火', '500540': '华为非商店-星火', '500541': '华为非商店-星火',
    '500504': '微博-蜜橘', '500505': '微博-蜜橘',
    '500367': '微博-央广', '500368': '微博-央广', '500369': '微博-央广',
    '500498': '广点通（5.22起）', '500497': '广点通（5.22起）', '500500': '广点通（5.22起）', 
    '500501': '广点通（5.22起）', '500496': '广点通（5.22起）', '500499': '广点通（5.22起）',
    '500514': '网易易效', '500515': '网易易效', '500516': '网易易效'
}

# ==================== 日期处理函数 ====================
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

# ==================== 数据类型转换函数 ====================
def safe_convert_to_numeric(value):
    """
    安全地将值转换为数值类型
    """
    if pd.isna(value) or value == '' or value is None:
        return 0
    try:
        # 如果是字符串，先去除空格
        if isinstance(value, str):
            value = value.strip()
            if value == '' or value.lower() in ['nan', 'null', 'none']:
                return 0
        return pd.to_numeric(value, errors='coerce')
    except:
        return 0

# ==================== 数据结构标准化函数 ====================
def standardize_output_columns(df):
    """
    标准化输出列结构，确保包含指定的列顺序，并正确处理数据类型
    """
    print("正在标准化输出列结构...")

    # 定义目标列顺序
    target_columns = [
        '数据来源', 'date', '数据来源_date',
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
        '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
        '21', '22', '23', '24', '25', '26', '27', '28', '29', '30',
        '数据来源_日期', '日期', '回传新增数', 'is_target_month', 'month', 'stat_date'
    ]

    # 按目标列顺序创建结果DataFrame
    result_df = pd.DataFrame()

    # 按精确顺序添加每一列
    for col_name in target_columns:
        if col_name == '数据来源':
            result_df[col_name] = df[col_name].astype(str) if col_name in df.columns else ''
        elif col_name == 'date':
            if col_name in df.columns:
                result_df[col_name] = df[col_name].astype(str)
            elif 'stat_date' in df.columns:
                result_df[col_name] = df['stat_date'].astype(str)
            else:
                result_df[col_name] = ''
        elif col_name == '数据来源_date':
            # 创建数据来源_date列
            data_source = df['数据来源'].astype(str) if '数据来源' in df.columns else pd.Series([''] * len(df))
            
            if 'date' in df.columns:
                date_col_str = df['date'].astype(str)
            elif 'stat_date' in df.columns:
                date_col_str = df['stat_date'].astype(str)
            else:
                date_col_str = pd.Series([''] * len(df))

            result_df[col_name] = data_source + date_col_str
        elif col_name == '数据来源_日期':
            # 创建数据来源_日期列
            data_source = df['数据来源'].astype(str) if '数据来源' in df.columns else pd.Series([''] * len(df))

            if '日期' in df.columns:
                date_col_str = df['日期'].astype(str)
            elif 'date' in df.columns:
                date_col_str = df['date'].astype(str)
            elif 'stat_date' in df.columns:
                date_col_str = df['stat_date'].astype(str)
            else:
                date_col_str = pd.Series([''] * len(df))

            result_df[col_name] = data_source + date_col_str
        elif col_name in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
                          '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
                          '21', '22', '23', '24', '25', '26', '27', '28', '29', '30']:
            # 数字列：确保转换为数值类型
            if col_name in df.columns:
                result_df[col_name] = df[col_name].apply(safe_convert_to_numeric)
            else:
                result_df[col_name] = 0
        elif col_name == '回传新增数':
            # 回传新增数列：确保转换为数值类型
            if col_name in df.columns:
                result_df[col_name] = df[col_name].apply(safe_convert_to_numeric)
            else:
                result_df[col_name] = 0
        else:
            # 其他列直接复制，如果不存在则填空
            if col_name in df.columns:
                result_df[col_name] = df[col_name]
            else:
                result_df[col_name] = ''

    # 添加原数据中存在但不在目标列表中的其他列（保持在最后）
    for col in df.columns:
        if col not in target_columns:
            result_df[col] = df[col]

    print(f"已标准化输出列结构，共 {len(result_df.columns)} 列，按指定顺序排列")
    return result_df

# ==================== 渠道映射处理函数 ====================
def parse_channel_mapping_from_excel(channel_file):
    """
    从上传的Excel文件解析渠道映射
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(channel_file)
        
        pid_to_channel = {}
        
        # 遍历每一行
        for _, row in df.iterrows():
            # 第一列是渠道名称
            channel_name = str(row.iloc[0]).strip()
            if pd.isna(channel_name) or channel_name == '' or channel_name == 'nan':
                continue
                
            # 从第二列开始是渠道号
            for col_idx in range(1, len(row)):
                pid = row.iloc[col_idx]
                if pd.isna(pid) or str(pid).strip() in ['', 'nan', '　', ' ']:
                    continue
                pid_str = str(pid).strip()
                if pid_str:
                    pid_to_channel[pid_str] = channel_name
                    
        return pid_to_channel
    except Exception as e:
        st.error(f"解析渠道映射文件失败：{str(e)}")
        return {}

# ==================== 文件整合核心函数 ====================
def integrate_excel_files_streamlit(uploaded_files, target_month=None, channel_mapping=None):
    """
    整合上传的Excel文件，支持新格式表和传统格式表
    """
    if target_month is None:
        target_month = get_default_target_month()

    all_data = pd.DataFrame()
    processed_count = 0
    mapping_warnings = []

    for uploaded_file in uploaded_files:
        source_name = os.path.splitext(uploaded_file.name)[0]

        # 渠道映射处理
        if channel_mapping and source_name in channel_mapping:
            mapped_source = channel_mapping[source_name]
        else:
            mapped_source = source_name
            if channel_mapping:
                mapping_warnings.append(f"文件 '{source_name}' 未在渠道映射表中找到对应项")

        try:
            # 读取Excel文件
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names

            # 查找目标工作表
            ocpx_sheet = None
            for sheet in sheet_names:
                if "ocpx监测留存数" in sheet:
                    ocpx_sheet = sheet
                    break

            if ocpx_sheet:
                file_data = pd.read_excel(uploaded_file, sheet_name=ocpx_sheet)
            else:
                file_data = pd.read_excel(uploaded_file, sheet_name=0)

            if file_data is not None and not file_data.empty:
                file_data_copy = file_data.copy()

                # ========== 检测文件格式类型 ==========
                # 检查是否是新格式表（包含stat_date和留存列）
                is_new_format = False
                has_stat_date = 'stat_date' in file_data_copy.columns
                retain_columns = [f'new_retain_{i}' for i in range(1, 31)]
                has_retain_columns = any(col in file_data_copy.columns for col in retain_columns)

                # ========== 处理新格式表 ==========
                if has_stat_date and has_retain_columns:
                    is_new_format = True
                    print(f"检测到 {uploaded_file.name} 是新格式表（含stat_date和留存列）")

                    # 创建标准的输出结构
                    standardized_data = file_data_copy.copy()

                    # 将new列的值映射到"回传新增数"列，确保是数值类型
                    if 'new' in standardized_data.columns:
                        standardized_data['回传新增数'] = standardized_data['new'].apply(safe_convert_to_numeric)

                    # 将new_retain_1到new_retain_30的值分别映射到数字列名(1到30)，确保是数值类型
                    for i in range(1, 31):
                        retain_col = f'new_retain_{i}'
                        if retain_col in standardized_data.columns:
                            standardized_data[str(i)] = standardized_data[retain_col].apply(safe_convert_to_numeric)

                    # 确保stat_date被视为日期列
                    date_col = 'stat_date'
                    standardized_data[date_col] = pd.to_datetime(standardized_data[date_col], errors='coerce')
                    # 将日期转为字符串格式
                    standardized_data[date_col] = standardized_data[date_col].dt.strftime('%Y-%m-%d')
                    # 添加"日期"列，与stat_date相同
                    standardized_data['日期'] = standardized_data[date_col]
                    # 添加月份列
                    standardized_data['month'] = standardized_data[date_col].str[:7]

                    # 筛选目标月份的数据
                    filtered_data = standardized_data[standardized_data['month'] == target_month].copy()

                    # 如果存在留存天数列，还要保留特殊行
                    retention_col = None
                    for col in standardized_data.columns:
                        if '留存天数' in str(col):
                            retention_col = col
                            break

                    if retention_col is not None:
                        # 找出留存天数为特定值的行
                        special_rows = standardized_data[(standardized_data[retention_col] == "2025-02-01") |
                                                         (standardized_data[retention_col] == "合计") |
                                                         (standardized_data[retention_col].astype(
                                                             str) == "2025-02-01") |
                                                         (standardized_data[retention_col].astype(str) == "合计")]

                        # 合并数据框：目标月份的数据和特殊行
                        if not special_rows.empty:
                            filtered_data = pd.concat([filtered_data, special_rows]).drop_duplicates()

                    if not filtered_data.empty:
                        # 添加数据来源列
                        filtered_data.insert(0, '数据来源', mapped_source)

                        # 处理date列
                        if retention_col is not None:
                            filtered_data.rename(columns={retention_col: 'date'}, inplace=True)
                        elif 'stat_date' in filtered_data.columns:
                            filtered_data['date'] = filtered_data['stat_date']

                        # 将筛选后的数据添加到总数据框
                        all_data = pd.concat([all_data, filtered_data], ignore_index=True)
                        processed_count += 1

                # ========== 处理传统格式表 ==========
                else:
                    # 查找留存天数列
                    retention_col = None
                    for col in file_data_copy.columns:
                        if '留存天数' in str(col):
                            retention_col = col
                            break

                    # 查找回传新增数列或total_new_users列
                    report_users_col = None
                    for col in file_data_copy.columns:
                        if '回传新增数' in str(col):
                            report_users_col = col
                            break
                        if 'total_new_users' in str(col).lower():
                            report_users_col = col
                            break

                    # 获取第二列作为备选
                    column_b = file_data_copy.columns[1] if len(file_data_copy.columns) > 1 else None

                    # 检查是否有日期列
                    date_col = None
                    for col in file_data_copy.columns:
                        if '日期' in str(col):
                            date_col = col
                            break

                    # ========== 处理回传新增数列映射 ==========
                    if report_users_col and report_users_col != '回传新增数':
                        file_data_copy['回传新增数'] = file_data_copy[report_users_col].apply(safe_convert_to_numeric)
                    elif not report_users_col and column_b:
                        # 如果没有找到相关列，使用第二列作为"回传新增数"
                        file_data_copy['回传新增数'] = file_data_copy[column_b].apply(safe_convert_to_numeric)

                    # ========== 处理数字列（1-30天留存数据）==========
                    for i in range(1, 31):
                        col_name = str(i)
                        if col_name in file_data_copy.columns:
                            file_data_copy[col_name] = file_data_copy[col_name].apply(safe_convert_to_numeric)

                    # ========== 处理日期列数据和筛选 ==========
                    if date_col:
                        # 将日期列转换为日期类型以便计算前后范围
                        try:
                            if not pd.api.types.is_datetime64_dtype(file_data_copy[date_col]):
                                temp_dates = pd.to_datetime(file_data_copy[date_col], errors='coerce')
                                file_data_copy[date_col] = temp_dates

                            # 提取目标月份的第一天和最后一天
                            target_year, target_month_num = map(int, target_month.split('-'))
                            first_day_of_month = pd.Timestamp(year=target_year, month=target_month_num, day=1)

                            # 计算下一个月的第一天
                            if target_month_num == 12:
                                next_month = pd.Timestamp(year=target_year + 1, month=1, day=1)
                            else:
                                next_month = pd.Timestamp(year=target_year, month=target_month_num + 1, day=1)

                            # 最后一天是下一个月的第一天减一天
                            last_day_of_month = next_month - pd.Timedelta(days=1)

                            # 计算目标范围（月份前后5天）
                            start_date = first_day_of_month - pd.Timedelta(days=5)
                            end_date = last_day_of_month + pd.Timedelta(days=5)

                            # 筛选日期在范围内的数据
                            mask = (file_data_copy[date_col] >= start_date) & (file_data_copy[date_col] <= end_date)

                            # 如果存在留存天数列，还要保留特殊值的行
                            if retention_col is not None:
                                # 生成指定月份的所有日期值的列表
                                all_month_dates = []
                                current_date = first_day_of_month
                                while current_date <= last_day_of_month:
                                    date_str = current_date.strftime('%Y-%m-%d')
                                    all_month_dates.append(date_str)
                                    current_date += pd.Timedelta(days=1)

                                # 添加"合计"作为特殊值
                                all_month_dates.append("合计")

                                # 找出留存天数为特定值的行
                                retention_col_str = file_data_copy[retention_col].astype(str)
                                special_rows_mask = np.zeros(len(file_data_copy), dtype=bool)

                                for date_val in all_month_dates:
                                    special_rows_mask = special_rows_mask | (retention_col_str == date_val)

                                # 合并筛选条件：日期在范围内，或留存天数为特定值
                                mask = mask | special_rows_mask

                            filtered_data = file_data_copy[mask].copy()

                            # 添加标记列和月份信息列
                            filtered_data['is_target_month'] = (filtered_data[date_col] >= first_day_of_month) & (
                                    filtered_data[date_col] <= last_day_of_month)
                            filtered_data['month'] = filtered_data[date_col].dt.strftime('%Y-%m')

                            # 将日期转回字符串格式
                            filtered_data[date_col] = filtered_data[date_col].dt.strftime('%Y-%m-%d')

                            if not filtered_data.empty:
                                # 添加数据来源列
                                filtered_data.insert(0, '数据来源', mapped_source)

                                # 将"留存天数"列重命名为"date"
                                if retention_col is not None:
                                    filtered_data.rename(columns={retention_col: 'date'}, inplace=True)
                                elif date_col != 'date':
                                    filtered_data['date'] = filtered_data[date_col]

                                # 将筛选后的数据添加到总数据框
                                all_data = pd.concat([all_data, filtered_data], ignore_index=True)
                                processed_count += 1

                        except Exception as e:
                            print(f"处理日期范围时出错: {str(e)}")
                            # 发生错误时，退回到仅筛选月份的方法
                            file_data_copy['month'] = file_data_copy[date_col].apply(
                                lambda x: x[:7] if isinstance(x, str) else None
                            )

                            # 筛选目标月份的数据
                            filtered_data = file_data_copy[file_data_copy['month'] == target_month].copy()

                            if 'month' in filtered_data.columns:
                                filtered_data.drop('month', axis=1, inplace=True)

                            if not filtered_data.empty:
                                # 添加数据来源列
                                filtered_data.insert(0, '数据来源', mapped_source)

                                # 处理date列
                                if retention_col is not None:
                                    filtered_data.rename(columns={retention_col: 'date'}, inplace=True)
                                elif date_col != 'date':
                                    filtered_data['date'] = filtered_data[date_col]

                                # 将筛选后的数据添加到总数据框
                                all_data = pd.concat([all_data, filtered_data], ignore_index=True)
                                processed_count += 1

                    else:
                        # 如果没有日期列，保留所有数据
                        # 添加数据来源列
                        file_data_copy.insert(0, '数据来源', mapped_source)

                        # 将"留存天数"列重命名为"date"，如果有的话
                        if retention_col is not None:
                            file_data_copy.rename(columns={retention_col: 'date'}, inplace=True)

                        # 将所有数据添加到总数据框
                        all_data = pd.concat([all_data, file_data_copy], ignore_index=True)
                        processed_count += 1

        except Exception as e:
            st.error(f"处理文件 {uploaded_file.name} 时出错: {str(e)}")

    # ========== 处理合并后的数据 ==========
    if not all_data.empty:
        # 查找date列
        date_col = None
        for col in all_data.columns:
            if col == 'date':
                date_col = col
                break

        # 为新格式表创建date列
        if date_col is None and 'stat_date' in all_data.columns:
            all_data['date'] = all_data['stat_date']
            date_col = 'date'

        # 排序处理
        sort_columns = []
        if '数据来源' in all_data.columns:
            sort_columns.append('数据来源')

        if date_col:
            try:
                all_data[date_col] = pd.to_datetime(all_data[date_col], errors='coerce')
                sort_columns.append(date_col)
            except:
                sort_columns.append(date_col)

        # 执行排序
        if sort_columns:
            all_data = all_data.sort_values(by=sort_columns)
            # 将日期列转回字符串格式
            if date_col and pd.api.types.is_datetime64_dtype(all_data[date_col]):
                all_data[date_col] = all_data[date_col].dt.strftime('%Y-%m-%d')

        # 标准化输出列结构
        standardized_df = standardize_output_columns(all_data)
        return standardized_df, processed_count, mapping_warnings
    else:
        return None, 0, mapping_warnings

# ==================== 数学建模函数 ====================
# 定义数学函数
def power_function(x, a, b):
    """幂函数：y = a * x^b"""
    return a * np.power(x, b)

def exponential_function(x, c, d):
    """指数函数：y = c * exp(d * x)"""
    return c * np.exp(d * x)

# ==================== 留存率计算函数 ====================
# 留存率计算
def calculate_retention_rates_advanced(df):
    retention_results = []
    data_sources = df['数据来源'].unique()

    for source in data_sources:
        source_data = df[df['数据来源'] == source].copy()
        all_days = []
        all_rates = []

        for _, row in source_data.iterrows():
            new_users = safe_convert_to_numeric(row.get('回传新增数', 0))
            if pd.isna(new_users) or new_users <= 0:
                continue

            for day in range(1, 31):
                day_col = str(day)
                if day_col in row and not pd.isna(row[day_col]):
                    retain_count = safe_convert_to_numeric(row[day_col])
                    if retain_count > 0:
                        retention_rate = retain_count / new_users
                        if 0 < retention_rate <= 1.5:
                            all_days.append(day)
                            all_rates.append(retention_rate)

        if all_days:
            df_temp = pd.DataFrame({'day': all_days, 'rate': all_rates})
            df_avg = df_temp.groupby('day')['rate'].mean().reset_index()

            retention_data = {
                'data_source': source,
                'days': df_avg['day'].values,
                'rates': df_avg['rate'].values
            }
            retention_results.append(retention_data)

    return retention_results

# ==================== 计算指定天数的累积LT值函数 ====================
def calculate_cumulative_lt(days_array, rates_array, target_days):
    """计算指定天数的累积LT值"""
    result = {}
    for day in target_days:
        idx = np.searchsorted(days_array, day, side='right')
        if idx > 0:
            # 计算到指定天数的累积LT值（包括第0天的1.0）
            cumulative_lt = 1.0 + np.sum(rates_array[1:idx])
            result[day] = cumulative_lt
    return result

# ==================== LT拟合分析函数 ====================
# LT拟合分析 - 使用第二段代码的逻辑
def calculate_lt_advanced(retention_result, channel_name, lt_years=5, return_curve_data=False, key_days=None):
    """
    按渠道规则计算 LT，允许 1-30 天数据不连续。
    参数:
        lt_years: 计算几年的LT，默认5年
        return_curve_data: 是否返回曲线数据用于可视化
        key_days: 关键时间点列表，用于计算这些时间点的累积LT值
    """
    # 渠道规则
    CHANNEL_RULES = {
        "华为": {"stage_2": [30, 120], "stage_3_base": [120, 220]},
        "小米": {"stage_2": [30, 190], "stage_3_base": [190, 290]},
        "oppo": {"stage_2": [30, 160], "stage_3_base": [160, 260]},
        "vivo": {"stage_2": [30, 150], "stage_3_base": [150, 250]},
        "iphone": {"stage_2": [30, 150], "stage_3_base": [150, 250]},
        "其他": {"stage_2": [30, 100], "stage_3_base": [100, 200]}
    }

    if re.search(r'华为', channel_name):
        rules = CHANNEL_RULES["华为"]
    elif re.search(r'小米', channel_name):
        rules = CHANNEL_RULES["小米"]
    elif re.search(r'oppo|OPPO', channel_name):
        rules = CHANNEL_RULES["oppo"]
    elif re.search(r'vivo', channel_name):
        rules = CHANNEL_RULES["vivo"]
    elif re.search(r'iphone|iPhone', channel_name):
        rules = CHANNEL_RULES["iphone"]
    else:
        rules = CHANNEL_RULES["其他"]

    stage_2_start, stage_2_end = rules["stage_2"]
    stage_3_base_start, stage_3_base_end = rules["stage_3_base"]

    # 计算最大天数（根据指定年数）
    max_days = lt_years * 365

    days = retention_result["days"]
    rates = retention_result["rates"]

    # 存储拟合参数，用于后续分析
    fit_params = {}

    # ----- 第一阶段 -----
    try:
        # 用已有数据对 1-30 天的留存率进行拟合
        popt_power, _ = curve_fit(power_function, days, rates)
        a, b = popt_power
        fit_params["power"] = {"a": a, "b": b}

        # 用拟合函数生成完整的 1-30 天留存率
        days_full = np.arange(1, 31)  # 连续的 1-30 天
        rates_full = power_function(days_full, a, b)

        # 第一阶段的 LT 累加值
        lt1_to_30 = np.sum(rates_full)
    except Exception as e:
        lt1_to_30 = 0.0
        a, b = 1.0, -1.0  # 默认参数

    # ----- 第二阶段 -----
    try:
        days_stage_2 = np.arange(stage_2_start, stage_2_end + 1)
        rates_stage_2 = power_function(days_stage_2, a, b)
        lt_stage_2 = np.sum(rates_stage_2)
    except Exception as e:
        lt_stage_2 = 0.0
        rates_stage_2 = np.array([])

    # ----- 第三阶段 -----
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
        days_stage_3 = np.arange(stage_3_base_start, max_days + 1)
        rates_stage_3 = power_function(days_stage_3, a, b) if 'a' in locals() else np.zeros(len(days_stage_3))
        lt_stage_3 = np.sum(rates_stage_3)

    # ----- 总 LT 计算 -----
    total_lt = 1.0 + lt1_to_30 + lt_stage_2 + lt_stage_3

    # 计算R²用于评估拟合质量
    try:
        predicted_rates = power_function(days, a, b)
        r2_score = 1 - np.sum((rates - predicted_rates) ** 2) / np.sum((rates - np.mean(rates)) ** 2)
    except:
        r2_score = 0.0

    if return_curve_data:
        # 返回不包含第0天的曲线数据用于可视化
        all_days = np.concatenate([
            days_full,      # 第1-30天
            days_stage_2,   # 第二阶段
            days_stage_3    # 第三阶段
        ])
        
        if 'rates_stage_2' not in locals():
            rates_stage_2 = power_function(days_stage_2, a, b)
        
        all_rates = np.concatenate([
            rates_full,                # 第1-30天
            rates_stage_2,             # 第二阶段
            rates_stage_3              # 第三阶段
        ])

        # 按天数排序
        sort_idx = np.argsort(all_days)
        all_days = all_days[sort_idx]
        all_rates = all_rates[sort_idx]

        # 只返回到指定年数的数据
        max_idx = np.searchsorted(all_days, lt_years * 365, side='right')
        all_days = all_days[:max_idx]
        all_rates = all_rates[:max_idx]

        # 计算关键时间点的累积LT值
        key_days_lt = {}
        if key_days:
            key_days_lt = calculate_cumulative_lt(all_days, all_rates, key_days)

        return {
            'lt_value': total_lt,
            'fit_params': fit_params,
            'power_r2': max(0, min(1, r2_score)),
            'success': True,
            'model_used': 'power+exponential',
            'curve_days': all_days,
            'curve_rates': all_rates,
            'key_days_lt': key_days_lt
        }

    return total_lt

# ==================== 可视化函数 - 使用第二段代码的逻辑 ====================
def visualize_lt_curves(visualization_data, years=2):
    """
    创建线性坐标LT曲线图
    渠道按LT值从低到高排序
    """
    # 按LT值从低到高排序渠道
    sorted_channels = sorted(visualization_data.items(), key=lambda x: x[1]['lt'])

    # 创建图表
    fig = plt.figure(figsize=(14, 8))
    ax = fig.add_subplot(111)

    # 设置颜色循环
    colors = plt.cm.tab10.colors

    # 为每个渠道绘制曲线
    for idx, (channel_name, data) in enumerate(sorted_channels):
        color = colors[idx % len(colors)]

        # 线性坐标图
        ax.plot(
            data["days"],
            data["rates"],
            label=f"{channel_name} (LT={data['lt']:.2f})",
            color=color,
            linewidth=2
        )

    # 线性坐标设置 - 修改为 0-60%
    ax.set_ylim(0, 0.6)
    ax.set_yticks([0, 0.15, 0.3, 0.45, 0.6])
    ax.set_yticklabels(['0%', '15%', '30%', '45%', '60%'])
    ax.grid(True, ls="--", alpha=0.5)
    ax.set_xlabel('留存天数')
    ax.set_ylabel('留存率')
    ax.set_title(f'所有渠道{years}年LT留存曲线比较 (按LT值从低到高排序)')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    return fig, colors, sorted_channels  # 返回颜色和排序后的渠道，以便后续使用

def visualize_log_comparison(visualization_data_2y, visualization_data_5y, colors=None, sorted_channels_2y=None):
    """
    创建2年和5年对数坐标比较图作为左右子图
    使用与线性图相同的颜色和排序
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # 如果没有提供排序渠道和颜色，则重新计算
    if sorted_channels_2y is None:
        sorted_channels_2y = sorted(visualization_data_2y.items(), key=lambda x: x[1]['lt'])
    if colors is None:
        colors = plt.cm.tab10.colors

    sorted_channels_5y = sorted(visualization_data_5y.items(), key=lambda x: x[1]['lt'])

    # 绘制2年对数图
    for idx, (channel_name, data) in enumerate(sorted_channels_2y):
        color = colors[idx % len(colors)]
        ax1.plot(
            data["days"],
            data["rates"],
            color=color,
            linewidth=2
        )

    # 绘制5年对数图
    for idx, (channel_name, data) in enumerate(sorted_channels_5y):
        color = colors[idx % len(colors)]
        ax2.plot(
            data["days"],
            data["rates"],
            color=color,
            linewidth=2
        )

    # 对数坐标设置 - 2年图
    ax1.set_yscale('log')
    ax1.set_ylim(0.001, 0.6)
    ax1.set_yticks([0.001, 0.01, 0.1, 0.6])
    ax1.set_yticklabels(['0.1%', '1%', '10%', '60%'])
    ax1.grid(True, ls="--", alpha=0.5)
    ax1.set_xlabel('留存天数')
    ax1.set_ylabel('留存率 (对数坐标)')
    ax1.set_title('2年LT留存曲线 (对数坐标)')

    # 对数坐标设置 - 5年图
    ax2.set_yscale('log')
    ax2.set_ylim(0.001, 0.6)
    ax2.set_yticks([0.001, 0.01, 0.1, 0.6])
    ax2.set_yticklabels(['0.1%', '1%', '10%', '60%'])
    ax2.grid(True, ls="--", alpha=0.5)
    ax2.set_xlabel('留存天数')
    ax2.set_title('5年LT留存曲线 (对数坐标)')

    plt.tight_layout()
    return fig

def visualize_fitting_comparison(original_data, visualization_data):
    """可视化拟合效果比较（实际数据vs拟合曲线）- 显示所有渠道"""
    # 按LT值从低到高排序渠道
    channels = sorted(visualization_data.keys(), key=lambda x: visualization_data[x]['lt'])

    # 计算需要多少行
    n_channels = len(channels)
    n_cols = 3
    n_rows = (n_channels + n_cols - 1) // n_cols  # 向上取整

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5*n_rows), squeeze=False)

    for i, channel_name in enumerate(channels):
        row = i // n_cols
        col = i % n_cols
        ax = axes[row, col]

        data = visualization_data[channel_name]

        # 绘制原始数据点
        if channel_name in original_data:
            ax.scatter(
                original_data[channel_name]["days"],
                original_data[channel_name]["rates"],
                color='red',
                s=50,
                alpha=0.7,
                label='实际数据'
            )

        # 绘制拟合曲线（限制在0-100天范围内更清晰展示拟合效果）
        fit_days = data["days"]
        fit_rates = data["rates"]

        # 限制显示范围到100天以内
        idx_100 = np.searchsorted(fit_days, 100, side='right')
        ax.plot(
            fit_days[:idx_100],
            fit_rates[:idx_100],
            color='blue',
            linewidth=2,
            label='拟合曲线'
        )

        ax.set_title(f'{channel_name} (LT={data["lt"]:.2f})')
        ax.set_xlabel('留存天数')
        ax.set_ylabel('留存率')
        ax.set_ylim(0, 0.6)
        ax.set_yticks([0, 0.15, 0.3, 0.45, 0.6])
        ax.set_yticklabels(['0%', '15%', '30%', '45%', '60%'])
        ax.grid(True, ls="--", alpha=0.3)
        ax.legend()

    # 隐藏未使用的子图
    for i in range(len(channels), n_rows * n_cols):
        row = i // n_cols
        col = i % n_cols
        fig.delaxes(axes[row, col])

    plt.tight_layout()
    return fig

# ==================== 页面初始化 ====================
# 主标题
st.markdown("""
<div class="main-header">
    <div class="main-title">用户生命周期价值分析系统</div>
    <div class="main-subtitle">基于分阶段数学建模的LTV预测</div>
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

# ==================== 分析步骤定义 ====================
# 分析步骤定义
ANALYSIS_STEPS = [
    {"name": "数据上传与汇总"},
    {"name": "异常数据剔除"},
    {"name": "留存率计算"},
    {"name": "LT拟合分析"},
    {"name": "ARPU计算"},
    {"name": "LTV结果报告"}
]

# ==================== 步骤状态检查函数 ====================
# 检查步骤完成状态
def get_step_status(step_index):
    if step_index == st.session_state.current_step:
        return "active"
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
    return "normal"

# ==================== 侧边栏导航 ====================
# 侧边栏导航
with st.sidebar:
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    st.markdown('<h4 style="text-align: center; margin-bottom: 1rem; color: #495057;">分析流程</h4>',
                unsafe_allow_html=True)

    for i, step in enumerate(ANALYSIS_STEPS):
        if st.button(f"{i + 1}. {step['name']}", key=f"nav_{i}",
                     use_container_width=True,
                     type="primary" if get_step_status(i) == "active" else "secondary"):
            st.session_state.current_step = i
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ==================== 辅助函数 ====================
def show_dependency_warning(required_step):
    st.warning(f"⚠️ 此步骤需要先完成「{required_step}」")
    st.info("您可以点击左侧导航直接跳转到对应步骤，或者继续查看当前步骤的功能介绍。")

# ==================== 页面路由 ====================
# 获取当前页面
current_page = ANALYSIS_STEPS[st.session_state.current_step]["name"]

# ==================== 页面内容 ====================

if current_page == "数据上传与汇总":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("渠道映射文件设置")
    
    # 渠道映射文件上传
    channel_mapping_file = st.file_uploader(
        "上传渠道映射文件 (Excel格式，可选)",
        type=['xlsx', 'xls'],
        help="格式：第一列为渠道名称，后续列为对应的渠道号"
    )
    
    if channel_mapping_file:
        try:
            custom_mapping = parse_channel_mapping_from_excel(channel_mapping_file)
            if custom_mapping and isinstance(custom_mapping, dict) and len(custom_mapping) > 0:
                st.session_state.channel_mapping = custom_mapping
                st.success(f"渠道映射文件加载成功！共包含 {len(custom_mapping)} 个映射关系")
                
                # 显示映射预览
                with st.expander("查看渠道映射详情"):
                    mapping_df = pd.DataFrame([
                        {'渠道号': pid, '渠道名称': channel}
                        for pid, channel in sorted(custom_mapping.items())
                    ])
                    st.dataframe(mapping_df, use_container_width=True)
            else:
                st.error("渠道映射文件解析失败，将使用默认映射")
        except Exception as e:
            st.error(f"读取渠道映射文件时出错：{str(e)}")
    else:
        st.info("未上传渠道映射文件，将使用默认映射关系")
        
        # 显示默认映射
        with st.expander("查看默认渠道映射"):
            default_mapping_df = pd.DataFrame([
                {'渠道号': pid, '渠道名称': channel}
                for pid, channel in sorted(DEFAULT_CHANNEL_MAPPING.items())
            ])
            st.dataframe(default_mapping_df, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("数据文件处理")

    uploaded_files = st.file_uploader(
        "选择Excel数据文件",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        help="支持上传多个Excel文件"
    )

    default_month = get_default_target_month()
    target_month = st.text_input("目标月份 (YYYY-MM)", value=default_month)

    if uploaded_files:
        st.info(f"已选择 {len(uploaded_files)} 个文件")

        if st.button("开始处理数据", type="primary", use_container_width=True):
            with st.spinner("正在处理数据文件..."):
                try:
                    merged_data, processed_count, mapping_warnings = integrate_excel_files_streamlit(
                        uploaded_files, target_month, st.session_state.channel_mapping
                    )

                    if merged_data is not None and not merged_data.empty:
                        st.session_state.merged_data = merged_data
                        st.success(f"数据处理完成！成功处理 {processed_count} 个文件")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("总记录数", f"{len(merged_data):,}")
                        with col2:
                            st.metric("数据来源数", merged_data['数据来源'].nunique())
                        with col3:
                            if '回传新增数' in merged_data.columns:
                                total_users = merged_data['回传新增数'].sum()
                                st.metric("总新增用户", f"{total_users:,.0f}")

                        # 显示映射警告
                        if mapping_warnings:
                            st.warning("以下文件未在渠道映射中找到对应关系：")
                            for warning in mapping_warnings:
                                st.text(f"• {warning}")

                        st.subheader("数据预览")
                        st.dataframe(merged_data.head(10), use_container_width=True)
                    else:
                        st.error("未找到有效数据")
                except Exception as e:
                    st.error(f"处理过程中出现错误：{str(e)}")
    else:
        st.info("请选择Excel文件开始数据处理")

    st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "异常数据剔除":
    if st.session_state.merged_data is None:
        show_dependency_warning("数据上传与汇总")
    else:
        merged_data = st.session_state.merged_data

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("异常数据剔除配置")
        st.info("注意：所有剔除条件必须同时满足才会被剔除（且关系）")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 按数据来源剔除")
            all_sources = merged_data['数据来源'].unique().tolist()
            excluded_sources = st.multiselect("选择要剔除的数据来源", options=all_sources)

        with col2:
            st.markdown("### 按日期剔除")
            if 'date' in merged_data.columns:
                all_dates = sorted(merged_data['date'].unique().tolist())
                excluded_dates = st.multiselect("选择要剔除的日期", options=all_dates)
            else:
                st.info("数据中无日期字段")
                excluded_dates = []

        try:
            exclusion_mask = pd.Series([True] * len(merged_data), index=merged_data.index)

            if excluded_sources:
                source_mask = merged_data['数据来源'].isin(excluded_sources)
                exclusion_mask &= source_mask

            if 'date' in merged_data.columns and excluded_dates:
                date_mask = merged_data['date'].isin(excluded_dates)
                exclusion_mask &= date_mask

            if not excluded_sources and not excluded_dates:
                exclusion_mask = pd.Series([False] * len(merged_data), index=merged_data.index)

            to_exclude = merged_data[exclusion_mask]
            to_keep = merged_data[~exclusion_mask]

        except Exception as e:
            st.error(f"计算剔除条件时出错: {str(e)}")
            to_exclude = pd.DataFrame()
            to_keep = merged_data.copy()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### 将被剔除的数据 ({len(to_exclude)} 条)")
            if len(to_exclude) > 0:
                st.dataframe(to_exclude.head(5), use_container_width=True)

        with col2:
            st.markdown(f"### 保留的数据 ({len(to_keep)} 条)")
            if len(to_keep) > 0:
                st.dataframe(to_keep.head(5), use_container_width=True)

        if st.button("确认剔除异常数据", type="primary", use_container_width=True):
            try:
                if len(to_exclude) > 0:
                    excluded_records = [f"{row.get('数据来源', 'Unknown')} - {row.get('date', 'Unknown')}"
                                        for _, row in to_exclude.iterrows()]
                    st.session_state.excluded_data = excluded_records
                    st.session_state.cleaned_data = to_keep.copy()
                    st.success(f"成功剔除 {len(to_exclude)} 条异常数据")
                else:
                    st.session_state.cleaned_data = merged_data.copy()
                    st.info("未发现需要剔除的异常数据")
            except Exception as e:
                st.error(f"剔除数据时出错: {str(e)}")

        st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "留存率计算":
    if st.session_state.cleaned_data is not None:
        working_data = st.session_state.cleaned_data
        data_source_info = "使用清理后的数据"
    elif st.session_state.merged_data is not None:
        working_data = st.session_state.merged_data
        data_source_info = "使用原始数据"
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
        selected_sources = st.multiselect("选择要分析的数据来源", options=data_sources, default=data_sources)

        if st.button("计算留存率", type="primary", use_container_width=True):
            if selected_sources:
                with st.spinner("正在计算留存率..."):
                    filtered_data = working_data[working_data['数据来源'].isin(selected_sources)]
                    retention_results = calculate_retention_rates_advanced(filtered_data)
                    st.session_state.retention_data = retention_results

                    st.success("留存率计算完成！")

                    for result in retention_results:
                        with st.expander(f"{result['data_source']} - 留存率详情"):
                            days = result['days']
                            rates = result['rates']

                            if len(days) > 0:
                                fig, ax = plt.subplots(figsize=(10, 6))
                                ax.scatter(days, rates, color='orange', s=80, alpha=0.8)
                                ax.plot(days, rates, '--', color='green', linewidth=2)
                                ax.set_xlabel('留存天数')
                                ax.set_ylabel('留存率')
                                ax.set_title(f'{result["data_source"]} 留存率曲线')
                                ax.grid(True, alpha=0.3)
                                plt.tight_layout()
                                st.pyplot(fig)
                                plt.close()
            else:
                st.error("请选择至少一个数据来源")

        st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "LT拟合分析":
    if st.session_state.retention_data is None:
        show_dependency_warning("留存率计算")
    else:
        retention_data = st.session_state.retention_data

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("分阶段拟合参数配置")

        lt_years = st.number_input("LT计算年限", min_value=1, max_value=10, value=5)
        st.info("系统将采用三阶段分层建模")

        if st.button("开始LT拟合分析", type="primary", use_container_width=True):
            with st.spinner("正在进行拟合计算..."):
                lt_results = []
                visualization_data = {}
                original_data = {}
                
                # 关键时间点列表
                key_days = [1, 7, 30, 60, 90, 100, 150, 200, 300]

                for retention_result in retention_data:
                    channel_name = retention_result['data_source']
                    lt_result = calculate_lt_advanced(retention_result, channel_name, lt_years, 
                                                    return_curve_data=True, key_days=key_days)

                    lt_results.append({
                        'data_source': channel_name,
                        'lt_value': lt_result['lt_value'],
                        'fit_success': lt_result['success'],
                        'fit_params': lt_result['fit_params'],
                        'power_r2': lt_result['power_r2'],
                        'model_used': lt_result['model_used']
                    })

                    visualization_data[channel_name] = {
                        "days": lt_result['curve_days'],
                        "rates": lt_result['curve_rates'],
                        "lt": lt_result['lt_value']
                    }

                    original_data[channel_name] = {
                        "days": retention_result['days'],
                        "rates": retention_result['rates']
                    }

                st.session_state.lt_results = lt_results
                st.success("LT拟合分析完成！")

                # 显示LT值表格
                if lt_results:
                    st.subheader("LT分析结果")
                    results_df = pd.DataFrame([
                        {
                            '渠道名称': r['data_source'],
                            f'{lt_years}年LT': round(r['lt_value'], 2),
                            '拟合状态': '成功' if r['fit_success'] else '失败',
                            'R²得分': round(r['power_r2'], 3),
                            '使用模型': r['model_used']
                        }
                        for r in lt_results
                    ])
                    st.dataframe(results_df, use_container_width=True)

                # 显示LT值对比柱状图
                if lt_results:
                    sorted_results = sorted(lt_results, key=lambda x: x['lt_value'])
                    sources = [r['data_source'] for r in sorted_results]
                    lt_values = [r['lt_value'] for r in sorted_results]

                    fig, ax = plt.subplots(figsize=(12, 8))
                    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(sources)))
                    bars = ax.bar(sources, lt_values, color=colors, alpha=0.8)

                    for bar, value in zip(bars, lt_values):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width() / 2., height + height * 0.01,
                                f'{value:.1f}', ha='center', va='bottom', fontweight='bold')

                    ax.set_xlabel('数据来源')
                    ax.set_ylabel('LT值 (天)')
                    ax.set_title(f'各渠道{lt_years}年LT值对比')
                    ax.tick_params(axis='x', rotation=45)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()

                # LT曲线比较
                if visualization_data:
                    fig_curves, _, _ = visualize_lt_curves(visualization_data, years=lt_years)
                    st.pyplot(fig_curves)
                    plt.close()

                # 拟合效果比较
                if visualization_data and original_data:
                    fig_fitting = visualize_fitting_comparison(original_data, visualization_data)
                    st.pyplot(fig_fitting)
                    plt.close()

        st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "ARPU计算":
    if st.session_state.lt_results is None:
        show_dependency_warning("LT拟合分析")

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("ARPU数据处理")

    arpu_file = st.file_uploader("选择ARPU数据文件 (Excel格式)", type=['xlsx', 'xls'])

    if arpu_file:
        try:
            arpu_df = pd.read_excel(arpu_file)
            st.success("ARPU文件上传成功！")
            st.dataframe(arpu_df.head(10), use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                source_col = st.selectbox("数据来源列", options=arpu_df.columns)
                arpu_col = st.selectbox("ARPU值列", options=arpu_df.columns)

            with col2:
                if arpu_col in arpu_df.columns:
                    arpu_values = pd.to_numeric(arpu_df[arpu_col], errors='coerce')
                    st.metric("平均ARPU", f"{arpu_values.mean():.2f}")
                    st.metric("有效记录数", f"{arpu_values.notna().sum():,}")

            if st.button("处理并保存ARPU数据", type="primary", use_container_width=True):
                try:
                    processed_arpu = arpu_df.copy()
                    processed_arpu['data_source'] = processed_arpu[source_col].astype(str).str.strip()
                    processed_arpu['arpu_value'] = pd.to_numeric(processed_arpu[arpu_col], errors='coerce')

                    valid_data = processed_arpu[
                        processed_arpu['arpu_value'].notna() & (processed_arpu['arpu_value'] > 0)]
                    arpu_summary = valid_data.groupby('data_source')['arpu_value'].agg(['mean', 'count']).reset_index()
                    arpu_summary.columns = ['data_source', 'arpu_value', 'record_count']

                    st.session_state.arpu_data = arpu_summary
                    st.success("ARPU数据处理完成！")
                    st.dataframe(arpu_summary, use_container_width=True)

                except Exception as e:
                    st.error(f"ARPU数据处理失败：{str(e)}")

        except Exception as e:
            st.error(f"文件读取失败：{str(e)}")

    else:
        st.info("请上传ARPU数据文件，或使用手动设置功能")

        if st.session_state.lt_results:
            st.subheader("手动设置ARPU值")
            arpu_inputs = {}

            col1, col2 = st.columns(2)
            for i, result in enumerate(st.session_state.lt_results):
                source = result['data_source']
                with col1 if i % 2 == 0 else col2:
                    arpu_value = st.number_input(
                        f"{source}", min_value=0.0, value=10.0, step=0.01,
                        format="%.2f", key=f"arpu_{source}"
                    )
                    arpu_inputs[source] = arpu_value

            if st.button("保存手动ARPU设置", type="primary", use_container_width=True):
                arpu_df = pd.DataFrame([
                    {'data_source': source, 'arpu_value': value, 'record_count': 1}
                    for source, value in arpu_inputs.items()
                ])
                st.session_state.arpu_data = arpu_df
                st.success("ARPU设置已保存！")
                st.dataframe(arpu_df, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "LTV结果报告":
    if st.session_state.lt_results is None:
        show_dependency_warning("LT拟合分析")
    elif st.session_state.arpu_data is None:
        show_dependency_warning("ARPU计算")
    else:
        lt_results = st.session_state.lt_results
        arpu_data = st.session_state.arpu_data
        retention_data = st.session_state.retention_data

        ltv_results = []
        ltv_2y_results = []
        ltv_5y_results = []

        for lt_result in lt_results:
            source = lt_result['data_source']
            lt_value = lt_result['lt_value']

            arpu_row = arpu_data[arpu_data['data_source'] == source]
            if not arpu_row.empty:
                arpu_value = arpu_row.iloc[0]['arpu_value']
            else:
                arpu_value = 0
                st.warning(f"渠道 '{source}' 未找到ARPU数据")

            lt_value_2y = lt_value * 0.6
            ltv_value = lt_value * arpu_value
            ltv_value_2y = lt_value_2y * arpu_value

            ltv_results.append({
                'data_source': source,
                'lt_value': lt_value,
                'arpu_value': arpu_value,
                'ltv_value': ltv_value,
                'fit_success': lt_result['fit_success'],
                'model_used': lt_result.get('model_used', 'unknown')
            })

            ltv_2y_results.append({'data_source': source, 'ltv_2y': ltv_value_2y})
            ltv_5y_results.append({'data_source': source, 'ltv_5y': ltv_value})

        st.session_state.ltv_results = ltv_results

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("LTV综合计算结果")

        ltv_df = pd.DataFrame(ltv_results)
        display_df = ltv_df.rename(columns={
            'data_source': '数据来源',
            'lt_value': 'LT值',
            'arpu_value': 'ARPU',
            'ltv_value': 'LTV',
            'fit_success': '拟合状态',
            'model_used': '使用模型'
        })

        display_df['LT值'] = display_df['LT值'].round(2)
        display_df['ARPU'] = display_df['ARPU'].round(2)
        display_df['LTV'] = display_df['LTV'].round(2)
        display_df['拟合状态'] = display_df['拟合状态'].map({True: '成功', False: '失败'})

        st.dataframe(display_df, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 2年和5年LTV排名对比
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("各渠道2年5年LTV排名对比")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

        # 2年LTV排名
        ltv_2y_df = pd.DataFrame(ltv_2y_results).sort_values('ltv_2y', ascending=True)
        colors_2y = plt.cm.Set1(np.linspace(0, 1, len(ltv_2y_df)))
        bars1 = ax1.barh(ltv_2y_df['data_source'], ltv_2y_df['ltv_2y'], color=colors_2y, alpha=0.8)

        for bar, value in zip(bars1, ltv_2y_df['ltv_2y']):
            width = bar.get_width()
            ax1.text(width + width * 0.01, bar.get_y() + bar.get_height() / 2,
                     f'{value:.1f}', ha='left', va='center', fontweight='bold')

        ax1.set_xlabel('2年LTV值')
        ax1.set_ylabel('数据来源')
        ax1.set_title('各渠道2年LTV排名')
        if retention_data:
            # 准备可视化数据
            visualization_data_2y = {}
            visualization_data_5y = {}
            original_data = {}

            for retention_result in retention_data:
                channel_name = retention_result['data_source']
                
                # 计算2年LT和曲线数据
                lt_result_2y = calculate_lt_advanced(
                    retention_result, channel_name, lt_years=2, 
                    return_curve_data=True, key_days=[1, 7, 30, 60, 90]
                )
                
                # 计算5年LT和曲线数据
                lt_result_5y = calculate_lt_advanced(
                    retention_result, channel_name, lt_years=5, 
                    return_curve_data=True, key_days=[1, 7, 30, 60, 90]
                )

                # 保存可视化数据
                visualization_data_2y[channel_name] = {
                    "days": lt_result_2y['curve_days'],
                    "rates": lt_result_2y['curve_rates'],
                    "lt": lt_result_2y['lt_value']
                }

                visualization_data_5y[channel_name] = {
                    "days": lt_result_5y['curve_days'],
                    "rates": lt_result_5y['curve_rates'],
                    "lt": lt_result_5y['lt_value']
                }

                # 保存原始数据
                original_data[channel_name] = {
                    "days": retention_result['days'],
                    "rates": retention_result['rates']
                }

            # 1. 拟合效果比较图
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("拟合效果比较图")
            if visualization_data_2y and original_data:
                fig_fitting = visualize_fitting_comparison(original_data, visualization_data_2y)
                st.pyplot(fig_fitting)
                plt.close()
            st.markdown('</div>', unsafe_allow_html=True)

            # 2. 2年LT曲线
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("2年LT留存曲线比较")
            if visualization_data_2y:
                fig_lt_2y, colors_2y, sorted_channels_2y = visualize_lt_curves(visualization_data_2y, years=2)
                st.pyplot(fig_lt_2y)
                plt.close()
            st.markdown('</div>', unsafe_allow_html=True)

            # 3. 5年LT曲线
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("5年LT留存曲线比较")
            if visualization_data_5y:
                fig_lt_5y, colors_5y, sorted_channels_5y = visualize_lt_curves(visualization_data_5y, years=5)
                st.pyplot(fig_lt_5y)
                plt.close()
            st.markdown('</div>', unsafe_allow_html=True)

            # 4. 对数坐标比较图
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("对数坐标比较图")
            if visualization_data_2y and visualization_data_5y:
                fig_log_comparison = visualize_log_comparison(
                    visualization_data_2y, visualization_data_5y, 
                    colors_2y if 'colors_2y' in locals() else None, 
                    sorted_channels_2y if 'sorted_channels_2y' in locals() else None
                )
                st.pyplot(fig_log_comparison)
                plt.close()
            st.markdown('</div>', unsafe_allow_html=True)

        # 数据导出
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("分析结果导出")

        col1, col2 = st.columns(2)

        with col1:
            csv_data = display_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="下载LTV分析结果 (CSV)",
                data=csv_data,
                file_name=f"LTV_Analysis_Results_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col2:
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
• 最高LTV: {display_df['LTV'].max():.2f}
• 最低LTV: {display_df['LTV'].min():.2f}
• 平均LT值: {display_df['LT值'].mean():.2f} 天
• 平均ARPU: {display_df['ARPU'].mean():.2f}

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

# ==================== 底部信息 ====================
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
