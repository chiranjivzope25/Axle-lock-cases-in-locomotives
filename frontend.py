import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
from streamlit_echarts import st_echarts
import streamlit.components.v1 as components

# ==========================================
# 1. PAGE CONFIGURATION & LAYOUT
# ==========================================
st.set_page_config(
    page_title="Locomotive Axle Monitoring",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for the 'real' digital look and color shifts
st.markdown("""
<style>
    /* Main background */
    .reportview-container { background: #0e1117; color: white; }
    /* Digital Font (Optional) */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500&display=swap');
    
    /* Global classes for color shifts */
    .digital-ok { color: #00ff00 !important; font-family: 'Orbitron', sans-serif; }
    .digital-alert { color: #ff0000 !important; font-family: 'Orbitron', sans-serif; }
    
    /* Styling for the large alert status text */
    .alert-banner {
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        font-size: 24px;
        margin-bottom: 1rem;
    }
    .alert-ok-banner { background-color: rgba(0, 255, 0, 0.1); border: 2px solid #00ff00; }
    .alert-danger-banner { background-color: rgba(255, 0, 0, 0.1); border: 2px solid #ff0000; }

    /* Telemetry card styling */
    .telemetry-card {
        background-color: #1a1c24;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
</style>
""", unsafe_allow_html=True)

st.title("LOCMOTIVE AXLE LOCK DASHBOARD")
st.markdown("---")

# ==========================================
# 2. SIDEBAR - SIMULATION CONTROLS (Telemetry)
# ==========================================
st.sidebar.header("SENSOR TELEMETRY INPUTS")
st.sidebar.markdown("Adjust sliders to simulate live locomotive data:")

# Simulation Controls
sim_v_loco = st.sidebar.slider("Simulation Velocity (km/h)", 0.0, 120.0, 30.0)
sim_axle_healthy_speed = st.sidebar.slider("Axle Speed - Healthy (rad/s)", 0.0, 60.0, 15.43)
sim_axle_fault_speed = st.sidebar.slider("Axle 1 Speed - Fault (rad/s)", 0.0, 15.0, 0.0)
sim_axle1_slip_healthy = 0.0
sim_axle1_slip_fault = 1.0

# Define test scenarios
scenario = st.sidebar.selectbox("Test Scenario", ["Normal Operation", "Axle 1 Lock Event", "Manual Control"])

if scenario == "Normal Operation":
    st_v_loco = 30.0
    st_a1_speed = 15.43
    st_slip = 0.0
elif scenario == "Axle 1 Lock Event":
    st_v_loco = 30.0
    st_a1_speed = 0.0  # Force lock
    st_slip = 1.0  # Force maximum slip
else:
    # Manual control from sliders
    st_v_loco = sim_v_loco
    st_a1_speed = sim_axle_healthy_speed if scenario == "Normal Operation" else sim_axle_fault_speed
    st_slip = sim_axle1_slip_fault if st_a1_speed < (st_v_loco/3.6*0.95) else sim_axle1_slip_healthy

# Set the input dictionary (matching image_0.png telemetry)
input_data = {
  "v_loco_kmh": st_v_loco,
  "axle1_speed_rads": st_a1_speed,
  "axle2_speed_rads": sim_axle_healthy_speed,
  "axle3_speed_rads": sim_axle_healthy_speed,
  "axle4_speed_rads": sim_axle_healthy_speed,
  "axle1_slip_ratio": st_slip
}


# ==========================================
# 3. INTERFACE VISUALIZATIONS (Main Area)
# ==========================================
fastapi_url = "http://127.0.0.1:8000/predict"
# Make the live API request to the backend
try:
    response = requests.post(fastapi_url, json=input_data, timeout=2)
    response_json = response.json()
    prediction = response_json['prediction']
    probability = response_json['lock_probability']
except Exception as e:
    st.error(f"Error connecting to FastAPI backend. Ensure uvicorn is running: {e}")
    prediction = 0
    probability = 0.0

# UI State determined by Prediction
is_alert = (prediction == 1)
alert_class = "digital-alert" if is_alert else "digital-ok"
banner_class = "alert-danger-banner" if is_alert else "alert-ok-banner"
status_text = "AXLE LOCK DETECTED" if is_alert else "NORMAL OPERATION"
theme_color = "#ff0000" if is_alert else "#00ff00"


# Layout Grid
col_schematic, col_telemetry = st.columns([2, 1])

with col_schematic:
    st.markdown(f'<div class="alert-banner {banner_class}">ALERT STATUS: {status_text}</div>', unsafe_allow_html=True)
    
    st.subheader("BOGIE STATE VISUALIZATION")
    
    # Advanced ECharts Schematic (Digitalization vs Reference Image)
    # This visualization dynamically shows wheels turning (healthy) or stopping (fault)
    
    # Schematic configuration
    base_size = 180
    healthy_wheel_speed = 3000 if not is_alert else 0 # Delay in ms for rotation animation
    
    # We use a custom HTML/SVG component within Streamlit for complete control over
    # the animation realism of the wheel rotation schematic.
    
    schematic_svg = f"""
    <svg width="100%" height="400" viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg" style="background:#1a1c24; border-radius:10px; border: 1px solid #30363d;">
        <!-- Tracks -->
        <rect x="0" y="320" width="800" height="20" fill="#30363d" />
        <rect x="0" y="360" width="800" height="20" fill="#30363d" />
        
        <!-- Bogie Frame -->
        <rect x="150" y="100" width="500" height="150" rx="15" fill="#1f2937" stroke="#30363d" stroke-width="3"/>
        
        <!-- Define Wheel Rotation Animations -->
        <defs>
            <path id="wheel-shape" d="M -{base_size/2} 0 A {base_size/2} {base_size/2} 0 1 1 {base_size/2} 0 A {base_size/2} {base_size/2} 0 1 1 -{base_size/2} 0 Z" fill="none" stroke="{theme_color}" stroke-width="5"/>
            <rect id="hub" x="-15" y="-15" width="30" height="30" rx="5" fill="{theme_color}" />
            <line id="spoke" x1="0" y1="-{base_size/2}" x2="0" y2="{base_size/2}" stroke="{theme_color}" stroke-width="2" />
            <line id="spoke2" x1="-{base_size/2}" y1="0" x2="{base_size/2}" y2="0" stroke="{theme_color}" stroke-width="2" />
            
            <g id="animated-wheel">
                <use href="#wheel-shape" />
                <use href="#hub" />
                <use href="#spoke" />
                <use href="#spoke2" />
                <!-- The continuous rotation animation -->
                <animateTransform attributeName="transform" type="rotate" from="0 0 0" to="360 0 0" dur="{healthy_wheel_speed}ms" repeatCount="indefinite" />
            </g>
            
            <g id="locked-wheel">
                <use href="#wheel-shape" stroke="#ff4444" stroke-width="10"/>
                <use href="#hub" fill="#ff4444" />
                <use href="#spoke" stroke="#ff4444"/>
                <use href="#spoke2" stroke="#ff4444"/>
                <rect x="-{base_size/2+20}" y="-{base_size/2+20}" width="{base_size+40}" height="{base_size+40}" rx="10" fill="rgba(255,0,0,0.1)" stroke="red" stroke-width="2" stroke-dasharray="10 10"/>
            </g>
        </defs>

        <!-- Place Axles/Wheels (matching image_0.png labels) -->
        <!-- Axle 1 (Top Left) - DYNAMIC STATE -->
        <g transform="translate(250, 175) scale(0.6)">
            {f'<use href="#locked-wheel"/>' if is_alert else f'<use href="#animated-wheel"/>'}
            <text x="0" y="100" text-anchor="middle" fill="white" font-size="24">AXLE 1</text>
            {f'<text x="0" y="-100" text-anchor="middle" fill="red" font-size="30" font-weight="bold">LOCKED</text>' if is_alert else f'<text x="0" y="-100" text-anchor="middle" fill="#00ff00" font-size="20">ROLLING</text>'}
        </g>
        
        <!-- Axle 2 (Bottom Left) - ALWAYS HEALTHY -->
        <g transform="translate(250, 310) scale(0.6)">
            <use href="#animated-wheel"/>
            <text x="0" y="100" text-anchor="middle" fill="white" font-size="24">AXLE 2</text>
        </g>
        
        <!-- Axle 3 (Top Right) - ALWAYS HEALTHY -->
        <g transform="translate(550, 175) scale(0.6)">
            <use href="#animated-wheel"/>
            <text x="0" y="100" text-anchor="middle" fill="white" font-size="24">AXLE 3</text>
        </g>
        
        <!-- Axle 4 (Bottom Right) - ALWAYS HEALTHY -->
        <g transform="translate(550, 310) scale(0.6)">
            <use href="#animated-wheel"/>
            <text x="0" y="100" text-anchor="middle" fill="white" font-size="24">AXLE 4</text>
        </g>
    </svg>
    """
    components.html(schematic_svg, height=400)


with col_telemetry:
    st.subheader("REAL-TIME ANALYTICS")
    
    # Realism Injection: Liquid Fill Gauge for Probability
    # Replace plain text probability with a sleek digital gauge
    
    st.markdown('<div class="telemetry-card">', unsafe_allow_html=True)
    
    prob_percent = round(probability * 100, 2)
    
    gauge_option = {
        "title": {
            "text": "LOCK PROBABILITY",
            "left": 'center',
            "top": '8%',
            "textStyle": {"color": "white", "fontSize": 18}
        },
        "series": [{
            "type": 'liquidFill',
            "data": [probability, probability-0.05, probability-0.1],
            "radius": '80%',
            "center": ['50%', '60%'],
            "color": [theme_color, theme_color, theme_color],
            "backgroundStyle": {"color": "#1a1c24"},
            "label": {
                "fontSize": 40,
                "color": "#fff",
                "insideColor": "#fff",
                "formatter": f"{prob_percent}%",
                "fontFamily": 'Orbitron'
            },
            "outline": {
                "show": True,
                "borderDistance": 5,
                "itemStyle": {
                    "borderColor": theme_color,
                    "borderWidth": 5,
                }
            }
        }]
    }
    
    st_echarts(option=gauge_option, height="280px")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Additional Realism: Velocity Readout
    st.markdown('<div class="telemetry-card">', unsafe_allow_html=True)
    col_label, col_val = st.columns([2, 1])
    col_label.markdown("#### CURRENT VELOCITY")
    col_val.markdown(f"## <span class='{alert_class}'>{input_data['v_loco_kmh']} km/h</span>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

# Additional data visualization (Bottom Area)
st.subheader("Historical Lock Analysis")
st.line_chart(np.random.randn(20, 1) + (1.0 if is_alert else 0.0))