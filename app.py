import joblib
import pandas as pd  # Added missing import
from fastapi import FastAPI 

app = FastAPI()

# Load saved artifacts
model = joblib.load("models/axle_lock_xgb.joblib")
transformer = joblib.load("models/power_transformer.joblib")

@app.get("/")
def home():
    return {"message": "Welcome to the Axle Lock Detection API"}

# API Route for Single Prediction
@app.post("/predict")
def predict(data: dict):
    try:
        # Convert JSON dictionary to DataFrame row
        x_single = pd.DataFrame([data])
        
        # 1. Transform Data using the fitted scaler
        x_scaled = transformer.transform(x_single)
        
        # 2. Predict the label using the XGBoost model
        prediction = model.predict(x_scaled)
        
        # 3. Map output to human-readable format
        if prediction[0] == 1:
            result_text = "AXLE LOCK DETECTED"
            color = "red"
        else:
            result_text = "No Axle Lock"
            color = "green"
            
        return {
            "prediction_numeric": int(prediction[0]),
            "alert_status": result_text,
            "display_color": color,
            "message": f"Alert Status: {result_text}"
        }
    except Exception as e:
        return {"error": str(e)}