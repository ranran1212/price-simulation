import streamlit as st
import math
import pandas as pd
import numpy as np
import datetime

# セッション状態を初期化
if 'weights' not in st.session_state:
    st.session_state['weights'] = {}
if 'decrease_thresholds' not in st.session_state:
    st.session_state['decrease_thresholds'] = {}

# 価格設定を計算する関数
def calculate_dynamic_pricing(current_price, adjustment_factor, weeks,
                              requests, call_time, waiting_time, active_days, repeat_rate, penalty_points, approval_rate,
                              weight_requests, weight_call_time, weight_waiting_time,
                              weight_active_days, weight_repeat_rate, weight_penalty_points, weight_approval_rate,
                              decrease_thresholds):
    prices = [current_price]
    for week_number in range(1, weeks + 1):
        last_price = prices[-1]
        
        #正規化
        normalized_requests = requests / 84
        normalized_call_time = call_time / 2520
        normalized_waiting_time = waiting_time / 2520
        normalized_active_days = active_days / 7
        normalized_penalty_points = penalty_points / 5
        
        #重みづけの計算
        variable_effect = (normalized_requests * weight_requests +
                   normalized_call_time * weight_call_time +
                   normalized_waiting_time * weight_waiting_time +
                   normalized_active_days * weight_active_days +
                   repeat_rate * weight_repeat_rate +
                   normalized_penalty_points * weight_penalty_points +
                   approval_rate * weight_approval_rate) 

        #減少閾値を下回る場合の計算
        decrease_effect = 0
        if waiting_time <= decrease_thresholds['waiting_time']:
            decrease_effect -= math.exp(week_number / weeks)
        if active_days <= decrease_thresholds['active_days']:
            decrease_effect -= math.exp(week_number / weeks)
        if penalty_points >= decrease_thresholds['penalty_points']:
            decrease_effect -= math.exp(week_number / weeks)
        if approval_rate <= decrease_thresholds['approval_rate']:
            decrease_effect -= math.exp(week_number / weeks)

        increase_rate = (variable_effect + decrease_effect) * adjustment_factor
        new_price = last_price * (1 + increase_rate)
        prices.append(new_price)

    return prices


# Streamlit のページレイアウトを定義
st.set_page_config(
                page_title="価格シミュレーション",
                page_icon ="🧐", 
                layout = "wide"
)

# タブの定義
tab1, tab2, tab3 = st.tabs(["simulation:条件設定・計算結果", "simulation:グラフ", "💛次週価格計算💛"])


# タブ1: 条件設定・計算結果
with tab1:
    col1, col2 = st.columns([2,1])

    with col1:
        st.header('条件設定')
        current_price = st.number_input('現在の価格', value=1000, step=100)
        adjustment_factor = st.number_input('調整係数', min_value=0.0, max_value=1.0, value=0.15, step=0.01)
        weeks = 12
        
        # 変数の入力
        st.subheader('変数の入力')
        requests = st.slider('リクエスト数（件）', 0, 100, 20)
        call_time = st.slider('通話時間（分）', 0, 3000, 500)
        waiting_time = st.slider('待機時間（分）', 0, 3000, 1500)
        active_days = st.slider('アクティブ日数（日）', 0, 7, 4)
        repeat_rate = st.slider('リピート率（%）', 0.0, 1.0, 0.5, step=0.1)
        approval_rate = st.slider('承認率（%）', 0.0, 1.0, 0.85, step=0.05) 
        penalty_points = st.slider('ペナルティ点数', 0, 10, 0)

        # 重みの設定
        st.subheader('重みの設定')
        weight_requests = st.number_input('リクエスト数の重み', min_value=0.0, max_value=1.0, value=0.5, step=0.1)
        weight_call_time = st.number_input('通話時間の重み', min_value=0.0, max_value=1.0, value=0.5, step=0.1)
        weight_waiting_time = st.number_input('待機時間の重み', min_value=0.0, max_value=1.0, value=0.6, step=0.1)
        weight_active_days = st.number_input('アクティブ日数の重み', min_value=0.0, max_value=1.0, value=0.6, step=0.1)
        weight_repeat_rate = st.number_input('リピート率の重み', min_value=0.0, max_value=1.0, value=0.7, step=0.1)
        weight_approval_rate = st.number_input('承認率の重み', min_value=-1.0, max_value=1.0, value=-0.8, step=0.1)
        weight_penalty_points = st.number_input('ペナルティ点数の重み', min_value=-1.0, max_value=0.8, value=-0.5, step=0.1)
        
        # 減少閾値
        st.subheader('減少閾値の設定')
        decrease_waiting_time = st.number_input('待機時間', min_value=0, value=180, step=10)
        decrease_active_days = st.number_input('アクティブ日数', min_value=0, value=2)
        decrease_approval_rate = st.number_input('承認率', min_value=0.0, max_value=1.0, value=0.8, step=0.05)
        decrease_call_time = st.number_input('通話時間', min_value=0, value=1500, step=50) 
        decrease_penalty_points = st.number_input('ペナルティ点数', min_value=0, value=1)

        
        # セッション状態に条件を保存
        st.session_state['adjustment_factor'] = adjustment_factor
        st.session_state['weights'] = {
            'requests': weight_requests,
            'call_time': weight_call_time,
            'waiting_time': weight_waiting_time,
            'active_days': weight_active_days,
            'repeat_rate': weight_repeat_rate,
            'approval_rate': weight_approval_rate,
            'penalty_points': weight_penalty_points
        }
        st.session_state['decrease_thresholds'] = {
            'waiting_time': decrease_waiting_time,
            'active_days': decrease_active_days,
            'penalty_points': decrease_penalty_points,
            'call_time': decrease_call_time,
            'approval_rate': decrease_approval_rate
        }
        
    with col2:
        st.header('計算結果')

        decrease_thresholds = {
            'waiting_time': decrease_waiting_time,
            'active_days': decrease_active_days,
            'penalty_points': decrease_penalty_points,
            'call_time': decrease_call_time,
            'approval_rate': decrease_approval_rate
        }
        
        # 価格計算を実行
        prices = calculate_dynamic_pricing(current_price, adjustment_factor, weeks,
                                   requests, call_time, waiting_time, active_days, repeat_rate, penalty_points,
                                   approval_rate,
                                   weight_requests, weight_call_time, weight_waiting_time,
                                   weight_active_days, weight_repeat_rate, weight_penalty_points, weight_approval_rate,
                                   decrease_thresholds)

        df_prices = pd.DataFrame({'Week': np.arange(1, weeks + 2), 'Price': prices})
        df_prices['増減金額'] = df_prices['Price'].diff().fillna(0).astype(int)
        st.dataframe(df_prices, height=500)


# タブ2: グラフ
with tab2:
    st.header('グラフ')
    st.line_chart(df_prices.set_index('Week')['Price'])  # 価格のみをプロット


import pandas as pd
import streamlit as st
import datetime

# タブ3: 次週価格計算
with tab3:
    st.header('次週価格計算')
    uploaded_file = st.file_uploader("CSVファイルを選択してください", type='csv')
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)

        # セッション状態から重みと減少条件を取得
        weights = st.session_state['weights']
        decrease_thresholds = st.session_state['decrease_thresholds']
        adjustment_factor = st.session_state['adjustment_factor']

        # 設定条件のログを作成
        settings_summary = pd.DataFrame({
            '項目名': [
                'リクエスト数', '通話時間', '待機時間', 'アクティブ日数',
                'リピート率', '承認率', 'ペナルティ点数', '調整係数'
            ],
            '重み': [
                weights['requests'],
                weights['call_time'],
                weights['waiting_time'],
                weights['active_days'],
                weights['repeat_rate'],
                weights['approval_rate'],
                weights['penalty_points'],
                adjustment_factor
            ],
            '減少閾値': [
                '',  # リクエスト数には減少条件なし
                decrease_thresholds.get('call_time', ''),
                decrease_thresholds.get('waiting_time', ''),
                decrease_thresholds.get('active_days', ''),
                '',  # リピート率には減少条件なし
                decrease_thresholds.get('approval_rate', ''),
                decrease_thresholds.get('penalty_points', ''),
                ''  # 調整係数には減少条件なし
            ]
        })

        st.write('設定条件:', settings_summary)

        # 次週価格の計算
        for index, row in data.iterrows():
            next_price = calculate_dynamic_pricing(
                current_price=row['今週の価格'],
                adjustment_factor=adjustment_factor,
                weeks=1,
                requests=row['リクエスト数'],
                call_time=row['通話時間'],
                waiting_time=row['待機時間'],
                active_days=row['アクティブ日数'],
                repeat_rate=row['リピート率'],
                penalty_points=row['ペナルティ点数'],
                approval_rate=row['承認率'],
                weight_requests=weights['requests'],
                weight_call_time=weights['call_time'],
                weight_waiting_time=weights['waiting_time'],
                weight_active_days=weights['active_days'],
                weight_repeat_rate=weights['repeat_rate'],
                weight_penalty_points=weights['penalty_points'],
                weight_approval_rate=weights['approval_rate'],
                decrease_thresholds=decrease_thresholds
            )
            data.loc[index, '次週価格'] = round(next_price[-1])  # 四捨五入して最終価格を取得
            data.loc[index, '増減金額'] = round(next_price[-1] - row['今週の価格']) 

        st.write('次週価格:', data)

        # 空の列を作成
        empty_col = pd.DataFrame([''] * data.shape[0], columns=[''])

        # 計算後のデータと設定条件のログを結合してCSVとしてダウンロード
        combined_data = pd.concat([data, empty_col, settings_summary], axis=1)

        # ファイル名の設定
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f'nextweek_prices_{current_time}.csv'
        
        # CSVとしてダウンロード
        st.download_button(
            label="計算結果と設定条件をダウンロード",
            data=combined_data.to_csv(index=False).encode('utf-8'),
            file_name=file_name,
            mime='text/csv',
        )
