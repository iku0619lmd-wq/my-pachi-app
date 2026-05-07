import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="最強パチ収支管理", layout="wide")

st.title("🎰 パチンコ収支管理 (スプシ連動版)")

# スプレッドシートへの接続設定
conn = st.connection("gsheets", type=GSheetsConnection)

# データの読み込み
try:
    df = conn.read()
except:
    # シートが空の場合の初期データ
    df = pd.DataFrame(columns=['date', 'model_name', 'investment', 'recovery', 'balance'])

# --- 入力フォーム ---
with st.form("input_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("日付", datetime.now())
        model_name = st.text_input("機種名")
    with col2:
        investment = st.number_input("投資 (円)", min_value=0, step=100)
        recovery = st.number_input("回収 (円)", min_value=0, step=100)
    
    submit = st.form_submit_button("収支を記録する")

if submit:
    if model_name:
        new_data = pd.DataFrame([{
            "date": date.strftime('%Y-%m-%d'),
            "model_name": model_name,
            "investment": investment,
            "recovery": recovery,
            "balance": recovery - investment
        }])
        
        # 既存データと結合して保存
        updated_df = pd.concat([df, new_data], ignore_index=True)
        conn.update(data=updated_df)
        st.success(f"【{model_name}】の記録完了！スプシに保存したよ！")
        st.balloons()
        # 画面を更新
        st.rerun()
    else:
        st.error("機種名を入れてね！")

# --- 履歴表示 ---
st.header("📊 収支履歴")
if not df.empty:
    # 日付で降順ソート
    display_df = df.sort_values(by='date', ascending=False)
    st.dataframe(display_df, use_container_width=True)
    
    total_balance = df['balance'].astype(int).sum()
    st.metric("トータル収支", f"{total_balance:,} 円")
else:
    st.info("まだデータがないよ。初勝利を記録しよう！")
