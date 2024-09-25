# Valorant Player Scoring System

This project implements a pipeline for analyzing player performance in Valorant games using LSTM models and visualizing the results in a Streamlit-based dashboard. The workflow includes data extraction, preprocessing, model training, inference, and visualization.

## Project Structure:

1.  Python Notebook: `lstm_data_preparation.ipynb`   
   - Extracts data from a PostgreSQL database and prepares it for LSTM model training.  
   - Data is transformed and preprocessed, making it ready for the LSTM model.
   
    Steps to run :  
   Open the Jupyter notebook and execute the steps sequentially to preprocess your data. Ensure that your database credentials are configured correctly in the `config.json` file.

2.  Python Notebook: `lstm_model_training.ipynb`   
   - Trains an LSTM model using the combat score as the target variable.  
   - Evaluates the model's performance on validation data.

    Steps to run :  
   Open the Jupyter notebook and follow the steps to train the model using the preprocessed data. Adjust hyperparameters and experiment with different architectures as needed.

3.  Inference Step: `inference.py`   
   - Outputs predictions (EG Rating - EGR) with corresponding metadata, including agent role columns.  
   - This script requires the data prepared using the data preparation script.

    Steps to run :  
   ```bash
   python inference.py /path/to/data.csv --model_path /path/to/model.keras --scaler_path /path/to/scaler.pkl
   ```

4.  PostgreSQL Integration: `sql_utils.py`   
   - Uploads the prediction results (CSV) to PostgreSQL or deletes existing tables.

    Steps to run :  
   ```bash
   python sql_utils.py results.csv
   ```
   The script will prompt you to choose an action:
   - Type `upload` to upload the CSV to PostgreSQL.
   - Type `delete` to delete the existing table in PostgreSQL.

   Refer to `config.json` for database credentials and table names.

5.  Streamlit App: `eg_app.py`   
   - Implements a dashboard for visualizing player performance.  
   - Interactive and dynamic charts display various EGR metrics and player statistics.

    Steps to run :  
   ```bash
   streamlit run eg_app.py --server.port 8501 --server.maxUploadSize 100
   ```
   Adjust the `--server.port` and `--server.maxUploadSize` as needed.

## Configuration:
-  Configuration File: `config.json`   
  Stores essential configuration settings like database credentials, table names, and other project-specific configurations.

## Usage:

1.  Data Preparation :  
   Use `lstm_data_preparation.ipynb` to extract and preprocess your data from the PostgreSQL database.
   
2.  Model Training :  
   Train the LSTM model using `lstm_model_training.ipynb`. Ensure your data is preprocessed before running this notebook.

3.  Inference :  
   Run `inference.py` to generate EGR predictions using the trained model.

4.  Upload Results to PostgreSQL :  
   Use `sql_utils.py` to upload the predictions into PostgreSQL.

5.  Visualize Results :  
   Use `eg_app.py` to run the Streamlit app and visualize player performance based on the EGR predictions.

## Notes:
- Make sure to configure `config.json` with your database credentials and necessary settings before running any scripts.
