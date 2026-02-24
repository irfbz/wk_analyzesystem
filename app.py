import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.lines as mlines

st.title('Rugby Match Analysis')

# ファイルアップロード
uploaded_files = st.file_uploader("Upload CSV files", accept_multiple_files=True, type="csv")

if uploaded_files:
    data_frames = []
    for file in uploaded_files:
        df = pd.read_csv(file)
        df['fileName'] = file.name
        data_frames.append(df)

    data = pd.concat(data_frames, ignore_index=True)

    if st.checkbox('Show data overview'):
        st.write(data.head())
        st.write("Unique action names:", data['actionName'].unique())
        st.write("Unique action result names:", data['ActionResultName'].unique())
        st.write("Unique action type names:", data['ActionTypeName'].unique())

    game_names = list(data['fileName'].unique())
    selected_games = st.multiselect('Select Games', options=game_names, default=game_names)
    data = data[data['fileName'].isin(selected_games)]

    if data.empty:
        st.warning("選択された試合にはデータが含まれていません。別の試合を選んでください。")
        st.stop()

    team_name = st.selectbox('Select Team', data['teamName'].unique())
    exclude_team = st.checkbox("Exclude selected team data?")

    if exclude_team:
        team_filtered_data = data[data['teamName'] != team_name]
    else:
        team_filtered_data = data[data['teamName'] == team_name]

    exclude_actions = ['Defensive Exits', 'Defensive Action', 'Counter Attack', 'Lineout Take', 'Period', 'Ref Review', 'Sub In', 'Sub Out', 'Card']
    filtered_action_names = [action for action in data['actionName'].unique() if action not in exclude_actions and pd.notna(action)]

    sorted_action_names = ['Kick', 'Attacking Qualities', 'Penalty Conceded', 'Goal Kick', 'Tackle', 'Missed Tackle', 'Carry', 'Ruck', 'Ruck OOA', 'Playmaker Options', 'Attacking 22 Entry', 'Possession', 'Restart', 'Collection', 'Pass', 'Turnover', 'Sequences', 'Scrum', 'Lineout Throw', 'Try', 'Maul']
    filtered_action_names = [action for action in sorted_action_names if action in filtered_action_names]

    action_name = st.selectbox('Select Action', filtered_action_names)

    filtered_data = team_filtered_data[team_filtered_data['actionName'] == action_name]

    player_name = st.selectbox('Select Player (optional)', ['All'] + list(filtered_data['playerName'].unique()))
    if player_name != 'All':
        filtered_data = filtered_data[filtered_data['playerName'] == player_name]

    time_min = int(filtered_data['MatchTime'].min())
    time_max = int(filtered_data['MatchTime'].max())
    time_range = st.slider('Select time range', min_value=time_min, max_value=time_max, value=(time_min, time_max))
    filtered_data = filtered_data[(filtered_data['MatchTime'] >= time_range[0]) & (filtered_data['MatchTime'] <= time_range[1])]

    details = filtered_data[['playerShirtNumber', 'playerName', 'x_coord', 'y_coord', 'x_coord_end', 'y_coord_end', 'ActionTypeName', 'ActionResultName']]
    action_type = st.selectbox('Select Action Type (optional)', ['All'] + list(details['ActionTypeName'].unique()))
    if action_type != 'All':
        details = details[details['ActionTypeName'] == action_type]

    display_option = st.selectbox('Select Display Option', ['ActionResultName', 'ActionTypeName'])
    show_heatmap = st.checkbox('Show Heatmap')

    if show_heatmap:
        bw_adjust = st.slider('Adjust Heatmap Bandwidth', 0.1, 1.0, 0.4)

    fig, ax = plt.subplots(figsize=(12, 8))

    if show_heatmap:
        sns.kdeplot(x=details['x_coord'], y=details['y_coord'], fill=True, cmap='Reds', ax=ax, bw_adjust=bw_adjust)
    else:
        sns.scatterplot(x=details['x_coord'], y=details['y_coord'], hue=details[display_option], palette='bright', ax=ax)
        sns.scatterplot(x=details['x_coord_end'], y=details['y_coord_end'], hue=details[display_option], palette='bright', ax=ax, marker='X', s=100, legend=False)

        for _, row in details.iterrows():
            if not (row['x_coord_end'] == 0 and row['y_coord_end'] == 0):
                ax.plot([row['x_coord'], row['x_coord_end']], [row['y_coord'], row['y_coord_end']], color='grey', linestyle='--')

    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    ax.set_xlim(0, 100)
    ax.set_ylim(68, 0)
    ax.set_xticks([0, 22, 40, 50, 60, 78, 100])
    ax.set_xticklabels(['0m', '22m', '10m', 'Half', '10m', '22m', '0m'])
    ax.axvline(x=22, color='grey', linestyle='--')
    ax.axvline(x=40, color='grey', linestyle='--')
    ax.axvline(x=60, color='grey', linestyle='--')
    ax.axvline(x=78, color='grey', linestyle='--')
    ax.axvline(x=50, color='black', linestyle='-')

    if not show_heatmap:
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[:len(details[display_option].unique())], labels[:len(details[display_option].unique())])

    st.pyplot(fig)

    st.write(f"Player involvement in {action_type} Actions by {display_option}:")
    pivot_table = details.pivot_table(index=['playerShirtNumber', 'playerName'], columns=display_option, aggfunc='size', fill_value=0)
    pivot_table['Total'] = pivot_table.sum(axis=1)
    pivot_table = pivot_table[['Total'] + [col for col in pivot_table.columns if col != 'Total']]
    pivot_table.index.set_names(['No.', 'Player'], inplace=True)
    pivot_table = pivot_table.replace(0, '')
    st.write(pivot_table)

    st.write(f"Results for {action_type} Actions by {display_option}:")
    st.write(details[display_option].value_counts())

    # -----------------------------
    # Attack Area
    # -----------------------------
    st.subheader("Attack Area")
    if 'qualifier5Name' in data.columns:
        movement_rows = data[
            (data['qualifier5Name'].str.contains("Movement", na=False)) &
            (data['teamName'] == team_name)
        ]

        def classify_movement_zone(q5):
            q5 = str(q5).lower()
            if 'close' in q5:
                return 'Close'
            elif 'mid' in q5:
                return 'Mid'
            elif 'tight' in q5:
                return 'Tight'
            elif 'wide' in q5:
                return 'Wide'
            else:
                return 'N/A'

        movement_rows['ZoneCategory'] = movement_rows['qualifier5Name'].apply(classify_movement_zone)
        movement_table = movement_rows[['actionName', 'qualifier5Name', 'ZoneCategory']].drop_duplicates()

        filtered_rows = movement_rows[movement_rows['ZoneCategory'] != 'N/A']


        fig_mv, ax_mv = plt.subplots(figsize=(12, 8))

        marker_styles = {
            'Ruck': 'o',           # Circle
            'Maul': 'X',           # X-large
            'Lineout Throw': 's',  # Square
            'Scrum': '^'           # Triangle
        }

        zone_colors = {
            'Close': '#D7263D',
            'Mid': '#1B9AAA',
            'Tight': '#119822',
            'Wide': '#F29E38'
        }

        for _, row in filtered_rows.iterrows():
            action = row['actionName']
            zone = row['ZoneCategory']
            marker = marker_styles.get(action, 'o')
            color = zone_colors.get(zone, 'gray')
            ax_mv.scatter(row['x_coord'], row['y_coord'], color=color, marker=marker, s=120, edgecolor='black', linewidth=0.5)

        # Action Legend (Marker)
        action_handles = [
            mlines.Line2D([], [], color='black', marker=marker_styles[a], linestyle='None', markersize=10, label=a)
            for a in marker_styles.keys()
        ]
        action_legend = ax_mv.legend(handles=action_handles, title='Action (Marker)', loc='upper right')
        ax_mv.add_artist(action_legend)

        # Zone Legend (Color)
        zone_handles = [
            mlines.Line2D([], [], color=color, marker='o', linestyle='None', markersize=10, label=z)
            for z, color in zone_colors.items()
        ]
        ax_mv.legend(handles=zone_handles, title='Zone (Color)', loc='lower right')

        ax_mv.set_xlabel('X Coordinate')
        ax_mv.set_ylabel('Y Coordinate')
        ax_mv.set_xlim(0, 100)
        ax_mv.set_ylim(68, 0)
        ax_mv.set_xticks([0, 22, 40, 50, 60, 78, 100])
        ax_mv.set_xticklabels(['0m', '22m', '10m', 'Half', '10m', '22m', '0m'])
        ax_mv.axvline(x=22, color='grey', linestyle='--')
        ax_mv.axvline(x=40, color='grey', linestyle='--')
        ax_mv.axvline(x=60, color='grey', linestyle='--')
        ax_mv.axvline(x=78, color='grey', linestyle='--')
        ax_mv.axvline(x=50, color='black', linestyle='-')

        st.pyplot(fig_mv)

        # --- Pie Chart Filter（All / Scrum / Lineout Throw） ---
        pie_filter = st.selectbox(
            "Pie Chart Filter",
            options=["All", "Scrum", "Lineout Throw"],
            index=0
        )

        if pie_filter == "All":
            pie_rows = filtered_rows
        else:
            pie_rows = filtered_rows[filtered_rows["actionName"] == pie_filter]

        # --- Pie Chart（順番固定：Tight → Close → Mid → Wide、12時スタート・時計回り） ---
        zone_order = ['Tight', 'Close', 'Mid', 'Wide']
        zone_counts = (
            pie_rows['ZoneCategory']
            .value_counts()
            .reindex(zone_order, fill_value=0)
        )

        # Guard for empty data before pie chart
        if pie_rows.empty:
            st.info("選択された条件（Pie Chart Filter）に該当するデータがありません。")
        else:
            fig_zone, ax_zone = plt.subplots()
            ax_zone.pie(
                zone_counts,
                labels=zone_counts.index,
                autopct='%1.1f%%',
                colors=[zone_colors.get(z, 'gray') for z in zone_counts.index],
                startangle=90,        # 12時スタート
                counterclock=False    # 時計回り
            )
            st.pyplot(fig_zone)


    else:
        st.info("'qualifier5Name' column is not found in the dataset.")