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

# 解决中文显示问题 - 简化版本
def setup_chinese_font():
    """设置中文字体 - 简化版本避免错误"""
    try:
        # 使用简单的字体设置，不使用复杂的检测
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.size'] = 10
        return True
    except Exception as e:
        # 如果设置失败，使用默认配置
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.size'] = 10
        st.info(f"📝 中文字体设置失败，将在图表中使用英文标签")
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

    /* 导航步骤样式 */
    .nav-container {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        color: white;
        box-shadow: 0 4px 20px rgba(30, 64, 175, 0.3);
    }

    /* 按钮样式 - 彻底修改所有状态，覆盖Streamlit默认样式 */
    .stButton > button {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(30, 64, 175, 0.3) !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(29, 78, 216, 0.4) !important;
        color: white !important;
    }
    
    .stButton > button:active {
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
        color: white !important;
    }
    
    .stButton > button:focus {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(30, 64, 175, 0.3) !important;
    }
    
    /* 针对特定类型的按钮 */
    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%) !important;
        color: white !important;
    }
    
    div[data-testid="stButton"] > button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
        color: white !important;
    }

    /* 子步骤样式 */
    .sub-steps {
        font-size: 0.8rem;
        color: rgba(255,255,255,0.7);
        margin-top: 0.3rem;
        line-height: 1.2;
    }

    /* 警告文字颜色 */
    .warning-text {
        color: #f59e0b !important;
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

    /* 隐藏默认的Streamlit元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 修改散点图标签颜色为浅蓝色 */
    .element-container .stScatter {
        color: #3b82f6 !important;
    }
    
    /* 修改metric标签颜色 */
    [data-testid="metric-container"] > div > div > div > div {
        color: #3b82f6 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 默认配置数据 - 重构为渠道名称->渠道号列表 ====================
DEFAULT_CHANNEL_MAPPING = {
    '总体': ['9000'],
    '新媒体': ['500345', '500346', '500447', '500449', '500450', '500531', '500542'],
    '应用宝': ['5007XS', '500349', '500350'],
    '鼎乐-盛世6': ['500285'],
    '鼎乐-盛世7': ['500286'],
    '酷派': ['5108', '5528'],
    '新美-北京1': ['500274'],
    '新美-北京2': ['500275'],
    'A_深圳蛋丁2': ['500316'],
    '荣耀': ['500297'],
    '华为': ['5057'],
    'vivo': ['5237'],
    '小米': ['5599'],
    'OPPO': ['5115'],
    '网易': ['500471', '500480', '500481', '500482'],
    '华为非商店-品众': ['500337', '500338', '500343', '500445', '500383', '500444', '500441'],
    '华为非商店-微创': ['500543', '500544', '500545', '500546'],
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

# 创建反向映射：渠道号->渠道名称
def create_reverse_mapping(channel_mapping):
    reverse_mapping = {}
    for channel_name, pids in channel_mapping.items():
        for pid in pids:
            reverse_mapping[str(pid)] = channel_name
    return reverse_mapping

# ==================== 日期处理函数 ====================
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
    """安全地将值转换为数值类型"""
    if pd.isna(value) or value == '' or value is None:
        return 0
    try:
        if isinstance(value, str):
            value = value.strip()
            if value == '' or value.lower() in ['nan', 'null', 'none']:
                return 0
        return pd.to_numeric(value, errors='coerce')
    except:
        return 0

# ==================== 数据预览优化函数 ====================
def optimize_dataframe_for_preview(df, max_rows=2):
    """优化DataFrame预览：有值的列放前面，跳过date为'日期'的行"""
    preview_df = df.copy()
    
    # 跳过date值为"日期"的行
    if 'date' in preview_df.columns:
        preview_df = preview_df[preview_df['date'] != '日期']
    if '日期' in preview_df.columns:
        preview_df = preview_df[preview_df['日期'] != '日期']
    
    # 取前max_rows行
    preview_df = preview_df.head(max_rows)
    
    if preview_df.empty:
        return preview_df
    
    # 计算每列的非空值数量
    non_null_counts = {}
    for col in preview_df.columns:
        non_null_count = preview_df[col].notna().sum()
        # 排除全为0或空的数值列
        if preview_df[col].dtype in ['int64', 'float64']:
            non_zero_count = (preview_df[col] != 0).sum()
            non_null_counts[col] = non_null_count + non_zero_count
        else:
            non_null_counts[col] = non_null_count
    
    # 按非空值数量排序列
    sorted_columns = sorted(non_null_counts.keys(), key=lambda x: non_null_counts[x], reverse=True)
    
    # 确保'数据来源'列在最前面（如果存在）
    if '数据来源' in sorted_columns:
        sorted_columns.remove('数据来源')
        sorted_columns.insert(0, '数据来源')
    
    return preview_df[sorted_columns]

# ==================== 渠道映射处理函数 - 修改为支持新格式 ====================
def parse_channel_mapping_from_excel(channel_file):
    """从上传的Excel文件解析渠道映射"""
    try:
        df = pd.read_excel(channel_file)
        channel_mapping = {}
        
        for _, row in df.iterrows():
            channel_name = str(row.iloc[0]).strip()
            if pd.isna(channel_name) or channel_name == '' or channel_name == 'nan':
                continue
                
            pids = []
            for col_idx in range(1, len(row)):
                pid = row.iloc[col_idx]
                if pd.isna(pid) or str(pid).strip() in ['', 'nan', '　', ' ']:
                    continue
                # 确保渠道号为字符串格式，去除小数
                pid_str = str(int(float(pid))) if isinstance(pid, (int, float)) else str(pid).strip()
                if pid_str:
                    pids.append(pid_str)
            
            if pids:
                channel_mapping[channel_name] = pids
                    
        return channel_mapping
    except Exception as e:
        st.error(f"解析渠道映射文件失败：{str(e)}")
        return {}

# ==================== 内置ARPU数据 ====================
def get_builtin_arpu_data():
    """获取内置的2024.1-2025.4的ARPU基础数据"""
    # 方法1: 从本地CSV文件加载（推荐）
    try:
        # 如果有本地CSV文件，取消下面这行的注释并修改文件路径
        # builtin_df = pd.read_csv('path/to/your/builtin_arpu_data.csv')
        # return builtin_df
        pass
    except:
        pass
    
    # 方法2: 从Excel文件加载
    try:
        # 如果有本地Excel文件，取消下面这行的注释并修改文件路径
        # builtin_df = pd.read_excel('path/to/your/builtin_arpu_data.xlsx')
        # return builtin_df
        pass
    except:
        pass
    
    # 方法3: 直接在代码中定义数据（适合较小数据量）
    # 示例数据结构 - 请替换为您的实际数据
    builtin_data = []
    
    # 2024年1月到2025年4月的月份列表
    months = []
    for year in [2024, 2025]:
        start_month = 1 if year == 2024 else 1
        end_month = 12 if year == 2024 else 4
        for month in range(start_month, end_month + 1):
            months.append(f"{year}-{month:02d}")
    
    # 为每个渠道和月份生成数据
    # 这里是示例数据，请替换为您的实际数据
    sample_arpu_data = {
        # 格式: 'pid': {'months': [月份列表], 'users': [用户数列表], 'revenue': [收入列表]}
        '9000': {  # 总体
            'users': [1000, 1200, 1100, 1300, 1250, 1400, 1350, 1500, 1450, 1600, 1550, 1700, 1650, 1800, 1750, 1900],
            'revenue': [50000, 60000, 55000, 65000, 62500, 70000, 67500, 75000, 72500, 80000, 77500, 85000, 82500, 90000, 87500, 95000]
        },
        '5057': {  # 华为
            'users': [800, 900, 850, 950, 920, 1000, 980, 1050, 1020, 1100, 1080, 1150, 1120, 1200, 1180, 1250],
            'revenue': [40000, 45000, 42500, 47500, 46000, 50000, 49000, 52500, 51000, 55000, 54000, 57500, 56000, 60000, 59000, 62500]
        },
        '5599': {  # 小米
            'users': [600, 700, 650, 750, 720, 800, 780, 850, 820, 900, 880, 950, 920, 1000, 980, 1050],
            'revenue': [30000, 35000, 32500, 37500, 36000, 40000, 39000, 42500, 41000, 45000, 44000, 47500, 46000, 50000, 49000, 52500]
        },
        # 继续添加其他渠道的数据...
        # 您需要为 DEFAULT_CHANNEL_MAPPING 中的所有 pid 添加数据
    }
    
    # 将示例数据转换为标准格式
    for pid, data in sample_arpu_data.items():
        users_list = data['users']
        revenue_list = data['revenue']
        
        for i, month in enumerate(months):
            if i < len(users_list):  # 确保有数据
                builtin_data.append({
                    '月份': month,
                    'pid': pid,
                    'stat_date': f"{month}-15",  # 月中日期
                    'instl_user_cnt': users_list[i],
                    'ad_all_rven_1d_m': revenue_list[i]
                })
    
    return pd.DataFrame(builtin_data)

def load_builtin_arpu_from_file():
    """从上传的文件加载内置ARPU数据"""
    st.subheader("🔧 管理员功能：上传内置ARPU数据")
    
    uploaded_builtin_file = st.file_uploader(
        "上传内置ARPU数据文件 (将替换系统默认数据)",
        type=['xlsx', 'xls', 'csv'],
        help="包含2024.1-2025.4期间的完整ARPU数据",
        key="builtin_arpu_upload"
    )
    
    if uploaded_builtin_file:
        try:
            if uploaded_builtin_file.name.endswith('.csv'):
                uploaded_df = pd.read_csv(uploaded_builtin_file)
            else:
                uploaded_df = pd.read_excel(uploaded_builtin_file)
            
            # 验证数据格式
            required_cols = ['月份', 'pid', 'stat_date', 'instl_user_cnt', 'ad_all_rven_1d_m']
            missing_cols = [col for col in required_cols if col not in uploaded_df.columns]
            
            if missing_cols:
                st.error(f"❌ 文件缺少必需列: {', '.join(missing_cols)}")
                return None
            else:
                st.success(f"✅ 内置ARPU数据上传成功！包含 {len(uploaded_df)} 条记录")
                
                # 显示数据摘要
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("记录总数", f"{len(uploaded_df):,}")
                with col2:
                    st.metric("渠道数量", uploaded_df['pid'].nunique())
                with col3:
                    st.metric("月份数量", uploaded_df['月份'].nunique())
                
                # 显示数据预览
                st.markdown("**数据预览：**")
                st.dataframe(uploaded_df.head(10), use_container_width=True)
                
                return uploaded_df
                
        except Exception as e:
            st.error(f"❌ 文件处理失败：{str(e)}")
            return None
    
    return None

def load_user_arpu_data_after_april(uploaded_file, builtin_df):
    """加载用户上传的5月及之后的ARPU数据，并与内置数据合并"""
    try:
        user_df = pd.read_excel(uploaded_file)
        
        # 检查必需列
        required_cols = ['pid', 'instl_user_cnt', 'ad_all_rven_1d_m']
        missing_cols = [col for col in required_cols if col not in user_df.columns]
        
        if missing_cols:
            return None, f"文件缺少必需列: {', '.join(missing_cols)}"
        
        # 筛选5月及之后的数据
        if '月份' in user_df.columns:
            # 使用月份列筛选
            user_df['month_num'] = pd.to_datetime(user_df['月份'], format='%Y-%m', errors='coerce')
            april_2025 = pd.to_datetime('2025-04', format='%Y-%m')
            user_df = user_df[user_df['month_num'] > april_2025]
        elif 'stat_date' in user_df.columns:
            # 使用日期列筛选
            user_df['stat_date'] = pd.to_datetime(user_df['stat_date'], errors='coerce')
            user_df['month'] = user_df['stat_date'].dt.to_period('M')
            april_2025 = pd.Period('2025-04', freq='M')
            user_df = user_df[user_df['month'] > april_2025]
        else:
            return None, "未找到月份或日期列进行筛选"
        
        # 合并内置数据和用户数据
        combined_df = pd.concat([builtin_df, user_df], ignore_index=True)
        
        return combined_df, "数据合并成功"
        
    except Exception as e:
        return None, f"处理文件时出错：{str(e)}"
def parse_channel_mapping_from_excel(channel_file):
    """从上传的Excel文件解析渠道映射"""
    try:
        df = pd.read_excel(channel_file)
        channel_mapping = {}
        
        for _, row in df.iterrows():
            channel_name = str(row.iloc[0]).strip()
            if pd.isna(channel_name) or channel_name == '' or channel_name == 'nan':
                continue
                
            pids = []
            for col_idx in range(1, len(row)):
                pid = row.iloc[col_idx]
                if pd.isna(pid) or str(pid).strip() in ['', 'nan', '　', ' ']:
                    continue
                # 确保渠道号为字符串格式，去除小数
                pid_str = str(int(float(pid))) if isinstance(pid, (int, float)) else str(pid).strip()
                if pid_str:
                    pids.append(pid_str)
            
            if pids:
                channel_mapping[channel_name] = pids
                    
        return channel_mapping
    except Exception as e:
        st.error(f"解析渠道映射文件失败：{str(e)}")
        return {}

# ==================== 文件整合核心函数 - 优化性能 ====================
@st.cache_data
def integrate_excel_files_cached(file_names, file_contents, target_month, channel_mapping):
    """缓存版本的文件整合函数"""
    all_data = pd.DataFrame()
    processed_count = 0
    mapping_warnings = []

    for i, (file_name, file_content) in enumerate(zip(file_names, file_contents)):
        source_name = os.path.splitext(file_name)[0].strip()  # 去除空格
        
        # 渠道映射处理 - 修复匹配逻辑
        mapped_source = source_name  # 默认使用文件名
        
        # 首先检查是否直接是渠道名称
        if source_name in channel_mapping:
            mapped_source = source_name
        else:
            # 检查是否是渠道号
            reverse_mapping = create_reverse_mapping(channel_mapping)
            if source_name in reverse_mapping:
                mapped_source = reverse_mapping[source_name]
            else:
                # 都不匹配时才报警告
                mapping_warnings.append(f"文件 '{source_name}' 未在渠道映射表中找到对应项")
                
        # 调试信息（可选）
        # print(f"文件: {file_name}, source_name: '{source_name}', mapped_source: '{mapped_source}'")

        try:
            # 从内存中读取Excel文件
            xls = pd.ExcelFile(io.BytesIO(file_content))
            sheet_names = xls.sheet_names

            # 查找目标工作表
            ocpx_sheet = None
            for sheet in sheet_names:
                if "ocpx监测留存数" in sheet:
                    ocpx_sheet = sheet
                    break

            if ocpx_sheet:
                file_data = pd.read_excel(io.BytesIO(file_content), sheet_name=ocpx_sheet)
            else:
                file_data = pd.read_excel(io.BytesIO(file_content), sheet_name=0)

            if file_data is not None and not file_data.empty:
                # 数据处理逻辑（保持原有逻辑）
                file_data_copy = file_data.copy()
                
                # 检测并处理数据格式
                has_stat_date = 'stat_date' in file_data_copy.columns
                retain_columns = [f'new_retain_{i}' for i in range(1, 31)]
                has_retain_columns = any(col in file_data_copy.columns for col in retain_columns)

                if has_stat_date and has_retain_columns:
                    # 新格式表处理
                    standardized_data = file_data_copy.copy()
                    if 'new' in standardized_data.columns:
                        standardized_data['回传新增数'] = standardized_data['new'].apply(safe_convert_to_numeric)

                    for i in range(1, 31):
                        retain_col = f'new_retain_{i}'
                        if retain_col in standardized_data.columns:
                            standardized_data[str(i)] = standardized_data[retain_col].apply(safe_convert_to_numeric)

                    date_col = 'stat_date'
                    standardized_data[date_col] = pd.to_datetime(standardized_data[date_col], errors='coerce')
                    standardized_data[date_col] = standardized_data[date_col].dt.strftime('%Y-%m-%d')
                    standardized_data['日期'] = standardized_data[date_col]
                    standardized_data['month'] = standardized_data[date_col].str[:7]

                    filtered_data = standardized_data[standardized_data['month'] == target_month].copy()

                    if not filtered_data.empty:
                        filtered_data.insert(0, '数据来源', mapped_source)
                        if 'stat_date' in filtered_data.columns:
                            filtered_data['date'] = filtered_data['stat_date']
                        all_data = pd.concat([all_data, filtered_data], ignore_index=True)
                        processed_count += 1
                else:
                    # 传统格式表处理
                    retention_col = None
                    for col in file_data_copy.columns:
                        if '留存天数' in str(col):
                            retention_col = col
                            break

                    report_users_col = None
                    for col in file_data_copy.columns:
                        if '回传新增数' in str(col):
                            report_users_col = col
                            break
                        if 'total_new_users' in str(col).lower():
                            report_users_col = col
                            break

                    column_b = file_data_copy.columns[1] if len(file_data_copy.columns) > 1 else None

                    if report_users_col and report_users_col != '回传新增数':
                        file_data_copy['回传新增数'] = file_data_copy[report_users_col].apply(safe_convert_to_numeric)
                    elif not report_users_col and column_b:
                        file_data_copy['回传新增数'] = file_data_copy[column_b].apply(safe_convert_to_numeric)

                    for i in range(1, 31):
                        col_name = str(i)
                        if col_name in file_data_copy.columns:
                            file_data_copy[col_name] = file_data_copy[col_name].apply(safe_convert_to_numeric)

                    # 简化日期处理，直接按月份筛选
                    date_col = None
                    for col in file_data_copy.columns:
                        if '日期' in str(col):
                            date_col = col
                            break

                    if date_col:
                        file_data_copy['month'] = file_data_copy[date_col].apply(
                            lambda x: str(x)[:7] if isinstance(x, str) else None
                        )
                        filtered_data = file_data_copy[file_data_copy['month'] == target_month].copy()
                    else:
                        filtered_data = file_data_copy.copy()

                    if not filtered_data.empty:
                        filtered_data.insert(0, '数据来源', mapped_source)
                        if retention_col is not None:
                            filtered_data.rename(columns={retention_col: 'date'}, inplace=True)
                        elif date_col and date_col != 'date':
                            filtered_data['date'] = filtered_data[date_col]
                        all_data = pd.concat([all_data, filtered_data], ignore_index=True)
                        processed_count += 1

        except Exception as e:
            st.error(f"处理文件 {file_name} 时出错: {str(e)}")

    return all_data, processed_count, mapping_warnings

def integrate_excel_files_streamlit(uploaded_files, target_month=None, channel_mapping=None):
    """优化性能的文件整合函数"""
    if target_month is None:
        target_month = get_default_target_month()

    # 使用传入的渠道映射，如果没有则使用默认映射
    if channel_mapping is None:
        channel_mapping = DEFAULT_CHANNEL_MAPPING

    # 准备缓存数据
    file_names = [f.name for f in uploaded_files]
    file_contents = [f.read() for f in uploaded_files]
    
    return integrate_excel_files_cached(file_names, file_contents, target_month, channel_mapping)

# ==================== 留存率计算函数 - 确保使用数字列名 ====================
def calculate_retention_rates_new_method(df):
    """OCPX格式留存率计算：各天留存列（1、2、3...）平均值÷回传新增数平均值"""
    retention_results = []
    data_sources = df['数据来源'].unique()

    for source in data_sources:
        source_data = df[df['数据来源'] == source].copy()
        
        # 计算平均新增用户数作为基数
        new_users_values = []
        for _, row in source_data.iterrows():
            new_users = safe_convert_to_numeric(row.get('回传新增数', 0))
            if new_users > 0:
                new_users_values.append(new_users)
        
        if not new_users_values:
            continue
        
        avg_new_users = np.mean(new_users_values)
        
        # 计算1-30天的平均留存数，使用数字列名"1"、"2"、"3"...
        retention_data = {'data_source': source, 'avg_new_users': avg_new_users}
        days = []
        rates = []
        
        for day in range(1, 31):
            day_col = str(day)  # 确保使用字符串格式的数字列名
            day_retain_values = []
            
            # 检查该列是否存在
            if day_col not in source_data.columns:
                continue
            
            for _, row in source_data.iterrows():
                if day_col in row.index and not pd.isna(row[day_col]):
                    retain_count = safe_convert_to_numeric(row[day_col])
                    if retain_count >= 0:  # 允许0值
                        day_retain_values.append(retain_count)
            
            if day_retain_values:
                avg_retain = np.mean(day_retain_values)
                # OCPX计算方法：留存率 = 平均留存数 / 平均新增数
                retention_rate = avg_retain / avg_new_users if avg_new_users > 0 else 0
                
                # 留存率范围为 0 ≤ 留存率 ≤ 1.0
                if 0 <= retention_rate <= 1.0:
                    days.append(day)
                    rates.append(retention_rate)
        
        if days:
            retention_results.append({
                'data_source': source,
                'days': np.array(days),
                'rates': np.array(rates),
                'avg_new_users': avg_new_users
            })

    return retention_results

# ==================== 数学建模函数 ====================
def power_function(x, a, b):
    """幂函数：y = a * x^b"""
    return a * np.power(x, b)

def exponential_function(x, c, d):
    """指数函数：y = c * exp(d * x)"""
    return c * np.exp(d * x)

def calculate_cumulative_lt(days_array, rates_array, target_days):
    """计算指定天数的累积LT值"""
    result = {}
    for day in target_days:
        idx = np.searchsorted(days_array, day, side='right')
        if idx > 0:
            cumulative_lt = 1.0 + np.sum(rates_array[1:idx])
            result[day] = cumulative_lt
    return result

def calculate_lt_advanced(retention_result, channel_name, lt_years=5, return_curve_data=False, key_days=None):
    """按渠道规则计算 LT"""
    # 渠道规则
    CHANNEL_RULES = {
        "华为": {"stage_2": [30, 120], "stage_3_base": [120, 220]},
        "小米": {"stage_2": [30, 190], "stage_3_base": [190, 290]},
        "oppo": {"stage_2": [30, 160], "stage_3_base": [160, 260]},
        "vivo": {"stage_2": [30, 150], "stage_3_base": [150, 250]},
        "iphone": {"stage_2": [30, 150], "stage_3_base": [150, 250], "stage_2_func": "log"},
        "其他": {"stage_2": [30, 100], "stage_3_base": [100, 200]}
    }

    # 渠道规则匹配
    if re.search(r'华为', channel_name):
        rules = CHANNEL_RULES["华为"]
    elif re.search(r'小米', channel_name):
        rules = CHANNEL_RULES["小米"]
    elif re.search(r'[oO][pP][pP][oO]', channel_name):
        rules = CHANNEL_RULES["oppo"]
    elif re.search(r'vivo', channel_name):
        rules = CHANNEL_RULES["vivo"]
    elif re.search(r'[iI][pP]hone', channel_name):
        rules = CHANNEL_RULES["iphone"]
    else:
        rules = CHANNEL_RULES["其他"]
        
    stage_2_start, stage_2_end = rules["stage_2"]
    stage_3_base_start, stage_3_base_end = rules["stage_3_base"]

    max_days = lt_years * 365

    days = retention_result["days"]
    rates = retention_result["rates"]

    fit_params = {}

    # 第一阶段 - 幂函数拟合
    try:
        popt_power, _ = curve_fit(power_function, days, rates)
        a, b = popt_power
        fit_params["power"] = {"a": a, "b": b}

        days_full = np.arange(1, 31)
        rates_full = power_function(days_full, a, b)
        lt1_to_30 = np.sum(rates_full)
    except Exception as e:
        lt1_to_30 = 0.0
        a, b = 1.0, -1.0

    # 第二阶段
    try:
        days_stage_2 = np.arange(stage_2_start, stage_2_end + 1)
        rates_stage_2 = power_function(days_stage_2, a, b)
        lt_stage_2 = np.sum(rates_stage_2)
    except Exception as e:
        lt_stage_2 = 0.0
        rates_stage_2 = np.array([])

    # 第三阶段 - 指数拟合
    try:
        days_stage_3_base = np.arange(stage_3_base_start, stage_3_base_end + 1)
        rates_stage_3_base = power_function(days_stage_3_base, a, b)

        initial_c = rates_stage_3_base[0]
        initial_d = -0.001
        popt_exp, _ = curve_fit(
            exponential_function,
            days_stage_3_base,
            rates_stage_3_base,
            p0=[initial_c, initial_d],
            bounds=([0, -np.inf], [np.inf, 0])
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

    total_lt = 1.0 + lt1_to_30 + lt_stage_2 + lt_stage_3

    try:
        predicted_rates = power_function(days, a, b)
        r2_score = 1 - np.sum((rates - predicted_rates) ** 2) / np.sum((rates - np.mean(rates)) ** 2)
    except:
        r2_score = 0.0

    if return_curve_data:
        all_days = np.concatenate([days_full, days_stage_2, days_stage_3])
        
        if 'rates_stage_2' not in locals():
            rates_stage_2 = power_function(days_stage_2, a, b)
        
        all_rates = np.concatenate([rates_full, rates_stage_2, rates_stage_3])

        sort_idx = np.argsort(all_days)
        all_days = all_days[sort_idx]
        all_rates = all_rates[sort_idx]

        max_idx = np.searchsorted(all_days, lt_years * 365, side='right')
        all_days = all_days[:max_idx]
        all_rates = all_rates[:max_idx]

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

# ==================== 单渠道图表生成函数 - 修复中文显示 ====================
def create_individual_channel_chart(channel_name, curve_data, original_data, max_days=100):
    """创建单个渠道的100天LT拟合图表 - 简化中文显示"""
    
    # 设置中文字体 - 简化方法
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # 绘制实际数据点
    if channel_name in original_data:
        ax.scatter(
            original_data[channel_name]["days"],
            original_data[channel_name]["rates"],
            color='#ef4444',
            s=60,
            alpha=0.8,
            label='实际数据',
            zorder=3
        )
    
    # 限制拟合曲线到100天
    curve_days = curve_data["days"]
    curve_rates = curve_data["rates"]
    
    # 筛选100天内的数据
    mask = curve_days <= max_days
    curve_days_filtered = curve_days[mask]
    curve_rates_filtered = curve_rates[mask]
    
    # 绘制拟合曲线
    ax.plot(
        curve_days_filtered,
        curve_rates_filtered,
        color='#3b82f6',
        linewidth=2.5,
        label='拟合曲线',
        zorder=2
    )
    
    # 设置图表样式
    ax.set_xlim(0, max_days)
    ax.set_ylim(0, 0.6)
    
    try:
        # 尝试使用中文
        ax.set_xlabel('留存天数', fontsize=12)
        ax.set_ylabel('留存率', fontsize=12)
        ax.set_title(f'{channel_name} ({max_days}天LT拟合)', fontsize=14, fontweight='bold')
    except:
        # 如果中文失败，使用英文
        ax.set_xlabel('Retention Days', fontsize=12)
        ax.set_ylabel('Retention Rate', fontsize=12)
        ax.set_title(f'{channel_name} ({max_days}d LT Fitting)', fontsize=14, fontweight='bold')
    
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.legend(fontsize=10)
    
    # 设置Y轴刻度为百分比
    y_ticks = [0, 0.15, 0.3, 0.45, 0.6]
    y_labels = ['0%', '15%', '30%', '45%', '60%']
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    
    plt.tight_layout()
    return fig

# ==================== 主应用程序 ====================

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
    'lt_results_2y', 'lt_results_5y', 'arpu_data', 'ltv_results', 'current_step',
    'excluded_data', 'excluded_dates_info', 'show_exclusion', 'show_manual_arpu',
    'visualization_data_5y', 'original_data', 'show_upload_interface'
]
for key in session_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# 设置默认值
if st.session_state.channel_mapping is None:
    st.session_state.channel_mapping = DEFAULT_CHANNEL_MAPPING
if st.session_state.current_step is None:
    st.session_state.current_step = 0
if st.session_state.show_exclusion is None:
    st.session_state.show_exclusion = False
if st.session_state.show_manual_arpu is None:
    st.session_state.show_manual_arpu = False
if st.session_state.show_upload_interface is None:
    st.session_state.show_upload_interface = False

# ==================== 分析步骤定义 - 重构为3步 ====================
ANALYSIS_STEPS = [
    {
        "name": "LT模型构建",
        "sub_steps": ["数据上传汇总", "异常剔除", "留存率计算", "LT拟合分析"]
    },
    {"name": "ARPU计算"},
    {"name": "LTV结果报告"}
]

# ==================== 侧边栏导航 ====================
with st.sidebar:
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    st.markdown('<h4 style="text-align: center; margin-bottom: 1rem; color: white;">分析流程</h4>',
                unsafe_allow_html=True)

    for i, step in enumerate(ANALYSIS_STEPS):
        button_text = f"{i + 1}. {step['name']}"
        if st.button(button_text, key=f"nav_{i}", use_container_width=True,
                     type="primary" if i == st.session_state.current_step else "secondary"):
            st.session_state.current_step = i
            st.rerun()
        
        # 只在LT模型构建时显示子步骤
        if "sub_steps" in step and i == st.session_state.current_step and step['name'] == "LT模型构建":
            sub_steps_text = " • ".join(step["sub_steps"])
            st.markdown(f'<div class="sub-steps">{sub_steps_text}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ==================== 页面路由 ====================
current_page = ANALYSIS_STEPS[st.session_state.current_step]["name"]

# ==================== 页面内容 ====================

if current_page == "LT模型构建":
    # 原理解释
    st.markdown("""
    <div class="principle-box">
        <div class="principle-title">📚 LT模型构建原理</div>
        <div class="principle-content">
        LT模型构建包含四个核心步骤：<br>
        <strong>1. 数据上传汇总：</strong>整合多个Excel文件，支持新格式表和传统格式表<br>
        <strong>2. 异常剔除：</strong>按需清理异常数据，提高模型准确性<br>
        <strong>3. 留存率计算：</strong>OCPX格式表按渠道计算，各天留存列（1、2、3...）平均值÷回传新增数平均值<br>
        <strong>4. LT拟合分析：</strong>采用三阶段分层建模，预测用户生命周期长度
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 步骤1：数据上传与汇总
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("1. 数据上传与汇总")
    
    # 默认渠道映射 - 默认展开，添加上传选择
    st.subheader("渠道映射配置")
    with st.expander("📋 默认渠道映射（请按渠道名称命名文件）", expanded=True):
        st.markdown("""
        <div class="step-tip">
            <div class="step-tip-title">💡 重要提示</div>
            <div class="step-tip-content">
            <strong>文件命名规则：</strong>请将Excel文件按照下表中的<strong>渠道名称</strong>进行命名<br>
            例如：<code>鼎乐-盛世7.xlsx</code>、<code>华为.xlsx</code>、<code>小米.xlsx</code> 等<br>
            <strong>用途：</strong>正确命名可自动匹配ARPU数据和渠道分析
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        default_mapping_rows = []
        for channel_name, pids in DEFAULT_CHANNEL_MAPPING.items():
            for pid in pids:
                default_mapping_rows.append({'渠道名称': channel_name, '渠道号': pid})
        default_mapping_df = pd.DataFrame(default_mapping_rows)
        st.dataframe(default_mapping_df, use_container_width=True)
        
    # 添加是否需要上传渠道映射的选择
    st.markdown("### 渠道映射选项")
    need_custom_mapping = st.radio(
        "选择渠道映射方式：",
        options=["✅ 使用默认渠道映射", "📤 上传自定义渠道映射"],
        index=0,
        help="如果您的渠道与默认映射不同，请选择上传自定义映射"
    )
    
    # 按钮控制显示上传界面
    if not st.session_state.show_upload_interface:
        if st.button("📤 开始数据上传", type="primary", use_container_width=True):
            st.session_state.show_upload_interface = True
            st.rerun()
        
        # 显示当前渠道映射摘要
        with st.expander("🔍 查看当前渠道映射摘要", expanded=False):
            current_channels = list(st.session_state.channel_mapping.keys())
            st.markdown(f"**当前共有 {len(current_channels)} 个渠道：**")
            channels_text = "、".join(current_channels)
            st.text(channels_text)
    else:
        # 渠道映射文件上传 - 只在选择自定义映射时显示
        if need_custom_mapping == "📤 上传自定义渠道映射":
            st.markdown("### 上传自定义渠道映射文件")
            channel_mapping_file = st.file_uploader(
                "选择渠道映射Excel文件",
                type=['xlsx', 'xls'],
                help="格式：第一列为渠道名称，后续列为对应的渠道号",
                key="custom_channel_mapping"
            )
            
            if channel_mapping_file:
                try:
                    custom_mapping = parse_channel_mapping_from_excel(channel_mapping_file)
                    if custom_mapping and isinstance(custom_mapping, dict) and len(custom_mapping) > 0:
                        st.session_state.channel_mapping = custom_mapping
                        st.success(f"✅ 自定义渠道映射加载成功！共包含 {len(custom_mapping)} 个渠道")
                        
                        # 自动展开映射详情
                        with st.expander("查看自定义渠道映射详情", expanded=True):
                            mapping_rows = []
                            for channel_name, pids in custom_mapping.items():
                                for pid in pids:
                                    mapping_rows.append({'渠道名称': channel_name, '渠道号': pid})
                            mapping_df = pd.DataFrame(mapping_rows)
                            st.dataframe(mapping_df, use_container_width=True)
                    else:
                        st.error("❌ 渠道映射文件解析失败，将使用默认映射")
                except Exception as e:
                    st.error(f"❌ 读取渠道映射文件时出错：{str(e)}")
            else:
                st.info("📤 请上传自定义渠道映射文件")
        else:
            st.success("✅ 正在使用默认渠道映射")

        # 数据文件上传
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
                            st.success(f"✅ 数据处理完成！成功处理 {processed_count} 个文件")

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("总记录数", f"{len(merged_data):,}")
                            with col2:
                                st.metric("数据来源数", merged_data['数据来源'].nunique())
                            with col3:
                                if '回传新增数' in merged_data.columns:
                                    total_users = merged_data['回传新增数'].sum()
                                    st.metric("总新增用户", f"{total_users:,.0f}")

                            # 显示文件匹配情况
                            st.subheader("📋 文件匹配情况")
                            unique_sources = merged_data['数据来源'].unique()
                            match_info = []
                            for source in unique_sources:
                                # 检查是否在默认映射中
                                is_in_mapping = source in st.session_state.channel_mapping
                                match_info.append({
                                    '文件/渠道名称': source,
                                    '匹配状态': '✅ 已匹配' if is_in_mapping else '⚠️ 未匹配',
                                    '记录数': len(merged_data[merged_data['数据来源'] == source])
                                })
                            
                            match_df = pd.DataFrame(match_info)
                            st.dataframe(match_df, use_container_width=True)

                            if mapping_warnings:
                                st.warning("⚠️ 以下文件未在渠道映射中找到对应关系：")
                                for warning in mapping_warnings:
                                    st.text(f"• {warning}")
                                st.info("💡 提示：请确保文件名与渠道映射表中的渠道名称完全一致")

                            # 优化的数据预览 - 每个文件显示两行
                            st.subheader("数据预览")
                            
                            for source in unique_sources:
                                source_data = merged_data[merged_data['数据来源'] == source]
                                optimized_preview = optimize_dataframe_for_preview(source_data, max_rows=2)
                                st.markdown(f"**{source}：**")
                                st.dataframe(optimized_preview, use_container_width=True)
                                
                        else:
                            st.error("未找到有效数据")
                    except Exception as e:
                        st.error(f"处理过程中出现错误：{str(e)}")
        else:
            st.info("请选择Excel文件开始数据处理")

    st.markdown('</div>', unsafe_allow_html=True)

    # 步骤2：异常数据剔除（按需显示）
    if st.session_state.merged_data is not None:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("2. 异常数据剔除")
        
        if not st.session_state.show_exclusion:
            if st.button("需要异常数据剔除", use_container_width=True):
                st.session_state.show_exclusion = True
                st.rerun()
            st.info("如无需剔除异常数据，可直接进行下一步")
        else:
            merged_data = st.session_state.merged_data
            
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

            # 计算剔除结果
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
                    preview_exclude = optimize_dataframe_for_preview(to_exclude, max_rows=5)
                    st.dataframe(preview_exclude, use_container_width=True)

            with col2:
                st.markdown(f"### 保留的数据 ({len(to_keep)} 条)")
                if len(to_keep) > 0:
                    preview_keep = optimize_dataframe_for_preview(to_keep, max_rows=5)
                    st.dataframe(preview_keep, use_container_width=True)

            if st.button("确认剔除异常数据", type="primary", use_container_width=True):
                try:
                    if len(to_exclude) > 0:
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
                except Exception as e:
                    st.error(f"剔除数据时出错: {str(e)}")

        st.markdown('</div>', unsafe_allow_html=True)

    # 步骤3：留存率计算
    if st.session_state.merged_data is not None:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("3. 留存率计算")
        
        st.markdown("""
        <div class="step-tip">
            <div class="step-tip-title">📋 OCPX格式留存率计算方法</div>
            <div class="step-tip-content">
            <strong>OCPX表计算方法：</strong>以平均新增用户数作为基数<br>
            • 计算每个渠道的<strong>回传新增数</strong>的平均值作为基数<br>
            • 计算各天留存列（<strong>列名必须为：1、2、3...30</strong>）的平均值<br>
            • 留存率 = 各天留存数平均值 ÷ 回传新增数平均值<br>
            • ⚠️ <strong>重要：</strong>确保Excel表格中留存数据的列名为数字：1、2、3、4...30
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 确定使用的数据
        if st.session_state.cleaned_data is not None:
            working_data = st.session_state.cleaned_data
            st.info("使用清理后的数据进行计算")
        else:
            working_data = st.session_state.merged_data
            st.info("使用原始数据进行计算")

        data_sources = working_data['数据来源'].unique()
        selected_sources = st.multiselect("选择要分析的数据来源", options=data_sources, default=data_sources)

        if st.button("计算留存率", type="primary", use_container_width=True):
            if selected_sources:
                with st.spinner("正在计算留存率..."):
                    filtered_data = working_data[working_data['数据来源'].isin(selected_sources)]
                    retention_results = calculate_retention_rates_new_method(filtered_data)
                    st.session_state.retention_data = retention_results

                    st.success("留存率计算完成！")

                    # 创建留存率表格显示
                    if retention_results:
                        st.subheader("留存率详细数据")
                        
                        # 创建表格数据
                        table_data = []
                        days_range = range(1, 31)
                        
                        for day in days_range:
                            row = {'天数': day}
                            for result in retention_results:
                                channel_name = result['data_source']
                                days = result['days']
                                rates = result['rates']
                                
                                # 查找对应天数的留存率
                                day_index = np.where(days == day)[0]
                                if len(day_index) > 0:
                                    rate = rates[day_index[0]]
                                    row[channel_name] = f"{rate:.4f}"
                                else:
                                    row[channel_name] = "-"
                            table_data.append(row)
                        
                        # 创建DataFrame并显示
                        retention_table_df = pd.DataFrame(table_data)
                        
                        # 使用expander展开表格，限制高度并显示滚动条
                        with st.expander("留存率数据表（1-30天）", expanded=True):
                            st.dataframe(
                                retention_table_df, 
                                use_container_width=True,
                                height=400  # 设置固定高度，约10行的高度
                            )
            else:
                st.error("请选择至少一个数据来源")

        st.markdown('</div>', unsafe_allow_html=True)

    # 步骤4：LT拟合分析
    if st.session_state.retention_data is not None:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("4. LT拟合分析")
        
        retention_data = st.session_state.retention_data

        # 渠道规则说明
        st.markdown("""
        <div class="step-tip">
            <div class="step-tip-title">📋 三阶段拟合规则</div>
            <div class="step-tip-content">
            <strong>第一阶段：</strong>1-30天，幂函数拟合实际数据<br>
            <strong>第二阶段：</strong>31-X天，延续幂函数模型<br>
            <strong>第三阶段：</strong>Y天后，指数函数建模长期衰减<br>
            不同渠道采用不同的阶段划分点
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("开始LT拟合分析", type="primary", use_container_width=True):
            with st.spinner("正在进行拟合计算..."):
                lt_results_2y = []
                lt_results_5y = []
                visualization_data_2y = {}
                visualization_data_5y = {}
                original_data = {}
                
                key_days = [1, 7, 30, 60, 90, 100, 150, 200, 300]

                for retention_result in retention_data:
                    channel_name = retention_result['data_source']
                    
                    # 计算2年LT
                    lt_result_2y = calculate_lt_advanced(retention_result, channel_name, 2, 
                                                       return_curve_data=True, key_days=key_days)
                    
                    # 计算5年LT
                    lt_result_5y = calculate_lt_advanced(retention_result, channel_name, 5, 
                                                       return_curve_data=True, key_days=key_days)

                    lt_results_2y.append({
                        'data_source': channel_name,
                        'lt_value': lt_result_2y['lt_value'],
                        'fit_success': lt_result_2y['success'],
                        'fit_params': lt_result_2y['fit_params'],
                        'power_r2': lt_result_2y['power_r2'],
                        'model_used': lt_result_2y['model_used']
                    })
                    
                    lt_results_5y.append({
                        'data_source': channel_name,
                        'lt_value': lt_result_5y['lt_value'],
                        'fit_success': lt_result_5y['success'],
                        'fit_params': lt_result_5y['fit_params'],
                        'power_r2': lt_result_5y['power_r2'],
                        'model_used': lt_result_5y['model_used']
                    })

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

                st.session_state.lt_results_2y = lt_results_2y
                st.session_state.lt_results_5y = lt_results_5y
                st.session_state.visualization_data_5y = visualization_data_5y
                st.session_state.original_data = original_data
                st.success("LT拟合分析完成！")

                # 显示LT值表格
                if lt_results_5y:
                    st.subheader("LT分析结果")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 2年LT结果")
                        results_2y_df = pd.DataFrame([
                            {
                                '渠道名称': r['data_source'],
                                '2年LT': round(r['lt_value'], 2),
                                'R²得分': round(r['power_r2'], 3)
                            }
                            for r in lt_results_2y
                        ])
                        st.dataframe(results_2y_df, use_container_width=True)
                    
                    with col2:
                        st.markdown("#### 5年LT结果")
                        results_5y_df = pd.DataFrame([
                            {
                                '渠道名称': r['data_source'],
                                '5年LT': round(r['lt_value'], 2),
                                'R²得分': round(r['power_r2'], 3)
                            }
                            for r in lt_results_5y
                        ])
                        st.dataframe(results_5y_df, use_container_width=True)

                # 显示单渠道图表 - 100天版本
                if visualization_data_5y and original_data:
                    st.subheader("各渠道100天LT拟合图表")
                    
                    # 按LT值排序
                    sorted_channels = sorted(visualization_data_5y.items(), key=lambda x: x[1]['lt'])
                    
                    # 每行显示2个图表
                    for i in range(0, len(sorted_channels), 2):
                        cols = st.columns(2)
                        for j, col in enumerate(cols):
                            if i + j < len(sorted_channels):
                                channel_name, curve_data = sorted_channels[i + j]
                                with col:
                                    fig = create_individual_channel_chart(
                                        channel_name, curve_data, original_data, max_days=100
                                    )
                                    st.pyplot(fig, use_container_width=True)
                                    plt.close(fig)

        st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "ARPU计算":
    # 原理解释
    st.markdown("""
    <div class="principle-box">
        <div class="principle-title">📚 ARPU计算原理</div>
        <div class="principle-content">
        ARPU（Average Revenue Per User）计算基于用户新增数和收入数据。系统支持Excel文件上传，根据PID进行渠道匹配，
        按月份筛选数据，计算公式为：ARPU = 总收入 ÷ 总新增用户数。
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("ARPU数据处理")

    # 添加数据源选择
    st.markdown("### 数据源选择")
    data_source_option = st.radio(
        "选择ARPU数据来源：",
        options=[
            "🔧 管理员模式：上传内置数据", 
            "📊 使用内置数据(2024.1-2025.4) + 上传新数据(2025.5+)", 
            "📤 完全上传自定义数据"
        ],
        index=1,
        help="选择不同的数据处理模式"
    )

    if data_source_option == "🔧 管理员模式：上传内置数据":
        # 管理员模式：上传内置数据
        st.markdown("""
        <div class="step-tip">
            <div class="step-tip-title">🔧 管理员模式</div>
            <div class="step-tip-content">
            • 上传包含2024年1月至2025年4月的完整ARPU数据<br>
            • 数据将作为系统内置数据使用<br>
            • 必须包含列：<strong>月份、pid、stat_date、instl_user_cnt、ad_all_rven_1d_m</strong><br>
            • 支持Excel(.xlsx/.xls)和CSV格式
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 使用新的函数加载内置数据
        uploaded_builtin_data = load_builtin_arpu_from_file()
        
        if uploaded_builtin_data is not None:
            # 使用上传的数据作为内置数据
            arpu_df = uploaded_builtin_data
            process_arpu_calculation = True
            st.info("💾 将使用您上传的数据作为内置ARPU数据")
        else:
            # 使用默认示例数据
            builtin_df = get_builtin_arpu_data()
            arpu_df = builtin_df
            process_arpu_calculation = True
            st.warning("⚠️ 未上传数据，使用系统示例数据")
            
    elif data_source_option == "📊 使用内置数据(2024.1-2025.4) + 上传新数据(2025.5+)":
        # 使用内置数据 + 新数据
        st.markdown("""
        <div class="step-tip">
            <div class="step-tip-title">📋 内置数据 + 新数据模式</div>
            <div class="step-tip-content">
            • 系统内置2024年1月至2025年4月的ARPU基础数据<br>
            • 您只需上传2025年5月及之后的Excel数据<br>
            • 必须包含列：<strong>月份、pid、stat_date、instl_user_cnt、ad_all_rven_1d_m</strong><br>
            • 系统自动合并内置数据和新数据进行计算
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 显示内置数据信息
        builtin_df = get_builtin_arpu_data()
        st.info(f"内置数据包含 {len(builtin_df)} 条记录，覆盖 {builtin_df['月份'].nunique()} 个月份")
        
        # 上传新数据文件
        new_arpu_file = st.file_uploader(
            "上传2025年5月及之后的ARPU数据 (Excel格式)", 
            type=['xlsx', 'xls'],
            key="new_arpu_file"
        )
        
        if new_arpu_file:
            try:
                combined_df, message = load_user_arpu_data_after_april(new_arpu_file, builtin_df)
                if combined_df is not None:
                    st.success(message)
                    st.info(f"合并后数据包含 {len(combined_df)} 条记录")
                    
                    # 显示合并后数据预览
                    preview_combined = optimize_dataframe_for_preview(combined_df, max_rows=10)
                    st.dataframe(preview_combined, use_container_width=True)
                    
                    # 使用合并后的数据进行ARPU计算
                    arpu_df = combined_df
                    process_arpu_calculation = True
                else:
                    st.error(message)
                    process_arpu_calculation = False
            except Exception as e:
                st.error(f"处理新数据文件失败：{str(e)}")
                process_arpu_calculation = False
        else:
            # 只使用内置数据
            st.info("未上传新数据，将仅使用内置数据计算ARPU")
            arpu_df = builtin_df
            process_arpu_calculation = True
    
    else:
        # 完全自定义数据

    else:
        # 完全自定义数据
        st.markdown("""
        <div class="step-tip">
            <div class="step-tip-title">📤 完全自定义数据模式</div>
            <div class="step-tip-content">
            • Excel格式(.xlsx/.xls)或CSV格式<br>
            • 必须包含以下列：<br>
            &nbsp;&nbsp;- <strong>月份</strong>：月份信息<br>
            &nbsp;&nbsp;- <strong>pid</strong>：渠道号<br>
            &nbsp;&nbsp;- <strong>stat_date</strong>：统计日期<br>
            &nbsp;&nbsp;- <strong>instl_user_cnt</strong>：新增用户数<br>
            &nbsp;&nbsp;- <strong>ad_all_rven_1d_m</strong>：收入数据<br>
            • 支持按月份筛选数据
            </div>
        </div>
        """, unsafe_allow_html=True)

        arpu_file = st.file_uploader("选择ARPU数据文件", type=['xlsx', 'xls', 'csv'])

        if arpu_file:
            try:
                with st.spinner("正在读取ARPU文件..."):
                    if arpu_file.name.endswith('.csv'):
                        arpu_df = pd.read_csv(arpu_file)
                    else:
                        arpu_df = pd.read_excel(arpu_file)
                st.success("✅ ARPU文件上传成功！")
                
                # 检查必需列
                required_cols = ['pid', 'instl_user_cnt', 'ad_all_rven_1d_m']
                missing_cols = [col for col in required_cols if col not in arpu_df.columns]
                
                if missing_cols:
                    st.error(f"❌ 文件缺少必需列: {', '.join(missing_cols)}")
                    st.info("可用列: " + ", ".join(arpu_df.columns.tolist()))
                    process_arpu_calculation = False
                else:
                    # 显示数据预览
                    preview_arpu = optimize_dataframe_for_preview(arpu_df, max_rows=10)
                    st.dataframe(preview_arpu, use_container_width=True)
                    process_arpu_calculation = True
                    
            except Exception as e:
                st.error(f"❌ 文件读取失败：{str(e)}")
                process_arpu_calculation = False
        else:
            st.info("📤 请上传ARPU数据文件")
            process_arpu_calculation = False

    # 统一的ARPU计算处理
    if process_arpu_calculation and 'arpu_df' in locals():
                
    # 统一的ARPU计算处理
    if process_arpu_calculation and 'arpu_df' in locals():
        # 月份筛选 - 优先使用月份列，其次使用stat_date列
        st.subheader("月份筛选")
        
        if '月份' in arpu_df.columns:
            # 使用月份列
            available_months = sorted(arpu_df['月份'].dropna().unique())
            available_months = [str(m) for m in available_months]
            
            if available_months:
                col1, col2 = st.columns(2)
                with col1:
                    start_month = st.selectbox("开始月份", options=available_months)
                with col2:
                    end_month = st.selectbox("结束月份", options=available_months, 
                                           index=len(available_months)-1)
            else:
                st.warning("月份列无有效数据，将使用所有数据")
                start_month = end_month = None
                
        elif 'stat_date' in arpu_df.columns:
            # 使用stat_date列
            arpu_df['stat_date'] = pd.to_datetime(arpu_df['stat_date'], errors='coerce')
            arpu_df['month'] = arpu_df['stat_date'].dt.to_period('M')
            available_months = arpu_df['month'].dropna().unique()
            available_months = sorted([str(m) for m in available_months])
            
            if available_months:
                col1, col2 = st.columns(2)
                with col1:
                    start_month = st.selectbox("开始月份", options=available_months)
                with col2:
                    end_month = st.selectbox("结束月份", options=available_months, 
                                           index=len(available_months)-1)
            else:
                st.warning("无法解析stat_date数据，将使用所有数据")
                start_month = end_month = None
        else:
            st.info("未找到月份或stat_date列，将使用所有数据")
            start_month = end_month = None

        if st.button("计算ARPU", type="primary", use_container_width=True):
            with st.spinner("正在计算ARPU..."):
                try:
                    # 月份筛选
                    if start_month and end_month:
                        if '月份' in arpu_df.columns:
                            mask = (arpu_df['月份'] >= start_month) & (arpu_df['月份'] <= end_month)
                        else:
                            mask = (arpu_df['month'] >= start_month) & (arpu_df['month'] <= end_month)
                        filtered_arpu_df = arpu_df[mask].copy()
                        st.info(f"筛选月份: {start_month} 至 {end_month}")
                    else:
                        filtered_arpu_df = arpu_df.copy()
                        st.info("使用全部数据")

                    # 确保pid为字符串格式
                    filtered_arpu_df['pid'] = filtered_arpu_df['pid'].astype(str).str.replace('.0', '', regex=False)
                    
                    # 创建反向渠道映射
                    reverse_mapping = create_reverse_mapping(st.session_state.channel_mapping)
                    
                    # 按渠道匹配和汇总
                    arpu_results = []
                    
                    for pid, group in filtered_arpu_df.groupby('pid'):
                        if pid in reverse_mapping:
                            channel_name = reverse_mapping[pid]
                            total_users = group['instl_user_cnt'].sum()
                            total_revenue = group['ad_all_rven_1d_m'].sum()
                            
                            if total_users > 0:
                                arpu_value = total_revenue / total_users
                                arpu_results.append({
                                    'data_source': channel_name,
                                    'total_users': total_users,
                                    'total_revenue': total_revenue,
                                    'arpu_value': arpu_value,
                                    'record_count': len(group)
                                })

                    if arpu_results:
                        # 按渠道合并相同渠道的数据
                        final_arpu = {}
                        for result in arpu_results:
                            channel = result['data_source']
                            if channel in final_arpu:
                                final_arpu[channel]['total_users'] += result['total_users']
                                final_arpu[channel]['total_revenue'] += result['total_revenue']
                                final_arpu[channel]['record_count'] += result['record_count']
                            else:
                                final_arpu[channel] = result.copy()
                        
                        # 重新计算ARPU
                        arpu_summary = []
                        for channel, data in final_arpu.items():
                            arpu_value = data['total_revenue'] / data['total_users'] if data['total_users'] > 0 else 0
                            arpu_summary.append({
                                'data_source': channel,
                                'arpu_value': arpu_value,
                                'record_count': data['record_count']
                            })
                        
                        arpu_summary_df = pd.DataFrame(arpu_summary)
                        st.session_state.arpu_data = arpu_summary_df
                        st.success("ARPU计算完成！")
                        
                        # 显示结果
                        display_arpu_df = arpu_summary_df.copy()
                        display_arpu_df['ARPU'] = display_arpu_df['arpu_value'].round(4)
                        display_arpu_df = display_arpu_df[['data_source', 'ARPU', 'record_count']]
                        display_arpu_df.columns = ['渠道名称', 'ARPU值', '记录数']
                        st.dataframe(display_arpu_df, use_container_width=True)
                    else:
                        st.error("未找到匹配的渠道数据")

                except Exception as e:
                    st.error(f"ARPU计算失败：{str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

    # 手动设置ARPU（按需显示）
    if st.session_state.lt_results_5y:
        if not st.session_state.show_manual_arpu:
            if st.button("手动设置ARPU值"):
                st.session_state.show_manual_arpu = True
                st.rerun()
        else:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("手动设置ARPU值")
            
            arpu_inputs = {}
            
            col1, col2 = st.columns(2)
            for i, result in enumerate(st.session_state.lt_results_5y):
                source = result['data_source']
                with col1 if i % 2 == 0 else col2:
                    arpu_value = st.number_input(
                        f"{source}", min_value=0.0, value=0.04, step=0.001,
                        format="%.4f", key=f"manual_arpu_{source}"
                    )
                    arpu_inputs[source] = arpu_value

            if st.button("保存手动ARPU设置", type="primary", use_container_width=True):
                arpu_df = pd.DataFrame([
                    {'data_source': source, 'arpu_value': value, 'record_count': 1}
                    for source, value in arpu_inputs.items()
                ])
                st.session_state.arpu_data = arpu_df
                st.success("ARPU设置已保存！")
                st.dataframe(arpu_df[['data_source', 'arpu_value']], use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "LTV结果报告":
    # 原理解释
    st.markdown("""
    <div class="principle-box">
        <div class="principle-title">📚 LTV结果报告</div>
        <div class="principle-content">
        LTV结果报告整合了LT拟合分析和ARPU计算的结果，通过LTV = LT × ARPU公式计算最终的用户生命周期价值。
        报告提供2年和5年双段对比，包含详细的拟合模型信息和质量评估。
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.lt_results_5y is not None and st.session_state.arpu_data is not None:
        lt_results_2y = st.session_state.lt_results_2y
        lt_results_5y = st.session_state.lt_results_5y
        arpu_data = st.session_state.arpu_data

        # 计算LTV结果
        ltv_results = []
        
        for lt_result_5y in lt_results_5y:
            source = lt_result_5y['data_source']
            
            # 查找对应的2年LT数据
            lt_result_2y = next((r for r in lt_results_2y if r['data_source'] == source), None)
            
            # 查找ARPU数据
            arpu_row = arpu_data[arpu_data['data_source'] == source]
            if not arpu_row.empty:
                arpu_value = arpu_row.iloc[0]['arpu_value']
            else:
                arpu_value = 0
                st.warning(f"渠道 '{source}' 未找到ARPU数据")

            ltv_5y = lt_result_5y['lt_value'] * arpu_value
            ltv_2y = lt_result_2y['lt_value'] * arpu_value if lt_result_2y else 0

            ltv_results.append({
                'data_source': source,
                'lt_2y': lt_result_2y['lt_value'] if lt_result_2y else 0,
                'lt_5y': lt_result_5y['lt_value'],
                'arpu_value': arpu_value,
                'ltv_2y': ltv_2y,
                'ltv_5y': ltv_5y,
                'fit_success': lt_result_5y['fit_success'],
                'model_used': lt_result_5y.get('model_used', 'unknown'),
                'power_params': lt_result_5y.get('fit_params', {}).get('power', {}),
                'exp_params': lt_result_5y.get('fit_params', {}).get('exponential', {})
            })

        st.session_state.ltv_results = ltv_results

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("LTV综合计算结果")

        # 创建完整的结果表格
        display_data = []
        for result in ltv_results:
            # 获取拟合参数信息 - 修改备注换行
            power_params = result['power_params']
            exp_params = result['exp_params']
            
            备注_parts = []
            if power_params:
                power_func = f"幂函数: y = {power_params.get('a', 0):.4f} * x^{power_params.get('b', 0):.4f}"
                备注_parts.append(power_func)
            
            if exp_params:
                exp_func = f"指数函数: y = {exp_params.get('c', 0):.4f} * exp({exp_params.get('d', 0):.4f} * x)"
                备注_parts.append(exp_func)
            
            备注 = "\n".join(备注_parts) if 备注_parts else "未知"
            
            display_data.append({
                '渠道名称': result['data_source'],
                '5年LT': round(result['lt_5y'], 2),
                '5年ARPU': round(result['arpu_value'], 4),
                '5年LTV': round(result['ltv_5y'], 2),
                '2年LT': round(result['lt_2y'], 2),
                '2年ARPU': round(result['arpu_value'], 4),
                '2年LTV': round(result['ltv_2y'], 2),
                '备注': 备注
            })

        results_df = pd.DataFrame(display_data)
        
        # 重新排列列顺序
        column_order = ['渠道名称', '5年LT', '5年ARPU', '5年LTV', '2年LT', '2年ARPU', '2年LTV', '备注']
        results_df = results_df[column_order]
        
        st.dataframe(results_df, use_container_width=True, height=600)
        st.markdown('</div>', unsafe_allow_html=True)

        # 显示所有拟合曲线 - 一行四个
        if st.session_state.visualization_data_5y and st.session_state.original_data:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("所有渠道拟合曲线（100天）")
            
            visualization_data_5y = st.session_state.visualization_data_5y
            original_data = st.session_state.original_data
            
            # 按LT值排序
            sorted_channels = sorted(visualization_data_5y.items(), key=lambda x: x[1]['lt'])
            
            # 每行显示4个图表
            for i in range(0, len(sorted_channels), 4):
                cols = st.columns(4)
                for j, col in enumerate(cols):
                    if i + j < len(sorted_channels):
                        channel_name, curve_data = sorted_channels[i + j]
                        with col:
                            fig = create_individual_channel_chart(
                                channel_name, curve_data, original_data, max_days=100
                            )
                            st.pyplot(fig, use_container_width=True)
                            plt.close(fig)
            
            st.markdown('</div>', unsafe_allow_html=True)

        # 数据导出
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("分析结果导出")

        col1, col2 = st.columns(2)

        with col1:
            # CSV导出
            csv_data = results_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="下载LTV分析结果 (CSV)",
                data=csv_data.encode('utf-8-sig'),
                file_name=f"LTV_Analysis_Results_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col2:
            # 详细报告
            data_source_desc = ""
            if st.session_state.excluded_dates_info and len(st.session_state.excluded_dates_info) > 0:
                excluded_dates_str = ", ".join(st.session_state.excluded_dates_info)
                data_source_desc = f"已剔除以下日期数据：{excluded_dates_str}"
            elif st.session_state.cleaned_data is not None:
                data_source_desc = "使用清理后数据"
            else:
                data_source_desc = "使用原始数据"
            
            report_text = f"""
LTV用户生命周期价值分析报告
===========================================
生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

执行摘要
-----------
本报告基于三阶段分层数学建模方法，对 {len(results_df)} 个渠道进行了用户生命周期价值分析。

核心指标汇总
-----------
• 参与分析的渠道数量: {len(results_df)}
• 5年平均LTV: {results_df['5年LTV'].mean():.2f}
• 5年最高LTV: {results_df['5年LTV'].max():.2f}
• 5年最低LTV: {results_df['5年LTV'].min():.2f}
• 2年平均LTV: {results_df['2年LTV'].mean():.2f}
• 平均5年LT值: {results_df['5年LT'].mean():.2f} 天
• 平均2年LT值: {results_df['2年LT'].mean():.2f} 天
• 平均ARPU: {results_df['5年ARPU'].mean():.4f}

详细结果
-----------
{results_df[['渠道名称', '5年LT', '5年ARPU', '5年LTV', '2年LT', '2年ARPU', '2年LTV']].to_string(index=False)}

数据来源说明
-----------
{data_source_desc}

计算方法
-----------
• LT拟合: 三阶段分层建模（1-30天幂函数 + 31-X天幂函数延续 + Y天后指数函数）
• LTV公式: LTV = LT × ARPU
• 渠道规则: 按华为、小米、OPPO、vivo、iPhone分类设定不同拟合参数
• 留存率计算: OCPX格式表各天留存列（1、2、3...）平均值÷回传新增数平均值

报告生成: LTV智能分析平台 v3.3
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
        missing_components = []
        if st.session_state.lt_results_5y is None:
            missing_components.append("LT拟合分析")
        if st.session_state.arpu_data is None:
            missing_components.append("ARPU计算")
        
        st.info(f"请先完成：{', '.join(missing_components)}")
        st.markdown('</div>', unsafe_allow_html=True)

# ==================== 底部信息 ====================
with st.sidebar:
    st.markdown("---")
    st.markdown("""
    <div class="nav-container">
        <h4 style="text-align: center; color: white;">使用指南</h4>
        <p style="font-size: 0.9rem; color: rgba(255,255,255,0.9); text-align: center;">
        按步骤完成分析流程，每步都有详细指导。
        </p>
        <p style="font-size: 0.8rem; color: rgba(255,255,255,0.7); text-align: center;">
        LTV智能分析平台 v3.3<br>
        基于三阶段数学建模
        </p>
    </div>
    """, unsafe_allow_html=True)
