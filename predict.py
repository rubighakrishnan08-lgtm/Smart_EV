import joblib
import numpy as np

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(BASE_DIR, "models", "load_model.pkl")

model = joblib.load(model_path)

def predict_load(hour, day, month, prev_load):
    features = np.array([[hour, day, month, prev_load]])
    prediction = model.predict(features)
    return float(prediction[0])