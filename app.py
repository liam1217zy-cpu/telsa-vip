import streamlit as st
import pandas as pd
import requests
import urllib.parse
import io
import time
from typing import Optional, Dict, List, Tuple

# ============================================================================
# CONFIGURATION
# ============================================================================
try:
    ACCESS_PASSWORD = st.secrets["ACCESS_PASSWORD"]
    SHORTIO_API_KEY = st.secrets["SHORTIO_API_KEY"]
    SHORTIO_DOMAIN = st.secrets["SHORTIO_DOMAIN"]
except Exception:
    st.error("Missing Secrets! Please configure ACCESS_PASSWORD, SHORTIO_API_KEY, and SHORTIO_DOMAIN.")
    st.stop()

SHORTIO_API_URL = "https://api.short.io/links"

# 批量生成的文案模板
CONTENT_TEMPLATES = {
    "Option 1: New Registration": {
        "EN": {
            "subject": "💎 {username}, You’ve been handpicked for VIP Onboarding.",
            "body": "Hi {username}, don't leave your rewards to chance. We’ve handpicked {m_name}, our VIP Guide, to help you navigate your account privileges and ensure you don't miss a single perk.\n\nConnect with {m_name} here: 👉 {short_link}\n\n{m_name} will personally walk you through how to fully utilize your new account status."
        },
        "JP": {
            "subject": "💎 {username}様、VIPオンボーディングの担当に選出されました。",
            "body": "{username}様、特典を逃さないでください。専属ガイドの{m_name}が、アカウントの特権を最大限に活用できるようサポートいたします。\n\nこちらから{m_name}に連絡してください：👉 {short_link}\n\n{m_name}が、新しいアカウントステータスの活用方法を個別にご案内いたします。"
        }
    },
    "Option 2: Retention": {
        "EN": {
            "subject": "💎 Welcome back {username}! Your VIP status is waiting.",
            "body": "Hi {username}, we missed you! {m_name} is ready to sync your account privileges and provide the latest standby links.\n\nReconnect with {m_name} here: 👉 {short_link}\n\n{m_name} will ensure your account is fully optimized for your return."
        },
        "JP": {
            "subject": "💎 {username}様、お帰りなさい！VIPステータスが待機中です。",
            "body": "{username}様、お久しぶりです！{m_name}がアカウント特典の同期と最新の予備リンクをご案内いたします。\n\nこちらから{m_name}に再接続してください：👉 {short_link}\n\n{m_name}が、お客様の復帰に合わせてアカウントを最適化いたします。"
        }
    }
}

# ============================================================================
# UI: UNICORN GUNDAM THEME
# ============================================================================
def inject_ui():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700;800&display=swap');
    .stApp { background: radial-gradient(circle at 50% 100%, #f8fafc 0%, #ffffff 100%) !important; font-family: 'Plus Jakarta Sans', sans-serif !important; }
    .main-title { font-size: 3.5rem; font-weight: 800; background: linear-gradient(135deg, #f97316 0%, #22c55e 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 0px; filter: drop-shadow(0 0 10px rgba(34, 197, 94, 0.2)); }
    .glass-card { background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(25px); border-radius: 30px; padding: 2.5rem; border: 2px solid; border-image: linear-gradient(135deg, #f97316, #22c55e) 1; box-shadow: 0 25px 50px rgba(0,0,0,0.08); margin-top: 1.5rem; }
    .stButton>button { background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important; color: white !important; height: 3.5rem !important; font-weight: 700 !important; border-radius: 18px !important; border: none !important; box-shadow: 0 10px 20px rgba(34, 197, 94, 0.3) !important; width: 100%; transition: 0.4s; }
    .stButton>button:hover { transform: translateY(-3px); box-shadow: 0 15px 30px rgba(34, 197, 94, 0.4) !important; }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea { border-radius: 12px !important; border: 1px solid #e2e8f0 !important; }
    h3 { color: #1e293b; font-weight: 800; margin-bottom: 1rem; }
    </style>
    """, unsafe_allow_html=True)

def shorten_url(long_url: str) -> Tuple[Optional[str], Optional[str]]:
    headers = {"Authorization": SHORTIO_API_KEY, "Content-Type": "application/json"}
    payload = {"domain": SHORTIO_DOMAIN, "originalURL": long_url}
    try:
        response = requests.post(SHORTIO_API_URL, headers=headers, json=payload, timeout=15)
        if response.status_code in [200, 201]: return response.json().get("shortURL"), None
        return None, f"Error {response.status_code}"
    except Exception as e: return None, str(e)

# ============================================================================
# MAIN
# ============================================================================
def main():
    st.set_page_config(page_title="RX-0 VIP PRO", layout="centered")
    inject_ui()
    
    if 'auth' not in st.session_state: st.session_state.auth = False
    st.markdown('<h1 class="main-title">VIP RX-0 [TERMINAL]</h1>', unsafe_allow_html=True)

    if not st.session_state.auth:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        pwd = st.text_input("Unlock Psycho-Frame System", type="password")
        if st.button("SYSTEM ACTIVATION"):
            if pwd == ACCESS_PASSWORD:
                st.session_state.auth = True
                st.rerun()
            else: st.error("Access Denied.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # --- 功能 1: 批量生成 (原有的逻辑保留) ---
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🚀 Batch Link Generation")
    c1, c2 = st.columns(2)
    with c1:
        m_id = st.text_input("Telegram ID", value="max_bkio", key="batch_tid")
        m_name = st.text_input("Manager Name", value="Max", key="batch_mname")
    with c2:
        scenario = st.selectbox("Strategic Scenario", list(CONTENT_TEMPLATES.keys()))
        file = st.file_uploader("Upload Target Data (XLSX/CSV)", type=['csv', 'xlsx'])

    if st.button("🚀 EXECUTE BATCH GENERATION"):
        if not file:
            st.warning("Please upload a file.")
        else:
            df = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file)
            user_col = next((c for c in df.columns if 'username' in c.lower()), None)
            country_col = next((c for c in df.columns if 'country' in c.lower()), None)
            
            if not user_col:
                st.error("Column 'username' missing.")
            else:
                results = []
                bar = st.progress(0)
                rows = df.to_dict('records')
                for idx, row in enumerate(rows):
                    user = str(row.get(user_col, "")).strip()
                    if not user or user.lower() == 'nan': continue
                    country = str(row.get(country_col, "")).upper() if country_col else "GLOBAL"
                    lang = "JP" if any(x in country for x in ["JAPAN", "JP"]) else "EN"
                    
                    tg_msg = f"Hi {m_name}, I am {user}." if lang == "EN" else f"こんにちは {m_name}、{user} です。"
                    long_url = f"https://t.me/{m_id}?text={urllib.parse.quote(tg_msg)}"
                    short_link, _ = shorten_url(long_url)
                    
                    template = CONTENT_TEMPLATES[scenario][lang]
                    results.append({
                        "Username": user,
                        "Short Link": short_link or "Error",
                        "Subject": template["subject"].format(username=user),
                        "Full Content": template["body"].format(username=user, m_name=m_name, short_link=short_link or "ERR")
                    })
                    bar.progress((idx + 1) / len(rows))
                
                res_df = pd.DataFrame(results)
                st.success("Batch Complete!")
                st.dataframe(res_df)
                
                # 下载按钮
                ex_io = io.BytesIO()
                with pd.ExcelWriter(ex_io, engine='openpyxl') as writer:
                    res_df.to_excel(writer, index=False)
                st.download_button("📂 Download Results (.xlsx)", ex_io.getvalue(), "vip_export.xlsx")

    st.markdown('</div>', unsafe_allow_html=True)

    # --- 功能 2: 手动输入 (新增的功能) ---
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### ✍️ Single Manual Generator")
    st.caption("No Short.io required. Generate content for a single user instantly.")
    
    mc1, mc2 = st.columns(2)
    with mc1:
        manual_user = st.text_input("Customer Name", placeholder="e.g. Liam777", key="man_user")
        manual_manager = st.text_input("Manager Name", value="Max", key="man_mname")
    with mc2:
        manual_lang = st.radio("Language Mode", ["English 🌍", "Japanese 🇯🇵"], horizontal=True)
    
    manual_content = st.text_area("Content Body", 
                                  placeholder="Type your message here. Use {username} to auto-insert the customer's name.",
                                  height=150)

    if st.button("✨ GENERATE MANUAL TEXT"):
        if not manual_user or not manual_content:
            st.warning("Please enter both Customer Name and Content.")
        else:
            # 简单的变量替换逻辑
            final_text = manual_content.replace("{username}", manual_user).replace("{m_name}", manual_manager)
            
            st.markdown("#### ✅ Generated Output:")
            st.code(final_text, language="text")
            st.info("You can now copy the text above directly.")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<p style='text-align:center; color:#cbd5e1; margin-top:2rem;'>RX-0 PSYCHO-FRAME SYSTEM v4.0</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
