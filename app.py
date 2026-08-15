import os
import joblib
import pandas as pd
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import hf_hub_download
import uvicorn
from huggingface_hub import spaces
# Hugging Face Model Repository ID
REPO_ID = "Chiranjivzope25/axle-lock-models"

# Storage dictionary for model instances in global memory
artifacts = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # -------------------------------------------------------------
    # LOAD ARTIFACTS FROM HUGGING FACE MODEL HUB ON STARTUP
    # -------------------------------------------------------------
    try:
        path_kinematic = hf_hub_download(repo_id=REPO_ID, filename="axle_lock_xgb.joblib")
        path_transformer_kin = hf_hub_download(repo_id=REPO_ID, filename="power_transformer.joblib")
        path_phy = hf_hub_download(repo_id=REPO_ID, filename="phy_axle_lock_xgb.joblib")
        path_transformer_phy = hf_hub_download(repo_id=REPO_ID, filename="phy_power_transformer.joblib")

        artifacts["model_kinematic"] = joblib.load(path_kinematic)
        artifacts["transformer_kinematic"] = joblib.load(path_transformer_kin)
        artifacts["model_phy"] = joblib.load(path_phy)
        artifacts["transformer_phy"] = joblib.load(path_transformer_phy)

        print("✅ All ML models and transformers loaded successfully from Hugging Face Hub!")
    except Exception as e:
        print(f"❌ Critical Error loading ML models: {e}")
        raise RuntimeError(e)
    
    yield
    artifacts.clear()

app = FastAPI(
    title="Locomotive Axle Lock Early Warning System",
    description="Two-Stage Kinematic & Physical Sensor Fusion API",
    version="2.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------
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

# -------------------------------------------------------------
# ENDPOINTS
# -------------------------------------------------------------
@app.get("/")
@spaces.GPU
def home():
    return {
        "status": "Online",
        "system": "Locomotive Axle Lock Dual-Model Inference Service"
    }

@app.post("/predict")
@spaces.GPU
def predict(request: DualModelRequest):
    try:
        # Pydantic v2 syntax: .model_dump()
        df_kinematic = pd.DataFrame([request.data_axel.model_dump()])
        df_phy = pd.DataFrame([request.data_phy.model_dump()])
        
        # Pull loaded artifacts from global app state
        transformer_kinematic = artifacts["transformer_kinematic"]
        transformer_phy = artifacts["transformer_phy"]
        model_kinematic = artifacts["model_kinematic"]
        model_phy = artifacts["model_phy"]
        
        # 1. Transform Features
        x_scaled_kin = transformer_kinematic.transform(df_kinematic)
        x_scaled_phy = transformer_phy.transform(df_phy)
        
        # 2. Get Predictions & Probabilities
        pred_kin = int(model_kinematic.predict(x_scaled_kin)[0])
        prob_kin = float(model_kinematic.predict_proba(x_scaled_kin)[0][1])
        
        pred_phy = int(model_phy.predict(x_scaled_phy)[0])
        prob_phy = float(model_phy.predict_proba(x_scaled_phy)[0][1])
        
        # 3. Safety Rule Override
        speeds = [
            request.data_axel.axle1_speed_rads,
            request.data_axel.axle2_speed_rads,
            request.data_axel.axle3_speed_rads,
            request.data_axel.axle4_speed_rads
        ]
        if request.data_axel.v_loco_kmh > 15.0 and any(s < 5.0 for s in speeds):
            pred_kin = 1
            prob_kin = max(prob_kin, 0.99)

        # 4. Severity Mapping Logic
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
                "kinematic_model": {
                    "prediction": pred_kin,
                    "confidence_score": round(prob_kin, 4)
                },
                "physical_model": {
                    "prediction": pred_phy,
                    "confidence_score": round(prob_phy, 4)
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Inference Error: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=7860, reload=False)