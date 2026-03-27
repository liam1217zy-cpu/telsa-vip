import streamlit as st
import pandas as pd
import requests
import urllib.parse
import io
import time
from typing import Optional, Dict, List, Tuple

# ============================================================================
# CONFIGURATION (Read from Streamlit Secrets)
# ============================================================================
try:
    # 为了保护安全，请确保在 Streamlit 后台 Secrets 设置好这些值
    ACCESS_PASSWORD = st.secrets["ACCESS_PASSWORD"]
    SHORTIO_API_KEY = st.secrets["SHORTIO_API_KEY"]
    SHORTIO_DOMAIN = st.secrets["SHORTIO_DOMAIN"]
except Exception:
    st.error("Missing Secrets! Please configure ACCESS_PASSWORD, SHORTIO_API_KEY, and SHORTIO_DOMAIN in Streamlit Settings.")
    st.stop()

SHORTIO_API_URL = "https://api.short.io/links"
DEFAULT_MANAGER_ID = "max_bkio"
DEFAULT_MANAGER_NAME = "Max"

# 话术模板 (EN/JP 自动匹配)
TEMPLATES = {
    "Option 1: New Registration": {
        "EN": "Hello {manager_name}, I am {username}. I've opened an account. Please help confirm if my account has VIP priority access enabled and the most stable deposit method currently.",
        "JP": "こんにちは {manager_name}、{username} です。口座を開设しました。私のカウントが VIP 优先アクセスに対応しているかと、现在最も安定した入金方法を確認してください。"
    },
    "Option 2: Retention": {
        "EN": "Hello {manager_name}, I am {username}. I haven't been online for a while. Please help check if my account status is normal and provide the latest alternative URLs.",
        "JP": "こんにちは {manager_name}、{username} です。久しぶりにログインしました。アカウントの状態が正常かどうかを確認し、最新の予备 URL を教えてください。"
    }
}

# ============================================================================
# UNICORN GUNDAM MODE UI DESIGN (White + Orange/Green Glow)
# ============================================================================
def inject_unicorn_ui():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;700&display=swap');
    
    /* 整体背景：纯白/浅灰，模拟高达白色外甲 */
    .stApp {
        background: radial-gradient(circle at 50% 100%, #f1f5f9 0%, #ffffff 100%) !important;
        font-family: 'Space Grotesk', sans-serif !important;
        color: #0f172a !important;
    }
    
    /* 标题：橙绿双色发光渐变 */
    .main-title {
        font-size: 3.8rem;
        font-weight: 800;
        letter-spacing: -2px;
        background: linear-gradient(135deg, #f97316 0%, #22c55e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0px;
        filter: drop-shadow(0 0 15px rgba(34, 197, 94, 0.2));
    }
    
    /* 玻璃卡片：精神感应框架（Psycho-Frame）边框 */
    .glass-card {
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 28px;
        padding: 3rem;
        /* 关键：橙绿渐变边框 */
        border: 2px solid;
        border-image: linear-gradient(135deg, #f97316, #22c55e) 1;
        
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.1),
                    0 0 30px rgba(34, 197, 94, 0.15); /* 绿色发光投影 */
        margin-top: 2rem;
        position: relative;
    }
    
    /* 输入框样式定制：白色底，橙色焦点边框 */
    .stTextInput>div>div>input {
        background: rgba(255, 255, 255, 0.9) !important;
        color: #0f172a !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 14px !important;
        padding: 12px 18px !important;
        transition: all 0.3s ease;
    }
    .stTextInput>div>div>input:focus {
        border-color: #f97316 !important; /* 橙色焦点 */
        box-shadow: 0 0 10px rgba(249, 115, 22, 0.2) !important;
    }
    
    /* 引导文字和标签色 */
    .stCaption, label {
        color: #64748b !important;
        font-weight: 600;
    }
    
    /* 生成按钮：绿色精神能量 */
    .stButton>button {
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
        color: #ffffff !important;
        border: none !important;
        height: 3.8rem !important;
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        letter-spacing: 1px;
        border-radius: 18px !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        box-shadow: 0 15px 25px -5px rgba(34, 197, 94, 0.4) !important;
        width: 100%;
        margin-top: 30px;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px) scale(1.01);
        box-shadow: 0 25px 35px -5px rgba(34, 197, 94, 0.5) !important;
    }
    
    /* 下载按钮美化 */
    .download-btn>div>button {
        background: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: none !important;
        height: 3rem !important;
    }
    .download-btn>div>button:hover {
        background: #f8fafc !important;
        border-color: #cbd5e1 !important;
    }

    /* 进度条绿色 */
    .stProgress>div>div>div>div {
        background-color: #22c55e !important;
    }
    
    /* 数据表格美化 */
    .stDataFrame {
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# LOGIC FUNCTIONS
# ============================================================================
def shorten_url(long_url: str) -> Tuple[Optional[str], Optional[str]]:
    headers = {"Authorization": SHORTIO_API_KEY, "Content-Type": "application/json"}
    payload = {"domain": SHORTIO_DOMAIN, "originalURL": long_url}
    try:
        response = requests.post(SHORTIO_API_URL, headers=headers, json=payload, timeout=15)
        if response.status_code in [200, 201]:
            return response.json().get("shortURL"), None
        return None, f"Error {response.status_code}"
    except Exception as e:
        return None, str(e)

# ============================================================================
# MAIN APPLICATION
# ============================================================================
def main():
    # 💎 高达独角兽 Pro 模式
    st.set_page_config(page_title="VIP Link Gen [RX-0]", page_icon="💎", layout="centered")
    inject_unicorn_ui()
    
    if 'auth' not in st.session_state: st.session_state.auth = False

    st.markdown('<h1 class="main-title">VIP LINK [RX-0]</h1>', unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#94a3b8; font-weight:600; letter-spacing:3px;'>PSYCHO-FRAME SYSTEM</p>", unsafe_allow_html=True)

    # --- 1. LOGIN (White Glass) ---
    if not st.session_state.auth:
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### 🔑 System Activation")
            pwd = st.text_input("Enter Vault Password", type="password", placeholder="System Key Required")
            if st.button("ACTIVATE SYSTEM"):
                if pwd == ACCESS_PASSWORD:
                    st.session_state.auth = True
                    st.rerun()
                else: st.error("Activation Failed. System Locked.")
            st.markdown('</div>', unsafe_allow_html=True)
        return

    # --- 2. MAIN TOOL (White Glass + Orange/Green Glow) ---
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    st.markdown("#### 👤 Manager Configuration")
    c1, c2 = st.columns(2)
    with c1:
        # 防空引导
        m_id = st.text_input("Telegram ID", placeholder="e.g. max_bkio")
        if not m_id: st.caption("⚠️ Required for Deep-Link Generation.")
    with c2:
        m_name = st.text_input("Display Name", placeholder="e.g. Max")
        if not m_name: st.caption("⚠️ Required for Customer Message.")

    st.markdown("---")
    st.markdown("#### 📂 Batch Data Processing")
    
    sc1, sc2 = st.columns(2)
    with sc1:
        scenario = st.selectbox("Scenario Strategy", ["Option 1: New Registration", "Option 2: Retention"])
    with sc2:
        file = st.file_uploader("Upload Data (CSV/XLSX)", type=['csv', 'xlsx'])

    # --- 3. PROCESSING (Green Energy Flow) ---
    if st.button("🚀 EXECUTE BULK GENERATION"):
        # 防空检查
        if not m_id or not m_name:
            st.error("🚨 CRITICAL ERROR: Telegram ID and Manager Name are empty!")
            st.toast("System Stop.")
            return
        
        if not file:
            st.warning("📋 Awaiting File Upload.")
            return

        # Data Loading
        try:
            # 根据后缀读取数据
            df = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file)
            
            # 查找核心列
            user_col = next((c for c in df.columns if 'username' in c.lower()), None)
            country_col = next((c for c in df.columns if 'country' in c.lower()), None)
            
            if not user_col:
                st.error("Column 'username' not found in file!")
                return
            
            results = []
            rows = df.to_dict('records')
            
            # 绿色进度条
            progress = st.progress(0)
            status_text = st.empty()

            for idx, row in enumerate(rows):
                # 提取用户名
                user = str(row.get(user_col, "")).strip()
                if not user or user.lower() == 'nan': continue
                
                # 自动判别语言 (JP vs Global)
                country = str(row.get(country_col, "")).upper() if country_col else "OTHER"
                lang_code = "JP" if any(x in country for x in ["JAPAN", "JP"]) else "EN"
                
                # 构建内容
                msg_template = TEMPLATES[scenario][lang_code]
                full_msg = msg_template.format(manager_name=m_name, username=user)
                
                # 安全编码链接
                encoded_msg = urllib.parse.quote(full_msg)
                long_url = f"https://t.me/{m_id}?text={encoded_msg}"
                
                # 缩短链接 (Short.io)
                short_url, err = shorten_url(long_url)
                
                # 收集结果
                results.append({
                    "Username": user,
                    "Region": "Japan 🇯🇵" if lang_code == "JP" else "Global 🌍",
                    "Short Link": short_url or "Error",
                    "Status": "✅ Success" if short_url else f"❌ {err}"
                })
                
                # 更新进度
                progress.progress((idx + 1) / len(rows))
                status_text.caption(f"Generating for: {user}...")
                # 稍微延迟防止 API 限流
                time.sleep(0.02) 

            # 显示结果表格
            res_df = pd.DataFrame(results)
            st.success("Batch Generation Complete!")
            st.dataframe(res_df, use_container_width=True)

            # --- 4. EXPORT (CSV / XLSX) ---
            st.markdown("#### 📥 Download Results")
            ec1, ec2 = st.columns(2)
            
            # Excel Download
            ex_bio = io.BytesIO()
            with pd.ExcelWriter(ex_bio, engine='openpyxl') as writer:
                res_df.to_excel(writer, index=False)
            # 使用 CSS 类美化下载按钮
            ec1.markdown('<div class="download-btn">', unsafe_allow_html=True)
            ec1.download_button("Excel (.xlsx)", ex_bio.getvalue(), "vip_links_rx0.xlsx", use_container_width=True)
            ec1.markdown('</div>', unsafe_allow_html=True)
            
            # CSV Download
            csv_data = res_df.to_csv(index=False).encode('utf-8-sig')
            ec2.markdown('<div class="download-btn">', unsafe_allow_html=True)
            ec2.download_button("CSV (.csv)", csv_data, "vip_links_rx0.csv", use_container_width=True)
            ec2.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"System Error: {e}")

    st.markdown('</div>', unsafe_allow_html=True)
    # 高达 RX-0 标识
    st.markdown("<p style='text-align:center; color:#94a3b8; margin-top:2.5rem; font-size:0.8rem;'>Secured by BK8 VIP OPS • RX-0 PSYCHO-FRAME SYSTEM</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
