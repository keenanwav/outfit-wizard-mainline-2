```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from typing import List, Dict, Optional, Tuple
import joblib
import os
import logging
from datetime import datetime

class FitPredictor:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.label_encoders = {}
        self.feature_names = ['type', 'style', 'color', 'size']
        self.model_path = 'models/fit_predictor.joblib'
        self.initialize_model()
    
    def initialize_model(self):
        """Initialize or load the existing model"""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.label_encoders = joblib.load(self.model_path.replace('.joblib', '_encoders.joblib'))
                logging.info("Loaded existing fit prediction model")
            except Exception as e:
                logging.error(f"Error loading model: {str(e)}")
                self._initialize_new_model()
        else:
            self._initialize_new_model()

    def _initialize_new_model(self):
        """Initialize a new model if none exists"""
        os.makedirs('models', exist_ok=True)
        for feature in self.feature_names:
            self.label_encoders[feature] = LabelEncoder()
        logging.info("Initialized new fit prediction model")

    def preprocess_item(self, item: Dict) -> np.ndarray:
        """Preprocess a single clothing item for prediction"""
        features = []
        for feature in self.feature_names:
            value = str(item.get(feature, '')).lower()
            if feature not in self.label_encoders:
                self.label_encoders[feature] = LabelEncoder()
            
            # Fit the encoder if it's a new value
            try:
                encoded = self.label_encoders[feature].transform([value])[0]
            except ValueError:
                # If new category encountered, refit the encoder
                self.label_encoders[feature].fit(list(self.label_encoders[feature].classes_) + [value])
                encoded = self.label_encoders[feature].transform([value])[0]
            
            features.append(encoded)
        return np.array(features)

    def train(self, outfits: List[Dict], feedback_scores: List[float]):
        """Train the model on historical outfit data and feedback"""
        if not outfits or not feedback_scores:
            logging.warning("No training data provided")
            return False

        X = []
        for outfit in outfits:
            outfit_features = []
            for item_type in ['shirt', 'pants', 'shoes']:
                if item_type in outfit:
                    item_features = self.preprocess_item(outfit[item_type])
                    outfit_features.extend(item_features)
            X.append(outfit_features)

        X = np.array(X)
        y = np.array(feedback_scores)

        try:
            self.model.fit(X, y)
            # Save the model and encoders
            os.makedirs('models', exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.label_encoders, self.model_path.replace('.joblib', '_encoders.joblib'))
            logging.info("Successfully trained and saved fit prediction model")
            return True
        except Exception as e:
            logging.error(f"Error training model: {str(e)}")
            return False

    def predict_fit(self, outfit: Dict) -> Tuple[float, Dict[str, float]]:
        """Predict fit score for a given outfit"""
        try:
            outfit_features = []
            item_scores = {}
            
            for item_type in ['shirt', 'pants', 'shoes']:
                if item_type in outfit:
                    item_features = self.preprocess_item(outfit[item_type])
                    outfit_features.extend(item_features)
                    
                    # Calculate individual item scores
                    item_prediction = self.model.predict_proba(item_features.reshape(1, -1))
                    item_scores[item_type] = float(item_prediction[0][1])

            if not outfit_features:
                return 0.0, {}

            # Predict overall outfit fit
            outfit_features = np.array(outfit_features).reshape(1, -1)
            prediction = self.model.predict_proba(outfit_features)
            fit_score = float(prediction[0][1])  # Probability of good fit

            return fit_score, item_scores
            
        except Exception as e:
            logging.error(f"Error predicting fit: {str(e)}")
            return 0.0, {}

    def update_feedback(self, outfit_id: str, feedback_score: float):
        """Update model with new feedback"""
        from data_manager import get_outfit_details
        
        outfit = get_outfit_details(outfit_id)
        if outfit:
            self.train([outfit], [feedback_score])
            logging.info(f"Updated model with feedback for outfit {outfit_id}")
            return True
        return False
```
