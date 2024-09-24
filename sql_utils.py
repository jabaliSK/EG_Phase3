import pandas as pd
import psycopg2
from sqlalchemy import create_engine, inspect
import json
import sys
import os

def load_config(config_file='config.json'):
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not parse the configuration file '{config_file}'.")
        sys.exit(1)

def upload_csv_to_postgres(db_params, file_path, table_name):
    try:
        # Step 1: Read the CSV file into a DataFrame and drop columns with "Unnamed" in their names
        df = pd.read_csv(file_path)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

        # Step 2: Connect to PostgreSQL
        engine = create_engine(f"postgresql+psycopg2://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}")
        with engine.connect() as connection:
            # Extract schema and table names
            schema_name, bare_table_name = table_name.split('.')

            # Step 3: Check if table exists
            inspector = inspect(engine)
            if bare_table_name in inspector.get_table_names(schema=schema_name):
                # Step 4: Insert data into the existing table
                df.to_sql(bare_table_name, con=connection, schema=schema_name, if_exists='append', index=False)
            else:
                # Step 3: Create the table and insert data
                df.to_sql(bare_table_name, con=connection, schema=schema_name, if_exists='replace', index=False)

        print(f"Data from {file_path} has been successfully uploaded to the {table_name} table.")
        
    except pd.errors.EmptyDataError:
        print(f"Error: The file {file_path} is empty.")
    except pd.errors.ParserError as e:
        print(f"Error: Could not parse the file {file_path}: {e}")
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except Exception as error:
        print(f"Error uploading data: {error}")

def fetch_data_from_table(columns='*', conditions=None):
    
    config = load_config()
    
    db_params=config['db_params']
    table_name=config['table_name']
    """
    Fetch data from the specified table with optional filters.
    
    :param db_params: Dictionary with connection parameters (host, port, user, password, dbname).
    :param table_name: Schema-qualified table name (e.g., 'schema.table').
    :param columns: Columns to select, defaults to '*' (all columns).
    :param conditions: SQL WHERE clause conditions (optional).
    :return: Pandas DataFrame containing the query results.
    """
    try:
        # Step 1: Connect to PostgreSQL
        engine = create_engine(f"postgresql+psycopg2://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}")
        with engine.connect() as connection:
            # Step 2: Build the SQL query
            query = f"SELECT {columns} FROM {table_name}"
            if conditions:
                query += f" WHERE {conditions}"

            # Step 3: Execute the query and fetch the data into a DataFrame
            df = pd.read_sql(query, connection)

        return df

    except Exception as error:
        print(f"Error fetching data: {error}")
        return pd.DataFrame()

def delete_table(db_params, table_name):
    """
    Delete the specified table from the database after user confirmation.
    
    :param db_params: Dictionary with connection parameters (host, port, user, password, dbname).
    :param table_name: Schema-qualified table name (e.g., 'schema.table').
    """
    try:
        # Step 1: Connect to PostgreSQL
        engine = create_engine(f"postgresql+psycopg2://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}")
        with engine.connect() as connection:
            # Extract schema and table names
            schema_name, bare_table_name = table_name.split('.')

            # Step 2: Check if table exists
            inspector = inspect(engine)
            if bare_table_name in inspector.get_table_names(schema=schema_name):
                # Step 3: Ask for user confirmation
                confirmation = input(f"Are you sure you want to delete the table '{table_name}'? This action cannot be undone. (yes/no): ").strip().lower()
                if confirmation == 'yes':
                    # Step 4: Delete the table
                    connection.execute(f"DROP TABLE {schema_name}.{bare_table_name} CASCADE")
                    print(f"Table '{table_name}' has been deleted successfully.")
                else:
                    print("Table deletion canceled.")
            else:
                print(f"Table '{table_name}' does not exist in the database.")
    
    except Exception as error:
        print(f"Error deleting table: {error}")

config = load_config()


if __name__ == "__main__":
    # Load configuration
    

    # Get the file path from command line arguments
    if len(sys.argv) < 2:
        print("Error: Please provide the CSV file path as an argument.")
        sys.exit(1)

    csv_file_path = sys.argv[1]

    # Ensure the file exists
    if not os.path.exists(csv_file_path):
        print(f"Error: The file '{csv_file_path}' does not exist.")
        sys.exit(1)

    # Example usage
    action = input("Choose an action: upload or delete: ").strip().lower()

    if action == 'upload':
        # Upload CSV to PostgreSQL
        upload_csv_to_postgres(config['db_params'], csv_file_path, config['table_name'])

    elif action == 'delete':
        # Delete table from PostgreSQL
        delete_table(config['db_params'], config['table_name'])

    else:
        print("Invalid action. Please choose 'upload' or 'delete'.")
