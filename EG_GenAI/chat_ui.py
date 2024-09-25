import streamlit as st
import random
import time

import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List, Union, Generator, Iterator, Dict
import os
from pydantic import BaseModel
from llama_index.llms.ollama import Ollama
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core import SQLDatabase, PromptTemplate
import aiohttp
import asyncio
from datetime import datetime
import streamlit_chat


connection_params = {
    'database': 'eg_valorant',
    'user': 'udaya',
    'password': '&ETa$Tdj9z7msLo#',
    'host': '216.151.12.162',
    'port': '4928'
}

engine = create_engine(f"postgresql+psycopg2://{connection_params['user']}:{connection_params['password']}@{connection_params['host']}:{connection_params['port']}/{connection_params['database']}")

sql_database = SQLDatabase(engine, include_tables=["egr_results"], schema="grid_valorant_hpe")

llm = Ollama(model='llama3.1:latest', context_window=30000, request_timeout=300.0)


def extract_sql_query(response_object):
    for key, value in response_object.items():
        if isinstance(value, dict) and 'sql_query' in value:
            return value['sql_query']
        elif key == 'sql_query':
            return value
            
    return None


def handle_streaming_response(response_gen):
    # Process the streaming response and convert it to a single string
    response_list = list(response_gen)
    return "".join(response_list)

 
def chat_bot(user_query, game_id, date, context_history):


    # Few-shot examples as context
    few_shot_examples = [
        {
            "query": "Give me players from EG",
            "response": "SELECT DISTINCT player FROM egr_results WHERE team = 'EG';"
        },
        {
            "query": "Give me how many rounds Team EG has won",
            "response": "WITH unique_outcomes AS (SELECT DISTINCT round_num, team, game_id, won FROM egr_results) SELECT game_id, team, COUNT(*) AS rounds_won FROM unique_outcomes WHERE won = True GROUP BY game_id, team HAVING team = 'EG';"
        },
        {
            "query": "Give me how many kills each round player JAWGEMO has got",
            "response": "SELECT round_num, game_id, SUM(kill_change) AS total_kills FROM egr_results WHERE player = 'JAWGEMO' GROUP BY round_num, game_id;"
        },
        {
            "query": "Give me how many kills did EG team get in each round",
            "response": "SELECT round_num, game_id, SUM(kill_change) AS total_kills FROM egr_results WHERE Team = 'EG' GROUP BY round_num, game_id;"
        },
        {
            "query": "Find all rounds where player JAWGEMO had a kill and an assist",
            "response": "WITH jawgemo_data AS (SELECT DISTINCT game_id, round_num, kill_change, assists FROM egr_results WHERE player = 'JAWGEMO' AND kill_change > 0 AND assists > 0) SELECT game_id, round_num, kill_change, assists FROM jawgemo_data;"
        },
        {
            "query": "Find all rounds that were close (at some point in round, it was a 2v2 or 3v3 for at least 5 seconds)",
            "response": "WITH filtered_events AS (SELECT *, seconds - LAG(seconds, 1, seconds) OVER (PARTITION BY round_num, game_id ORDER BY seconds) AS time_diff FROM egr_results WHERE our_team_alive IN (2, 3) AND opponent_team_alive IN (2, 3)), grouped_events AS (SELECT round_num, game_id, SUM(time_diff) AS total_time_diff FROM filtered_events GROUP BY round_num, game_id) SELECT round_num, game_id FROM grouped_events WHERE total_time_diff >= 5;"
        }
    ]

    # Build the few-shot context
    context_prompt = "\n".join([f"Q: {example['query']}\nA: {example['response']}" for example in few_shot_examples])

    # Define the final prompt with few-shot examples
    text_to_sql_prompt = f"""
    {context_prompt}

    You are a highly experienced Postgres SQL expert with over 15 years of expertise in converting text descriptions into efficient SQL queries.
    Your task is to convert the following text into a Postgres SQL query.

    Keep the following in mind:
    - Use the correct syntax and structure of Postgres SQL.
    - Include all relevant details (e.g., table names, column names, conditions).
    - Use a LIMIT of 5 results unless specified otherwise.
    - Avoid SELECT *; only select relevant columns based on the question.
    - Use DISTINCT to avoid duplicates where necessary.
    - Ensure column names match the schema provided.

    Respond in this format:
    SQLQuery: The SQL query to run
    SQLResult: The result of the SQL query
    Answer: Your final answer

    Only use tables from the schema below:
    {{schema}}

    Question: {{query_str}}
    SQLQuery:
    """

    text_to_sql_template = PromptTemplate(text_to_sql_prompt)
    
    print("text_to_sql_template: ", text_to_sql_template)

    
    query_engine = NLSQLTableQueryEngine(sql_database=sql_database,
                                         tables=["egr_results"],
                                         llm=llm,
                                         embed_model="local",
                                         text_to_sql_prompt=text_to_sql_template,
                                         streaming=True
                                        )


    print("game id selected: ", game_id)
    print("date selected: ", date)

    if game_id:
        user_prompt = f"""Where game_id in {game_id}"""
        # query = f"""Show me players with both kills and assits from EG team? {user_prompt}"""
        query = f"""{user_query} \n {user_prompt}"""
    else:
        query = f"""{user_query}"""

    print("user_query: ", query)

    s = datetime.now()
    
    response = query_engine.query(query)
    # print("response", response)
    print("type(response)", type(response))

    # Check if the response is indeed a streaming response
    if isinstance(response.response_gen, Generator):
        print("if part")
        final_response = handle_streaming_response(response.response_gen)
    else:
        # Fallback: if the response is a string (not streaming)
        print("else part")
        final_response = response.response
    
    e = datetime.now()
    print("Latency: ", (e-s).total_seconds())

    sql_query = extract_sql_query(response.metadata)
    print("sql_query: ", sql_query)
    
    # final_response = handle_streaming_response(response.response_gen)
    print("final_response: ", final_response)

    # final_response2 = handle_streaming_response(response.response)
    # print("final_response2: ", final_response2)

    # Save the current interaction to the context history
    context_history.append({
        'query': query,
        'response': final_response
    })

    print("before appending context history:", context_history)

    # Limit the context history to the last 5 interactions for example
    context_history = context_history[-5:]
    print("appended context history:", context_history)

    result = f"Generated SQL Query:\n```sql\n{sql_query}\n```\nResponse:\n{final_response}"
    print("final final result", result)

    # return result
    return sql_query, final_response


# def get_chat_answer(query, game_id, date, context_history):
#     if st.session_state.messages and st.session_state.messages[-1]["role"] != "assistant":
#         with st.chat_message("assistant"):
#             with st.spinner("Thinking..."):
#                 response = chat_bot(query, game_id, date, context_history)
#                 placeholder = st.empty()
#                 # Simulate typing out the response one character at a time
#                 for i in range(len(response) + 1):
#                     partial_response = response[:i]
#                     placeholder.markdown(partial_response)
#                     time.sleep(0.03)  # Adjust the speed of typing here
#                 # Append the full response to the messages
#                 message = {"role": "user", "content": response}
#                 st.session_state.messages.append(message)


example_user_prompts = [
    "find all rounds where player X had a kill and an assist",
    "find all rounds where player X got the first kill and ended with EGR > .2",
    "find all rounds that were close (at some point in round, it was a 2v2 or 3v3 for at least 5 seconds)",
]


def move_focus():
    # inspect the html to determine which control to specify to receive focus (e.g. text or textarea).
    st.components.v1.html(
        f"""
            <script>
                var textarea = window.parent.document.querySelectorAll("textarea[type=textarea]");
                for (var i = 0; i < textarea.length; ++i) {{
                    textarea[i].focus();
                }}
            </script>
        """,
    )


def userid_change():
    st.session_state.userid = st.session_state.userid_input
    
    
def complete_messages(nbegin,nend, query, game_id, date, context_history,stream=False):
    messages = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]
    # with st.spinner(f"Waiting for {nbegin}/{nend} responses from EG ChatBot."):
    with st.spinner(f"Waiting for response from EG ChatBot."):
        sql_query, final_response = chat_bot(query, game_id, date, context_history)       
    return sql_query, final_response



def chatui(game_id, date, context_history):        
    # st.title("ChatBot")
    
    # Initialize chat history
    # if "messages" not in st.session_state:
    #     st.session_state.messages = []

    # # Display chat messages from history on app rerun
    # for message in st.session_state.messages:
    #     with st.chat_message(message["role"]):
    #         st.markdown(message["content"])
    # if prompt := st.chat_input():
    #     st.session_state.messages.append({"role": "user", "content": prompt})
    #     with st.chat_message("user"):
    #         st.write(prompt)
    #     get_chat_answer(prompt, game_id, date, context_history)   
    #     st.session_state.messages.append({"role": "user", "content": prompt})


    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # with st.container():
    #     st.title("EG ChatBot")

    if st.sidebar.button("Clear Conversation", key='clear_chat_button'):
        st.session_state.messages = []
        move_focus()
    for i,message in enumerate(st.session_state.messages):
        nkey = int(i/2)
        if message["role"] == "user":
            streamlit_chat.message(message["content"], is_user=True, avatar_style="adventurer", key='chat_messages_user_'+str(nkey))
        else:
            streamlit_chat.message(message["content"], is_user=False, key='chat_messages_assistant_'+str(nkey))

    if user_content := st.chat_input("Type your question here."):
        nkey = int(len(st.session_state.messages)/2)
        streamlit_chat.message(user_content, is_user=True, avatar_style="adventurer",seed=44, key='chat_messages_user_'+str(nkey))
        # st.session_state.messages.append({"role": "user", "content": user_content})
        llm_generated_sql, assistant_content = complete_messages(0,1,user_content, game_id, date, context_history)
        # streamlit_chat.message(assistant_content,avatar_style="avataaars", key='chat_messages_assistant_'+str(nkey))
        streamlit_chat.message(assistant_content,avatar_style="adventurer",seed=44, key='chat_messages_assistant_'+str(nkey))
        # st.session_state.messages.append({"role": "assistant", "content": assistant_content})
        #len(st.session_state.messages)

    # Accept user input
    # if prompt := st.chat_input("What is up?"):
    #     # Display user message in chat message container
    #     with st.chat_message("user"):
    #         st.markdown(prompt)
    #     # Add user message to chat history

    #     with st.chat_message("assistant"):
    #         user_query = prompt
    #         result = chat_bot(user_query)
    #         text_response = st.write(result)