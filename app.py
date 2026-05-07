import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# ページ設定
st.set_page_config(page_title="Pachi-Log Pro", layout="wide", page_icon="🎰")

# --- タイトルとデザイン ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_index=True)

st.title("📈 Pachi-Log Pro")
st.caption("24時間・スプシ連動型 収支管理システム")

# スプレッドシートへの接続
conn = st.connection("gsheets", type=GSheetsConnection)

# データの読み込み
try:
    df = conn.read()
    # 数値列が文字列になってしまう場合の対策
    df['investment'] = pd.to_numeric(df['investment'], errors='coerce').fillna(0)
    df['recovery'] = pd.to_numeric(df['recovery'], errors='coerce').fillna(0)
    df['balance'] = pd.to_numeric(df['balance'], errors='coerce').fillna(0)
    df['date'] = pd.to_datetime(df['date']).dt.date
except:
    df = pd.DataFrame(columns=['date', 'model_name', 'investment', 'recovery', 'balance'])

# --- サイドバー：入力フォーム ---
with st.sidebar:
    st.header("📥 新規記録")
    with st.form("input_form", clear_on_submit=True):
        date = st.date_input("日付", datetime.now())
        model_name = st.text_input("機種名 (例: エヴァ15)")
        investment = st.number_input("投資 (円)", min_value=0, step=1000)
        recovery = st.number_input("回収 (円)", min_value=0, step=1000)
        submit = st.form_submit_button("スプシに送信 🚀")

    if submit and model_name:
        new_row = pd.DataFrame([{
            "date": date.strftime('%Y-%m-%d'),
            "model_name": model_name,
            "investment": int(investment),
            "recovery": int(recovery),
            "balance": int(recovery - investment)
        }])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        conn.update(data=updated_df)
        st.success("スプシを更新しました！")
        st.balloons()
        st.rerun()

# --- メイン画面：分析エリア ---
if not df.empty:
    # 1. 概要メトリクス
    total_inv = int(df['investment'].sum())
    total_rec = int(df['recovery'].sum())
    total_bal = int(df['balance'].sum())
    win_rate = (df['balance'] > 0).mean() * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("トータル収支", f"{total_bal:,} 円", delta=f"{total_bal:,} 円")
    col2.metric("総投資", f"{total_inv:,} 円")
    col3.metric("勝率", f"{win_rate:.1f} %")
    col4.metric("稼働日数", f"{len(df)} 日")

    st.divider()

    # 2. 収支グラフ
    tab1, tab2 = st.tabs(["📊 推移グラフ", "📋 履歴一覧"])
    
    with tab1:
        # 日付ごとの累積収支
        df_sorted = df.sort_values('date')
        df_sorted['cumulative'] = df_sorted['balance'].cumsum()
        fig = px.line(df_sorted, x='date', y='cumulative', title='累積収支の推移',
                     labels={'cumulative': '累計収支', 'date': '日付'})
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)

        # 機種別集計
        model_summary = df.groupby('model_name')['balance'].sum().sort_values()
        fig_model = px.bar(model_summary, orientation='h', title='機種別トップ/ワースト')
        st.plotly_chart(fig_model, use_container_width=True)

    with tab2:
        st.dataframe(df.sort_values('date', ascending=False), use_container_width=True)

else:
    st.info("まだデータがありません。サイドバーから入力してね！")
