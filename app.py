import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ページ設定
st.set_page_config(page_title="収支表", layout="wide")

st.title("収支表")

# Googleスプレッドシートへの接続
conn = st.connection("gsheets", type=GSheetsConnection)

# データの読み込み
try:
    df = conn.read()
    if not df.empty:
        df['investment'] = pd.to_numeric(df['investment'], errors='coerce').fillna(0)
        df['recovery'] = pd.to_numeric(df['recovery'], errors='coerce').fillna(0)
        df['balance'] = pd.to_numeric(df['balance'], errors='coerce').fillna(0)
        df['date'] = pd.to_datetime(df['date']).dt.date
except Exception:
    df = pd.DataFrame(columns=['date', 'model_name', 'investment', 'recovery', 'balance'])

# --- 入力エリア ---
with st.form("input_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("日付", datetime.now())
        model_name = st.text_input("機種名")
    with col2:
        investment = st.number_input("投資 (円)", min_value=0, step=100)
        recovery = st.number_input("回収 (円)", min_value=0, step=100)
    
    submit = st.form_submit_button("記録する")

if submit:
    if model_name:
        new_row = pd.DataFrame([{
            "date": date.strftime('%Y-%m-%d'),
            "model_name": model_name,
            "investment": int(investment),
            "recovery": int(recovery),
            "balance": int(recovery - investment)
        }])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        conn.update(data=updated_df)
        st.success("保存しました")
        st.rerun()
    else:
        st.error("機種名を入力してください")

# --- 表示エリア ---
if not df.empty:
    # トータル収支の計算
    total_balance = int(df['balance'].sum())
    st.header(f"トータル収支: {total_balance:,} 円")

    # 履歴の一覧表示
    st.subheader("履歴一覧")
    st.dataframe(df.sort_values('date', ascending=False), use_container_width=True, hide_index=True)

else:
    st.info("データを入力してください")
