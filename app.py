import os
import joblib
import pandas as pd
import gradio as gr
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import hf_hub_download

# 1. Initialize FastAPI
app = FastAPI(
    title="Locomotive Axle Lock Early Warning System",
    description="Two-Stage Kinematic & Physical Sensor Fusion API",
    version="2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Load ML Models
REPO_ID = "Chiranjivzope25/locomotive"

try:
    path_kinematic = hf_hub_download(repo_id=REPO_ID, filename="axle_lock_xgb.joblib")
    path_transformer_kin = hf_hub_download(repo_id=REPO_ID, filename="power_transformer.joblib")
    path_phy = hf_hub_download(repo_id=REPO_ID, filename="phy_axle_lock_xgb.joblib")
    path_transformer_phy = hf_hub_download(repo_id=REPO_ID, filename="phy_power_transformer.joblib")

    model_kinematic = joblib.load(path_kinematic)
    transformer_kinematic = joblib.load(path_transformer_kin)
    model_phy = joblib.load(path_phy)
    transformer_phy = joblib.load(path_transformer_phy)
except Exception as e:
    raise RuntimeError(f"Critical Error loading ML models: {e}")

# 3. Schemas & Endpoints
class KinematicInput(BaseModel):
    v_loco_kmh: float = Field(..., json_schema_extra={"example": 80.0})
    axle1_speed_rads: float = Field(..., json_schema_extra={"example": 55.1})
    axle2_speed_rads: float = Field(..., json_schema_extra={"example": 55.2})
    axle3_speed_rads: float = Field(..., json_schema_extra={"example": 55.0})
    axle4_speed_rads: float = Field(..., json_schema_extra={"example": 54.8})
    axle1_slip_ratio: float = Field(..., json_schema_extra={"example": 0.0})

class PhysicalInput(BaseModel):
    axle1_bearing_temp_c: float = Field(..., json_schema_extra={"example": 105.4})
    axle1_vibration_g: float = Field(..., json_schema_extra={"example": 3.8})
    axle1_motor_current_amp: float = Field(..., json_schema_extra={"example": 520.0})
    axle2_bearing_temp_c: float = Field(..., json_schema_extra={"example": 45.0})
    axle2_vibration_g: float = Field(..., json_schema_extra={"example": 0.3})
    axle2_motor_current_amp: float = Field(..., json_schema_extra={"example": 300.0})
    axle3_bearing_temp_c: float = Field(..., json_schema_extra={"example": 46.2})
    axle3_vibration_g: float = Field(..., json_schema_extra={"example": 0.35})
    axle3_motor_current_amp: float = Field(..., json_schema_extra={"example": 305.0})
    axle4_bearing_temp_c: float = Field(..., json_schema_extra={"example": 44.8})
    axle4_vibration_g: float = Field(..., json_schema_extra={"example": 0.28})
    axle4_motor_current_amp: float = Field(..., json_schema_extra={"example": 298.0})

class DualModelRequest(BaseModel):
    data_axel: KinematicInput
    data_phy: PhysicalInput

@app.post("/predict")
def predict(request: DualModelRequest):
    try:
        df_kinematic = pd.DataFrame([request.data_axel.model_dump()])
        df_phy = pd.DataFrame([request.data_phy.model_dump()])
        
        x_scaled_kin = transformer_kinematic.transform(df_kinematic)
        x_scaled_phy = transformer_phy.transform(df_phy)
        
        pred_kin = int(model_kinematic.predict(x_scaled_kin)[0])
        prob_kin = float(model_kinematic.predict_proba(x_scaled_kin)[0][1])
        
        pred_phy = int(model_phy.predict(x_scaled_phy)[0])
        prob_phy = float(model_phy.predict_proba(x_scaled_phy)[0][1])
        
        speeds = [
            request.data_axel.axle1_speed_rads,
            request.data_axel.axle2_speed_rads,
            request.data_axel.axle3_speed_rads,
            request.data_axel.axle4_speed_rads
        ]
        if request.data_axel.v_loco_kmh > 15.0 and any(s < 5.0 for s in speeds):
            pred_kin = 1
            prob_kin = max(prob_kin, 0.99)

        if pred_kin == 1 and pred_phy == 1:
            alert_status = "CRITICAL: AXLE LOCK & MECHANICAL SEIZURE CONFIRMED"
            color = "red"
            risk_level = "HIGH"
        elif pred_phy == 1:
            alert_status = "WARNING: HIGH BEARING TEMP / VIBRATION DETECTED"
            color = "orange"
            risk_level = "MEDIUM"
        elif pred_kin == 1:
            alert_status = "CAUTION: WHEEL SLIP OR KINEMATIC LOCK DETECTED"
            color = "yellow"
            risk_level = "LOW-MEDIUM"
        else:
            alert_status = "SYSTEM NORMAL"
            color = "green"
            risk_level = "NORMAL"
            
        return {
            "overall_status": alert_status,
            "display_color": color,
            "risk_level": risk_level,
            "model_outputs": {
                "kinematic_model": {"prediction": pred_kin, "confidence_score": round(prob_kin, 4)},
                "physical_model": {"prediction": pred_phy, "confidence_score": round(prob_phy, 4)}
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. Mount FastAPI into Gradio Interface
demo = gr.Interface(fn=lambda x: "API is active", inputs="text", outputs="text", title="Locomotive API Service")
app = gr.mount_gradio_app(app, demo, path="/")