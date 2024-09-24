import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
from PIL import Image  # For loading images
from sql_utils import fetch_data_from_table

# Page configuration
st.set_page_config(
    page_title="Valorant Data Analysis",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enable dark theme for Altair charts
alt.themes.enable("dark")

# Sidebar Logo and File Upload
with st.sidebar:
    # Add Logo
    st.markdown("<h2 style='text-align: center;'>🎮 Valorant Analysis</h2>", unsafe_allow_html=True)
    logo_image = "./eglogo.jpg"  # Path to your local logo image
    try:
        logo = Image.open(logo_image)
        st.image(logo, use_column_width=True)
    except FileNotFoundError:
        st.warning("Logo image not found. Please ensure 'logo.png' is in the correct directory.")

    # Data Source Selection
    st.markdown("<h3 style='margin-top: 30px;'>Select Data Source</h3>", unsafe_allow_html=True)
    data_source = st.radio("Choose data source", options=["Upload CSV", "SQL Database"])

    if data_source == "Upload CSV":
        uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.success("File uploaded successfully!")
            except Exception as e:
                st.error(f"Error loading file: {e}")
                st.stop()
        else:
            st.info("Awaiting CSV file upload. Using sample data for now.")
            hardcoded_file = "./res.csv"
            df = pd.read_csv(hardcoded_file)  # Default sample dataset
            st.info(f"Reading data from {hardcoded_file}")

    elif data_source == "SQL Database":
        try:
            #hardcoded_file = "./res.csv"
            df =df =fetch_data_from_table()
            st.success("Data fetched from SQL database successfully!")
        except Exception as e:
            st.error(f"Error fetching data from SQL: {e}")
            st.stop()

# Required columns for analysis
required_columns = ['round_num', 'game_id', 'player', 'inventory_value', 'event_num',
                    'game_version', 'game_datetime', 'round_start_time', 'event_time',
                    'seconds', 'kills', 'assists', 'deaths', 'money', 'inventory',
                    'combat_score_round', 'combat_score_total', 'ability1_base_charges',
                    'ability1_max_charges', 'ability1_temp_charges',
                    'ability2_base_charges', 'ability2_max_charges',
                    'ability2_temp_charges', 'grenade_base_charges', 'grenade_max_charges',
                    'grenade_temp_charges', 'ultimate_base_charges', 'ultimate_max_charges',
                    'ultimate_temp_charges', 'hp', 'armor', 'x', 'y', 'z', 'velocity_x',
                    'velocity_y', 'velocity_z', 'view_x', 'view_y', 'view_z',
                    'spike_planted', 'clock_time', 'account_id', 'agent_id', 'team',
                    'agent_name', 'side', 'attacking_team', 'teamId_value', 'kill_change',
                    'death_change', 'is_alive', 'our_team_alive', 'our_team_health',
                    'team_inventory_value', 'spike_event', 'opponent_team',
                    'opponent_team_alive', 'opponent_team_health',
                    'opponent_team_inventory_value', 'ability1_base_charges_change',
                    'ability1_base_charges_gained', 'ability1_base_charges_used',
                    'ability2_base_charges_change', 'ability2_base_charges_gained',
                    'ability2_base_charges_used', 'grenade_base_charges_change',
                    'grenade_base_charges_gained', 'grenade_base_charges_used',
                    'ultimate_base_charges_change', 'ultimate_base_charges_gained',
                    'ultimate_base_charges_used', 'damage_dealt', 'damage_taken', 'kill_c',
                    'death_c', 'damage_dealt_c', 'damage_taken_c', 'player_kill_c',
                    'player_death_c', 'player_damage_dealt_c', 'player_damage_taken_c',
                    'opponent_kill_c', 'opponent_death_c', 'opponent_damage_dealt_c',
                    'opponent_damage_taken_c', 'spike_diffused', 'team_id', 'won',
                    'map_name', 'EGR','role']

# Function to validate columns
def validate_columns(df, required_columns):
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        st.error(f"The following required columns are missing from the dataset: {missing_cols}")
        return False
    return True

# Validate uploaded dataset
if not validate_columns(df, required_columns):
    st.stop()


# Sidebar Filters
with st.sidebar:
    st.markdown("<h3 style='margin-top: 30px;'>Filter Data</h3>", unsafe_allow_html=True)
    filter_won = st.multiselect('Select Win Status', options=df['won'].unique(), default=df['won'].unique())
    filter_players = st.multiselect('Select Players', options=df['player'].unique(), default=df['player'].unique())
    filter_game_version = st.multiselect('Select Game Version', options=df['game_version'].unique(), default=df['game_version'].unique())
    filter_team = st.multiselect('Select Team', options=df['team'].unique(), default=df['team'].unique())
    filter_side = st.multiselect('Select Side', options=df['side'].unique(), default=df['side'].unique())

# Filter dataframe based on selection
filtered_df = df[
    (df['won'].isin(filter_won)) &
    (df['player'].isin(filter_players)) &
    (df['game_version'].isin(filter_game_version)) &
    (df['team'].isin(filter_team)) &
    (df['side'].isin(filter_side))
]

# Convert date column to datetime
filtered_df['date'] = pd.to_datetime(filtered_df['game_datetime'])

# Page Title
st.markdown("<h1 style='text-align: center; margin-bottom: 50px;'>Valorant Data Analysis Dashboard</h1>", unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3 = st.tabs(["Player Stats", "Team Stats", "Model Stats"])

with tab1:
    st.markdown("<h2 style='font-size: 20px; text-align: center;'>Player Stats</h2>", unsafe_allow_html=True)

    # Filters Section
    st.markdown("<h3 style='font-size: 18px; text-align: center;'>Filters</h3>", unsafe_allow_html=True)

    # Date range filter
    start_date, end_date = st.date_input("Select date range", [filtered_df['date'].min().date(), filtered_df['date'].max().date()])
    filtered_df = filtered_df[(filtered_df['date'].dt.date >= start_date) & (filtered_df['date'].dt.date <= end_date)]

    # Game ID filter
    game_id = st.selectbox('Select Game ID', filtered_df['game_id'].unique())

    # Role filter
    selected_roles = st.multiselect('Select Roles', filtered_df['role'].unique(), default=filtered_df['role'].unique())

    # Agent name filter
    selected_agents = st.multiselect('Select Agent Names', filtered_df['agent_name'].unique(), default=filtered_df['agent_name'].unique())

    # Apply filters
    filtered_df_g1 = filtered_df[(filtered_df['game_id'] == game_id) & 
                              (filtered_df['role'].isin(selected_roles)) & 
                              (filtered_df['agent_name'].isin(selected_agents))]

    # Player Performance (EGR) Across Rounds
    st.markdown("<h3 style='font-size: 18px; text-align: center;'>Player Performance (EGR) Across Rounds</h3>", unsafe_allow_html=True)
    
    fig1 = alt.Chart(filtered_df_g1).mark_line(point=True).encode(
        x=alt.X('round_num', title='Round Number'),
        y=alt.Y('EGR', title='EGR'),
        color='player:N',
        tooltip=['round_num', 'EGR', 'player', 'team', 'won', 'role', 'agent_name']
    ).properties(
        title='Player Performance (EGR) Across Rounds'
    )

    st.altair_chart(fig1, use_container_width=True)

    # Overall EGR Per Player with Team, Role, and Agent Name Filters
    st.markdown("<h3 style='font-size: 18px; text-align: center;'>Overall EGR Per Player</h3>", unsafe_allow_html=True)
    
    selected_teams = st.multiselect('Select Teams to Highlight', filtered_df['team'].unique())
    
    apply_team_filter = st.button('Apply Team Filter')

    if apply_team_filter:
        overall_egr_per_player = filtered_df.groupby(['team', 'player', 'agent_name', 'role'])['EGR'].mean().reset_index()
        overall_egr_per_player["EGR"]=overall_egr_per_player["EGR"]*100
        overall_egr_per_player.sort_values('EGR', ascending=False, inplace=True)
        overall_egr_per_player.reset_index(drop=True, inplace=True)

        overall_egr_per_player['color'] = overall_egr_per_player['team'].apply(
            lambda x: 'rgba(39, 174, 96, 0.7)' if x in selected_teams else 'rgba(44, 62, 80, 0.7)'
        )

        fig2 = go.Figure(data=[go.Table(
            columnwidth=[80, 150, 150, 150, 80],
            header=dict(
                values=['<b>Team</b>', '<b>Player</b>', '<b>Agent Name</b>', '<b>Role</b>', '<b>Average EGR</b>'],
                fill_color='rgba(52, 73, 94, 1)',
                line_color='darkslategray',
                align='center',
                font=dict(color='white', size=14),
                height=40
            ),
            cells=dict(
                values=[
                    overall_egr_per_player['team'],
                    overall_egr_per_player['player'],
                    overall_egr_per_player['agent_name'],
                    overall_egr_per_player['role'],
                    overall_egr_per_player['EGR'].round(2)
                ],
                fill_color=[overall_egr_per_player['color']],
                line_color='darkslategray',
                align='center',
                font=dict(color='white', size=12),
                height=30
            )
        )])

        fig2.update_layout(
            title={'text': 'Overall EGR Per Player', 'x': 0.5, 'xanchor': 'center', 'font': {'size': 20}},
            margin=dict(l=20, r=20, t=50, b=20),
            height=600,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig2, use_container_width=True)

   # Shared Filters for Table and Chart
    st.markdown("<h3 style='font-size: 18px; text-align: center;'>Filters for Detailed Player Stats and Inventory Value vs EGR</h3>", unsafe_allow_html=True)

    selected_game_id = st.selectbox('Select Game ID for Table and Chart', df['game_id'].unique(), index=0)
    filtered_df_for_game = filtered_df[filtered_df['game_id'] == selected_game_id]

    selected_round_num = st.selectbox('Select Round Number', sorted(filtered_df_for_game['round_num'].unique()), index=0)
    available_players = sorted(filtered_df_for_game['player'].unique())
    selected_players = st.multiselect('Select Players', available_players, default=available_players)

    # Apply Button
    apply_filter = st.button('Apply Filters')

    if apply_filter:
        col1, col2 = st.columns([1, 1], gap="large")

        with col1:
            # Detailed Player Stats for Selected Game and Round
            st.markdown("<h3 style='font-size: 18px; text-align: center;'>Detailed Player Stats for Selected Game and Round</h3>", unsafe_allow_html=True)

            filtered_table_df = filtered_df_for_game[
                (filtered_df_for_game['round_num'] == selected_round_num) &
                (filtered_df_for_game['player'].isin(selected_players))
            ]

            table_display_df = (
                filtered_table_df.groupby('player').last()
                .sort_values(by='EGR', ascending=False)
                .reset_index()[['player', 'round_num', 'kills', 'assists', 'deaths', 'our_team_alive', 'opponent_team_alive', 'is_alive', 'combat_score_round', 'EGR', 'won']]
            )

            st.dataframe(table_display_df, use_container_width=True)

        with col2:
            # Inventory Value vs EGR for Selected Game and Round
            st.markdown("<h3 style='font-size: 18px; text-align: center;'>Inventory Value vs EGR for Selected Game and Round</h3>", unsafe_allow_html=True)

            # Group by game_id, round_num, and player, then take the first row
            filtered_data_chart = (
                filtered_df_for_game[filtered_df_for_game['round_num'] == selected_round_num]
                .groupby(['game_id', 'round_num', 'player', 'team'], as_index=False)
                .first()
            )

            # Define colors for different teams
            team_colors = {
                filtered_data_chart['team'].unique()[0]: 'lightblue',
                filtered_data_chart['team'].unique()[1]: 'orange'
            }
            filtered_data_chart['color'] = filtered_data_chart['team'].map(team_colors)

            # Create a dual-axis plot
            fig3 = go.Figure()

            # Add bar plot for original inventory values
            fig3.add_trace(go.Bar(
                x=filtered_data_chart['player'],
                y=filtered_data_chart['inventory_value'],
                name='Inventory Value',
                marker=dict(color=filtered_data_chart['color']),
                hovertemplate='<b>Player</b>: %{x}<br><b>Inventory Value</b>: %{y}<br><b>Team</b>: %{customdata}',
                customdata=filtered_data_chart['team'],  # Show team information on hover
                yaxis='y1'
            ))

            # Add line plot for EGR on a separate axis
            fig3.add_trace(go.Scatter(
                x=filtered_data_chart['player'],
                y=filtered_data_chart['EGR'],
                mode='lines+markers',
                name='EGR',
                line=dict(color='red'),
                yaxis='y2'
            ))

            # Update layout with two y-axes
            fig3.update_layout(
                title=f'Inventory Value and EGR for Game ID: {selected_game_id}, Round: {selected_round_num}',
                xaxis_title='Player',
                yaxis=dict(
                    title='Inventory Value',
                    titlefont=dict(color='lightblue'),
                    tickfont=dict(color='lightblue')
                ),
                yaxis2=dict(
                    title='EGR',
                    titlefont=dict(color='red'),
                    tickfont=dict(color='red'),
                    overlaying='y',
                    side='right'
                ),
                legend=dict(x=0.8, y=1.2, bgcolor='rgba(0,0,0,0)'),
                height=600,
                margin=dict(l=20, r=20, t=50, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )

            st.plotly_chart(fig3, use_container_width=True)





# Team Stats Tab
with tab2:
    st.markdown("<h2 style='font-size: 20px;'>Team Stats</h2>", unsafe_allow_html=True)
    
    # Filter by game_id with a unique key
    selected_game_id = st.selectbox('Select Game ID', df['game_id'].unique(), key='team_stats_game_id')
    filtered_df = df[df['game_id'] == selected_game_id]

    # Aggregate EGR scores for all players within each team and round
    team_round_egr = filtered_df.groupby(['team', 'round_num']).agg({'EGR': 'mean'}).reset_index()


    # Define team_game_egr_trend for EGR Score Trend Analysis
    team_game_egr_trend = filtered_df.groupby(['team', 'round_num']).agg({'EGR': 'mean', 'won': 'max'}).reset_index()

    # EGR Score Trend Analysis (Using Plotly)
    st.markdown("<h3 style='font-size: 18px;'>EGR Score Trend Analysis</h3>", unsafe_allow_html=True)
    fig2 = px.line(team_game_egr_trend, x='round_num', y='EGR', color='team', markers=True,
                   labels={'round_num': 'Round Number', 'EGR': 'Average EGR Score'},
                   title=f'EGR Score Trend Analysis for Game {selected_game_id}')
    
    # Add win markers
    for team in team_game_egr_trend['team'].unique():
        team_data = team_game_egr_trend[team_game_egr_trend['team'] == team]
        won_rounds = team_data[team_data['won'] == 1]
        fig2.add_trace(go.Scatter(
            x=won_rounds['round_num'], y=won_rounds['EGR'],
            mode='markers',
            marker=dict(size=12, color='gold', line=dict(width=2, color='black')),
            name=f'{team} Win'
        ))
    
    fig2.update_layout(title_font_size=20)
    st.plotly_chart(fig2, use_container_width=True)

    # EGR vs Combat Score (Using Plotly)
    st.markdown("<h3 style='font-size: 18px;'>EGR vs Combat Score</h3>", unsafe_allow_html=True)
    fig3 = px.scatter(filtered_df, x='combat_score_round', y='EGR', color='won',
                      trendline='ols', trendline_color_override='red',
                      labels={'combat_score_round': 'Combat Score', 'EGR': 'EGR Value'},
                      title='EGR vs Combat Score with Trend Line')
    fig3.update_layout(title_font_size=20)
    st.plotly_chart(fig3, use_container_width=True)





# Model Stats Tab
with tab3:


    grouped_df = df.groupby(['game_id', 'round_num', 'won']).agg({
    'EGR': 'mean',
    'combat_score_round': 'mean'}).reset_index()

    # Separate the data into won=True and won=False
    won_true = grouped_df[grouped_df['won'] == True]
    won_false = grouped_df[grouped_df['won'] == False]
    st.markdown("<h2 style='font-size: 20px;'>Model Stats</h2>", unsafe_allow_html=True)

    # EGR and Combat Score Distributions by Win Status
    st.markdown("<h3 style='font-size: 18px;'>EGR and Combat Score Distributions by Win Status</h3>", unsafe_allow_html=True)
    
    # Separate columns for won=True and won=False EGR
    st.markdown("#### EGR Distribution")
    col1, col2 = st.columns(2)

    with col1:
        fig_egr_true = px.histogram(
            won_true, 
            x="EGR", 
            nbins=20, 
            title="EGR Distribution (won=True)", 
            color_discrete_sequence=['blue']
        )
        fig_egr_true.update_layout(
            xaxis_title="EGR Values",
            yaxis_title="Frequency",
            title_font_size=20
        )
        st.plotly_chart(fig_egr_true, use_container_width=True)

    with col2:
        fig_egr_false = px.histogram(
            won_false, 
            x="EGR", 
            nbins=20, 
            title="EGR Distribution (won=False)", 
            color_discrete_sequence=['orange']
        )
        fig_egr_false.update_layout(
            xaxis_title="EGR Values",
            yaxis_title="Frequency",
            title_font_size=20
        )
        st.plotly_chart(fig_egr_false, use_container_width=True)

    # Separate columns for won=True and won=False Combat Score
    st.markdown("#### Combat Score Round Distribution")
    col3, col4 = st.columns(2)

    with col3:
        fig_combat_true = px.histogram(
            won_true, 
            x="combat_score_round", 
            nbins=20, 
            title="Combat Score Distribution (won=True)", 
            color_discrete_sequence=['blue']
        )
        fig_combat_true.update_layout(
            xaxis_title="Combat Score Round Values",
            yaxis_title="Frequency",
            title_font_size=20
        )
        st.plotly_chart(fig_combat_true, use_container_width=True)

    with col4:
        fig_combat_false = px.histogram(
            won_false, 
            x="combat_score_round", 
            nbins=20, 
            title="Combat Score Distribution (won=False)", 
            color_discrete_sequence=['orange']
        )
        fig_combat_false.update_layout(
            xaxis_title="Combat Score Round Values",
            yaxis_title="Frequency",
            title_font_size=20
        )
        st.plotly_chart(fig_combat_false, use_container_width=True)