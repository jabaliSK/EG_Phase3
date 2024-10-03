
## Overview
 EG GenAIBot  is a Streamlit-based application providing an interactive chat interface for querying a Valorant game database.

## Quick Start Guide

### Prerequisites
- Python 3.8+
- Packages: `pandas`, `plotly`, `streamlit`, `streamlit-authenticator`, `psycopg2`, `sqlalchemy`, `llama-index`, `streamlit-chat`
- Ollama (LLM model) installed. Visit [Ollama](https://ollama.com/) for installation details.

### Steps to Get Started


1.  Install Required Packages 
   ```bash
   pip install -r requirements.txt
   ```

2.  Install Ollama 
 
   - For other OS, follow instructions on [Ollama's website](https://ollama.com/).
   model used: llama3.1


3.  Configure Database Connection 
   - Modify `config.json` with your database connection details:
     ```json
     {
       "db_params": {
         "user": "your_db_user",
         "password": "your_db_password",
         "host": "your_db_host",
         "port": "your_db_port",
         "dbname": "your_db_name"
       },
       "table_name": "schema_name.table_name"
     }
     ```


4. 

PostgreSQL Integration: sql_utils.py
Uploads the prediction results (CSV) to PostgreSQL or deletes existing tables (optional if already uploaded , just change it in config file)
Steps to run :  

   ```bash
   python sql_utils.py results.csv
  
   ```
5.
.  Run the Application 
   ```bash
   streamlit run app.py
   ```
   - Open the provided URL (e.g., `http://localhost:8501`) in your web browser.

### Usage
-  Login : Enter username and password to access the chat interface.
-  Sidebar : Use filters for game data.
-  Chat : Ask questions in natural language, and the bot will convert them into SQL queries to fetch data.
