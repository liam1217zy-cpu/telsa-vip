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
    ACCESS_PASSWORD = st.secrets["ACCESS_PASSWORD"]
    SHORTIO_API_KEY = st.secrets["SHORTIO_API_KEY"]
    SHORTIO_DOMAIN = st.secrets["SHORTIO_DOMAIN"]
except Exception:
    st.error("Missing Secrets Configuration in Streamlit Backend!")
    st.stop()

SHORTIO_API_URL = "https://api.short.io/links"

# 话术模板 (后台自动匹配语言)
TEMPLATES = {
    "Option 1: New Registration": {
        "EN": "Hello {manager_name}, I am {username}. I've opened an account. Please help confirm if my account has VIP priority access enabled and the most stable deposit method currently.",
        "JP": "こんにちは {manager_name}、{username} です。口座を開設しました。私のカウントが VIP 優先アクセスに対応しているかと、現在最も安定した入金方法を確認してください。"
    },
    "Option 2: Retention": {
        "EN": "Hello {manager_name}, I am {username}. I haven't been online for a while. Please help check if my account status is normal and provide the latest alternative URLs.",
        "JP": "こんにちは {manager_name}、{username} です。久しぶりにログインしました。アカウントの状態が正常かどうかを確認し、最新の予備 URL を教えてください。"
    }
}

# ============================================================================
# ULTRA MODERN UI DESIGN
# ============================================================================
def inject_ui():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    /* 整体背景：深蓝色径向渐变 */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #1e293b 0%, #0f172a 100%) !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    /* 标题：发光渐变效果 */
    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(to right, #4edea3, #2dd4bf, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0px;
        filter: drop-shadow(0 0 10px rgba(78, 222, 163, 0.3));
    }
    
    /* 玻璃卡片：带渐变边框 */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 2.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        margin-top: 1.5rem;
        transition: transform 0.3s ease;
    }
    
    /* 输入框样式定制 */
    .stTextInput>div>div>input {
        background: rgba(15, 23, 42, 0.5) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 10px 15px !important;
    }
    
    /* 按钮样式：带有悬停缩放动画 */
    .stButton>button {
        background: linear-gradient(135deg, #4edea3 0%, #059669 100%) !important;
        color: #064e3b !important;
        border: none !important;
        height: 3.5rem !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        border-radius: 16px !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        box-shadow: 0 15px 20px -5px rgba(78, 222, 163, 0.4) !important;
        width: 100%;
        margin-top: 20px;
    }
    
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 25px 30px -5px rgba(78, 222, 163, 0.5) !important;
    }

    /* 状态统计芯片 */
    .stat-badge {
        background: rgba(78, 222, 163, 0.15);
        color: #4edea3;
        padding: 5px 12px;
        border-radius: 8px;
        font-weight: 600;
        border: 1px solid rgba(78, 222, 163, 0.3);
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
# MAIN APP
# ============================================================================
def main():
    st.set_page_config(page_title="VIP Link Gen Pro", page_icon="💎", layout="centered")
    inject_ui()
    
    if 'auth' not in st.session_state: st.session_state.auth = False

    st.markdown('<h1 class="main-title">VIP LINK PRO</h1>', unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#64748b; font-weight:600; letter-spacing:2px;'>INTELLIGENT DEEP-LINK SYSTEM</p>", unsafe_allow_html=True)

    # --- 1. LOGIN ---
    if not st.session_state.auth:
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            pwd = st.text_input("🔑 System Access Key", type="password", placeholder="Enter Vault Password")
            if st.button("UNLOCK DASHBOARD"):
                if pwd == ACCESS_PASSWORD:
                    st.session_state.auth = True
                    st.rerun()
                else: st.error("Incorrect Password. Access Denied.")
            st.markdown('</div>', unsafe_allow_html=True)
        return

    # --- 2. MAIN TOOL ---
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    st.markdown("#### 👤 Manager Configuration")
    c1, c2 = st.columns(2)
    with c1:
        # 防空设计：设置 Placeholder 引导填写
        m_id = st.text_input("Telegram ID", placeholder="e.g. max_bkio")
        if not m_id: st.caption("⚠️ Telegram ID is required for link generation.")
    with c2:
        m_name = st.text_input("Display Name", placeholder="e.g. Max")
        if not m_name: st.caption("⚠️ This name will appear in the customer's message.")

    st.markdown("---")
    st.markdown("#### 📂 Batch Processing")
    
    sc1, sc2 = st.columns(2)
    with sc1:
        scenario = st.selectbox("Scenario Strategy", ["Option 1: New Registration", "Option 2: Retention"])
    with sc2:
        file = st.file_uploader("Upload Data (CSV/XLSX)", type=['csv', 'xlsx'])

    # --- 3. PROCESSING ---
    if st.button("🚀 GENERATE BULK LINKS"):
        # 防空检查逻辑
        if not m_id or not m_name:
            st.error("🚨 STOP: Telegram ID and Manager Name cannot be empty!")
            return
        
        if not file:
            st.warning("📋 Please upload a file first.")
            return

        # 数据加载
        try:
            df = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file)
            user_col = next((c for c in df.columns if 'username' in c.lower()), None)
            country_col = next((c for c in df.columns if 'country' in c.lower()), None)
            
            if not user_col:
                st.error("Column 'username' not found!")
                return
            
            results = []
            rows = df.to_dict('records')
            progress = st.progress(0)
            status = st.empty()

            for idx, row in enumerate(rows):
                user = str(row.get(user_col, "")).strip()
                if not user or user.lower() == 'nan': continue
                
                # 自动判别语言 (JP vs EN)
                country = str(row.get(country_col, "")).upper() if country_col else "OTHER"
                lang = "JP" if any(x in country for x in ["JAPAN", "JP"]) else "EN"
                
                # 构建内容
                msg = TEMPLATES[scenario][lang].format(manager_name=m_name, username=user)
                long_url = f"https://t.me/{m_id}?text={urllib.parse.quote(msg)}"
                
                short_url, err = shorten_url(long_url)
                
                results.append({
                    "Username": user,
                    "Region": "Japan 🇯🇵" if lang == "JP" else "Global 🌍",
                    "Short Link": short_url or "Error",
                    "Status": "✅ Success" if short_url else f"❌ {err}"
                })
                
                progress.progress((idx + 1) / len(rows))
                status.caption(f"Generating links for {user}...")
                time.sleep(0.02)

            res_df = pd.DataFrame(results)
            st.success("Batch Processing Complete!")
            st.dataframe(res_df, use_container_width=True)

            # --- 4. EXPORT ---
            st.markdown("#### 📥 Download Results")
            ec1, ec2 = st.columns(2)
            
            # Excel
            ex_bio = io.BytesIO()
            with pd.ExcelWriter(ex_bio, engine='openpyxl') as writer:
                res_df.to_excel(writer, index=False)
            ec1.download_button("📂 Download Excel (.xlsx)", ex_bio.getvalue(), "vip_links.xlsx", use_container_width=True)
            
            # CSV
            csv_data = res_df.to_csv(index=False).encode('utf-8-sig')
            ec2.download_button("📄 Download CSV (.csv)", csv_data, "vip_links.csv", use_container_width=True)

        except Exception as e:
            st.error(f"Error processing file: {e}")

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#475569; margin-top:2rem; font-size:0.8rem;'>Secured by BK8 VIP OPS • 2026</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
