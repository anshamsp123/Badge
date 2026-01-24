"""
Fraud Detection Module
Uses Random Forest to classify claims as specific fraud types based on labeled historical data.
"""
import pandas as pd
import numpy as np
import os
import joblib
import glob
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from typing import Dict, Tuple

class FraudDetector:
    def __init__(self, data_dir: str = None, model_path: str = "fraud_model.pkl"):
        """
        Initialize Fraud Detector.
        Args:
            data_dir: Path to the directory containing CSV datasets. 
                      Defaults to the hardcoded path if not provided.
            model_path: Path to save/load the trained model.
        """
        if data_dir is None:
            # Default to the path provided by the user
            self.data_dir = r"F:\Sem 5\EDAI\new new new\insurance claims\Fraud_detection_datasets"
        else:
            self.data_dir = data_dir
            
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.encoders = {}
        # Feature columns we expect after preprocessing
        self.feature_columns = [
            'age', 'gender_encoded', 'amount_billed', 'duration_days', 'diagnosis_encoded'
        ]
        
        # Load or train model
        self._load_or_train()

    def _load_or_train(self):
        """Load existing model or train a new one if not found."""
        if os.path.exists(self.model_path):
            try:
                print(f"Loading fraud detection model from {self.model_path}...")
                saved_data = joblib.load(self.model_path)
                self.model = saved_data['model']
                self.scaler = saved_data['scaler']
                self.encoders = saved_data['encoders']
                self.feature_columns = saved_data.get('feature_columns', self.feature_columns)
                print("Model loaded successfully.")
            except Exception as e:
                print(f"Error loading model: {e}. Retraining...")
                self.train_model()
        else:
            print("Model not found. Training new model...")
            self.train_model()

    def _load_data(self) -> pd.DataFrame:
        """Load and merge data from CSV files in the directory."""
        if not os.path.exists(self.data_dir):
            print(f"Data directory {self.data_dir} does not exist.")
            return pd.DataFrame()

        all_files = glob.glob(os.path.join(self.data_dir, "*.csv"))
        df_list = []
        
        print(f"Found {len(all_files)} CSV files in {self.data_dir}")
        
        for filename in all_files:
            try:
                # heuristic to skip summary or unrelated files could go here
                # For now load all and filter by columns
                
                print(f"Loading {filename}...")
                df = pd.read_csv(filename)
                
                # Normalize column names to upper case for easier matching
                df.columns = [str(c).upper().strip() for c in df.columns]
                
                # Map various column names to our standard internal names
                rename_map = {}
                for col in df.columns:
                    if 'AGE' in col: rename_map[col] = 'age'
                    elif 'GENDER' in col or 'SEX' in col: rename_map[col] = 'gender'
                    elif 'AMOUNT' in col or 'BILLED' in col or 'COST' in col: rename_map[col] = 'amount_billed'
                    elif 'DIAGNOSIS' in col: rename_map[col] = 'diagnosis'
                    elif ('FRAUD' in col and 'TYPE' in col): rename_map[col] = 'fraud_type'
                    # Dates
                    elif 'ADMIT' in col or 'ENCOUNTER' in col or 'START' in col: rename_map[col] = 'date_start'
                    elif 'DISCHARGE' in col or 'END' in col: rename_map[col] = 'date_end'
                
                df = df.rename(columns=rename_map)
                
                # minimal required columns
                required_cols = ['age', 'gender', 'amount_billed', 'diagnosis', 'fraud_type']
                
                # Check if we have enough columns to be useful
                present_cols = [c for c in required_cols if c in df.columns]
                if len(present_cols) >= 4: # Allow missing one if we can impute, but fraud_type is critical
                    if 'fraud_type' not in df.columns:
                        # Maybe it is a file with a binary label? 
                        # Check for 'FRAUD' or 'IS_FRAUD'
                        pass
                    
                    # Keep only relevant columns found
                    input_cols = present_cols + [c for c in ['date_start', 'date_end'] if c in df.columns]
                    df_subset = df[input_cols].copy()
                    df_list.append(df_subset)
                else:
                    print(f"Skipping {filename}: Not enough matching columns. Found: {df.columns.tolist()}")
            
            except Exception as e:
                print(f"Error loading {filename}: {e}")

        if not df_list:
            print("No valid datasets found.")
            return pd.DataFrame()
            
        combined_df = pd.concat(df_list, ignore_index=True)
        print(f"Combined dataset shape: {combined_df.shape}")
        return combined_df

    def train_model(self):
        """Train Random Forest model."""
        try:
            print("Starting model training process...")
            df = self._load_data()
            
            if df.empty:
                print("No data available to train. Model will be inactive.")
                return

            # --- Preprocessing ---
            
            # 1. Target Variable (Fraud)
            if 'fraud_type' in df.columns:
                df['fraud_type'] = df['fraud_type'].astype(str).str.title().str.strip()
                # Treat 'No Fraud', 'None', 'Nan' as non-fraud (0), others as fraud (1)
                non_fraud_labels = ['No Fraud', 'None', 'Nan', 'Nb', '0']
                df['is_fraud'] = df['fraud_type'].apply(lambda x: 0 if x in non_fraud_labels or pd.isna(x) else 1)
            else:
                # If no fraud_type, assume all are legitimate? Or try to find another label?
                # For now, if no label, we can't do supervised learning comfortably.
                # However, we'll assume the user provided labeled data as requested.
                print("Warning: 'fraud_type' column missing. Cannot train supervised model.")
                return

            # 2. Cleaning & Filling Missing Values
            # Age
            df['age'] = pd.to_numeric(df['age'], errors='coerce')
            df['age'] = df['age'].fillna(df['age'].mean())
            
            # Amount
            df['amount_billed'] = pd.to_numeric(df['amount_billed'], errors='coerce')
            df['amount_billed'] = df['amount_billed'].fillna(0.0)
            
            # Gender
            if 'gender' not in df.columns:
                df['gender'] = 'Unknown'
            df['gender'] = df['gender'].fillna('Unknown').astype(str)
            
            # Diagnosis
            if 'diagnosis' not in df.columns:
                df['diagnosis'] = 'Unknown'
            df['diagnosis'] = df['diagnosis'].fillna('Unknown').astype(str)
            
            # 3. Feature Engineering: Duration
            df['duration_days'] = 1 # Default
            if 'date_start' in df.columns and 'date_end' in df.columns:
                s = pd.to_datetime(df['date_start'], errors='coerce')
                e = pd.to_datetime(df['date_end'], errors='coerce')
                dur = (e - s).dt.days
                # Fill NaNs with 1, ensure at least 1 day
                df['duration_days'] = dur.fillna(1).apply(lambda x: max(1, int(x)) if not pd.isna(x) else 1)
            
            # 4. Encoding
            # Gender
            le_gender = LabelEncoder()
            df['gender_encoded'] = le_gender.fit_transform(df['gender'])
            self.encoders['gender'] = le_gender
            
            # Diagnosis
            le_diag = LabelEncoder()
            # Handle high cardinality if needed, but for now simple LabelEncoding
            df['diagnosis_encoded'] = le_diag.fit_transform(df['diagnosis'])
            self.encoders['diagnosis'] = le_diag
            
            # 5. Prepare Train Vectors
            X = df[self.feature_columns]
            y = df['is_fraud']
            
            # Scale
            X_scaled = self.scaler.fit_transform(X)
            
            # Train Random Forest
            print(f"Training Random Forest on {len(df)} records...")
            self.model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
            self.model.fit(X_scaled, y)
            
            # Save
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler,
                'encoders': self.encoders,
                'feature_columns': self.feature_columns
            }, self.model_path)
            print("Fraud detection model trained and saved successfully.")
            
        except Exception as e:
            print(f"Failed to train model: {e}")
            import traceback
            traceback.print_exc()

    def predict_fraud(self, claim_data: Dict) -> Tuple[float, str]:
        """
        Predict fraud likelihood for a claim.
        Returns: 
            score (0.0 to 1.0, higher is more likely fraud)
            risk_level ('Low', 'Medium', 'High')
        """
        if self.model is None:
            # Try loading again?
            return 0.0, "Unknown - No Model"
            
        try:
            # Prepare input inputs
            # Map external keys to internal keys
            # claim_data might come from the frontend form.
            # Typical keys: 'patient_name', 'diagnosis', 'treatment_date', 'claimed_amount', 'policy_number'
            
            # Defaults
            age = 35
            gender = 'Unknown'
            amount = 0.0
            diagnosis = 'Unknown'
            days = 1
            
            # Extract
            if 'age' in claim_data: age = claim_data['age']
            if 'gender' in claim_data: gender = claim_data['gender']
            if 'diagnosis' in claim_data: diagnosis = claim_data['diagnosis']
            if 'claimed_amount' in claim_data: amount = claim_data['claimed_amount']
            elif 'amount' in claim_data: amount = claim_data['amount']
            
            # Construct DataFrame
            input_df = pd.DataFrame([{
                'age': age,
                'gender': gender,
                'amount_billed': amount,
                'diagnosis': diagnosis,
                'duration_days': days # Simplified as we don't always get start/end dates from simple form
            }])
            
            # Preprocess Input
            # Age/Amount numeric
            input_df['age'] = pd.to_numeric(input_df['age'], errors='coerce').fillna(35)
            input_df['amount_billed'] = pd.to_numeric(input_df['amount_billed'], errors='coerce').fillna(0)
            
            # Encoders
            # Gender
            enc_gen = self.encoders.get('gender')
            if enc_gen:
                val = str(input_df['gender'].iloc[0])
                if val in enc_gen.classes_:
                    input_df['gender_encoded'] = enc_gen.transform([val])
                else:
                    input_df['gender_encoded'] = 0 # Default/Unknown
            else:   
                 input_df['gender_encoded'] = 0

            # Diagnosis
            enc_diag = self.encoders.get('diagnosis')
            if enc_diag:
                val = str(input_df['diagnosis'].iloc[0])
                if val in enc_diag.classes_:
                    input_df['diagnosis_encoded'] = enc_diag.transform([val])
                else:
                    input_df['diagnosis_encoded'] = 0
            else:
                input_df['diagnosis_encoded'] = 0
            
            # Select Cols
            X = input_df[self.feature_columns]
            
            # Scale
            X_scaled = self.scaler.transform(X)
            
            # Predict Probability of Class 1 (Fraud)
            classes = self.model.classes_
            fraud_idx = np.where(classes == 1)[0][0] if 1 in classes else -1
            
            if fraud_idx != -1:
                fraud_prob = self.model.predict_proba(X_scaled)[0][fraud_idx]
            else:
                fraud_prob = 0.0
            
            # Determine Risk
            if fraud_prob > 0.7:
                risk_level = "High"
            elif fraud_prob > 0.4:
                risk_level = "Medium"
            else:
                risk_level = "Low"
                
            return float(fraud_prob), risk_level
            
        except Exception as e:
            print(f"Error predicting fraud: {e}")
            return 0.0, "Unknown"

# Singleton instance
fraud_detector = FraudDetector()
