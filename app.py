import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ページ設定（シンプル）
st.set_page_config(page_title="パチンコ収支管理", layout="centered")

# データベースの初期化
def init_db():
    conn = sqlite3.connect('pachi_balance.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            model_name TEXT NOT NULL,
            investment INTEGER NOT NULL,
            recovery INTEGER NOT NULL,
            balance INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# DBからデータを取得する共通関数
def get_data(query, params=()):
    conn = sqlite3.connect('pachi_balance.db')
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# アプリのタイトル
st.title("パチンコ収支管理")

# タブで画面を切り替え
tab1, tab2, tab3 = st.tabs(["収支入力", "履歴・検索", "機種別分析"])

# ==========================================
# タブ1: 収支入力
# ==========================================
with tab1:
    st.header("収支の登録")
    
    existing_models_df = get_data("SELECT DISTINCT model_name FROM records ORDER BY model_name")
    existing_models = existing_models_df['model_name'].tolist()
    
    selected_model = st.selectbox(
        "機種名を選択（文字を入力すると検索できます）", 
        ["(新規入力)"] + existing_models
    )
    
    if selected_model == "(新規入力)":
        model_name = st.text_input("新しい機種名を入力してください")
    else:
        model_name = selected_model

    date = st.date_input("稼働日", datetime.today())
    
    col1, col2 = st.columns(2)
    with col1:
        investment = st.number_input("投資額 (円)", min_value=0, step=500, format="%d")
    with col2:
        recovery = st.number_input("回収額 (円)", min_value=0, step=500, format="%d")
        
    if st.button("登録する", type="primary"):
        if not model_name:
            st.error("機種名を入力してください。")
        else:
            balance = recovery - investment
            conn = sqlite3.connect('pachi_balance.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO records (date, model_name, investment, recovery, balance)
                VALUES (?, ?, ?, ?, ?)
            ''', (date.strftime('%Y-%m-%d'), model_name, investment, recovery, balance))
            conn.commit()
            conn.close()
            st.success(f"【{model_name}】の収支（{balance:+,}円）を記録しました。")

# ==========================================
# タブ2: 履歴・検索
# ==========================================
with tab2:
    st.header("収支履歴")
    
    search_query = st.text_input("機種名で絞り込み検索", "")
    
    if search_query:
        query = "SELECT date AS 日付, model_name AS 機種名, investment AS 投資額, recovery AS 回収額, balance AS 収支 FROM records WHERE model_name LIKE ? ORDER BY date DESC"
        df_history = get_data(query, ('%' + search_query + '%',))
    else:
        query = "SELECT date AS 日付, model_name AS 機種名, investment AS 投資額, recovery AS 回収額, balance AS 収支 FROM records ORDER BY date DESC"
        df_history = get_data(query)

    if df_history.empty:
        st.info("データがありません。")
    else:
        st.dataframe(df_history, use_container_width=True, hide_index=True)
        
        csv = df_history.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="現在の表示データをCSVでダウンロード",
            data=csv,
            file_name=f"pachi_history_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

# ==========================================
# タブ3: 機種別分析（タップで詳細表示）
# ==========================================
with tab3:
    st.header("機種別パフォーマンス")
    
    query = '''
        SELECT 
            model_name AS 機種名,
            COUNT(*) AS 稼働回数,
            SUM(investment) AS 総投資,
            SUM(recovery) AS 総回収,
            SUM(balance) AS 合計収支,
            AVG(balance) AS 平均収支,
            (CAST(SUM(CASE WHEN balance > 0 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*)) * 100 AS 勝率
        FROM records
        GROUP BY model_name
        ORDER BY 合計収支 DESC
    '''
    df_analysis = get_data(query)
    
    if df_analysis.empty:
        st.info("分析するデータがありません。")
    else:
        df_analysis['平均収支'] = df_analysis['平均収支'].astype(int)
        df_analysis['勝率'] = df_analysis['勝率'].map('{:.1f}%'.format)
        
        total_balance = df_analysis['合計収支'].sum()
        if total_balance > 0:
            st.success(f"トータル収支: +{total_balance:,} 円")
        elif total_balance < 0:
            st.error(f"トータル収支: {total_balance:,} 円")
        else:
            st.warning(f"トータル収支: ±0 円")

        st.write("▼ 機種名の行をタップ（クリック）すると、下部に詳細履歴が表示されます")
        
        # 選択可能なデータフレームとして表示
        event = st.dataframe(
            df_analysis, 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",        # 行が選ばれたら画面を更新する設定
            selection_mode="single-row" # 1行だけ選択できるようにする設定
        )

        # もし行がタップ（選択）されたら、詳細データを表示する処理
        selected_rows = event.selection.rows
        if selected_rows:
            # 選択された行の機種名を取得
            selected_index = selected_rows[0]
            selected_model = df_analysis.iloc[selected_index]['機種名']
            
            st.markdown(f"### 【{selected_model}】の日別データ")
            
            # その機種だけの日別データをデータベースから取得
            detail_query = "SELECT date AS 日付, investment AS 投資額, recovery AS 回収額, balance AS 収支 FROM records WHERE model_name = ? ORDER BY date DESC"
            df_detail = get_data(detail_query, (selected_model,))
            
            # 詳細データを表示
            st.dataframe(df_detail, use_container_width=True, hide_index=True)