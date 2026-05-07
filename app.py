import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# ページ設定 (絵文字なし)
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

# --- 入力フォーム (元の横並びレイアウトに戻す) ---
with st.form("input_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("日付", datetime.now())
        model_name = st.text_input("機種名")
    with col2:
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
        updated_df = pd.concat([df, new_row], ignore_index=True)
        conn.update(data=updated_df)
        st.success("保存しました")
        st.rerun()
    else:
        st.error("機種名を入力してください")

# --- データとグラフの表示 (タブを廃止し、縦に並べる) ---
if not df.empty:
    st.subheader("収支データ")
    
    total_bal = int(df['balance'].sum())
    total_inv = int(df['investment'].sum())
    win_rate = (df['balance'] > 0).mean() * 100

    c1, c2, c3 = st.columns(3)
    c1.metric("トータル収支", f"{total_bal:,} 円")
    c2.metric("総投資", f"{total_inv:,} 円")
    c3.metric("勝率", f"{win_rate:.1f} %")

    # 履歴をそのまま表示
    st.dataframe(df.sort_values('date', ascending=False), use_container_width=True)

    st.subheader("分析グラフ")
    
    # グラフもそのまま表示
    df_sorted = df.sort_values('date')
    df_sorted['cumulative'] = df_sorted['balance'].cumsum()
    fig = px.line(df_sorted, x='date', y='cumulative', title='収支の推移')
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("データを入力してください")
