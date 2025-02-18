import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.title('Rugby Match Analysis')

# ファイルアップロード
uploaded_files = st.file_uploader("Upload CSV files", accept_multiple_files=True, type="csv")

if uploaded_files:
    # 各ファイルに対応するデータフレームを作成し、ファイル名を追加
    data_frames = []
    for file in uploaded_files:
        df = pd.read_csv(file)
        df['fileName'] = file.name
        data_frames.append(df)
    
    # すべてのデータフレームを統合
    data = pd.concat(data_frames, ignore_index=True)

    # データフレームの概要表示（初回実行時の確認用）
    if st.checkbox('Show data overview'):
        st.write(data.head())
        st.write("Unique action names:", data['actionName'].unique())
        st.write("Unique action result names:", data['ActionResultName'].unique())
        st.write("Unique action type names:", data['ActionTypeName'].unique())

    # チームの選択
    team_name = st.selectbox('Select Team', data['teamName'].unique())
    # 選択したチームを除外するかどうかのチェックボックス
    exclude_team = st.checkbox("Exclude selected team data?")

    # 試合の選択
    game_names = ['All'] + list(data['fileName'].unique())
    selected_game = st.selectbox('Select Game', game_names)
    if selected_game != 'All':
        data = data[data['fileName'] == selected_game]

    # チームフィルタリングの適用（除外する場合と通常の場合）
    if exclude_team:
        team_filtered_data = data[data['teamName'] != team_name]
    else:
        team_filtered_data = data[data['teamName'] == team_name]

    # アクション名の不要な項目をフィルタリング
    exclude_actions = ['Defensive Exits', 'Defensive Action', 'Counter Attack', 'Lineout Take', 'Period', 'Ref Review', 'Sub In', 'Sub Out', 'Card']
    filtered_action_names = [action for action in data['actionName'].unique() if action not in exclude_actions and pd.notna(action)]

    # アクション名の選択順序を指定
    sorted_action_names = ['Kick', 'Attacking Qualities', 'Penalty Conceded', 'Goal Kick', 'Tackle', 'Missed Tackle', 'Carry', 'Ruck', 'Ruck OOA', 'Playmaker Options', 'Attacking 22 Entry', 'Possession', 'Restart', 'Collection', 'Pass', 'Turnover', 'Sequences', 'Scrum', 'Lineout Throw', 'Try', 'Maul']
    filtered_action_names = [action for action in sorted_action_names if action in filtered_action_names]

    # アクション名の選択
    action_name = st.selectbox('Select Action', filtered_action_names)

    # チームとアクション名でフィルタリング
    filtered_data = team_filtered_data[team_filtered_data['actionName'] == action_name]

    # 通常のアクションの処理（選手名でのフィルタリング）
    player_name = st.selectbox('Select Player (optional)', ['All'] + list(filtered_data['playerName'].unique()))
    if player_name != 'All':
        filtered_data = filtered_data[filtered_data['playerName'] == player_name]

    # 時間のスライダー
    time_min = int(filtered_data['MatchTime'].min())
    time_max = int(filtered_data['MatchTime'].max())
    time_range = st.slider('Select time range', min_value=time_min, max_value=time_max, value=(time_min, time_max))

    # 時間でフィルタリング
    filtered_data = filtered_data[(filtered_data['MatchTime'] >= time_range[0]) & (filtered_data['MatchTime'] <= time_range[1])]

    details = filtered_data[['playerShirtNumber', 'playerName', 'x_coord', 'y_coord', 'x_coord_end', 'y_coord_end', 'ActionTypeName', 'ActionResultName']]
    action_type = st.selectbox('Select Action Type (optional)', ['All'] + list(details['ActionTypeName'].unique()))
    if action_type != 'All':
        details = details[details['ActionTypeName'] == action_type]

    # 表示する情報の選択（ActionResultName または ActionTypeName）
    display_option = st.selectbox('Select Display Option', ['ActionResultName', 'ActionTypeName'])

    # 散布図とヒートマップの切り替え
    show_heatmap = st.checkbox('Show Heatmap')

    # KDEバンド幅調整用のスライダーを追加
    if show_heatmap:
        bw_adjust = st.slider('Adjust Heatmap Bandwidth', 0.1, 1.0, 0.4)

    # プロットの作成
    fig, ax = plt.subplots(figsize=(12, 8))

    if show_heatmap:
        # ヒートマップの作成
        sns.kdeplot(x=details['x_coord'], y=details['y_coord'], fill=True, cmap='Reds', ax=ax, bw_adjust=bw_adjust)
        ax.set_title(f"Heatmap for {team_name} - {action_name} Actions")
    else:
        # 散布図の作成
        sns.scatterplot(x=details['x_coord'], y=details['y_coord'], hue=details[display_option], palette='bright', ax=ax)
        sns.scatterplot(x=details['x_coord_end'], y=details['y_coord_end'], hue=details[display_option], palette='bright', ax=ax, marker='X', s=100, legend=False)

        # 起点と終点を線で結ぶ（終了点が(0, 0)でない場合）
        for _, row in details.iterrows():
            if not (row['x_coord_end'] == 0 and row['y_coord_end'] == 0):
                ax.plot([row['x_coord'], row['x_coord_end']], [row['y_coord'], row['y_coord_end']], color='grey', linestyle='--')

        ax.set_title(f"Scatter Plot for {team_name} - {action_name} Actions")

    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    ax.set_xlim(0, 100)  # フィールドの長さ
    ax.set_ylim(0, 68)  # フィールドの幅

    # カスタムx軸ラベルを設定
    ax.set_xticks([0, 22, 40, 50, 60, 78, 100])
    ax.set_xticklabels(['0m', '22m', '10m', 'Half', '10m', '22m', '0m'])

    # 破線と実線を追加
    ax.axvline(x=22, color='grey', linestyle='--')
    ax.axvline(x=40, color='grey', linestyle='--')
    ax.axvline(x=60, color='grey', linestyle='--')
    ax.axvline(x=78, color='grey', linestyle='--')
    ax.axvline(x=50, color='black', linestyle='-')

    # 凡例の設定（ヒートマップの場合は表示しない）
    if not show_heatmap:
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[:len(details[display_option].unique())], labels[:len(details[display_option].unique())])

    # Streamlitでプロットを表示
    st.pyplot(fig)

    # プレイヤーごとのアクション結果のカウントを表示
    st.write(f"Player involvement in {action_type} Actions by {display_option}:")
    pivot_table = details.pivot_table(index=['playerShirtNumber', 'playerName'], columns=display_option, aggfunc='size', fill_value=0)
    # 総数のカウントを追加
    pivot_table['Total'] = pivot_table.sum(axis=1)
    # 総数を一番左の列に移動
    pivot_table = pivot_table[['Total'] + [col for col in pivot_table.columns if col != 'Total']]
    # インデックス名をNo.に変更
    pivot_table.index.set_names(['No.', 'Player'], inplace=True)
    # 値が0のところを空白に置き換える
    pivot_table = pivot_table.replace(0, '')

    st.write(pivot_table)

    # アクションの結果を表示
    st.write(f"Results for {action_type} Actions by {display_option}:")
    st.write(details[display_option].value_counts())
