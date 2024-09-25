import pickle
from pathlib import Path
from datetime import date
import pandas as pd  # pip install pandas openpyxl
import plotly.express as px  # pip install plotly-express
import streamlit as st  # pip install streamlit
import streamlit_authenticator as stauth  # pip install streamlit-authenticator
import streamlit.components.v1 as components
from typing import List, Union, Generator, Iterator, Dict

import yaml
from yaml.loader import SafeLoader
# from userprofile import user_profile
from chat_ui import chatui


# Function to authenticate a user
def authenticate_user(username, password):
    return True

def clear_chat_history():
    st.session_state.messages = []
    
sh = ""
context_history: List[Dict[str, str]] = []


# st.set_page_config(page_title="Valorant ChatBot", page_icon=":video_game:", layout="wide")
st.set_page_config(
    page_title="EG GenAIBot",
    page_icon="./images/img.png",
    layout="wide",
    initial_sidebar_state="expanded",
)
#show logo
logo = "./images/logo.png"
st.sidebar.image(logo, use_column_width=True)
st.markdown("""
<style>
    #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.st-emotion-cache-bm2z3a.ea3mdgi8 > div.block-container.st-emotion-cache-1jicfl2.ea3mdgi5 > div > div {
            width: 600px;
            margin : auto;
    }
</style>
""", unsafe_allow_html=True)
# st.logo(logo)
# st.html("""
#      <style>
#      [alt=Logo] {height: 5rem;}
#      </style>
#      """)

#load csv files  
df_video = pd.read_csv('./EG_Youtube.csv')
df = pd.read_csv('./egr_eg_results.csv')   


name, authentication_status, username = 'Tanya', True, 'Tanya'


if authentication_status == False:
    st.error("Username/password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password")
#----------------------------------------LOGIN----------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.subheader("Admin Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, _, _, col2 = st.columns([1, 2, 1, 1])
    userflag = 999
    with col1:
        if st.button("Login"):
            user = authenticate_user(username, password)
            if user:
                userflag = 1
            else:
                userflag = 0
    with col2:
        if st.button("Sign Up"):
            st.info("Please use the 'Sign Up' option in the menu.")
    if userflag == 1:
        st.success(f"Logged in as {username}")
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.password = password
        st.rerun()
    elif userflag == 0:
        st.error("Invalid username or password")
#----------------------------------------LOGIN ENDS-----------------------------------------------


else:
    # Get the current year
    current_year = date.today().year
    # Get the first day of the current year
    first_day_of_year = date(current_year, 1, 1)
# if authentication_status: 
     # ---- SIDEBAR ----
    with st.sidebar:
        with st.expander("Game Options"):
            # st.multiselect("Select Game Version", ["V1", "V2", "V3"])
            st.multiselect("Select Game Version", df['game_version'].unique())
            date = st.date_input("Choose Dates", value=(date.today(), date.today()))
            # date = st.date_input("Choose Dates")
            st.multiselect("Select Team", df['team'].unique())
            st.multiselect("Select Opponent Team", df['opponent_team'].unique())
            st.multiselect("Select Map", df['map_name'].unique())
            game_id = st.multiselect("Select Game IDs", df['game_id'].unique())
            st.button("Filter")
            # with st.expander("Chat History"):
         # st.button('Clear Chat History', on_click=clear_chat_history)
        # authenticator.logout("Logout", "sidebar")
         # sh = st.button("Show History")
    # st.write("History shown here")
        # st.write("______________________")
        # components.html(user_profile(name), height=300, width=300)

     # ---- MAINPAGE ----

        st.markdown("""
            <style>
            .st-e6 {
                background-color: white;
            }
            .stTabs [data-baseweb="tab"] {
                background-color: #f0f0f0;
                color: black;
                padding: 15px;
                border-radius: 5px;
                margin-right: 5px;
                cursor: pointer;
            }
            .stTabs [data-baseweb="tab"]:hover {
                background-color: #25325f;
                color: white;
            }
            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                background-color: #25325f;
                color: white;
                border: 2px solid blue;
            }
            .stTabs button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
            font-size: 20px;
            }
        </style>
        """, unsafe_allow_html=True)

    
    tab1, tab2 = st.tabs(["Chat","Display Video"])
       
    with tab1:
        chatui(game_id, date, context_history)
    with tab2:
        if game_id:
            st.video(df_video[df_video['game_id']==game_id[0]]['Video'].iloc[0])
        else:
            st.write("Select game id from sidebar")
                 
    reduce_space = """
         <style>
         .block-container
         {
             padding-top: 0rem;
             padding-bottom: 0rem;
             margin-top: 0rem;
         }
         </style>"""
    st.markdown(reduce_space, unsafe_allow_html=True)
     
    # ---- HIDE STREAMLIT STYLE ----
    hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
    st.markdown(hide_st_style, unsafe_allow_html=True)
    hide_streamlit_style = """
        <style>
        .css-hi6a2p {padding-top: 0rem;}
        </style>

        """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)