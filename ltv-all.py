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
import gc  # 垃圾回收
import difflib  # 添加difflib导入

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

    /* 按钮样式 - 修复所有状态的颜色 */
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
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%) !important;
        color: white !important;
        transform: translateY(0px) !important;
    }
    
    .stButton > button:focus {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(30, 64, 175, 0.3) !important;
        outline: none !important;
    }
    
    .stButton > button:focus:not(:active) {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%) !important;
        color: white !important;
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
    
    div[data-testid="stButton"] > button:active {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%) !important;
        color: white !important;
    }
    
    div[data-testid="stButton"] > button:focus {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%) !important;
        color: white !important;
        outline: none !important;
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

    /* 修改数据来源标签颜色为浅蓝色 */
    .element-container .stScatter {
        color: #3b82f6 !important;
    }
    
    /* 修改metric标签颜色 */
    [data-testid="metric-container"] > div > div > div > div {
        color: #3b82f6 !important;
    }
    
    /* 修改数据预览中的数据来源为浅蓝色 */
    .stDataFrame div[data-testid="stDataFrame"] {
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    /* 隐藏默认的Streamlit元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==================== 默认配置数据 ====================
DEFAULT_CHANNEL_MAPPING = {
    '总体': [],  # 总体没有渠道号，是所有值的总和
    '安卓': [],  # 安卓没有渠道号，是总体减去iPhone
    'iPhone': ['9000'],  # iPhone渠道号9000
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
        # 跳过没有渠道号的特殊渠道（总体、安卓）
        if not pids:
            continue
        for pid in pids:
            reverse_mapping[str(pid)] = channel_name
    return reverse_mapping

# ==================== 永久数据存储管理 ====================
ADMIN_DATA_FILE = "admin_default_arpu_data.csv"

@st.cache_data
def load_admin_data_from_file():
    """从本地文件加载管理员上传的ARPU数据"""
    try:
        if os.path.exists(ADMIN_DATA_FILE):
            df = pd.read_csv(ADMIN_DATA_FILE)
            return df
    except Exception as e:
        st.error(f"加载管理员数据文件失败：{str(e)}")
    return None

def save_admin_data_to_file(df):
    """保存管理员上传的ARPU数据到本地文件"""
    try:
        df.to_csv(ADMIN_DATA_FILE, index=False, encoding='utf-8-sig')
        return True
    except Exception as e:
        st.error(f"保存管理员数据文件失败：{str(e)}")
        return False

@st.cache_data
def get_builtin_arpu_data():
    """获取内置的ARPU基础数据 - 优先使用管理员上传的数据"""
    # 尝试从文件读取管理员数据
    admin_data = load_admin_data_from_file()
    if admin_data is not None:
        return admin_data.copy()
    
    # 如果没有管理员数据，返回示例数据
    return get_sample_arpu_data()

@st.cache_data
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
    
    # 为主要渠道生成示例数据，包含iPhone渠道号9000
    sample_channels = ['9000', '5057', '5599', '5237', '5115', '500285', '500286']
    
    for pid in sample_channels:
        for month in months:
            # 生成示例数据
            base_users = {
                '9000': 12000, '5057': 8000, '5599': 6000, 
                '5237': 5500, '5115': 5000, '500285': 2000, '500286': 2200
            }.get(pid, 1000)
            
            base_revenue = {
                '9000': 600000, '5057': 320000, '5599': 240000,
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

def load_admin_default_arpu_data():
    """管理员上传默认ARPU数据的界面"""
    st.subheader("管理员功能：上传默认ARPU数据")
    
    st.markdown("""
    <div class="step-tip">
        <div class="step-tip-title">管理员数据上传说明</div>
        <div class="step-tip-content">
        • 上传包含完整历史ARPU数据的Excel文件（支持xlsx格式）<br>
        • 必须包含列：<strong>月份、pid、stat_date、instl_user_cnt、ad_all_rven_1d_m</strong><br>
        • 上传后将永久保存，供所有用户使用<br>
        • 数据格式示例：<br>
        &nbsp;&nbsp;月份: 2024-01, 2024-02...<br>
        &nbsp;&nbsp;pid: 渠道号<br>
        &nbsp;&nbsp;stat_date: 统计日期<br>
        &nbsp;&nbsp;instl_user_cnt: 新增用户数<br>
        &nbsp;&nbsp;ad_all_rven_1d_m: 收入数据
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 显示当前默认数据状态
    current_data = load_admin_data_from_file()
    if current_data is not None:
        st.success("已加载管理员上传的默认数据")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总记录数", f"{len(current_data):,}")
        with col2:
            st.metric("渠道数量", current_data['pid'].nunique())
        with col3:
            st.metric("月份数量", current_data['月份'].nunique())
        with col4:
            # 计算数据时间范围
            months = sorted(current_data['月份'].unique())
            if months:
                time_range = f"{months[0]} 至 {months[-1]}"
                st.metric("时间范围", time_range)
        
        # 显示数据预览
        with st.expander("查看当前默认数据预览", expanded=False):
            preview_data = optimize_dataframe_for_preview(current_data, max_rows=10)
            st.dataframe(preview_data, use_container_width=True)
            
        # 提供清除选项
        if st.button("清除管理员数据（恢复示例数据）", help="清除后将使用系统示例数据"):
            # 删除本地文件
            try:
                if os.path.exists(ADMIN_DATA_FILE):
                    os.remove(ADMIN_DATA_FILE)
                # 清除缓存
                st.cache_data.clear()
            except:
                pass
            st.success("已清除管理员数据，恢复为系统示例数据")
            st.rerun()
    else:
        st.info("当前使用系统示例数据")
        sample_data = get_sample_arpu_data()
        st.metric("示例数据记录数", f"{len(sample_data):,}")
    
    # 文件上传区域
    st.markdown("---")
    st.markdown("### 上传新的默认ARPU数据")
    
    uploaded_default_file = st.file_uploader(
        "选择包含完整ARPU历史数据的Excel文件",
        type=['xlsx', 'xls'],
        help="上传后将永久保存为系统默认数据，供所有用户使用",
        key="admin_default_arpu_upload"
    )
    
    if uploaded_default_file:
        try:
            with st.spinner("正在读取和验证Excel文件..."):
                # 优化的Excel读取
                uploaded_df = pd.read_excel(uploaded_default_file, engine='openpyxl')
                
                # 验证必需列
                required_cols = ['月份', 'pid', 'stat_date', 'instl_user_cnt', 'ad_all_rven_1d_m']
                missing_cols = [col for col in required_cols if col not in uploaded_df.columns]
                
                if missing_cols:
                    st.error(f"文件缺少必需列: {', '.join(missing_cols)}")
                    st.info("文件包含的列: " + ", ".join(uploaded_df.columns.tolist()))
                    return None
                
                # 数据清理和格式化
                uploaded_df['pid'] = uploaded_df['pid'].astype(str).str.replace('.0', '', regex=False)
                uploaded_df['月份'] = uploaded_df['月份'].astype(str)
                
                # 基本数据验证
                if len(uploaded_df) == 0:
                    st.error("文件为空，请检查数据")
                    return None
                
                # 显示数据概览
                st.success(f"文件读取成功！包含 {len(uploaded_df):,} 条记录")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("总记录数", f"{len(uploaded_df):,}")
                with col2:
                    st.metric("渠道数量", uploaded_df['pid'].nunique())
                with col3:
                    st.metric("月份数量", uploaded_df['月份'].nunique())
                with col4:
                    # 数据时间范围
                    months = sorted(uploaded_df['月份'].unique())
                    if months:
                        time_range = f"{months[0]} 至 {months[-1]}"
                        st.metric("时间范围", time_range)
                
                # 显示数据预览
                st.markdown("**数据预览：**")
                preview_uploaded = optimize_dataframe_for_preview(uploaded_df, max_rows=10)
                st.dataframe(preview_uploaded, use_container_width=True)
                
                # 数据质量检查
                st.markdown("**数据质量检查：**")
                quality_checks = []
                
                # 检查空值
                null_counts = uploaded_df[required_cols].isnull().sum()
                if null_counts.sum() > 0:
                    quality_checks.append(f"发现空值: {dict(null_counts[null_counts > 0])}")
                else:
                    quality_checks.append("无空值")
                
                # 检查数值列
                numeric_cols = ['instl_user_cnt', 'ad_all_rven_1d_m']
                for col in numeric_cols:
                    try:
                        uploaded_df[col] = pd.to_numeric(uploaded_df[col], errors='coerce')
                        invalid_count = uploaded_df[col].isnull().sum()
                        if invalid_count > 0:
                            quality_checks.append(f"{col} 列有 {invalid_count} 个无效数值")
                        else:
                            quality_checks.append(f"{col} 列数值格式正确")
                    except:
                        quality_checks.append(f"{col} 列数值格式错误")
                
                # 显示质量检查结果
                for check in quality_checks:
                    if "无空值" in check or "数值格式正确" in check:
                        st.success(check)
                    elif "发现空值" in check or "无效数值" in check:
                        st.warning(check)
                    else:
                        st.error(check)
                
                # 确认上传按钮
                st.markdown("---")
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if st.button("确认设置为默认数据", type="primary", use_container_width=True):
                        # 永久保存到本地文件
                        if save_admin_data_to_file(uploaded_df):
                            # 清除缓存
                            st.cache_data.clear()
                            st.success("默认ARPU数据已永久保存！")
                            st.info("该数据现在将作为系统默认数据使用，所有用户都可以访问，且服务重启后仍然有效")
                        else:
                            st.warning("文件保存失败")
                        st.rerun()
                
                with col2:
                    # 提供下载清理后数据的选项
                    cleaned_csv = uploaded_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="下载清理后的数据",
                        data=cleaned_csv.encode('utf-8-sig'),
                        file_name=f"cleaned_arpu_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                return uploaded_df
                
        except Exception as e:
            st.error(f"文件处理失败：{str(e)}")
            st.info("请确保文件格式正确，包含所有必需列")
            return None
    
    return None

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

# ==================== 智能匹配函数 ====================
def calculate_similarity(str1, str2):
    """计算两个字符串的相似度（0-1之间，1表示完全相同）"""
    return difflib.SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def find_best_match(file_name, channel_mapping, threshold=0.6):
    """找到文件名的最佳匹配渠道名称"""
    best_match = None
    best_score = 0
    
    for channel_name in channel_mapping.keys():
        score = calculate_similarity(file_name, channel_name)
        if score > best_score and score >= threshold:
            best_score = score
            best_match = channel_name
    
    return best_match, best_score

def get_file_channel_suggestions(uploaded_files, channel_mapping):
    """获取文件的渠道名称建议"""
    suggestions = {}
    
    for uploaded_file in uploaded_files:
        file_name = os.path.splitext(uploaded_file.name)[0].strip()
        
        # 直接检查是否完全匹配
        if file_name in channel_mapping:
            continue
            
        # 检查是否是渠道号
        reverse_mapping = create_reverse_mapping(channel_mapping)
        if file_name in reverse_mapping:
            continue
            
        # 检查包含关系
        found_exact = False
        for channel_name in channel_mapping.keys():
            if channel_name in file_name or file_name in channel_name:
                found_exact = True
                break
                
        if found_exact:
            continue
            
        # 相似度匹配
        best_match, score = find_best_match(file_name, channel_mapping)
        if best_match:
            suggestions[file_name] = {
                'suggested_channel': best_match,
                'similarity_score': score,
                'file_object': uploaded_file
            }
    
    return suggestions

@st.cache_data
def parse_channel_mapping_from_excel(channel_file_content):
    """从上传的Excel文件解析渠道映射"""
    try:
        df = pd.read_excel(io.BytesIO(channel_file_content))
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

# ==================== OCPX数据合并函数 ====================
def merge_ocpx_data(retention_data, new_users_data, target_month):
    """合并OCPX格式的留存数据和新增数据
    
    Args:
        retention_data: ocpx监测留存数 sheet数据
        new_users_data: 监测渠道回传量 sheet数据  
        target_month: 目标月份 (YYYY-MM格式)
    
    Returns:
        合并后的DataFrame或None
    """
    try:
        # 处理新增数据 - 从"监测渠道回传量"sheet
        new_users_clean = new_users_data.copy()
        
        # 查找"日期"和"回传新增数"列
        date_col = None
        new_users_col = None
        
        # 精确匹配列名
        for col in new_users_clean.columns:
            col_str = str(col).strip()
            if col_str == '日期':
                date_col = col
            elif col_str == '回传新增数':
                new_users_col = col
        
        if date_col is None:
            # 模糊匹配日期列
            for col in new_users_clean.columns:
                if '日期' in str(col) or 'date' in str(col).lower():
                    date_col = col
                    break
                    
        if new_users_col is None:
            # 模糊匹配新增数列
            for col in new_users_clean.columns:
                if '回传新增数' in str(col) or '新增' in str(col):
                    new_users_col = col
                    break
        
        if date_col is None or new_users_col is None:
            st.error('监测渠道回传量表格式不正确，请检查是否包含"日期"和"回传新增数"列')
            return None
        
        # 清理新增数据
        new_users_dict = {}
        for _, row in new_users_clean.iterrows():
            try:
                date_val = row[date_col]
                
                # 跳过无效行
                if pd.isna(date_val) or str(date_val).strip().lower() in ['合计', 'total', '汇总', '小计', '', 'nan']:
                    continue
                
                # 标准化日期格式
                date_str = None
                if isinstance(date_val, str):
                    date_str = date_val.strip()
                    try:
                        parsed_date = pd.to_datetime(date_str)
                        date_str = parsed_date.strftime('%Y-%m-%d')
                    except:
                        pass
                else:
                    try:
                        date_str = pd.to_datetime(date_val).strftime('%Y-%m-%d')
                    except:
                        date_str = str(date_val)
                
                if date_str:
                    new_users_count = safe_convert_to_numeric(row[new_users_col])
                    if new_users_count > 0:
                        new_users_dict[date_str] = new_users_count
                        
            except Exception as e:
                continue
        
        # 处理留存数据 - 从"ocpx监测留存数"sheet
        retention_clean = retention_data.copy()
        
        # 查找"留存天数"列作为日期列
        retention_date_col = None
        for col in retention_clean.columns:
            col_str = str(col).strip()
            if col_str == '留存天数':
                retention_date_col = col
                break
        
        if retention_date_col is None:
            # 模糊匹配日期列
            for col in retention_clean.columns:
                col_str = str(col).lower()
                if '日期' in col_str or 'date' in col_str or '天数' in col_str:
                    retention_date_col = col
                    break
        
        if retention_date_col is None:
            st.error('ocpx监测留存数表格式不正确，请检查是否包含"留存天数"列')
            return None
        
        # 合并数据
        merged_data = []
        
        for _, row in retention_clean.iterrows():
            try:
                date_val = row[retention_date_col]
                
                # 跳过无效行
                if pd.isna(date_val) or str(date_val).strip().lower() in ['合计', 'total', '汇总', '小计', '', 'nan']:
                    continue
                
                # 标准化日期格式
                date_str = None
                if isinstance(date_val, str):
                    date_str = date_val.strip()
                    try:
                        parsed_date = pd.to_datetime(date_str)
                        date_str = parsed_date.strftime('%Y-%m-%d')
                    except:
                        pass
                else:
                    try:
                        date_str = pd.to_datetime(date_val).strftime('%Y-%m-%d')
                    except:
                        date_str = str(date_val)
                
                if not date_str:
                    continue
                
                # 检查是否在目标月份
                if target_month and not date_str.startswith(target_month):
                    continue
                
                # 构建合并后的行数据
                merged_row = {
                    'date': date_str,
                    'stat_date': date_str,
                    '日期': date_str,
                    '回传新增数': new_users_dict.get(date_str, 0)
                }
                
                # 添加留存数据（1、2、3...列）
                retention_found = False
                for col in retention_clean.columns:
                    col_str = str(col).strip()
                    # 检查是否是数字列名（1、2、3...）
                    if col_str.isdigit() and 1 <= int(col_str) <= 30:
                        retain_value = safe_convert_to_numeric(row[col])
                        merged_row[col_str] = retain_value
                        retention_found = True
                
                if retention_found:
                    merged_data.append(merged_row)
                    
            except Exception as e:
                continue
        
        if merged_data:
            result_df = pd.DataFrame(merged_data)
            st.success(f"OCPX数据合并成功，共处理 {len(result_df)} 条记录")
            return result_df
        else:
            st.warning(f"未找到目标月份 {target_month} 的有效数据")
            return None
            
    except Exception as e:
        st.error(f"处理OCPX数据时出错：{str(e)}")
        return None

# ==================== 文件整合核心函数 - 支持OCPX新格式 - 优化版本 ====================
@st.cache_data
def integrate_excel_files_cached_with_mapping(file_names, file_contents, target_month, channel_mapping, confirmed_mappings):
    """缓存版本的文件整合函数 - 支持OCPX新格式和智能映射 - 优化版本"""
    all_data = pd.DataFrame()
    processed_count = 0
    mapping_warnings = []

    for i, (file_name, file_content) in enumerate(zip(file_names, file_contents)):
        # 从文件名中提取渠道名称（去除扩展名和多余空格）
        source_name = os.path.splitext(file_name)[0].strip()
        
        # 渠道映射处理 - 支持用户确认的智能匹配
        mapped_source = source_name  # 默认使用文件名
        
        # 第一优先级：检查是否有用户确认的智能匹配
        if source_name in confirmed_mappings:
            mapped_source = confirmed_mappings[source_name]
        # 第二优先级：直接检查文件名是否在渠道映射的键中
        elif source_name in channel_mapping:
            mapped_source = source_name
        else:
            # 第三优先级：检查文件名是否是某个渠道的渠道号
            reverse_mapping = create_reverse_mapping(channel_mapping)
            if source_name in reverse_mapping:
                mapped_source = reverse_mapping[source_name]
            else:
                # 第四优先级：模糊匹配 - 检查文件名是否包含渠道名称
                found_match = False
                for channel_name in channel_mapping.keys():
                    if channel_name in source_name or source_name in channel_name:
                        mapped_source = channel_name
                        found_match = True
                        break
                
                if not found_match:
                    # 如果都不匹配，保持原文件名并记录警告
                    mapping_warnings.append(f"文件 '{source_name}' 未在渠道映射表中找到对应项")

        try:
            # 从内存中读取Excel文件 - 优化读取方式
            file_data = None
            
            with io.BytesIO(file_content) as buffer:
                xls = pd.ExcelFile(buffer, engine='openpyxl')
                sheet_names = xls.sheet_names

                # 查找OCPX格式的工作表 - 精确匹配
                retention_sheet = None
                new_users_sheet = None
                
                # 查找留存数据表 - 精确匹配"ocpx监测留存数"
                for sheet in sheet_names:
                    if sheet.strip() == "ocpx监测留存数":
                        retention_sheet = sheet
                        break
                
                # 查找新增数据表 - 精确匹配"监测渠道回传量"
                for sheet in sheet_names:
                    if sheet.strip() == "监测渠道回传量":
                        new_users_sheet = sheet
                        break
                
                # 如果找到OCPX格式的表，使用新的处理方法
                if retention_sheet and new_users_sheet:
                    try:
                        # 处理OCPX格式数据
                        retention_data = pd.read_excel(buffer, sheet_name=retention_sheet, engine='openpyxl')
                        new_users_data = pd.read_excel(buffer, sheet_name=new_users_sheet, engine='openpyxl')
                        
                        # 合并OCPX数据
                        file_data = merge_ocpx_data(retention_data, new_users_data, target_month)
                        if file_data is not None and not file_data.empty:
                            file_data.insert(0, '数据来源', mapped_source)
                            all_data = pd.concat([all_data, file_data], ignore_index=True)
                            processed_count += 1
                        continue
                    except Exception as e:
                        st.warning(f"OCPX格式处理失败，将尝试传统格式：{str(e)}")
                
                # 如果只找到留存数据表，按原有方式处理
                if retention_sheet:
                    try:
                        file_data = pd.read_excel(buffer, sheet_name=retention_sheet, engine='openpyxl')
                    except:
                        file_data = pd.read_excel(buffer, sheet_name=0, engine='openpyxl')
                else:
                    # 使用第一个工作表
                    file_data = pd.read_excel(buffer, sheet_name=0, engine='openpyxl')
            
            if file_data is not None and not file_data.empty:
                # 传统格式数据处理逻辑 - 增强兼容性
                file_data_copy = file_data.copy()
                
                # 检测并处理数据格式
                has_stat_date = 'stat_date' in file_data_copy.columns
                retain_columns = [f'new_retain_{i}' for i in range(1, 31)]
                has_retain_columns = any(col in file_data_copy.columns for col in retain_columns)

                if has_stat_date and has_retain_columns:
                    # 传统格式表处理（stat_date + new + new_retain_X格式）
                    standardized_data = file_data_copy.copy()
                    
                    # 处理新增数据列 - 增强匹配
                    new_col_found = False
                    for col in ['new', '新增', '新增用户', 'users']:
                        if col in standardized_data.columns:
                            standardized_data['回传新增数'] = standardized_data[col].apply(safe_convert_to_numeric)
                            new_col_found = True
                            break
                    
                    if not new_col_found:
                        if len(standardized_data.columns) > 1:
                            standardized_data['回传新增数'] = standardized_data.iloc[:, 1].apply(safe_convert_to_numeric)
                        else:
                            continue

                    # 处理留存数据列：new_retain_1 -> 1, new_retain_2 -> 2, ...
                    for i in range(1, 31):
                        retain_col = f'new_retain_{i}'
                        if retain_col in standardized_data.columns:
                            standardized_data[str(i)] = standardized_data[retain_col].apply(safe_convert_to_numeric)

                    # 处理日期列 - 增强日期处理
                    date_col = 'stat_date'
                    try:
                        standardized_data[date_col] = pd.to_datetime(standardized_data[date_col], errors='coerce')
                        standardized_data[date_col] = standardized_data[date_col].dt.strftime('%Y-%m-%d')
                        standardized_data['日期'] = standardized_data[date_col]
                        standardized_data['month'] = standardized_data[date_col].str[:7]
                    except:
                        continue

                    # 按目标月份筛选数据
                    filtered_data = standardized_data[standardized_data['month'] == target_month].copy()

                    if not filtered_data.empty:
                        filtered_data.insert(0, '数据来源', mapped_source)
                        if 'stat_date' in filtered_data.columns:
                            filtered_data['date'] = filtered_data['stat_date']
                        all_data = pd.concat([all_data, filtered_data], ignore_index=True)
                        processed_count += 1
                else:
                    # 其他格式表处理（兼容老版本） - 增强处理
                    
                    # 查找关键列 - 增强匹配
                    report_users_col = None
                    users_keywords = ['回传新增数', 'new', '新增', '用户数', '新增用户']
                    for col in file_data_copy.columns:
                        col_str = str(col).lower()
                        if any(keyword.lower() in col_str for keyword in users_keywords):
                            report_users_col = col
                            break

                    if report_users_col:
                        file_data_copy['回传新增数'] = file_data_copy[report_users_col].apply(safe_convert_to_numeric)
                    else:
                        # 使用第二列作为新增数
                        if len(file_data_copy.columns) > 1:
                            file_data_copy['回传新增数'] = file_data_copy.iloc[:, 1].apply(safe_convert_to_numeric)

                    # 确保数字列名（1、2、3...）被正确处理
                    for i in range(1, 31):
                        col_name = str(i)
                        if col_name in file_data_copy.columns:
                            file_data_copy[col_name] = file_data_copy[col_name].apply(safe_convert_to_numeric)

                    # 处理日期列 - 增强匹配
                    date_col = None
                    date_keywords = ['日期', 'date', '时间', '统计日期', 'stat_date']
                    for col in file_data_copy.columns:
                        col_str = str(col).lower()
                        if any(keyword.lower() in col_str for keyword in date_keywords):
                            date_col = col
                            break

                    if date_col:
                        try:
                            file_data_copy[date_col] = pd.to_datetime(file_data_copy[date_col], errors='coerce')
                            file_data_copy['month'] = file_data_copy[date_col].dt.strftime('%Y-%m')
                            filtered_data = file_data_copy[file_data_copy['month'] == target_month].copy()
                        except:
                            # 如果日期处理失败，尝试字符串截取
                            file_data_copy['month'] = file_data_copy[date_col].apply(
                                lambda x: str(x)[:7] if isinstance(x, str) and len(str(x)) >= 7 else None
                            )
                            filtered_data = file_data_copy[file_data_copy['month'] == target_month].copy()
                    else:
                        # 如果没找到日期列，使用所有数据
                        filtered_data = file_data_copy.copy()

                    if not filtered_data.empty:
                        filtered_data.insert(0, '数据来源', mapped_source)
                        if date_col and date_col != 'date':
                            filtered_data['date'] = filtered_data[date_col]
                        all_data = pd.concat([all_data, filtered_data], ignore_index=True)
                        processed_count += 1

        except Exception as e:
            st.error(f"处理文件 {file_name} 时出错: {str(e)}")
        finally:
            # 清理内存
            gc.collect()

    return all_data, processed_count, mapping_warnings

def integrate_excel_files_streamlit(uploaded_files, target_month=None, channel_mapping=None, confirmed_mappings=None):
    """优化性能的文件整合函数，支持用户确认的智能映射"""
    if target_month is None:
        target_month = get_default_target_month()

    # 使用传入的渠道映射，如果没有则使用默认映射
    if channel_mapping is None:
        channel_mapping = DEFAULT_CHANNEL_MAPPING
    
    # 如果没有确认映射，初始化为空字典
    if confirmed_mappings is None:
        confirmed_mappings = {}

    # 准备缓存数据 - 优化内存使用
    file_names = [f.name for f in uploaded_files]
    file_contents = []
    
    # 分批读取文件内容，避免内存过载
    for f in uploaded_files:
        file_contents.append(f.read())
    
    return integrate_excel_files_cached_with_mapping(file_names, file_contents, target_month, channel_mapping, confirmed_mappings)

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

# ==================== 单渠道图表生成函数 - 避免中文标题 ====================
def create_individual_channel_chart(channel_name, curve_data, original_data, max_days=100, lt_2y=None, lt_5y=None):
    """创建单个渠道的100天LT拟合图表 - 避免中文标题显示问题，添加2年5年LT显示"""
    
    # 使用英文字体设置
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
        label='Fitted Curve',
        zorder=2
    )
    
    # 设置图表样式 - 使用英文标题避免中文显示问题
    ax.set_xlim(0, max_days)
    ax.set_ylim(0, 0.6)
    
    ax.set_xlabel('Retention Days', fontsize=12)
    ax.set_ylabel('Retention Rate', fontsize=12)
    # 使用简洁的英文标题，避免中文显示问题
    ax.set_title(f'{max_days}-Day LT Fitting Analysis', fontsize=14, fontweight='bold')
    
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.legend(fontsize=10)
    
    # 设置Y轴刻度为百分比
    y_ticks = [0, 0.15, 0.3, 0.45, 0.6]
    y_labels = ['0%', '15%', '30%', '45%', '60%']
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    
    plt.tight_layout()
    return fig

# ==================== 【修复】加载5月后ARPU数据函数 ====================
@st.cache_data
def load_user_arpu_data_after_april(uploaded_file_content, builtin_df):
    """【修复版】加载用户上传的5月及之后的ARPU数据，并与内置数据合并"""
    try:
        # 读取用户上传的Excel文件
        user_df = pd.read_excel(io.BytesIO(uploaded_file_content), engine='openpyxl')
        
        # 检查必需列
        required_cols = ['pid', 'instl_user_cnt', 'ad_all_rven_1d_m']
        missing_cols = [col for col in required_cols if col not in user_df.columns]
        
        if missing_cols:
            return None, f"文件缺少必需列: {', '.join(missing_cols)}"
        
        # 数据清理和格式化
        user_df['pid'] = user_df['pid'].astype(str).str.replace('.0', '', regex=False)
        
        # 筛选5月及之后的数据 - 增强日期处理
        user_df_filtered = None
        
        if '月份' in user_df.columns:
            # 使用月份列筛选
            try:
                user_df['月份'] = user_df['月份'].astype(str)
                # 标准化月份格式
                user_df['month_standard'] = user_df['月份'].apply(lambda x: x[:7] if len(str(x)) >= 7 else str(x))
                
                # 筛选2025年5月及之后的数据
                user_df_filtered = user_df[user_df['month_standard'] >= '2025-05'].copy()
                
                if len(user_df_filtered) == 0:
                    return None, "未找到2025年5月及之后的数据，请检查月份格式"
                    
            except Exception as e:
                return None, f"处理月份列时出错：{str(e)}"
                
        elif 'stat_date' in user_df.columns:
            # 使用日期列筛选
            try:
                user_df['stat_date'] = pd.to_datetime(user_df['stat_date'], errors='coerce')
                # 筛选2025年5月及之后的数据
                april_2025_end = pd.to_datetime('2025-04-30')
                user_df_filtered = user_df[user_df['stat_date'] > april_2025_end].copy()
                
                if len(user_df_filtered) == 0:
                    return None, "未找到2025年5月及之后的数据，请检查日期格式"
                    
                # 添加月份列以便后续处理
                user_df_filtered['月份'] = user_df_filtered['stat_date'].dt.strftime('%Y-%m')
                
            except Exception as e:
                return None, f"处理stat_date列时出错：{str(e)}"
        else:
            return None, "未找到月份或stat_date列进行筛选"
        
        if user_df_filtered is None or len(user_df_filtered) == 0:
            return None, "筛选后无有效数据"
        
        # 数据验证
        numeric_cols = ['instl_user_cnt', 'ad_all_rven_1d_m']
        for col in numeric_cols:
            user_df_filtered[col] = pd.to_numeric(user_df_filtered[col], errors='coerce')
            # 移除无效数值行
            user_df_filtered = user_df_filtered.dropna(subset=[col])
        
        if len(user_df_filtered) == 0:
            return None, "数据清理后无有效记录"
        
        # 合并内置数据和用户数据
        # 确保列格式一致
        if 'month_standard' in user_df_filtered.columns:
            user_df_filtered = user_df_filtered.drop('month_standard', axis=1)
        
        # 确保两个DataFrame有相同的列
        builtin_cols = set(builtin_df.columns)
        user_cols = set(user_df_filtered.columns)
        
        # 只保留公共列
        common_cols = list(builtin_cols & user_cols)
        if not common_cols:
            return None, "内置数据与用户数据无公共列"
        
        builtin_subset = builtin_df[common_cols].copy()
        user_subset = user_df_filtered[common_cols].copy()
        
        # 合并数据
        combined_df = pd.concat([builtin_subset, user_subset], ignore_index=True)
        
        # 去重处理（如果有重复的月份+pid组合，保留用户数据）
        if '月份' in combined_df.columns and 'pid' in combined_df.columns:
            combined_df = combined_df.drop_duplicates(subset=['月份', 'pid'], keep='last')
        
        return combined_df, f"数据合并成功，新增 {len(user_df_filtered)} 条记录"
        
    except Exception as e:
        return None, f"处理文件时出错：{str(e)}"

# ==================== ARPU计算函数优化版本 ====================
def calculate_arpu_optimized(filtered_arpu_df, channel_mapping, batch_size=1000):
    """优化的ARPU计算函数，分批处理大数据，支持特殊渠道计算"""
    try:
        # 确保pid为字符串格式
        filtered_arpu_df['pid'] = filtered_arpu_df['pid'].astype(str).str.replace('.0', '', regex=False)
        
        # 数据清理 - 确保数值列为数值类型
        numeric_cols = ['instl_user_cnt', 'ad_all_rven_1d_m']
        for col in numeric_cols:
            filtered_arpu_df[col] = pd.to_numeric(filtered_arpu_df[col], errors='coerce')
        
        # 移除无效数据
        filtered_arpu_df = filtered_arpu_df.dropna(subset=numeric_cols)
        filtered_arpu_df = filtered_arpu_df[
            (filtered_arpu_df['instl_user_cnt'] > 0) & 
            (filtered_arpu_df['ad_all_rven_1d_m'] >= 0)
        ]
        
        if len(filtered_arpu_df) == 0:
            return None, "数据清理后无有效记录"
        
        # 创建反向渠道映射
        reverse_mapping = create_reverse_mapping(channel_mapping)
        
        # 分批处理数据以避免内存问题
        arpu_results = []
        
        # 先计算所有有渠道号的渠道
        for pid, group in filtered_arpu_df.groupby('pid'):
            if pid in reverse_mapping:
                channel_name = reverse_mapping[pid]
                
                # 分批处理大组
                for i in range(0, len(group), batch_size):
                    batch = group.iloc[i:i+batch_size]
                    
                    total_users = batch['instl_user_cnt'].sum()
                    total_revenue = batch['ad_all_rven_1d_m'].sum()
                    
                    if total_users > 0:
                        arpu_results.append({
                            'data_source': channel_name,
                            'total_users': total_users,
                            'total_revenue': total_revenue,
                            'record_count': len(batch)
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
            
            # 计算总体数据（所有渠道的总和）
            total_users_sum = sum(data['total_users'] for data in final_arpu.values())
            total_revenue_sum = sum(data['total_revenue'] for data in final_arpu.values())
            total_record_count = sum(data['record_count'] for data in final_arpu.values())
            
            if total_users_sum > 0:
                final_arpu['总体'] = {
                    'total_users': total_users_sum,
                    'total_revenue': total_revenue_sum,
                    'record_count': total_record_count
                }
            
            # 计算安卓数据（总体减去iPhone）
            iphone_data = final_arpu.get('iPhone', {'total_users': 0, 'total_revenue': 0, 'record_count': 0})
            android_users = total_users_sum - iphone_data['total_users']
            android_revenue = total_revenue_sum - iphone_data['total_revenue']
            android_records = total_record_count - iphone_data['record_count']
            
            if android_users > 0:
                final_arpu['安卓'] = {
                    'total_users': android_users,
                    'total_revenue': android_revenue,
                    'record_count': android_records
                }
            
            # 重新计算ARPU
            arpu_summary = []
            for channel, data in final_arpu.items():
                arpu_value = data['total_revenue'] / data['total_users'] if data['total_users'] > 0 else 0
                arpu_summary.append({
                    'data_source': channel,
                    'arpu_value': arpu_value,
                    'record_count': data['record_count'],
                    'total_users': data['total_users'],
                    'total_revenue': data['total_revenue']
                })
            
            arpu_summary_df = pd.DataFrame(arpu_summary)
            return arpu_summary_df, "ARPU计算完成"
        else:
            return None, "未找到匹配的渠道数据，请检查渠道映射配置"
            
    except Exception as e:
        return None, f"ARPU计算失败：{str(e)}"

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
    'visualization_data_5y', 'original_data', 'show_custom_mapping',
    'file_channel_confirmations'
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
if st.session_state.show_custom_mapping is None:
    st.session_state.show_custom_mapping = False

# ==================== 分析步骤定义 ====================
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
        <div class="principle-title">LT模型构建原理</div>
        <div class="principle-content">
        LT模型构建包含四个核心步骤：<br>
        <strong>1. 数据上传汇总：</strong>整合多个Excel文件，支持新格式表和传统格式表<br>
        <strong>2. 异常剔除：</strong>按需清理异常数据，提高模型准确性<br>
        <strong>3. 留存率计算：</strong>OCPX格式表按渠道计算，各天留存列（1、2、3...）平均值÷回传新增数平均值<br>
        <strong>4. LT拟合分析：</strong>采用三阶段分层建模，预测用户生命周期长度
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 步骤1：数据上传与汇总 - 始终显示
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("1. 数据上传与汇总")
    
    # 默认渠道映射 - 默认展开
    st.subheader("渠道映射配置")
    with st.expander("默认渠道映射（请按渠道名称命名文件）", expanded=True):
        st.markdown("""
        <div class="step-tip">
            <div class="step-tip-title">重要提示</div>
            <div class="step-tip-content">
            <strong>文件命名规则：</strong>请将Excel文件按照下表中的<strong>渠道名称</strong>进行命名<br>
            例如：<code>鼎乐-盛世7.xlsx</code> <code>华为.xlsx</code><br>
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
    if not st.session_state.show_custom_mapping:
        if st.button("需要上传自定义渠道映射", use_container_width=True):
            st.session_state.show_custom_mapping = True
            st.rerun()
        st.info("如无需自定义渠道映射，可直接进行数据上传")
    else:
        st.markdown("### 上传自定义渠道映射文件")
        channel_mapping_file = st.file_uploader(
            "选择渠道映射Excel文件",
            type=['xlsx', 'xls'],
            help="格式：第一列为渠道名称，后续列为对应的渠道号",
            key="custom_channel_mapping"
        )
        
        if channel_mapping_file:
            try:
                file_content = channel_mapping_file.read()
                custom_mapping = parse_channel_mapping_from_excel(file_content)
                if custom_mapping and isinstance(custom_mapping, dict) and len(custom_mapping) > 0:
                    st.session_state.channel_mapping = custom_mapping
                    st.success(f"自定义渠道映射加载成功！共包含 {len(custom_mapping)} 个渠道")
                    
                    # 自动展开映射详情
                    with st.expander("查看自定义渠道映射详情", expanded=True):
                        mapping_rows = []
                        for channel_name, pids in custom_mapping.items():
                            for pid in pids:
                                mapping_rows.append({'渠道名称': channel_name, '渠道号': pid})
                        mapping_df = pd.DataFrame(mapping_rows)
                        st.dataframe(mapping_df, use_container_width=True)
                else:
                    st.error("渠道映射文件解析失败，将使用默认映射")
            except Exception as e:
                st.error(f"读取渠道映射文件时出错：{str(e)}")
        else:
            st.info("请上传自定义渠道映射文件")

    # 显示当前渠道映射摘要
    with st.expander("查看当前渠道映射摘要", expanded=False):
        current_channels = list(st.session_state.channel_mapping.keys())
        st.markdown(f"**当前共有 {len(current_channels)} 个渠道：**")
        channels_text = "、".join(current_channels)
        st.text(channels_text)

    # 数据上传界面 - 默认展开
    st.markdown("### 数据文件上传")
    
    # 数据文件上传
    uploaded_files = st.file_uploader(
        "选择Excel数据文件",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        help="支持OCPX分离式格式（监测渠道回传量+ocpx监测留存数）和传统格式"
    )
    
    # 添加格式说明
    st.markdown("""
    <div class="step-tip">
        <div class="step-tip-title">支持的Excel格式</div>
        <div class="step-tip-content">
        <strong>OCPX分离式格式（推荐）：</strong><br>
        • Sheet1: "监测渠道回传量" - 包含"日期"和"回传新增数"列<br>
        • Sheet2: "ocpx监测留存数" - 包含"留存天数"列和留存数据（列名：1、2、3...）<br><br>
        <strong>传统格式：</strong><br>
        • 列名格式：<strong>stat_date</strong>（日期）、<strong>new</strong>（新增数）、<strong>new_retain_1、new_retain_2...</strong>（留存数）<br>
        • 系统自动将new_retain_X转换为标准列名1、2、3...<br><br>
        <strong>兼容格式：</strong><br>
        • 系统会尝试自动识别其他格式的Excel文件
        </div>
    </div>
    """, unsafe_allow_html=True)

    default_month = get_default_target_month()
    target_month = st.text_input("目标月份 (YYYY-MM)", value=default_month)

    if uploaded_files:
        st.info(f"已选择 {len(uploaded_files)} 个文件")
        
        # 检查是否需要渠道名称确认
        suggestions = get_file_channel_suggestions(uploaded_files, st.session_state.channel_mapping)
        
        # 初始化变量
        confirmed_mappings = {}
        process_button_key = "process_data_direct"
        
        if suggestions:
            st.markdown("### 📋 渠道名称确认")
            st.markdown("""
            <div class="step-tip">
                <div class="step-tip-title">智能匹配结果</div>
                <div class="step-tip-content">
                系统检测到以下文件名未完全匹配渠道名称，为您推荐了最相似的渠道。请确认是否正确：
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 初始化确认状态
            if 'file_channel_confirmations' not in st.session_state:
                st.session_state.file_channel_confirmations = {}
            
            all_confirmed = True
            
            for file_name, suggestion in suggestions.items():
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.markdown(f"**文件：** `{file_name}.xlsx`")
                
                with col2:
                    suggested_channel = suggestion['suggested_channel']
                    similarity_score = suggestion['similarity_score']
                    st.markdown(f"**建议渠道：** {suggested_channel}")
                    st.caption(f"相似度: {similarity_score:.2%}")
                
                with col3:
                    confirm_key = f"confirm_{file_name}"
                    if confirm_key not in st.session_state.file_channel_confirmations:
                        if st.button("✅ 确认", key=f"btn_confirm_{file_name}", use_container_width=True):
                            st.session_state.file_channel_confirmations[confirm_key] = suggested_channel
                            st.rerun()
                        all_confirmed = False
                    else:
                        confirmed_channel = st.session_state.file_channel_confirmations[confirm_key]
                        st.success(f"✅ 已确认为: {confirmed_channel}")
                        confirmed_mappings[file_name] = confirmed_channel
                
                st.markdown("---")
            
            if not all_confirmed:
                st.info("请确认所有文件的渠道名称后再继续处理数据")
                return
            
            # 所有文件都已确认，可以处理数据
            st.success("✅ 所有文件渠道名称已确认，可以开始处理数据")
            process_button_key = "process_data_with_confirmations"

        if st.button("开始处理数据", type="primary", use_container_width=True, key=process_button_key):
            with st.spinner("正在处理数据文件..."):
                try:
                    merged_data, processed_count, mapping_warnings = integrate_excel_files_streamlit(
                        uploaded_files, target_month, st.session_state.channel_mapping, confirmed_mappings
                    )

                    if merged_data is not None and not merged_data.empty:
                        st.session_state.merged_data = merged_data
                        # 清除确认状态，为下次使用做准备
                        if 'file_channel_confirmations' in st.session_state:
                            del st.session_state.file_channel_confirmations
                        
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

                        # 显示文件匹配情况
                        st.subheader("文件匹配情况")
                        unique_sources = merged_data['数据来源'].unique()
                        match_info = []
                        for source in unique_sources:
                            # 检查是否在映射中
                            is_in_mapping = source in st.session_state.channel_mapping or source in confirmed_mappings.values()
                            match_status = '已匹配'
                            if source in confirmed_mappings.values():
                                match_status = '智能匹配'
                            elif not is_in_mapping:
                                match_status = '未匹配'
                                
                            match_info.append({
                                '文件/渠道名称': source,
                                '匹配状态': match_status,
                                '记录数': len(merged_data[merged_data['数据来源'] == source])
                            })
                        
                        match_df = pd.DataFrame(match_info)
                        st.dataframe(match_df, use_container_width=True)

                        if mapping_warnings:
                            st.warning("以下文件未在渠道映射中找到对应关系：")
                            for warning in mapping_warnings:
                                st.text(f"• {warning}")

                        # 优化的数据预览 - 每个文件显示两行
                        st.subheader("数据预览")
                        
                        for source in unique_sources:
                            source_data = merged_data[merged_data['数据来源'] == source]
                            optimized_preview = optimize_dataframe_for_preview(source_data, max_rows=2)
                            
                            # 使用浅蓝色样式显示数据来源
                            st.markdown(f"""
                            <div style="background: rgba(59, 130, 246, 0.1); 
                                       border: 1px solid rgba(59, 130, 246, 0.3); 
                                       border-radius: 6px; 
                                       padding: 0.5rem; 
                                       margin: 0.5rem 0; 
                                       color: #1e40af; 
                                       font-weight: 600;">
                                {source}
                            </div>
                            """, unsafe_allow_html=True)
                            st.dataframe(optimized_preview, use_container_width=True)
                            
                    else:
                        st.error("未找到有效数据")
                except Exception as e:
                    st.error(f"处理过程中出现错误：{str(e)}")
    else:
        st.info("请选择Excel文件开始数据处理")

    st.markdown('</div>', unsafe_allow_html=True)

    # 步骤2：异常数据剔除 - 默认展开
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("2. 异常数据剔除")
    
    if st.session_state.merged_data is not None:
        merged_data = st.session_state.merged_data
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 按数据来源剔除")
            all_sources = sorted(merged_data['数据来源'].unique().tolist())
            excluded_sources = st.multiselect(
                "选择要剔除的数据来源", 
                options=all_sources, 
                key="exclude_sources_multiselect",
                help="选择需要从分析中排除的数据来源"
            )

        with col2:
            st.markdown("### 按日期剔除")
            if 'date' in merged_data.columns:
                all_dates = sorted(merged_data['date'].unique().tolist())
                excluded_dates = st.multiselect(
                    "选择要剔除的日期", 
                    options=all_dates, 
                    key="exclude_dates_multiselect",
                    help="选择需要从分析中排除的日期"
                )
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
            else:
                st.info("无数据将被剔除")

        with col2:
            st.markdown(f"### 保留的数据 ({len(to_keep)} 条)")
            if len(to_keep) > 0:
                preview_keep = optimize_dataframe_for_preview(to_keep, max_rows=5)
                st.dataframe(preview_keep, use_container_width=True)

        if len(to_exclude) > 0:
            if st.button("确认剔除异常数据", type="primary", use_container_width=True, key="confirm_exclude_btn"):
                try:
                    excluded_dates_info = []
                    for _, row in to_exclude.iterrows():
                        source = row.get('数据来源', 'Unknown')
                        date = row.get('date', 'Unknown')
                        excluded_dates_info.append(f"{source}-{date}")
                    
                    st.session_state.excluded_data = excluded_dates_info
                    st.session_state.excluded_dates_info = excluded_dates
                    st.session_state.cleaned_data = to_keep.copy()
                    st.success(f"成功剔除 {len(to_exclude)} 条异常数据")
                except Exception as e:
                    st.error(f"剔除数据时出错: {str(e)}")
        else:
            st.info("当前筛选条件下无需剔除数据")
            # 如果没有要剔除的数据，自动设置清理后数据
            if not excluded_sources and not excluded_dates:
                st.session_state.cleaned_data = merged_data.copy()
    else:
        st.info("请先完成数据上传与汇总")

    st.markdown('</div>', unsafe_allow_html=True)

    # 步骤3：留存率计算 - 默认展开
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("3. 留存率计算")
    
    st.markdown("""
    <div class="step-tip">
        <div class="step-tip-title">OCPX格式留存率计算方法</div>
        <div class="step-tip-content">
        <strong>支持两种OCPX表格式：</strong><br>
        <strong>方式1：分离式OCPX表格</strong><br>
        • <strong>"监测渠道回传量"</strong> sheet：包含"日期"和"回传新增数"列<br>
        • <strong>"ocpx监测留存数"</strong> sheet：包含"留存天数"列和各天留存数（列名为1、2、3...30）<br>
        • 系统自动合并两个表的数据进行计算<br><br>
        <strong>方式2：传统格式表格</strong><br>
        • 列名格式：<strong>stat_date</strong>（日期）、<strong>new</strong>（新增数）、<strong>new_retain_1、new_retain_2...</strong>（留存数）<br>
        • 系统自动将new_retain_X转换为标准列名1、2、3...<br><br>
        <strong>计算公式：</strong>留存率 = 各天留存数平均值 ÷ 回传新增数平均值
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.merged_data is not None:
        # 确定使用的数据
        if st.session_state.cleaned_data is not None:
            working_data = st.session_state.cleaned_data
            st.info("使用清理后的数据进行计算")
        else:
            working_data = st.session_state.merged_data
            st.info("使用原始数据进行计算")

        data_sources = working_data['数据来源'].unique()
        selected_sources = st.multiselect("选择要分析的数据来源", options=data_sources, default=data_sources, key="retention_sources")

        if st.button("计算留存率", type="primary", use_container_width=True, key="calc_retention"):
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
    else:
        st.info("请先完成数据上传与汇总")

    st.markdown('</div>', unsafe_allow_html=True)

    # 步骤4：LT拟合分析 - 默认展开
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("4. LT拟合分析")
    
    # 渠道规则说明
    st.markdown("""
    <div class="step-tip">
        <div class="step-tip-title">三阶段拟合规则</div>
        <div class="step-tip-content">
        <strong>第一阶段：</strong>1-30天，幂函数拟合实际数据<br>
        <strong>第二阶段：</strong>31-X天，延续幂函数模型<br>
        <strong>第三阶段：</strong>Y天后，指数函数建模长期衰减<br>
        不同渠道采用不同的阶段划分点
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.retention_data is not None:
        retention_data = st.session_state.retention_data

        if st.button("开始LT拟合分析", type="primary", use_container_width=True, key="start_lt_fitting"):
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

                # 显示单渠道图表 - 100天版本，同时显示2年5年LT
                if visualization_data_5y and original_data:
                    st.subheader("各渠道100天LT拟合图表")
                    
                    # 按5年LT值排序
                    sorted_channels = sorted(visualization_data_5y.items(), key=lambda x: x[1]['lt'])
                    
                    # 每行显示2个图表
                    for i
