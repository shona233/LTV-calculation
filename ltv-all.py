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

# 解决中文显示问题 - 增强版本
def setup_chinese_font():
    """设置中文字体"""
    try:
        import matplotlib.font_manager as fm
        
        # 系统中文字体列表（按优先级排序）
        chinese_fonts = [
            'SimHei',           # 黑体
            'Microsoft YaHei',  # 微软雅黑
            'SimSun',          # 宋体
            'KaiTi',           # 楷体
            'FangSong',        # 仿宋
            'STSong',          # 华文宋体
            'STHeiti',         # 华文黑体
            'Arial Unicode MS', # Arial Unicode MS
            'DejaVu Sans',     # 备用字体
        ]
        
        # 获取系统所有可用字体
        available_fonts = [f.name for f in fm.fontManager.ttflist]
        
        # 找到第一个可用的中文字体
        selected_font = None
        for font in chinese_fonts:
            if font in available_fonts:
                selected_font = font
                break
        
        if selected_font:
            # 设置matplotlib中文字体
            plt.rcParams['font.sans-serif'] = [selected_font, 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
            plt.rcParams['font.size'] = 10
            return True
        else:
            # 如果没有找到中文字体，使用默认设置
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            plt.rcParams['font.size'] = 10
            return False
        
    except Exception as e:
        # 使用默认设置作为备用
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.size'] = 10
        return False

# 初始化字体设置
setup_chinese_font()

# 设置页面配置
st.set_page_config(
    page_title="LTV Analytics Platform",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📊"
)

# ==================== CSS 样式定义 ====================
# 商业蓝色系配色样式（修改交互颜色为黄色）
st.markdown("""
<style>
    /* 全局样式 */
    .main {
        background: #f8fafc;
        min-height: 100vh;
    }

    .block-container {
        padding: 1rem 1rem 3rem 1rem;
        max-width: 100%;
        background: transparent;
    }

    /* 主标题区域 */
    .main-header {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(30, 64, 175, 0.3);
        margin-bottom: 1.5rem;
        text-align: center;
        color: white;
    }

    .main-title {
        font-size: 2rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }

    .main-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1.2rem;
        font-weight: 400;
    }

    /* 卡片样式 */
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px rgba(30, 64, 175, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        margin-bottom: 1.5rem;
        backdrop-filter: blur(10px);
    }

    /* 分界线 */
    .section-divider {
        height: 2px;
        background: linear-gradient(90deg, #1e40af, #3b82f6);
        margin: 1.5rem 0;
    }

    /* 指标卡片 */
    .metric-card {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
    }

    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: white;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }

    .metric-label {
        font-size: 0.95rem;
        color: rgba(255,255,255,0.9);
    }

    /* 状态卡片 */
    .status-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 4px solid #1e40af;
        box-shadow: 0 4px 15px rgba(30, 64, 175, 0.1);
        margin-bottom: 1rem;
    }

    /* 导航步骤样式 */
    .nav-container {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        color: white;
        box-shadow: 0 4px 20px rgba(30, 64, 175, 0.3);
    }

    /* 步骤详情样式 */
    .step-details {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 0.8rem;
        margin-top: 0.5rem;
        font-size: 0.85rem;
        color: rgba(255,255,255,0.8);
    }

    .step-details ul {
        margin: 0.3rem 0;
        padding-left: 1rem;
        list-style-type: disc;
    }

    .step-details li {
        margin-bottom: 0.2rem;
        line-height: 1.4;
    }

    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(30, 64, 175, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(30, 64, 175, 0.4);
    }

    /* 选择框样式 - 修改为黄色交互 */
    .stSelectbox label, .stMultiselect label, .stFileUploader label {
        font-weight: 600;
        color: #1e40af;
        margin-bottom: 0.5rem;
    }

    .stSelectbox > div > div > div {
        border-color: #f59e0b !important;
    }

    .stSelectbox > div > div > div:focus-within {
        border-color: #f59e0b !important;
        box-shadow: 0 0 0 1px #f59e0b !important;
    }

    .stMultiSelect > div > div > div {
        border-color: #f59e0b !important;
    }

    .stMultiSelect > div > div > div:focus-within {
        border-color: #f59e0b !important;
        box-shadow: 0 0 0 1px #f59e0b !important;
    }

    /* 标题样式 */
    h1, h2, h3, h4 {
        color: #1e40af;
        font-weight: 600;
        font-size: 1.2rem !important;
    }

    /* 说明文字样式 */
    .step-explanation {
        background: linear-gradient(135deg, rgba(30, 64, 175, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%);
        border-left: 4px solid #1e40af;
        padding: 1.5rem;
        margin-top: 2rem;
        border-radius: 0 12px 12px 0;
    }

    .step-explanation h4 {
        color: #1e40af;
        margin-bottom: 0.8rem;
        font-size: 1.2rem;
        font-weight: 700;
    }

    .step-explanation ul {
        margin: 0.5rem 0;
        padding-left: 1.5rem;
        list-style-type: disc;
    }

    .step-explanation li {
        margin-bottom: 0.5rem;
        color: #1e40af;
        line-height: 1.6;
    }

    .step-explanation strong {
        color: #1e40af;
        font-weight: 600;
    }

    /* 原理解释框样式 */
    .principle-box {
        background: rgba(59, 130, 246, 0.05);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }

    .principle-title {
        color: #1e40af;
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }

    .principle-content {
        color: #374151;
        font-size: 0.9rem;
        line-height: 1.5;
    }

    /* 提示框样式 */
    .step-tip {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #3b82f6;
    }

    .step-tip-title {
        color: #1e40af;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.5rem;
    }

    .step-tip-content {
        color: #374151;
        font-size: 0.85rem;
        line-height: 1.4;
    }

    /* 剔除信息样式 */
    .exclusion-info {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #ef4444;
    }

    .exclusion-info-title {
        color: #dc2626;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.5rem;
    }

    .exclusion-info-content {
        color: #374151;
        font-size: 0.85rem;
        line-height: 1.4;
    }

    /* 数据来源提示样式 */
    .data-source-info {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #22c55e;
    }

    .data-source-info-title {
        color: #16a34a;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.5rem;
    }

    .data-source-info-content {
        color: #374151;
        font-size: 0.85rem;
        line-height: 1.4;
    }

    /* 警告样式 - 修改为黄色 */
    .stAlert > div {
        background-color: #fef3c7 !important;
        border-color: #f59e0b !important;
        color: #92400e !important;
    }

    /* 隐藏默认的Streamlit元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==================== 默认配置数据 ====================
# 修改默认渠道映射数据 - 改为名称对应多个渠道号
DEFAULT_CHANNEL_MAPPING = {
    '总体': ['9000'],
    '新媒体': ['500345', '500346', '500447', '500449', '500450', '500531', '500542'],
    '应用宝': ['5007XS', '500349', '500350'],
    '鼎乐-盛世6': ['500285'],
    '鼎乐-盛世7': ['500286'],
    '酷派': ['5108', '5528'],
    '新美-北京2': ['500275'],
    '新美-北京1': ['500274'],
    'A_深圳蛋丁2': ['500316'],
    '荣耀': ['500297'],
    '华为': ['5057'],
    'vivo': ['5237'],
    '小米': ['5599'],
    'OPPO': ['5115'],
    '网易': ['500471', '500480', '500481', '500482'],
    '华为非商店-品众': ['500337', '500338', '500343', '500445', '500383', '500444', '500441'],
    '魅族': ['5072'],
    'OPPO非商店': ['500287', '500288'],
    'vivo非商店': ['5187'],
    '百度sem--百度时代安卓': ['500398', '500400', '500404'],
    '百度sem--百度时代ios': ['500402', '500403', '500405'],
    '百青藤-安卓': ['500377', '500379', '500435', '500436', '500490', '500491', '500434', '500492'],
    '百青藤-ios': ['500437'],
    '小米非商店': ['500170'],
    '华为非商店-星火': ['500532', '500533', '500534', '500537', '500538', '500539', '500540', '500541'],
    '微博-蜜橘': ['500504', '500505'],
    '微博-央广': ['500367', '500368', '500369'],
    '广点通': ['500498', '500497', '500500', '500501', '500496', '500499'],
    '网易易效': ['500514', '500515', '500516']
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
    从上传的Excel文件解析渠道映射，返回渠道名称到渠道号列表的映射
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(channel_file)
        
        channel_to_pids = {}
        
        # 遍历每一行
        for _, row in df.iterrows():
            # 第一列是渠道名称
            channel_name = str(row.iloc[0]).strip()
            if pd.isna(channel_name) or channel_name == '' or channel_name == 'nan':
                continue
                
            # 从第二列开始是渠道号
            pids = []
            for col_idx in range(1, len(row)):
                pid = row.iloc[col_idx]
                if pd.isna(pid) or str(pid).strip() in ['', 'nan', '　', ' ']:
                    continue
                # 确保渠道号是字符串格式，去除小数
                pid_str = str(int(float(pid))) if isinstance(pid, (int, float)) else str(pid).strip()
                if pid_str:
                    pids.append(pid_str)
            
            if pids:
                channel_to_pids[channel_name] = pids
                    
        return channel_to_pids
    except Exception as e:
        st.error(f"解析渠道映射文件失败：{str(e)}")
        return {}

def convert_mapping_for_lookup(channel_to_pids):
    """
    将渠道名称到渠道号列表的映射转换为渠道号到渠道名称的映射
    """
    pid_to_channel = {}
    for channel_name, pids in channel_to_pids.items():
        for pid in pids:
            pid_to_channel[str(pid)] = channel_name
    return pid_to_channel

# ==================== 文件整合核心函数 ====================
def integrate_excel_files_streamlit(uploaded_files, target_month=None, channel_mapping=None):
    """
    整合上传的Excel文件，支持新格式表和传统格式表，优化读取速度
    """
    if target_month is None:
        target_month = get_default_target_month()

    all_data = pd.DataFrame()
    processed_count = 0
    mapping_warnings = []
    file_previews = []  # 存储每个文件的预览数据

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
            # 优化文件读取 - 只读取需要的列和行
            try:
                # 先读取文件信息
                xls = pd.ExcelFile(uploaded_file)
                sheet_names = xls.sheet_names

                # 查找目标工作表
                ocpx_sheet = None
                for sheet in sheet_names:
                    if "ocpx监测留存数" in sheet:
                        ocpx_sheet = sheet
                        break

                if ocpx_sheet:
                    file_data = pd.read_excel(uploaded_file, sheet_name=ocpx_sheet, nrows=1000)  # 限制读取行数
                else:
                    file_data = pd.read_excel(uploaded_file, sheet_name=0, nrows=1000)  # 限制读取行数
            except Exception:
                # 如果快速读取失败，使用常规方法
                file_data = pd.read_excel(uploaded_file, sheet_name=0)

            if file_data is not None and not file_data.empty:
                # 添加文件预览数据（取前2行）
                preview_data = file_data.head(2).copy()
                preview_data.insert(0, '文件名', uploaded_file.name)
                file_previews.append(preview_data)
                
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
        return standardized_df, processed_count, mapping_warnings, file_previews
    else:
        return None, 0, mapping_warnings, file_previews

# ==================== 数学建模函数（参考第二段代码）====================
# 定义数学函数
def power_function(x, a, b):
    """幂函数：y = a * x^b"""
    return a * np.power(x, b)

def exponential_function(x, c, d):
    """指数函数：y = c * exp(d * x)"""
    return c * np.exp(d * x)

# ==================== 留存率计算函数 - 新的计算方法 ====================
def calculate_retention_rates_new_method(df):
    """
    新的留存率计算方法：对新增求均值，对1-30列也求均值，然后用1-30分别除以新增的平均值
    """
    retention_results = []
    data_sources = df['数据来源'].unique()

    for source in data_sources:
        source_data = df[df['数据来源'] == source].copy()
        
        # 计算新增用户数的平均值
        new_users_values = []
        for _, row in source_data.iterrows():
            new_users = safe_convert_to_numeric(row.get('回传新增数', 0))
            if not pd.isna(new_users) and new_users > 0:
                new_users_values.append(new_users)
        
        if not new_users_values:
            continue
            
        avg_new_users = np.mean(new_users_values)
        
        # 计算各天留存数的平均值，然后计算留存率
        days = []
        rates = []
        
        for day in range(1, 31):
            day_col = str(day)
            day_values = []
            
            for _, row in source_data.iterrows():
                if day_col in row and not pd.isna(row[day_col]):
                    retain_count = safe_convert_to_numeric(row[day_col])
                    if retain_count >= 0:  # 允许0值
                        day_values.append(retain_count)
            
            if day_values:
                avg_retain_count = np.mean(day_values)
                retention_rate = avg_retain_count / avg_new_users
                if 0 < retention_rate <= 1.0:  # 修改范围：0 < 留存率 ≤ 100%
                    days.append(day)
                    rates.append(retention_rate)

        if days:
            retention_data = {
                'data_source': source,
                'days': np.array(days),
                'rates': np.array(rates)
            }
            retention_results.append(retention_data)

    return retention_results

# ==================== 计算指定天数的累积LT值函数（参考第二段代码）====================
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

# ==================== LT拟合分析函数 - 完全参考第二段代码逻辑 ====================
def calculate_lt_advanced(retention_result, channel_name, lt_years=5, return_curve_data=False, key_days=None):
    """
    按渠道规则计算 LT，允许 1-30 天数据不连续。
    完全参考第二段代码逻辑
    """
    # 渠道规则 - 与第二段代码完全一致
    CHANNEL_RULES = {
        "华为": {"stage_2": [30, 120], "stage_3_base": [120, 220]},
        "小米": {"stage_2": [30, 190], "stage_3_base": [190, 290]},
        "oppo": {"stage_2": [30, 160], "stage_3_base": [160, 260]},
        "vivo": {"stage_2": [30, 150], "stage_3_base": [150, 250]},
        "iphone": {"stage_2": [30, 150], "stage_3_base": [150, 250], "stage_2_func": "log"},
        "其他": {"stage_2": [30, 100], "stage_3_base": [100, 200]}
    }

    # 渠道规则匹配 - 与第二段代码完全一致
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

    # 计算最大天数（根据指定年数）
    max_days = lt_years * 365

    days = retention_result["days"]
    rates = retention_result["rates"]

    # 存储拟合参数，用于后续分析
    fit_params = {}

    # ----- 第一阶段 - 与第二段代码完全一致 -----
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

    # ----- 第二阶段 - 与第二段代码完全一致 -----
    try:
        days_stage_2 = np.arange(stage_2_start, stage_2_end + 1)
        rates_stage_2 = power_function(days_stage_2, a, b)
        lt_stage_2 = np.sum(rates_stage_2)
    except Exception as e:
        lt_stage_2 = 0.0
        rates_stage_2 = np.array([])

    # ----- 第三阶段 - 与第二段代码完全一致 -----
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
        days_stage_3 = np.arange(stage_3_base_start, max_days + 1)  # 使用可变的最大天数
        rates_stage_3 = exponential_function(days_stage_3, c, d)
        lt_stage_3 = np.sum(rates_stage_3)
    except Exception as e:
        days_stage_3 = np.arange(stage_3_base_start, max_days + 1)  # 使用可变的最大天数
        rates_stage_3 = power_function(days_stage_3, a, b) if 'a' in locals() else np.zeros(len(days_stage_3))
        lt_stage_3 = np.sum(rates_stage_3)

    # ----- 总 LT 计算 - 与第二段代码完全一致 -----
    total_lt = 1.0 + lt1_to_30 + lt_stage_2 + lt_stage_3

    # 计算R²用于评估拟合质量
    try:
        predicted_rates = power_function(days, a, b)
        r2_score = 1 - np.sum((rates - predicted_rates) ** 2) / np.sum((rates - np.mean(rates)) ** 2)
    except:
        r2_score = 0.0

    if return_curve_data:
        # 返回不包含第0天的曲线数据用于可视化 - 与第二段代码完全一致
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

# ==================== 高质量可视化函数（修改为单渠道正方形图表）====================
def create_single_channel_charts(visualization_data_5y, original_data):
    """
    创建单渠道的5年LT拟合曲线图表（正方形）
    """
    # 确保中文字体设置
    setup_chinese_font()
    
    # 颜色配置
    colors = plt.cm.tab10.colors
    
    # 按LT值从低到高排序渠道
    sorted_channels = sorted(visualization_data_5y.items(), key=lambda x: x[1]['lt'])
    
    chart_figures = []
    
    # 创建单渠道图表
    for idx, (channel_name, data_5y) in enumerate(sorted_channels):
        color = colors[idx % len(colors)]
        
        # 创建正方形图表
        fig = plt.figure(figsize=(6, 6))  # 正方形尺寸
        ax = fig.add_subplot(111)
        
        # 绘制实际数据点
        if channel_name in original_data:
            ax.scatter(
                original_data[channel_name]["days"],
                original_data[channel_name]["rates"],
                color='red',
                s=50,
                alpha=0.7,
                label='实际数据',
                zorder=3
            )
        
        # 绘制5年拟合曲线
        ax.plot(
            data_5y["days"],
            data_5y["rates"],
            color='blue',
            linewidth=2,
            label='5年LT拟合曲线',
            zorder=2
        )
        
        # 设置图表样式
        ax.set_xlim(0, 1825)  # 5年
        ax.set_ylim(0, 0.6)
        ax.set_xlabel('留存天数', fontsize=12)
        ax.set_ylabel('留存率', fontsize=12)
        ax.set_title(f'{channel_name} - 5年LT: {data_5y["lt"]:.2f}', fontsize=14, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.legend(fontsize=10)
        
        # 设置Y轴刻度为百分比
        y_ticks = [0, 0.15, 0.3, 0.45, 0.6]
        y_labels = ['0%', '15%', '30%', '45%', '60%']
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)
        
        plt.tight_layout()
        
        chart_figures.append({
            'channel': channel_name,
            'figure': fig,
            'lt_value': data_5y["lt"]
        })
    
    return chart_figures

# ==================== ARPU处理函数 ====================
def process_arpu_data(df, start_month, end_month, channel_mapping):
    """
    处理ARPU数据：根据月份筛选，根据渠道映射匹配，计算ARPU
    """
    try:
        # 确保有必要的列
        required_cols = ['pid', 'instl_user_cnt', 'ad_all_rven_1d_m']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return None, f"缺少必要的列: {missing_cols}"
        
        # 添加月份列（如果有日期列）
        date_columns = [col for col in df.columns if '日期' in str(col) or 'date' in str(col).lower()]
        if date_columns:
            date_col = date_columns[0]
            df['month'] = pd.to_datetime(df[date_col], errors='coerce').dt.strftime('%Y-%m')
            
            # 筛选月份范围
            filtered_df = df[(df['month'] >= start_month) & (df['month'] <= end_month)].copy()
        else:
            # 如果没有日期列，使用全部数据
            filtered_df = df.copy()
        
        if filtered_df.empty:
            return None, "筛选月份后无数据"
        
        # 将pid转换为字符串
        filtered_df['pid'] = filtered_df['pid'].astype(str)
        
        # 根据渠道映射匹配渠道名称
        pid_to_channel = convert_mapping_for_lookup(channel_mapping)
        
        # 添加渠道名称列
        filtered_df['channel_name'] = filtered_df['pid'].map(pid_to_channel)
        
        # 只保留有渠道映射的数据
        mapped_df = filtered_df[filtered_df['channel_name'].notna()].copy()
        
        if mapped_df.empty:
            return None, "根据渠道映射筛选后无数据"
        
        # 确保数值列为数值类型
        mapped_df['instl_user_cnt'] = pd.to_numeric(mapped_df['instl_user_cnt'], errors='coerce').fillna(0)
        mapped_df['ad_all_rven_1d_m'] = pd.to_numeric(mapped_df['ad_all_rven_1d_m'], errors='coerce').fillna(0)
        
        # 按渠道名称聚合
        result_df = mapped_df.groupby('channel_name').agg({
            'instl_user_cnt': 'sum',
            'ad_all_rven_1d_m': 'sum'
        }).reset_index()
        
        # 计算ARPU
        result_df['arpu_value'] = result_df['ad_all_rven_1d_m'] / result_df['instl_user_cnt']
        result_df['arpu_value'] = result_df['arpu_value'].fillna(0)
        
        # 重命名列
        result_df = result_df.rename(columns={'channel_name': 'data_source'})
        
        return result_df, None
        
    except Exception as e:
        return None, f"处理ARPU数据时出错: {str(e)}"

# ==================== 页面初始化 ====================
# 主标题
st.markdown("""
<div class="main-header">
    <div class="main-title">用户生命周期价值分析系统</div>
    <div class="main-subtitle">基于分阶段数学建模的LTV预测 v2.0</div>
</div>
""", unsafe_allow_html=True)

# 初始化session state
session_keys = [
    'channel_mapping', 'merged_data', 'cleaned_data', 'retention_data',
    'lt_results_2y', 'lt_results_5y', 'arpu_data', 'ltv_results', 'current_step', 'excluded_data',
    'excluded_dates_info', 'file_previews', 'show_exclusion_panel'
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
if st.session_state.excluded_dates_info is None:
    st.session_state.excluded_dates_info = []
if st.session_state.show_exclusion_panel is None:
    st.session_state.show_exclusion_panel = False

# ==================== 分析步骤定义 ====================
# 修改分析步骤定义为3步
ANALYSIS_STEPS = [
    {
        "name": "LT模型构建",
        "sub_steps": ["数据上传汇总", "异常剔除", "留存率计算", "LT拟合分析"]
    },
    {
        "name": "ARPU计算",
        "sub_steps": []
    },
    {
        "name": "LTV结果报告",
        "sub_steps": []
    }
]

# ==================== 步骤状态检查函数 ====================
def get_step_status(step_index):
    if step_index == st.session_state.current_step:
        return "active"
    if step_index == 0 and st.session_state.lt_results_5y is not None:
        return "completed"
    elif step_index == 1 and st.session_state.arpu_data is not None:
        return "completed"
    elif step_index == 2 and st.session_state.ltv_results is not None:
        return "completed"
    return "normal"

# ==================== 侧边栏导航 ====================
with st.sidebar:
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    st.markdown('<h4 style="text-align: center; margin-bottom: 1rem; color: white;">分析流程</h4>',
                unsafe_allow_html=True)

    for i, step in enumerate(ANALYSIS_STEPS):
        if st.button(f"{i + 1}. {step['name']}", key=f"nav_{i}",
                     use_container_width=True,
                     type="primary" if get_step_status(i) == "active" else "secondary"):
            st.session_state.current_step = i
            st.rerun()
        
        # 显示子步骤（仅对第一步）
        if i == 0 and step['sub_steps']:
            st.markdown('<div class="step-details">', unsafe_allow_html=True)
            st.markdown('<ul>', unsafe_allow_html=True)
            for sub_step in step['sub_steps']:
                st.markdown(f'<li>{sub_step}</li>', unsafe_allow_html=True)
            st.markdown('</ul>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    
    # 使用指南
    st.markdown("---")
    st.markdown("""
    <div class="nav-container">
        <h4 style="text-align: center; color: white;">使用指南</h4>
        <p style="font-size: 0.9rem; color: rgba(255,255,255,0.9); text-align: center;">
        点击上方步骤可直接跳转，系统会提供相应的操作指导。
        </p>
        <p style="font-size: 0.8rem; color: rgba(255,255,255,0.7); text-align: center;">
        LTV智能分析平台 v2.0<br>
        基于分阶段数学建模
        </p>
    </div>
    """, unsafe_allow_html=True)

# ==================== 辅助函数 ====================
def show_dependency_tip(required_step):
    """显示依赖提示，但不阻止继续操作"""
    st.markdown(f"""
    <div class="step-tip">
        <div class="step-tip-title">💡 建议</div>
        <div class="step-tip-content">建议先完成「{required_step}」步骤，以获得更好的分析效果。您也可以继续当前步骤的操作。</div>
    </div>
    """, unsafe_allow_html=True)

# ==================== 页面路由 ====================
current_page = ANALYSIS_STEPS[st.session_state.current_step]["name"]

# ==================== 页面内容 ====================

if current_page == "LT模型构建":
    # 原理解释
    st.markdown("""
    <div class="principle-box">
        <div class="principle-title">📚 LT模型构建原理</div>
        <div class="principle-content">
        LT模型构建包含四个核心步骤：数据上传汇总、异常剔除、留存率计算、LT拟合分析。系统集成多源Excel留存数据，支持HUE/ocpx双格式解析，经异常清洗后计算标准化留存率，最终通过三阶段数学建模生成精确的生命周期模型。
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 步骤1：数据上传汇总
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("步骤1：数据上传汇总")
    
    # 渠道映射文件设置
    st.markdown("### 渠道映射配置")
    
    # 文件格式说明
    st.markdown("""
    <div class="step-tip">
        <div class="step-tip-title">📋 渠道映射文件格式要求</div>
        <div class="step-tip-content">
        • Excel第一列：渠道名称<br>
        • 后续列：渠道号(一个渠道可对应多个渠道号)<br>
        • 渠道号支持整数和字符串格式
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
                st.success(f"渠道映射文件加载成功！共包含 {len(custom_mapping)} 个渠道映射")
                
                # 显示映射预览 - 默认展开
                with st.expander("查看渠道映射详情", expanded=True):
                    mapping_display_data = []
                    for channel, pids in custom_mapping.items():
                        mapping_display_data.append({
                            '渠道名称': channel,
                            '渠道号': ', '.join(pids)
                        })
                    mapping_df = pd.DataFrame(mapping_display_data)
                    st.dataframe(mapping_df, use_container_width=True)
            else:
                st.error("渠道映射文件解析失败，将使用默认映射")
        except Exception as e:
            st.error(f"读取渠道映射文件时出错：{str(e)}")
    else:
        st.info("未上传渠道映射文件，将使用默认映射关系")
        
        # 显示默认映射
        with st.expander("查看默认渠道映射"):
            default_mapping_display = []
            for channel, pids in DEFAULT_CHANNEL_MAPPING.items():
                default_mapping_display.append({
                    '渠道名称': channel,
                    '渠道号': ', '.join(pids)
                })
            default_mapping_df = pd.DataFrame(default_mapping_display)
            st.dataframe(default_mapping_df, use_container_width=True)
    
    st.markdown("### 数据文件上传")

    # 数据文件格式说明
    st.markdown("""
    <div class="step-tip">
        <div class="step-tip-title">📋 数据文件格式要求</div>
        <div class="step-tip-content">
        <strong>HUE导出表：</strong><br>
        • 包含stat_date列（日期）<br>
        • 包含new列（新增用户数）<br>
        • 包含new_retain_1到new_retain_30列（各天留存数）<br><br>
        <strong>ocpx导出表：</strong><br>
        • 包含留存天数列<br>
        • 包含回传新增数列<br>
        • 包含1-30数字列（各天留存数）<br>
        • 支持Excel工作表名包含"ocpx监测留存数"的特殊表格
        </div>
    </div>
    """, unsafe_allow_html=True)

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
                    # 转换渠道映射格式
                    pid_to_channel_mapping = convert_mapping_for_lookup(st.session_state.channel_mapping)
                    
                    merged_data, processed_count, mapping_warnings, file_previews = integrate_excel_files_streamlit(
                        uploaded_files, target_month, pid_to_channel_mapping
                    )

                    if merged_data is not None and not merged_data.empty:
                        st.session_state.merged_data = merged_data
                        st.session_state.file_previews = file_previews
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

                        # 显示每个文件的预览数据
                        st.subheader("各文件数据预览")
                        if file_previews:
                            for preview in file_previews:
                                with st.expander(f"文件：{preview['文件名'].iloc[0]}"):
                                    st.dataframe(preview, use_container_width=True)
                        
                    else:
                        st.error("未找到有效数据")
                except Exception as e:
                    st.error(f"处理过程中出现错误：{str(e)}")
    else:
        st.info("请选择Excel文件开始数据处理")

    st.markdown('</div>', unsafe_allow_html=True)
    
    # 步骤2：异常数据剔除（可选）
    if st.session_state.merged_data is not None:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("步骤2：异常数据剔除（可选）")
        
        if not st.session_state.show_exclusion_panel:
            if st.button("需要剔除异常数据", type="secondary", use_container_width=True):
                st.session_state.show_exclusion_panel = True
                st.rerun()
        else:
            merged_data = st.session_state.merged_data
            
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

            col1, col2 = st.columns(2)
            with col1:
                if st.button("确认剔除异常数据", type="primary", use_container_width=True):
                    try:
                        if len(to_exclude) > 0:
                            # 记录具体剔除的日期信息
                            excluded_dates_info = []
                            for _, row in to_exclude.iterrows():
                                source = row.get('数据来源', 'Unknown')
                                date = row.get('date', 'Unknown')
                                excluded_dates_info.append(f"{source}-{date}")
                            
                            st.session_state.excluded_data = excluded_dates_info
                            st.session_state.excluded_dates_info = excluded_dates
                            st.session_state.cleaned_data = to_keep.copy()
                            st.success(f"成功剔除 {len(to_exclude)} 条异常数据")
                        else:
                            st.session_state.cleaned_data = merged_data.copy()
                            st.session_state.excluded_dates_info = []
                            st.info("未发现需要剔除的异常数据")
                        st.session_state.show_exclusion_panel = False
                    except Exception as e:
                        st.error(f"剔除数据时出错: {str(e)}")
            
            with col2:
                if st.button("跳过异常剔除", type="secondary", use_container_width=True):
                    st.session_state.cleaned_data = merged_data.copy()
                    st.session_state.excluded_dates_info = []
                    st.session_state.show_exclusion_panel = False
                    st.info("跳过异常数据剔除，使用原始数据")

        st.markdown('</div>', unsafe_allow_html=True)
    
    # 步骤3：留存率计算
    working_data = st.session_state.cleaned_data if st.session_state.cleaned_data is not None else st.session_state.merged_data
    
    if working_data is not None:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("步骤3：留存率计算")
        
        # 数据来源信息
        data_source_info = "使用清理后的数据" if st.session_state.cleaned_data is not None else "使用原始数据（未经剔除处理）"
        st.markdown(f"""
        <div class="data-source-info">
            <div class="data-source-info-title">📊 数据来源</div>
            <div class="data-source-info-content">{data_source_info}</div>
        </div>
        """, unsafe_allow_html=True)

        # 显示剔除信息
        if st.session_state.excluded_dates_info and len(st.session_state.excluded_dates_info) > 0:
            excluded_dates_str = ", ".join(st.session_state.excluded_dates_info)
            st.markdown(f"""
            <div class="exclusion-info">
                <div class="exclusion-info-title">⚠️ 数据剔除信息</div>
                <div class="exclusion-info-content">
                已剔除以下日期的数据：{excluded_dates_str}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 数据质量要求说明
        st.markdown("""
        <div class="step-tip">
            <div class="step-tip-title">📋 数据质量要求与计算方法</div>
            <div class="step-tip-content">
            • 新增用户数必须大于0<br>
            • 留存率范围：0 < 留存率 ≤ 100% <br>
            • 计算方法：对新增用户数求均值，对1-30天各列求均值，然后用各天留存数均值除以新增用户数均值<br>
            • 支持1-30天留存数据的非连续输入
            </div>
        </div>
        """, unsafe_allow_html=True)

        data_sources = working_data['数据来源'].unique()
        selected_sources = st.multiselect("选择要分析的数据来源", options=data_sources, default=data_sources)

        if st.button("计算留存率", type="primary", use_container_width=True):
            if selected_sources:
                with st.spinner("正在计算留存率..."):
                    filtered_data = working_data[working_data['数据来源'].isin(selected_sources)]
                    retention_results = calculate_retention_rates_new_method(filtered_data)
                    st.session_state.retention_data = retention_results

                    st.success("留存率计算完成！")

                    # 创建留存率表格展示
                    if retention_results:
                        st.subheader("留存率计算结果")
                        
                        # 创建30天留存率表格
                        days_range = list(range(1, 31))
                        retention_table = pd.DataFrame({'天数': days_range})
                        
                        for result in retention_results:
                            channel_name = result['data_source']
                            days = result['days']
                            rates = result['rates']
                            
                            # 创建完整的留存率数组
                            full_rates = [None] * 30
                            for day, rate in zip(days, rates):
                                if 1 <= day <= 30:
                                    full_rates[day-1] = f"{rate:.4f}"
                            
                            retention_table[channel_name] = full_rates
                        
                        # 显示留存率表格（默认展开，显示10行）
                        with st.expander("留存率详细数据表", expanded=True):
                            st.dataframe(retention_table.head(10), use_container_width=True, height=400)
                            if len(retention_table) > 10:
                                st.info("表格显示前10行，可滚动查看更多数据")
            else:
                st.error("请选择至少一个数据来源")

        st.markdown('</div>', unsafe_allow_html=True)
    
    # 步骤4：LT拟合分析
    if st.session_state.retention_data is not None:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("步骤4：LT拟合分析")
        
        # 原理解释
        st.markdown("""
        <div class="principle-box">
            <div class="principle-title">📚 拟合分析原理</div>
            <div class="principle-content">
            LT拟合分析通过三个阶段模拟用户流失规律：<br>
            <strong>第一阶段(1-30天)：</strong>使用幂函数拟合前30天的真实留存数据，补全缺失的留存率<br>
            <strong>第二阶段(31-X天)：</strong>延续幂函数趋势，预测中期留存变化<br>
            <strong>第三阶段(Y-N年)：</strong>切换到指数函数，模拟长期用户的缓慢流失过程<br>
            不同渠道采用不同的阶段划分规则，确保拟合结果符合各渠道的用户行为特征。
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 渠道规则说明
        st.markdown("""
        <div class="step-tip">
            <div class="step-tip-title">📋 渠道拟合规则</div>
            <div class="step-tip-content">
            <strong>华为渠道：</strong>第二阶段30-120天，第三阶段120-220天<br>
            <strong>小米渠道：</strong>第二阶段30-190天，第三阶段190-290天<br>
            <strong>oppo渠道：</strong>第二阶段30-160天，第三阶段160-260天<br>
            <strong>vivo渠道：</strong>第二阶段30-150天，第三阶段150-250天<br>
            <strong>iPhone渠道：</strong>第二阶段30-150天，第三阶段150-250天<br>
            <strong>其他渠道：</strong>第二阶段30-100天，第三阶段100-200天
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("开始LT拟合分析", type="primary", use_container_width=True):
            with st.spinner("正在进行拟合计算..."):
                retention_data = st.session_state.retention_data
                
                lt_results_2y = []
                lt_results_5y = []
                visualization_data_5y = {}
                original_data = {}
                
                # 关键时间点列表
                key_days = [1, 7, 30, 60, 90, 100, 150, 200, 300]

                for retention_result in retention_data:
                    channel_name = retention_result['data_source']
                    
                    # 计算5年LT
                    lt_result_5y = calculate_lt_advanced(retention_result, channel_name, 5, 
                                                        return_curve_data=True, key_days=key_days)

                    # 计算2年LT
                    lt_result_2y = calculate_lt_advanced(retention_result, channel_name, 2, 
                                                       return_curve_data=True, key_days=key_days)

                    lt_results_5y.append({
                        'data_source': channel_name,
                        'lt_value': lt_result_5y['lt_value'],
                        'fit_success': lt_result_5y['success'],
                        'fit_params': lt_result_5y['fit_params'],
                        'power_r2': lt_result_5y['power_r2'],
                        'model_used': lt_result_5y['model_used']
                    })
                    
                    lt_results_2y.append({
                        'data_source': channel_name,
                        'lt_value': lt_result_2y['lt_value'],
                        'fit_success': lt_result_2y['success'],
                        'fit_params': lt_result_2y['fit_params'],
                        'power_r2': lt_result_2y['power_r2'],
                        'model_used': lt_result_2y['model_used']
                    })

                    # 保存可视化数据
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

                st.session_state.lt_results_5y = lt_results_5y
                st.session_state.lt_results_2y = lt_results_2y
                st.success("LT拟合分析完成！")

                # 显示LT值表格
                if lt_results_5y:
                    st.subheader("LT分析结果")
                    results_df = pd.DataFrame([
                        {
                            '渠道名称': r['data_source'],
                            '5年LT': round(r['lt_value'], 2),
                            '拟合状态': '成功' if r['fit_success'] else '失败',
                            'R²得分': round(r['power_r2'], 3),
                            '使用模型': r['model_used']
                        }
                        for r in lt_results_5y
                    ])
                    st.dataframe(results_df, use_container_width=True)

                # 创建单渠道拟合图表
                if visualization_data_5y and original_data:
                    st.subheader("各渠道5年LT拟合分析图表")
                    
                    with st.spinner("正在生成专业图表..."):
                        chart_figures = create_single_channel_charts(visualization_data_5y, original_data)
                    
                    # 显示单渠道图表（按LT值排序）
                    st.markdown("### 各渠道单独分析图表（按LT值从低到高排序）")
                    
                    # 每行显示3个图表
                    for i in range(0, len(chart_figures), 3):
                        cols = st.columns(3)
                        for j, col in enumerate(cols):
                            if i + j < len(chart_figures):
                                chart_data = chart_figures[i + j]
                                with col:
                                    st.pyplot(chart_data['figure'], use_container_width=True)
                                    plt.close(chart_data['figure'])

        st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "ARPU计算":
    # 依赖性提示
    if st.session_state.lt_results_5y is None:
        show_dependency_tip("LT模型构建")
    
    # 原理解释
    st.markdown("""
    <div class="principle-box">
        <div class="principle-title">📚 ARPU计算原理</div>
        <div class="principle-content">
        ARPU（Average Revenue Per User）是计算LTV的关键参数。系统支持Excel文件上传和手动设置两种方式。对于Excel文件，系统会根据pid列匹配渠道，按月份筛选数据，然后计算ARPU = ad_all_rven_1d_m求和 / instl_user_cnt求和。
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("ARPU数据处理")

    # ARPU文件格式说明
    st.markdown("""
    <div class="step-tip">
        <div class="step-tip-title">📋 ARPU文件格式要求</div>
        <div class="step-tip-content">
        • Excel格式(.xlsx/.xls)<br>
        • 必需列：pid、instl_user_cnt、ad_all_rven_1d_m<br>
        • 可选：日期列（用于月份筛选）<br>
        • 系统会根据渠道映射匹配pid，并按渠道聚合计算ARPU
        </div>
    </div>
    """, unsafe_allow_html=True)

    arpu_file = st.file_uploader("选择ARPU数据文件 (Excel格式)", type=['xlsx', 'xls'])

    if arpu_file:
        try:
            with st.spinner("正在读取ARPU文件..."):
                arpu_df = pd.read_excel(arpu_file)
            st.success("ARPU文件上传成功！")
            st.dataframe(arpu_df.head(10), use_container_width=True)

            # 检查必需列
            required_cols = ['pid', 'instl_user_cnt', 'ad_all_rven_1d_m']
            missing_cols = [col for col in required_cols if col not in arpu_df.columns]
            
            if missing_cols:
                st.error(f"文件缺少必需的列: {missing_cols}")
            else:
                # 月份筛选
                st.markdown("### 月份筛选")
                col1, col2 = st.columns(2)
                
                with col1:
                    start_month = st.text_input("开始月份 (YYYY-MM)", value="2024-04")
                with col2:
                    end_month = st.text_input("结束月份 (YYYY-MM)", value="2024-04")

                if st.button("处理并计算ARPU", type="primary", use_container_width=True):
                    try:
                        with st.spinner("正在处理ARPU数据..."):
                            result_df, error_msg = process_arpu_data(
                                arpu_df, start_month, end_month, st.session_state.channel_mapping
                            )
                        
                        if result_df is not None:
                            st.session_state.arpu_data = result_df
                            st.success("ARPU数据处理完成！")
                            
                            # 显示ARPU结果
                            display_df = result_df[['data_source', 'instl_user_cnt', 'ad_all_rven_1d_m', 'arpu_value']].copy()
                            display_df.columns = ['渠道名称', '安装用户数', '总收入', 'ARPU']
                            display_df['ARPU'] = display_df['ARPU'].round(4)
                            st.dataframe(display_df, use_container_width=True)
                        else:
                            st.error(f"ARPU数据处理失败：{error_msg}")

                    except Exception as e:
                        st.error(f"ARPU数据处理失败：{str(e)}")

        except Exception as e:
            st.error(f"文件读取失败：{str(e)}")

    else:
        st.info("请上传ARPU数据文件，或使用手动设置功能")

        # 手动设置ARPU
        if st.session_state.lt_results_5y:
            # 添加按钮控制手动输入面板
            if st.button("手动设置ARPU值", type="secondary", use_container_width=True):
                st.markdown("### 手动设置ARPU值")
                
                # 手动设置说明
                st.markdown("""
                <div class="step-tip">
                    <div class="step-tip-title">📋 手动设置说明</div>
                    <div class="step-tip-content">
                    为每个渠道设置对应的ARPU值，建议基于历史数据或业务预期进行设置。
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                arpu_inputs = {}

                col1, col2 = st.columns(2)
                for i, result in enumerate(st.session_state.lt_results_5y):
                    source = result['data_source']
                    with col1 if i % 2 == 0 else col2:
                        arpu_value = st.number_input(
                            f"{source}", min_value=0.0, value=0.04, step=0.001,
                            format="%.4f", key=f"arpu_{source}"
                        )
                        arpu_inputs[source] = arpu_value

                if st.button("保存手动ARPU设置", type="primary", use_container_width=True):
                    arpu_df = pd.DataFrame([
                        {'data_source': source, 'arpu_value': value, 'instl_user_cnt': 1, 'ad_all_rven_1d_m': value}
                        for source, value in arpu_inputs.items()
                    ])
                    st.session_state.arpu_data = arpu_df
                    st.success("ARPU设置已保存！")
                    st.dataframe(arpu_df[['data_source', 'arpu_value']].rename(columns={
                        'data_source': '渠道名称', 'arpu_value': 'ARPU'
                    }), use_container_width=True)
        else:
            st.info("请先完成LT模型构建以获取渠道列表")

    st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "LTV结果报告":
    # 依赖性提示
    if st.session_state.lt_results_5y is None:
        show_dependency_tip("LT模型构建")
    elif st.session_state.arpu_data is None:
        show_dependency_tip("ARPU计算")
    
    # 原理解释
    st.markdown("""
    <div class="principle-box">
        <div class="principle-title">📚 LTV结果报告原理</div>
        <div class="principle-content">
        LTV结果报告是整个分析流程的最终输出。系统通过LTV = LT × ARPU的公式计算每个渠道的用户生命周期价值，同时计算2年和5年两种时间周期的LTV，并生成详细的分析报告，为渠道投放决策提供数据支持。
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.lt_results_5y is not None and st.session_state.arpu_data is not None:
        lt_results_5y = st.session_state.lt_results_5y
        lt_results_2y = st.session_state.lt_results_2y if st.session_state.lt_results_2y else []
        arpu_data = st.session_state.arpu_data

        # 计算5年LTV结果
        ltv_results_5y = []
        ltv_results_2y = []

        for lt_result in lt_results_5y:
            source = lt_result['data_source']
            lt_value_5y = lt_result['lt_value']

            arpu_row = arpu_data[arpu_data['data_source'] == source]
            if not arpu_row.empty:
                arpu_value = arpu_row.iloc[0]['arpu_value']
            else:
                arpu_value = 0
                st.warning(f"渠道 '{source}' 未找到ARPU数据")

            ltv_value_5y = lt_value_5y * arpu_value

            ltv_results_5y.append({
                'data_source': source,
                'lt_value': lt_value_5y,
                'arpu_value': arpu_value,
                'ltv_value': ltv_value_5y,
                'fit_success': lt_result['fit_success'],
                'model_used': lt_result.get('model_used', 'unknown'),
                'fit_params': lt_result.get('fit_params', {})
            })

        # 计算2年LTV结果
        for lt_result in lt_results_2y:
            source = lt_result['data_source']
            lt_value_2y = lt_result['lt_value']

            arpu_row = arpu_data[arpu_data['data_source'] == source]
            if not arpu_row.empty:
                arpu_value = arpu_row.iloc[0]['arpu_value']
            else:
                arpu_value = 0

            ltv_value_2y = lt_value_2y * arpu_value

            ltv_results_2y.append({
                'data_source': source,
                'lt_value': lt_value_2y,
                'arpu_value': arpu_value,
                'ltv_value': ltv_value_2y,
                'fit_success': lt_result['fit_success'],
                'model_used': lt_result.get('model_used', 'unknown')
            })

        st.session_state.ltv_results = ltv_results_5y

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("LTV综合计算结果")

        # 计算公式说明
        st.markdown("""
        <div class="step-tip">
            <div class="step-tip-title">📋 计算公式</div>
            <div class="step-tip-content">
            <strong>LTV = LT × ARPU</strong><br>
            LT：用户生命周期长度（天数）<br>
            ARPU：单用户平均收入<br>
            LTV：用户生命周期价值
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 创建按要求格式的表格
        if ltv_results_5y and ltv_results_2y:
            # 合并5年和2年数据
            combined_data = []
            for result_5y in ltv_results_5y:
                # 查找对应的2年数据
                result_2y = next((r for r in ltv_results_2y if r['data_source'] == result_5y['data_source']), None)
                
                if result_2y:
                    # 获取拟合参数
                    fit_params = result_5y.get('fit_params', {})
                    power_params = fit_params.get('power', {})
                    exp_params = fit_params.get('exponential', {})
                    
                    # 格式化函数表达式
                    power_func = f"y = {power_params.get('a', 0):.4f} * x^{power_params.get('b', 0):.4f}" if power_params else "N/A"
                    exp_func = f"y = {exp_params.get('c', 0):.4f} * exp({exp_params.get('d', 0):.4f} * x)" if exp_params else "N/A"
                    
                    combined_data.append({
                        '备注': '',  # 空备注列
                        '渠道名称': result_5y['data_source'],
                        '5年LT': round(result_5y['lt_value'], 0),
                        '5年ARPU': round(result_5y['arpu_value'], 4),
                        '5年LTV': round(result_5y['ltv_value'], 1),
                        '2年LT': round(result_2y['lt_value'], 0),
                        '2年ARPU': round(result_2y['arpu_value'], 4),
                        '2年LTV': round(result_2y['ltv_value'], 1),
                        '第一段函数(幂函数)': power_func,
                        '第三段函数(指数函数)': exp_func,
                        '使用模型': result_5y['model_used']
                    })

            display_df = pd.DataFrame(combined_data)
            
            # 显示完整结果表格
            st.subheader("5年双段LTV vs 2年双段LTV 对比结果")
            st.dataframe(display_df, use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # 数据导出
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("分析结果导出")

        col1, col2 = st.columns(2)

        with col1:
            # 创建标准格式的CSV导出数据
            if 'display_df' in locals():
                export_df = display_df[['渠道名称', '5年LT', '5年ARPU', '5年LTV', '2年LT', '2年ARPU', '2年LTV']].copy()
                
                # 修复CSV导出的中文编码问题
                csv_data = export_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="下载LTV分析结果 (CSV)",
                    data=csv_data.encode('utf-8-sig'),
                    file_name=f"LTV_Analysis_Results_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        with col2:
            # 生成详细数据来源信息
            data_source_desc = ""
            if st.session_state.excluded_dates_info and len(st.session_state.excluded_dates_info) > 0:
                excluded_dates_str = ", ".join(st.session_state.excluded_dates_info)
                data_source_desc = f"已剔除以下日期数据：{excluded_dates_str}"
            elif st.session_state.cleaned_data is not None:
                data_source_desc = "使用清理后数据"
            else:
                data_source_desc = "使用原始数据"
            
            if 'display_df' in locals():
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
• 5年平均LTV: {display_df['5年LTV'].mean():.2f}
• 5年最高LTV: {display_df['5年LTV'].max():.2f}
• 5年最低LTV: {display_df['5年LTV'].min():.2f}
• 2年平均LTV: {display_df['2年LTV'].mean():.2f}
• 2年最高LTV: {display_df['2年LTV'].max():.2f}
• 2年最低LTV: {display_df['2年LTV'].min():.2f}

详细结果
-----------
{export_df.to_string(index=False) if 'export_df' in locals() else ''}

数据来源说明
-----------
{data_source_desc}

计算方法
-----------
• LT拟合: 三阶段分层建模（幂函数+指数函数）
• LTV公式: LTV = LT × ARPU
• 渠道规则: 按华为、小米、oppo、vivo、iPhone分类设定不同拟合参数
• 新的留存率计算方法: 对新增用户数和各天留存数分别求均值后计算留存率

报告生成: LTV智能分析平台 v2.0
"""

                st.download_button(
                    label="下载详细分析报告 (TXT)",
                    data=report_text.encode('utf-8'),
                    file_name=f"LTV_Detailed_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.info("请先完成LT模型构建和ARPU计算以生成LTV报告。")
        st.markdown('</div>', unsafe_allow_html=True)
