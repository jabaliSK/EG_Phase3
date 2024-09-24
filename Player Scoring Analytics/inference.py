import argparse
import joblib
import pandas as pd
import numpy as np
import tensorflow as tf
from datetime import datetime
from tqdm import tqdm

def load_data(file_path):
    df = pd.read_csv(file_path)
    df = df.sort_values(['game_id', 'team', 'player', 'round_num', 'seconds'])
    df['won'] = df['won'].replace({True: 1, False: 0})
    
    categorical_columns = ["agent_name", "map_name", "side", "spike_event", "spike_planted"]
    for col in categorical_columns:
        df[col] = df[col].astype("category").cat.codes
    
    return df

def check_and_handle_nan_inf(df, feature_columns):
    X = df[feature_columns]
    if np.any(np.isnan(X)) or np.any(np.isinf(X)):
        print("Input data contains NaNs or infinite values. Fixing...")
        X = X.fillna(X.mean())
        X = X.replace([np.inf, -np.inf], np.finfo(np.float64).max)
        print("NaNs and infinite values fixed.")
    else:
        print("No NaNs or infinite values found.")
    df[feature_columns] = X
    return df

def generate_samples(df, feature_columns, target_column):
    grouped = df.groupby(['game_id', 'player'])
    player_game_samples = []
    target_game_samples = []

    for _, group in grouped:
        rounds = []
        targets = []
        for _, round_group in group.groupby('round_num'):
            rounds.append(round_group[feature_columns].values)
            targets.append(round_group[target_column].iloc[-1])
        player_game_samples.append(rounds)
        target_game_samples.append(targets)
    
    return player_game_samples, target_game_samples

def pad_sequences(sequences):
    max_timesteps = max(seq.shape[0] for seq in sequences)
    padded_sequences = [np.pad(seq, ((0, max_timesteps - seq.shape[0]), (0, 0)), 'constant', constant_values=-999)
                        for seq in sequences]
    return np.stack(padded_sequences, axis=0)

def infer(model, new_data, feature_columns, scaler):
    # Normalize the target column
    new_data['cs_round_normalized'] = (new_data['combat_score_round'] - new_data['combat_score_round'].min()) / (new_data['combat_score_round'].max() - new_data['combat_score_round'].min())
    target_column = 'cs_round_normalized'

    # Handle NaNs and infinite values, scale features
    new_data = check_and_handle_nan_inf(new_data, feature_columns)
    new_data.loc[:, feature_columns] = scaler.transform(new_data.loc[:, feature_columns])

    # Generate samples and targets
    player_game_samples, target_game_samples = generate_samples(new_data, feature_columns, target_column)

    print("Player game samples:", len(player_game_samples))
    
    # Predictions
    predictions = []
    for sample, _ in tqdm(zip(player_game_samples, target_game_samples), total=len(player_game_samples), desc="Inferencing"):
        padded_sample = pad_sequences(sample)
        pred = model.predict(padded_sample)
        predictions.append(pred)
    
    print("Predictions length:", len(predictions))

    # Store results properly, tracking the correct game_id
    results = []
    grouped_keys = list(new_data.groupby(['game_id', 'player']).groups.keys())
    print("Grouped keys length:", len(grouped_keys))
    
    for i, (game_id, player) in enumerate(grouped_keys):
        if i >= len(predictions):
            print(f"Warning: Not enough predictions for game_id {game_id} and player {player}")
            continue
        for round_num, (pred_score, target_score) in enumerate(zip(predictions[i], target_game_samples[i])):
            results.append((game_id, player, round_num + 1, pred_score[0], target_score))
            print(f"Game ID: {game_id}, Player: {player}, Round Number: {round_num + 1}, Prediction Score: {pred_score[0]}, Target Score: {target_score}")
    
    results_df = pd.DataFrame(results, columns=['game_id', 'player', 'round_num', 'EGR', 'Target'])
    return results_df

def main():
    parser = argparse.ArgumentParser(description="Inference script for Valorant LSTM model.")
    parser.add_argument('csv_file', type=str, help='Path to the input CSV file.')
    parser.add_argument('--model_path', type=str, default='valorant_lstm_model_combatscore_target.keras', help='Path to the trained model.')
    parser.add_argument('--scaler_path', type=str, default='scaler_combatscore_target.pkl', help='Path to the scaler file.')
    args = parser.parse_args()
    
    print("Loading data...")
    df = load_data(args.csv_file)
    
    print("Loading model...")
    model = tf.keras.models.load_model(args.model_path)
    
    print("Loading scaler...")
    scaler = joblib.load(args.scaler_path)
    
    print("Starting inference...")
    results_df = infer(model, df, df.columns.difference([
        "game_id", "player", "game_version", "game_datetime", "inventory", "team_id", "attacking_team",
        "event_num", "event_time", "round_start_time", "clock_time", 'account_id', 'agent_id', 'team',
        "opponent_team", "spike_diffused", "teamId_value", "ability1_temp_charges", "ability1_max_charges",
        "ultimate_temp_charges", "ultimate_max_charges", "ability2_max_charges", "ability2_temp_charges",
        "grenade_temp_charges", "grenade_max_charges", "money", "combat_score_total", "damage_dealt",
        "damage_taken", "combat_score_round", "cs_round_normalized", "kills", "deaths", "assists", "won"
    ]), scaler)
    
    # Load the original data again for merging
    original_data = pd.read_csv(args.csv_file)
    rf = results_df.rename(columns={"game_id": "game_id", "player": "player", "round_num": "round_num"})
    merged_table = pd.merge(original_data, rf, on=['game_id', 'player', 'round_num'])
    
    # Add roles
    roles_dict = {
        'Controllers': ['Astra', 'Brimstone', 'Clove', 'Harbor', 'Omen', 'Viper'],
        'Duelists': ['Iso', 'Jett', 'Neon', 'Phoenix', 'Raze', 'Reyna', 'Yoru'],
        'Initiators': ['Breach', 'Fade', 'Gekko', 'KAY/O', 'Skye', 'Sova'],
        'Sentinels': ['Chamber', 'Cypher', 'Deadlock', 'Killjoy', 'Sage', 'Vyse']
    }
    agent_to_role = {agent.lower(): role for role, agents in roles_dict.items() for agent in agents}
    
    merged_table['role'] = merged_table['agent_name'].str.lower().map(agent_to_role)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f'results_{timestamp}.csv'
    merged_table.to_csv(output_filename, index=False)
    print(f"Inference completed. Results saved to {output_filename}")

if __name__ == "__main__":
    main()
