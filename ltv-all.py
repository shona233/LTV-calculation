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

# 解决中文显示问题 - 改为英文标签
def setup_chart_font():
    """设置图表字体 - 使用英文避免中文显示问题"""
    try:
        plt.rcParams['font.family'] = ['Arial', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.size'] = 10
        return True
    except Exception as e:
        plt.rcParams['font.family'] = ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.size'] = 10
        return False

# 初始化字体设置
setup_chart_font()

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

    /* 按钮样式 */
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

    /* 子步骤样式 */
    .sub-steps {
        font-size: 0.8rem;
        color: rgba(255,255,255,0.7);
        margin-top: 0.3rem;
        line-height: 1.2;
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

    /* 成功信息样式 */
    .success-info {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #22c55e;
    }

    /* 隐藏默认的Streamlit元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==================== 默认配置数据 ====================
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

# ==================== 内置ARPU数据管理 ====================
def get_builtin_arpu_data():
    """获取内置的ARPU基础数据 - 优先使用管理员上传的数据"""
    # 检查是否有管理员上传的默认数据
    if 'admin_default_arpu_data' in st.session_state and st.session_state.admin_default_arpu_data is not None:
        return st.session_state.admin_default_arpu_data.copy()
    
    # 如果没有管理员数据，返回示例数据
    return get_sample_arpu_data()

def get_sample_arpu_data():
    """生成示例ARPU数据（当没有管理员上传数据时使用）"""
    # 生成2024年1月到2025年4月的所有月份
    months = []
    for year in [2024, 2025]:
        start_month = 1 if year == 2024 else 1
        end_month = 12 if year == 2024 else 4
        for month in range(start_month, end_month + 1):
            months.append(f"{year}-{month:02d}")
    
    builtin_data = []
    
    # 为主要渠道生成示例数据
    sample_channels = ['9000', '5057', '5599', '5237', '5115', '500285', '500286']
    
    for pid in sample_channels:
        for month in months:
            # 生成示例数据
            base_users = {
                '9000': 50000, '5057': 8000, '5599': 6000, 
                '5237': 5500, '5115': 5000, '500285': 2000, '500286': 2200
            }.get(pid, 1000)
            
            base_revenue = {
                '9000': 2000000, '5057': 320000, '5599': 240000,
                '5237': 220000, '5115': 200000, '500285': 80000, '500286': 88000
            }.get(pid, 40000)
            
            # 添加月度波动
            month_index = months.index(month)
            fluctuation = 1 + (month_index % 3 - 1) * 0.1
            
            users = int(base_users * fluctuation)
            revenue = int(base_revenue * fluctuation)
            
            builtin_data.append({
                '月份': month,
                'pid': pid,
                'stat_date': f"{month}-15",
                'instl_user_cnt': users,
                'ad_all_rven_1d_m': revenue
            })
    
    return pd.DataFrame(builtin_data)

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

# ==================== 快速数据预览函数 ====================
def quick_preview(df, max_rows=3):
    """快速数据预览，最多显示3行"""
    if df.empty:
        return df
    
    # 只取前几行，减少处理时间
    preview_df = df.head(max_rows)
    
    # 简单排序：把有值的列放前面
    non_empty_cols = []
    empty_cols = []
    
    for col in preview_df.columns:
        if preview_df[col].notna().any():
            non_empty_cols.append(col)
        else:
            empty_cols.append(col)
    
    # 确保'数据来源'列在最前面（如果存在）
    if '数据来源' in non_empty_cols:
        non_empty_cols.remove('数据来源')
        non_empty_cols.insert(0, '数据来源')
    
    return preview_df[non_empty_cols + empty_cols]

# ==================== 渠道映射处理函数 ====================
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

# ==================== 优化的OCPX数据合并函数 ====================
def merge_ocpx_data_optimized(retention_data, new_users_data, target_month):
    """优化的OCPX格式数据合并函数"""
    try:
        # 处理新增数据
        new_users_clean = new_users_data.copy()
        
        # 快速查找关键列
        date_col = None
        new_users_col = None
        
        # 使用更精确的列名匹配
        for col in new_users_clean.columns:
            col_str = str(col).strip()
            if '日期' in col_str:
                date_col = col
            elif '回传新增数' in col_str or col_str in ['新增', 'new', '回传新增']:
                new_users_col = col
        
        if date_col is None or new_users_col is None:
            return None
        
        # 构建新增数据字典，只处理目标月份的数据
        new_users_dict = {}
        for _, row in new_users_clean.iterrows():
            date_val = row[date_col]
            if pd.isna(date_val):
                continue
            
            try:
                # 快速日期处理
                if isinstance(date_val, str):
                    date_str = date_val.strip()
                    # 跳过非目标月份的数据
                    if target_month and not date_str.startswith(target_month):
                        continue
                else:
                    date_str = pd.to_datetime(date_val).strftime('%Y-%m-%d')
                    if target_month and not date_str.startswith(target_month):
                        continue
                
                new_users_count = safe_convert_to_numeric(row[new_users_col])
                if new_users_count > 0:
                    new_users_dict[date_str] = new_users_count
            except:
                continue
        
        # 处理留存数据
        retention_clean = retention_data.copy()
        
        # 快速查找日期列
        retention_date_col = None
        for col in retention_clean.columns:
            if '日期' in str(col):
                retention_date_col = col
                break
        
        if retention_date_col is None:
            return None
        
        # 合并数据，只处理目标月份
        merged_data = []
        
        for _, row in retention_clean.iterrows():
            date_val = row[retention_date_col]
            if pd.isna(date_val):
                continue
            
            try:
                # 快速日期处理
                if isinstance(date_val, str):
                    date_str = date_val.strip()
                    if target_month and not date_str.startswith(target_month):
                        continue
                else:
                    date_str = pd.to_datetime(date_val).strftime('%Y-%m-%d')
                    if target_month and not date_str.startswith(target_month):
                        continue
                
                # 构建合并后的行数据
                merged_row = {
                    'date': date_str,
                    'stat_date': date_str,
                    '日期': date_str,
                    '回传新增数': new_users_dict.get(date_str, 0)
                }
                
                # 只添加数字列名的留存数据
                for col in retention_clean.columns:
                    col_str = str(col).strip()
                    if col_str.isdigit() and 1 <= int(col_str) <= 30:
                        retain_value = safe_convert_to_numeric(row[col])
                        merged_row[col_str] = retain_value
                
                merged_data.append(merged_row)
                
            except:
                continue
        
        return pd.DataFrame(merged_data) if merged_data else None
            
    except Exception as e:
        st.error(f"处理OCPX数据时出错：{str(e)}")
        return None

# ==================== 优化的文件整合核心函数 ====================
def integrate_excel_files_optimized(uploaded_files, target_month, channel_mapping):
    """优化版本的文件整合函数，提升处理速度"""
    all_data = pd.DataFrame()
    processed_count = 0
    file_status = []  # 记录文件处理状态

    for file in uploaded_files:
        # 从文件名中提取渠道名称
        source_name = os.path.splitext(file.name)[0].strip()
        
        # 渠道映射处理
        mapped_source = source_name
        if source_name in channel_mapping:
            mapped_source = source_name
        else:
            reverse_mapping = create_reverse_mapping(channel_mapping)
            if source_name in reverse_mapping:
                mapped_source = reverse_mapping[source_name]

        try:
            # 读取Excel文件
            file_content = file.read()
            xls = pd.ExcelFile(io.BytesIO(file_content))
            sheet_names = xls.sheet_names

            # 查找OCPX格式的工作表
            retention_sheet = None
            new_users_sheet = None
            
            # 精确匹配sheet名称
            for sheet in sheet_names:
                if "ocpx监测留存数" in sheet or "监测留存数" in sheet:
                    retention_sheet = sheet
                elif "监测渠道回传量" in sheet or "回传量" in sheet:
                    new_users_sheet = sheet
            
            # 优先处理OCPX分离式格式
            if retention_sheet and new_users_sheet:
                try:
                    retention_data = pd.read_excel(io.BytesIO(file_content), sheet_name=retention_sheet)
                    new_users_data = pd.read_excel(io.BytesIO(file_content), sheet_name=new_users_sheet)
                    
                    file_data = merge_ocpx_data_optimized(retention_data, new_users_data, target_month)
                    if file_data is not None and not file_data.empty:
                        file_data.insert(0, '数据来源', mapped_source)
                        all_data = pd.concat([all_data, file_data], ignore_index=True)
                        processed_count += 1
                        file_status.append(f"✅ {file.name} - OCPX分离式格式")
                    else:
                        file_status.append(f"⚠️ {file.name} - OCPX格式数据为空")
                    continue
                except Exception as e:
                    file_status.append(f"❌ {file.name} - OCPX格式处理失败: {str(e)}")
                    continue
            
            # 处理单sheet的传统格式或其他格式
            if retention_sheet:
                sheet_to_read = retention_sheet
            else:
                sheet_to_read = 0  # 使用第一个sheet
            
            try:
                file_data = pd.read_excel(io.BytesIO(file_content), sheet_name=sheet_to_read)
                
                if file_data is not None and not file_data.empty:
                    # 快速数据处理
                    file_data_copy = file_data.copy()
                    
                    # 检测传统格式（stat_date + new + new_retain_X）
                    has_stat_date = 'stat_date' in file_data_copy.columns
                    has_new = 'new' in file_data_copy.columns
                    
                    if has_stat_date and has_new:
                        # 传统格式处理
                        standardized_data = file_data_copy.copy()
                        standardized_data['回传新增数'] = standardized_data['new'].apply(safe_convert_to_numeric)
                        
                        # 处理留存数据列：new_retain_1 -> 1
                        for i in range(1, 31):
                            retain_col = f'new_retain_{i}'
                            if retain_col in standardized_data.columns:
                                standardized_data[str(i)] = standardized_data[retain_col].apply(safe_convert_to_numeric)
                        
                        # 处理日期和筛选
                        standardized_data['stat_date'] = pd.to_datetime(standardized_data['stat_date'], errors='coerce')
                        standardized_data['stat_date'] = standardized_data['stat_date'].dt.strftime('%Y-%m-%d')
                        standardized_data['日期'] = standardized_data['stat_date']
                        standardized_data['month'] = standardized_data['stat_date'].str[:7]
                        
                        filtered_data = standardized_data[standardized_data['month'] == target_month].copy()
                        
                        if not filtered_data.empty:
                            filtered_data.insert(0, '数据来源', mapped_source)
                            filtered_data['date'] = filtered_data['stat_date']
                            all_data = pd.concat([all_data, filtered_data], ignore_index=True)
                            processed_count += 1
                            file_status.append(f"✅ {file.name} - 传统格式")
                        else:
                            file_status.append(f"⚠️ {file.name} - 目标月份无数据")
                    else:
                        # 其他格式的兼容处理
                        file_status.append(f"⚠️ {file.name} - 格式未识别，跳过")
                        
            except Exception as e:
                file_status.append(f"❌ {file.name} - 处理失败: {str(e)}")

        except Exception as e:
            file_status.append(f"❌ {file.name} - 读取失败: {str(e)}")

    return all_data, processed_count, file_status

# ==================== 留存率计算函数 ====================
def calculate_retention_rates_optimized(df):
    """优化的留存率计算函数"""
    retention_results = []
    data_sources = df['数据来源'].unique()

    for source in data_sources:
        source_data = df[df['数据来源'] == source].copy()
        
        # 计算平均新增用户数
        new_users_values = source_data['回传新增数'].apply(safe_convert_to_numeric)
        new_users_values = new_users_values[new_users_values > 0]
        
        if len(new_users_values) == 0:
            continue
        
        avg_new_users = new_users_values.mean()
        
        # 计算各天留存率
        retention_data = {'data_source': source, 'avg_new_users': avg_new_users}
        days = []
        rates = []
        
        for day in range(1, 31):
            day_col = str(day)
            if day_col not in source_data.columns:
                continue
            
            day_retain_values = source_data[day_col].apply(safe_convert_to_numeric)
            day_retain_values = day_retain_values[day_retain_values >= 0]
            
            if len(day_retain_values) > 0:
                avg_retain = day_retain_values.mean()
                retention_rate = avg_retain / avg_new_users if avg_new_users > 0 else 0
                
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

def calculate_lt_advanced(retention_result, channel_name, lt_years=5, return_curve_data=False):
    """优化的LT计算函数"""
    # 渠道规则
    CHANNEL_RULES = {
        "华为": {"stage_2": [30, 120], "stage_3_base": [120, 220]},
        "小米": {"stage_2": [30, 190], "stage_3_base": [190, 290]},
        "oppo": {"stage_2": [30, 160], "stage_3_base": [160, 260]},
        "vivo": {"stage_2": [30, 150], "stage_3_base": [150, 250]},
        "iphone": {"stage_2": [30, 150], "stage_3_base": [150, 250]},
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

    # 第一阶段 - 幂函数拟合
    try:
        popt_power, _ = curve_fit(power_function, days, rates)
        a, b = popt_power
        
        days_full = np.arange(1, 31)
        rates_full = power_function(days_full, a, b)
        lt1_to_30 = np.sum(rates_full)
    except:
        lt1_to_30 = 0.0
        a, b = 1.0, -1.0

    # 第二阶段
    try:
        days_stage_2 = np.arange(stage_2_start, stage_2_end + 1)
        rates_stage_2 = power_function(days_stage_2, a, b)
        lt_stage_2 = np.sum(rates_stage_2)
    except:
        lt_stage_2 = 0.0

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
        
        days_stage_3 = np.arange(stage_3_base_start, max_days + 1)
        rates_stage_3 = exponential_function(days_stage_3, c, d)
        lt_stage_3 = np.sum(rates_stage_3)
    except:
        days_stage_3 = np.arange(stage_3_base_start, max_days + 1)
        rates_stage_3 = power_function(days_stage_3, a, b) if 'a' in locals() else np.zeros(len(days_stage_3))
        lt_stage_3 = np.sum(rates_stage_3)

    total_lt = 1.0 + lt1_to_30 + lt_stage_2 + lt_stage_3

    if return_curve_data:
        # 构建完整曲线数据
        all_days = np.concatenate([days_full, days_stage_2, days_stage_3])
        all_rates = np.concatenate([rates_full, rates_stage_2, rates_stage_3])

        # 排序并限制天数
        sort_idx = np.argsort(all_days)
        all_days = all_days[sort_idx]
        all_rates = all_rates[sort_idx]

        max_idx = np.searchsorted(all_days, lt_years * 365, side='right')
        all_days = all_days[:max_idx]
        all_rates = all_rates[:max_idx]

        return {
            'lt_value': total_lt,
            'success': True,
            'days': all_days,
            'rates': all_rates
        }

    return total_lt

# ==================== 图表生成函数 ====================
def create_channel_chart(channel_name, curve_data, original_data, max_days=100):
    """创建单个渠道的拟合图表"""
    plt.rcParams['font.family'] = ['Arial', 'DejaVu Sans']
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
            label='Actual Data',
            zorder=3
        )
    
    # 绘制拟合曲线（限制在max_days内）
    curve_days = curve_data["days"]
    curve_rates = curve_data["rates"]
    
    mask = curve_days <= max_days
    curve_days_filtered = curve_days[mask]
    curve_rates_filtered = curve_rates[mask]
    
    ax.plot(
        curve_days_filtered,
        curve_rates_filtered,
        color='#3b82f6',
        linewidth=2.5,
        label='Fitted Curve',
        zorder=2
    )
    
    # 设置图表样式
    ax.set_xlim(0, max_days)
    ax.set_ylim(0, 0.6)
    ax.set_xlabel('Retention Days', fontsize=12)
    ax.set_ylabel('Retention Rate', fontsize=12)
    ax.set_title(f'{channel_name} ({max_days}d LT Fitting)', fontsize=14, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.legend(fontsize=10)
    
    # Y轴百分比格式
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
    <div class="main-title">用户生命周期价值分析系统 - 优化版</div>
    <div class="main-subtitle">基于分阶段数学建模的LTV预测 | 提升上传速度</div>
</div>
""", unsafe_allow_html=True)

# 初始化session state
session_keys = [
    'channel_mapping', 'merged_data', 'retention_data', 'lt_results_2y', 
    'lt_results_5y', 'arpu_data', 'ltv_results', 'current_step',
    'visualization_data_5y', 'original_data', 'admin_default_arpu_data'
]
for key in session_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# 设置默认值
if st.session_state.channel_mapping is None:
    st.session_state.channel_mapping = DEFAULT_CHANNEL_MAPPING
if st.session_state.current_step is None:
    st.session_state.current_step = 0

# ==================== 分析步骤定义 ====================
ANALYSIS_STEPS = [
    {"name": "LT模型构建", "sub_steps": ["数据上传汇总", "异常值剔除", "留存率计算", "LT拟合分析"]},
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
        
        # 显示子步骤
        if "sub_steps" in step and i == st.session_state.current_step:
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
        <strong>1. 数据上传汇总：</strong>快速整合多个Excel文件，支持OCPX新格式<br>
        <strong>2. 异常值剔除：</strong>剔除异常渠道和日期数据，提高数据质量<br>
        <strong>3. 留存率计算：</strong>OCPX格式：各天留存列（1、2、3...）平均值÷回传新增数平均值<br>
        <strong>4. LT拟合分析：</strong>采用三阶段分层建模，预测用户生命周期长度
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 步骤1：数据上传与汇总
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("1. 数据上传与汇总")
    
    # OCPX格式说明
    st.markdown("""
    <div class="step-tip">
        <div class="step-tip-title">📋 支持的OCPX Excel格式</div>
        <div class="step-tip-content">
        <strong>方式1：OCPX分离式格式（推荐）</strong><br>
        • Sheet: <strong>"监测渠道回传量"</strong> - 列：日期、回传新增数<br>
        • Sheet: <strong>"ocpx监测留存数"</strong> - 列：日期、1、2、3、4、5...（天数）<br><br>
        <strong>方式2：传统格式</strong><br>
        • 列名：<strong>stat_date</strong>（日期）、<strong>new</strong>（新增）、<strong>new_retain_1、new_retain_2...</strong>（留存）<br><br>
        <strong>命名规则：</strong>请按渠道名称命名文件，如：华为.xlsx、小米.xlsx
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 渠道映射摘要
    with st.expander("🔍 查看渠道映射摘要", expanded=False):
        current_channels = list(st.session_state.channel_mapping.keys())
        st.markdown(f"**当前共有 {len(current_channels)} 个渠道**")
        channels_text = "、".join(current_channels[:10])
        if len(current_channels) > 10:
            channels_text += f"...等{len(current_channels)}个渠道"
        st.text(channels_text)

    # 自定义渠道映射（可选）
    if st.checkbox("需要上传自定义渠道映射"):
        channel_mapping_file = st.file_uploader(
            "选择渠道映射Excel文件",
            type=['xlsx', 'xls'],
            help="格式：第一列为渠道名称，后续列为对应的渠道号"
        )
        
        if channel_mapping_file:
            custom_mapping = parse_channel_mapping_from_excel(channel_mapping_file)
            if custom_mapping:
                st.session_state.channel_mapping = custom_mapping
                st.success(f"✅ 自定义渠道映射加载成功！共 {len(custom_mapping)} 个渠道")

    # 数据文件上传
    st.markdown("### 📤 数据文件上传")
    
    uploaded_files = st.file_uploader(
        "选择Excel数据文件",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        help="支持OCPX分离式格式和传统格式"
    )
    
    default_month = get_default_target_month()
    target_month = st.text_input("目标月份 (YYYY-MM)", value=default_month)

    if uploaded_files:
        st.info(f"已选择 {len(uploaded_files)} 个文件")

        if st.button("🚀 快速处理数据", type="primary", use_container_width=True):
            with st.spinner("正在快速处理数据文件..."):
                try:
                    merged_data, processed_count, file_status = integrate_excel_files_optimized(
                        uploaded_files, target_month, st.session_state.channel_mapping
                    )

                    if merged_data is not None and not merged_data.empty:
                        st.session_state.merged_data = merged_data
                        
                        # 显示处理结果
                        st.markdown("""
                        <div class="success-info">
                            <strong>✅ 数据处理完成！</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("处理成功", f"{processed_count} 个文件")
                        with col2:
                            st.metric("总记录数", f"{len(merged_data):,}")
                        with col3:
                            st.metric("渠道数", merged_data['数据来源'].nunique())

                        # 显示文件处理状态
                        with st.expander("📋 文件处理状态", expanded=True):
                            for status in file_status:
                                if "✅" in status:
                                    st.success(status)
                                elif "⚠️" in status:
                                    st.warning(status)
                                else:
                                    st.error(status)

                        # 简化的数据预览
                        st.subheader("数据预览")
                        for source in merged_data['数据来源'].unique():
                            source_data = merged_data[merged_data['数据来源'] == source]
                            with st.expander(f"📊 {source} ({len(source_data)} 条记录)", expanded=False):
                                preview = quick_preview(source_data, max_rows=3)
                                st.dataframe(preview, use_container_width=True)
                                
                    else:
                        st.error("未找到有效数据")
                except Exception as e:
                    st.error(f"处理过程中出现错误：{str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)


    # 步骤2：异常值剔除
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("2. 异常值剔除")
    
    if st.session_state.merged_data is not None:
        working_data = st.session_state.merged_data
        data_sources = working_data['数据来源'].unique()
        date_columns = [col for col in working_data.columns if '日期' in col or 'date' in col.lower()]
        
        # 异常值剔除选择
        col1, col2 = st.columns(2)
        with col1:
            excluded_channels = st.multiselect(
                "选择要剔除的渠道",
                options=data_sources,
                help="选中的渠道将在后续计算中被剔除"
            )
        with col2:
            excluded_dates = st.multiselect(
                "选择要剔除的日期",
                options=date_columns if date_columns else ['无日期列'],
                help="选中的日期列的数据将在后续计算中被剔除"
            )
        
        # 显示剔除规则
        if excluded_channels or (excluded_dates and excluded_dates != ['无日期列']):
            st.info(f"📋 剔除规则：渠道 {excluded_channels} 且日期 {excluded_dates} 的数据将被剔除")
            
            # 保存剔除规则到session_state
            st.session_state.excluded_channels = excluded_channels
            st.session_state.excluded_dates = excluded_dates
        else:
            st.session_state.excluded_channels = []
            st.session_state.excluded_dates = []
            
    else:
        st.info("请先完成数据上传与汇总")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # 步骤3：留存率计算（默认显示，不需要条件判断）
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("3. 留存率计算")
    
    if st.session_state.merged_data is not None:
        working_data = st.session_state.merged_data
        data_sources = working_data['数据来源'].unique()
        selected_sources = st.multiselect("选择要分析的数据来源", options=data_sources, default=data_sources)

        if st.button("💡 快速计算留存率", type="primary", use_container_width=True):
            if selected_sources:
                with st.spinner("正在计算留存率..."):
                    filtered_data = working_data[working_data['数据来源'].isin(selected_sources)]
                    retention_results = calculate_retention_rates_optimized(filtered_data)
                    st.session_state.retention_data = retention_results

                    st.success("留存率计算完成！")
                    
                    # 显示简化的结果摘要
                    if retention_results:
                        summary_data = []
                        for result in retention_results:
                            summary_data.append({
                                '渠道': result['data_source'],
                                '有效天数': len(result['days']),
                                '平均新增': f"{result['avg_new_users']:,.0f}",
                                '1天留存率': f"{result['rates'][0]:.3f}" if len(result['rates']) > 0 else "-"
                            })
                        
                        summary_df = pd.DataFrame(summary_data)
                        st.dataframe(summary_df, use_container_width=True)
            else:
                st.error("请选择至少一个数据来源")
    else:
        st.info("请先完成数据上传与汇总")

    st.markdown('</div>', unsafe_allow_html=True)

    # 步骤3：LT拟合分析（默认显示，不需要条件判断）
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("3. LT拟合分析")
    
    st.markdown("""
    <div class="step-tip">
        <div class="step-tip-title">📋 三阶段拟合规则</div>
        <div class="step-tip-content">
        <strong>第一阶段：</strong>1-30天，幂函数拟合实际数据<br>
        <strong>第二阶段：</strong>31-X天，延续幂函数模型<br>
        <strong>第三阶段：</strong>Y天后，指数函数建模长期衰减
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.retention_data is not None:
        if st.button("⚡ 快速LT拟合分析", type="primary", use_container_width=True):
            with st.spinner("正在进行拟合计算..."):
                lt_results_2y = []
                lt_results_5y = []
                visualization_data_5y = {}
                original_data = {}

                for retention_result in st.session_state.retention_data:
                    channel_name = retention_result['data_source']
                    
                    # 计算2年和5年LT
                    lt_result_2y = calculate_lt_advanced(retention_result, channel_name, 2, return_curve_data=True)
                    lt_result_5y = calculate_lt_advanced(retention_result, channel_name, 5, return_curve_data=True)

                    lt_results_2y.append({
                        'data_source': channel_name,
                        'lt_value': lt_result_2y['lt_value'],
                        'fit_success': lt_result_2y['success']
                    })
                    
                    lt_results_5y.append({
                        'data_source': channel_name,
                        'lt_value': lt_result_5y['lt_value'],
                        'fit_success': lt_result_5y['success']
                    })

                    # 保存可视化数据
                    visualization_data_5y[channel_name] = {
                        "days": lt_result_5y['days'],
                        "rates": lt_result_5y['rates'],
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
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 2年LT结果")
                    results_2y_df = pd.DataFrame([
                        {'渠道名称': r['data_source'], '2年LT': round(r['lt_value'], 2)}
                        for r in lt_results_2y
                    ])
                    st.dataframe(results_2y_df, use_container_width=True)
                
                with col2:
                    st.markdown("#### 5年LT结果")
                    results_5y_df = pd.DataFrame([
                        {'渠道名称': r['data_source'], '5年LT': round(r['lt_value'], 2)}
                        for r in lt_results_5y
                    ])
                    st.dataframe(results_5y_df, use_container_width=True)
    else:
        st.info("请先完成留存率计算")

    st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "ARPU计算":
    # 原理解释
    st.markdown("""
    <div class="principle-box">
        <div class="principle-title">📚 ARPU计算原理</div>
        <div class="principle-content">
        ARPU（Average Revenue Per User）= 总收入 ÷ 总新增用户数。
        支持管理员设置默认数据和用户上传最新数据合并计算。
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("ARPU数据处理")

    # 数据源选择（默认折叠）
    with st.expander("📋 选择ARPU数据来源", expanded=False):
        data_source_option = st.radio(
            "选择数据来源：",
            options=[
                "🔧 管理员模式:管理默认ARPU数据",
                "📊 使用默认数据 + 上传新数据(2025.5+)"
            ],
            index=1  # 默认值是第二个
        )

    # 管理员功能（默认折叠）
    if data_source_option == "🔧 管理员模式:管理默认ARPU数据":
        with st.expander("🔧 管理员功能：设置默认ARPU数据", expanded=False):
            st.markdown("### 🔧 管理员功能：设置默认ARPU数据")
            
            admin_arpu_file = st.file_uploader(
                "上传完整的ARPU历史数据文件",
                type=['xlsx', 'xls'],
                help="必须包含列：月份、pid、stat_date、instl_user_cnt、ad_all_rven_1d_m"
            )
            
            if admin_arpu_file:
                try:
                    admin_df = pd.read_excel(admin_arpu_file)
                    required_cols = ['月份', 'pid', 'stat_date', 'instl_user_cnt', 'ad_all_rven_1d_m']
                    missing_cols = [col for col in required_cols if col not in admin_df.columns]
                    
                    if missing_cols:
                        st.error(f"❌ 文件缺少必需列: {', '.join(missing_cols)}")
                    else:
                        st.success(f"✅ 管理员数据读取成功！{len(admin_df):,} 条记录")
                        
                        if st.button("设置为默认数据", type="primary"):
                            st.session_state.admin_default_arpu_data = admin_df.copy()
                            st.success("🎉 默认ARPU数据已更新！")
                except Exception as e:
                    st.error(f"读取文件失败：{str(e)}")
        
        # 使用默认数据进行处理
        arpu_df = get_builtin_arpu_data()
        st.info(f"📊 当前默认数据：{len(arpu_df):,} 条记录，覆盖 {arpu_df['月份'].nunique()} 个月份")
        process_arpu = True
    
    else:  # 使用默认数据 + 上传新数据(2025.5+)
        # 显示默认数据信息
        builtin_df = get_builtin_arpu_data()
        st.info(f"📊 默认数据：{len(builtin_df):,} 条记录，覆盖 {builtin_df['月份'].nunique()} 个月份")
        
        # 上传新数据
        new_arpu_file = st.file_uploader("上传2025年5月后的ARPU数据", type=['xlsx', 'xls'])
        
        if new_arpu_file:
            try:
                new_df = pd.read_excel(new_arpu_file)
                # 合并数据逻辑
                combined_df = pd.concat([builtin_df, new_df], ignore_index=True)
                st.success(f"数据合并成功！总计 {len(combined_df):,} 条记录")
                arpu_df = combined_df
                process_arpu = True
            except Exception as e:
                st.error(f"处理新数据失败：{str(e)}")
                process_arpu = False
        else:
            arpu_df = builtin_df
            process_arpu = True

    # ARPU计算
    if 'process_arpu' in locals() and process_arpu and 'arpu_df' in locals():
        if st.button("🚀 快速计算ARPU", type="primary", use_container_width=True):
            with st.spinner("正在计算ARPU..."):
                try:
                    # 确保pid为字符串格式
                    arpu_df['pid'] = arpu_df['pid'].astype(str).str.replace('.0', '', regex=False)
                    
                    # 创建反向渠道映射
                    reverse_mapping = create_reverse_mapping(st.session_state.channel_mapping)
                    
                    # 按渠道计算ARPU
                    arpu_results = []
                    
                    for pid, group in arpu_df.groupby('pid'):
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
                                    'arpu_value': arpu_value
                                })

                    if arpu_results:
                        # 合并相同渠道的数据
                        final_arpu = {}
                        for result in arpu_results:
                            channel = result['data_source']
                            if channel in final_arpu:
                                final_arpu[channel]['total_users'] += result['total_users']
                                final_arpu[channel]['total_revenue'] += result['total_revenue']
                            else:
                                final_arpu[channel] = result.copy()
                        
                        # 重新计算ARPU
                        arpu_summary = []
                        for channel, data in final_arpu.items():
                            arpu_value = data['total_revenue'] / data['total_users'] if data['total_users'] > 0 else 0
                            arpu_summary.append({
                                'data_source': channel,
                                'arpu_value': arpu_value
                            })
                        
                        arpu_summary_df = pd.DataFrame(arpu_summary)
                        st.session_state.arpu_data = arpu_summary_df
                        st.success("ARPU计算完成！")
                        
                        # 显示结果
                        display_df = arpu_summary_df.copy()
                        display_df['ARPU'] = display_df['arpu_value'].round(4)
                        display_df = display_df[['data_source', 'ARPU']]
                        display_df.columns = ['渠道名称', 'ARPU值']
                        st.dataframe(display_df, use_container_width=True)
                    else:
                        st.error("未找到匹配的渠道数据")

                except Exception as e:
                    st.error(f"ARPU计算失败：{str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "LTV结果报告":
    # 原理解释
    st.markdown("""
    <div class="principle-box">
        <div class="principle-title">📚 LTV结果报告</div>
        <div class="principle-content">
        LTV结果报告整合LT拟合分析和ARPU计算结果，通过LTV = LT × ARPU公式计算用户生命周期价值。
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

            ltv_5y = lt_result_5y['lt_value'] * arpu_value
            ltv_2y = lt_result_2y['lt_value'] * arpu_value if lt_result_2y else 0

            ltv_results.append({
                'data_source': source,
                'lt_2y': lt_result_2y['lt_value'] if lt_result_2y else 0,
                'lt_5y': lt_result_5y['lt_value'],
                'arpu_value': arpu_value,
                'ltv_2y': ltv_2y,
                'ltv_5y': ltv_5y
            })

        st.session_state.ltv_results = ltv_results

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("LTV综合计算结果")

        # 创建结果表格
        display_data = []
        for result in ltv_results:
            display_data.append({
                '渠道名称': result['data_source'],
                '5年LT': round(result['lt_5y'], 2),
                '5年ARPU': round(result['arpu_value'], 4),
                '5年LTV': round(result['ltv_5y'], 2),
                '2年LT': round(result['lt_2y'], 2),
                '2年LTV': round(result['ltv_2y'], 2)
            })

        results_df = pd.DataFrame(display_data)
        st.dataframe(results_df, use_container_width=True, height=400)
        st.markdown('</div>', unsafe_allow_html=True)

        # 显示拟合曲线图表
        if st.session_state.visualization_data_5y and st.session_state.original_data:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("渠道拟合曲线（100天）")
            
            visualization_data_5y = st.session_state.visualization_data_5y
            original_data = st.session_state.original_data
            
            # 按LT值排序显示
            sorted_channels = sorted(visualization_data_5y.items(), key=lambda x: x[1]['lt'])
            
            # 每行显示2个图表
            for i in range(0, len(sorted_channels), 2):
                cols = st.columns(2)
                for j, col in enumerate(cols):
                    if i + j < len(sorted_channels):
                        channel_name, curve_data = sorted_channels[i + j]
                        with col:
                            fig = create_channel_chart(
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
                label="📥 下载LTV结果 (CSV)",
                data=csv_data.encode('utf-8-sig'),
                file_name=f"LTV_Results_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col2:
            # 详细报告
            report_text = f"""
LTV用户生命周期价值分析报告
===========================================
生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

执行摘要
-----------
分析渠道数量: {len(results_df)}
5年平均LTV: {results_df['5年LTV'].mean():.2f}
5年最高LTV: {results_df['5年LTV'].max():.2f}
2年平均LTV: {results_df['2年LTV'].mean():.2f}

详细结果
-----------
{results_df.to_string(index=False)}

报告生成: LTV智能分析平台 v4.0 (优化版)
"""

            st.download_button(
                label="📋 下载详细报告 (TXT)",
                data=report_text.encode('utf-8'),
                file_name=f"LTV_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
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
        <h4 style="text-align: center; color: white;">优化说明</h4>
        <p style="font-size: 0.9rem; color: rgba(255,255,255,0.9); text-align: center;">
        ⚡ 优化上传速度<br>
        📊 简化数据预览<br>
        🚀 快速处理流程
        </p>
        <p style="font-size: 0.8rem; color: rgba(255,255,255,0.7); text-align: center;">
        <strong>OCPX格式支持：</strong><br>
        • 监测渠道回传量: 日期、回传新增数<br>
        • ocpx监测留存数: 日期、1、2、3...
        </p>
        <p style="font-size: 0.8rem; color: rgba(255,255,255,0.7); text-align: center;">
        LTV智能分析平台 v4.0<br>
        优化版 - 提升性能
        </p>
    </div>
    """, unsafe_allow_html=True)
