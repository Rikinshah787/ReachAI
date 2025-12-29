import pandas as pd
import os
import logging

class DataAgent:
    """
    Ingests and validates recruiter data from CSV.
    """
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.required_columns = ['first_name', 'email', 'company', 'role_hiring_for']
        
    def load_data(self):
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"CSV file not found at {self.csv_path}")
        
        df = pd.read_csv(self.csv_path)
        return self.validate(df)

    def validate(self, df):
        # Check for missing columns
        missing_cols = [col for col in self.required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Drop rows with missing critical info
        clean_df = df.dropna(subset=self.required_columns)
        
        # Basic email validation (very simple check)
        clean_df = clean_df[clean_df['email'].str.contains('@')]
        
        logging.info(f"Loaded {len(clean_df)} valid recruiter records.")
        return clean_df.to_dict('records')

if __name__ == "__main__":
    # Test logic
    agent = DataAgent("data/recruiters.csv")
    try:
        data = agent.load_data()
        print(data)
    except Exception as e:
        print(f"Error: {e}")
