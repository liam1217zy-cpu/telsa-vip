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
    st.error("Missing Secrets! Please configure ACCESS_PASSWORD, SHORTIO_API_KEY, and SHORTIO_DOMAIN in Streamlit Settings.")
    st.stop()

SHORTIO_API_URL = "https://api.short.io/links"
DEFAULT_MANAGER_ID = "max_bkio"
DEFAULT_MANAGER_NAME = "Max"

# 内部逻辑模板（界面不显示选择，后台自动匹配）
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
# PREMIUM UI DESIGN (Glassmorphism)
# ============================================================================
def inject_ui():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    .stApp {
        background: radial-gradient(circle at top right, #1e293b, #0f172a) !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #4edea3 0%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        border-radius: 20px;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        margin-top: 2rem;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #4edea3 0%, #3bc48a 100%) !important;
        color: #0f172a !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 10px 15px -3px rgba(78, 222, 163, 0.3) !important;
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 25px -5px rgba(78, 222, 163, 0.4) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# HELPER FUNCTIONS
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
    st.set_page_config(page_title="VIP Link Pro", page_icon="⚡", layout="centered")
    inject_ui()
    
    if 'auth' not in st.session_state: st.session_state.auth = False

    st.markdown('<h1 class="main-title">VIP Link Pro</h1>', unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#94a3b8;'>Premium Bulk Telegram Deep-Link Solution</p>", unsafe_allow_html=True)

    # 1. Login Logic
    if not st.session_state.auth:
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            pwd = st.text_input("System Vault Key", type="password")
            if st.button("Unlock Dashboard"):
                if pwd == ACCESS_PASSWORD:
                    st.session_state.auth = True
                    st.rerun()
                else: st.error("Access Key Invalid")
            st.markdown('</div>', unsafe_allow_html=True)
        return

    # 2. Tool Logic
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        m_id = st.text_input("Manager Telegram ID", value=DEFAULT_MANAGER_ID)
        m_name = st.text_input("Display Name", value=DEFAULT_MANAGER_NAME)
    with c2:
        scenario = st.selectbox("Select Scenario", ["Option 1: New Registration", "Option 2: Retention"])
        file = st.file_uploader("Upload CSV or XLSX", type=['csv', 'xlsx'])

    if file and st.button("🚀 Process & Generate Links"):
        # Load Data
        df = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file)
        
        # Identify columns
        user_col = next((c for c in df.columns if 'username' in c.lower()), None)
        country_col = next((c for c in df.columns if 'country' in c.lower()), None)
        
        if not user_col:
            st.error("Error: Could not find 'username' column in your file.")
        else:
            results = []
            progress = st.progress(0)
            status_text = st.empty()
            
            rows = df.to_dict('records')
            total = len(rows)

            for idx, row in enumerate(rows):
                user = str(row.get(user_col, "")).strip()
                if not user or user.lower() == 'nan': continue
                
                # 自动判断语言逻辑
                country = str(row.get(country_col, "")).upper() if country_col else "OTHER"
                lang_code = "JP" if any(x in country for x in ["JAPAN", "JP"]) else "EN"
                
                # 获取模板并生成链接
                msg_template = TEMPLATES[scenario][lang_code]
                full_msg = msg_template.format(manager_name=m_name, username=user)
                
                encoded_msg = urllib.parse.quote(full_msg)
                long_url = f"https://t.me/{m_id}?text={encoded_msg}"
                
                short_url, err = shorten_url(long_url)
                
                results.append({
                    "Username": user,
                    "Country": country,
                    "Language": lang_code,
                    "Short Link": short_url if short_url else "Error",
                    "Status": "Success" if short_url else err
                })
                
                progress.progress((idx + 1) / total)
                status_text.text(f"Processing: {idx+1}/{total}")
                time.sleep(0.05) # Rate limit protection

            res_df = pd.DataFrame(results)
            st.success(f"Successfully generated {len(res_df)} links!")
            st.dataframe(res_df, use_container_width=True)

            # Download Buttons
            st.markdown("### 📥 Download Results")
            dc1, dc2 = st.columns(2)
            
            # Excel Download
            excel_bio = io.BytesIO()
            with pd.ExcelWriter(excel_bio, engine='openpyxl') as writer:
                res_df.to_excel(writer, index=False)
            dc1.download_button("Export to Excel (.xlsx)", excel_bio.getvalue(), "vip_links.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            # CSV Download
            csv_data = res_df.to_csv(index=False).encode('utf-8-sig')
            dc2.download_button("Export to CSV (.csv)", csv_data, "vip_links.csv", "text/csv")

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
