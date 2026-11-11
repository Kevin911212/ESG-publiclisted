import io

import pandas as pd
import requests
import streamlit as st
import urllib3

# verify=False 會產生警告，這裡關閉警告訊息
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="資料下載與檢視", page_icon="📊", layout="wide")
st.title("📊 資料下載與檢視")

# ---------------- 側邊欄：設定 ----------------
with st.sidebar:
    st.header("設定")
    url = st.text_input(
        "CSV 連結",
        value="https://mopsfin.twse.com.tw/opendata/t187ap46_L_1.csv",  # 換連結
    )
    verify_ssl = st.checkbox("驗證 SSL 憑證", value=False)
    drop_na = st.checkbox("移除含空值的列 (dropna)", value=True)
    load_btn = st.button("載入資料", type="primary")


# ---------------- 取得資料（快取 1 小時） ----------------
@st.cache_data(ttl=3600, show_spinner="資料下載中...")
def load_data(url: str, verify: bool) -> pd.DataFrame:
    response = requests.get(url, verify=verify, timeout=30)
    response.raise_for_status()
    # 直接從記憶體讀取，不用先存成 data01.csv
    return pd.read_csv(io.BytesIO(response.content), encoding="utf-8-sig")  # 繁體中文


# ---------------- 主畫面 ----------------
if load_btn or "df" in st.session_state:
    if load_btn:
        try:
            st.session_state["df"] = load_data(url, verify_ssl)
        except Exception as e:
            st.session_state.pop("df", None)
            st.error(f"下載或解析失敗：{e}")

    if "df" in st.session_state:
        df = st.session_state["df"].copy()
        if drop_na:
            df = df.dropna()

        c1, c2 = st.columns(2)
        c1.metric("資料筆數", f"{len(df):,}")
        c2.metric("欄位數", len(df.columns))

        keyword = st.text_input("🔍 關鍵字搜尋（搜尋所有欄位）")
        if keyword:
            mask = df.astype(str).apply(
                lambda col: col.str.contains(keyword, case=False, na=False)
            )
            df = df[mask.any(axis=1)]
            st.caption(f"符合 {len(df):,} 筆")

        st.dataframe(df, use_container_width=True)

        st.download_button(
            "⬇️ 下載 CSV",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="data01.csv",
            mime="text/csv",
        )
else:
    st.info("請在左側確認連結後，按「載入資料」。")
