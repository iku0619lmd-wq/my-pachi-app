import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# ページ設定
st.set_page_config(page_title="収支表", layout="wide", page_icon="🎰")

# タイトル
st.title("🎰 収支表")

# Googleスプレッドシートへの接続
conn = st.connection("gsheets", type=GSheetsConnection)

# データの読み込み
try:
    df = conn.read()
    if not df.empty:
        # 数値データとして正しく処理する
        df['investment'] = pd.to_numeric(df['investment'], errors='coerce').fillna(0)
        df['recovery'] = pd.to_numeric(df['recovery'], errors='coerce').fillna(0)
        df['balance'] = pd.to_numeric(df['balance'], errors='coerce').fillna(0)
        df['date'] = pd.to_datetime(df['date']).dt.date
except Exception:
    df = pd.DataFrame(columns=['date', 'model_name', 'investment', 'recovery', 'balance'])

# --- サイドバー：入力フォーム ---
with st.sidebar:
    st.header("📥 記録入力")
    with st.form("input_form", clear_on_submit=True):
        date = st.date_input("日付", datetime.now())
        model_name = st.text_input("機種名")
        investment = st.number_input("投資 (円)", min_value=0, step=1000)
        recovery = st.number_input("回収 (円)", min_value=0, step=1000)
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
            # データを合体させてスプシを更新
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(data=updated_df)
            st.success("保存しました！")
            st.balloons()
            st.rerun()
        else:
            st.error("機種名を入力してください")

# --- メイン画面：分析エリア ---
if not df.empty:
    # 1. 数字の表示
    total_bal = int(df['balance'].sum())
    win_rate = (df['balance'] > 0).mean() * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("トータル収支", f"{total_bal:,} 円")
    col2.metric("勝率", f"{win_rate:.1f} %")
    col3.metric("稼働日数", f"{len(df)} 日")

    st.divider()

    # 2. グラフと履歴
    tab1, tab2 = st.tabs(["📊 グラフ分析", "📋 履歴一覧"])
    
    with tab1:
        # 累積収支の推移グラフ
        df_sorted = df.sort_values('date')
        df_sorted['cumulative'] = df_sorted['balance'].cumsum()
        fig = px.line(df_sorted, x='date', y='cumulative', title='収支の推移')
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)

        # 機種別の通算収支グラフ
        model_sum = df.groupby('model_name')['balance'].sum().sort_values()
        fig_model = px.bar(model_sum, orientation='h', title='機種別収支')
        st.plotly_chart(fig_model, use_container_width=True)

    with tab2:
        # 日付が新しい順に表示
        st.dataframe(df.sort_values('date', ascending=False), use_container_width=True)

else:
    st.info("左のメニューからデータを入力してください。")
