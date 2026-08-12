import streamlit as st
import requests
import pandas as pd
import streamlit.components.v1 as components
import math

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Locomotive Axle Lock Dashboard",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CUSTOM CSS FOR DARK INDUSTRIAL THEME
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    header {visibility: hidden;}
    section[data-testid="stSidebar"] { background-color: #1a1c24; border-right: 1px solid #2a2d3d; }
    div[data-testid="stMetricValue"] { font-family: monospace; font-size: 2rem !important; }
    .stSlider > div[data-baseweb="slider"] { padding-top: 10px; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; color: #e0e0e0; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# STATE MANAGEMENT
# ==========================================
default_states = {
    'v_loco': 80.0,
    'a1': 40.0,
    'a2': 40.0,
    'a3': 40.0,
    'a4': 40.0,
    'slip': 0.05
}

for k, v in default_states.items():
    if k not in st.session_state:
        st.session_state[k] = v

def set_preset(preset_type):
    if preset_type == "normal":
        st.session_state.v_loco = 80.0
        st.session_state.a1 = 40.0
        st.session_state.a2 = 40.0
        st.session_state.a3 = 40.0
        st.session_state.a4 = 40.0
        st.session_state.slip = 0.05
    elif preset_type == "fault_a1":
        st.session_state.v_loco = 80.0
        st.session_state.a1 = 0.0
        st.session_state.a2 = 40.0
        st.session_state.a3 = 40.0
        st.session_state.a4 = 40.0
        st.session_state.slip = 1.0
    elif preset_type == "fault_multi":
        st.session_state.v_loco = 80.0
        st.session_state.a1 = 40.0
        st.session_state.a2 = 0.0
        st.session_state.a3 = 0.0
        st.session_state.a4 = 40.0
        st.session_state.slip = 0.05

# ==========================================
# SIDEBAR CONTROLS
# ==========================================
with st.sidebar:
    st.markdown("## 🎛️ Control Panel")
    st.markdown("---")
    
    st.markdown("### ⚡ Quick Scenarios")
    st.button("🟢 Normal Running", on_click=set_preset, args=("normal",), use_container_width=True)
    st.button("🔴 Axle 1 Lock Fault", on_click=set_preset, args=("fault_a1",), use_container_width=True)
    st.button("🔴 Axles 2 & 3 Locked", on_click=set_preset, args=("fault_multi",), use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 📡 Telemetry Inputs")
    
    v_loco = st.slider("Locomotive Velocity (km/h)", 0.0, 150.0, key="v_loco")
    a1 = st.slider("Axle 1 Speed (rad/s)", 0.0, 80.0, key="a1")
    a2 = st.slider("Axle 2 Speed (rad/s)", 0.0, 80.0, key="a2")
    a3 = st.slider("Axle 3 Speed (rad/s)", 0.0, 80.0, key="a3")
    a4 = st.slider("Axle 4 Speed (rad/s)", 0.0, 80.0, key="a4")
    slip = st.slider("Axle 1 Slip Ratio", 0.0, 1.0, key="slip")

payload = {
    "v_loco_kmh": v_loco,
    "axle1_speed_rads": a1,
    "axle2_speed_rads": a2,
    "axle3_speed_rads": a3,
    "axle4_speed_rads": a4,
    "axle1_slip_ratio": slip
}

# ==========================================
# LOGIC & FAULT DETECTION
# ==========================================
# We evaluate each axle dynamically. If speed drops drastically below expected velocity, it's considered locked.
r_wheel = 0.54 # meters
v_loco_ms = v_loco / 3.6
expected_omega = v_loco_ms / r_wheel

axle_speeds = [a1, a2, a3, a4]
axle_states = []

is_any_locked = False
for spd in axle_speeds:
    # A wheel is considered locked if locomotive is moving but wheel isn't rotating as expected
    is_locked = (spd < (expected_omega * 0.3)) and (v_loco > 5.0)
    
    if is_locked:
        is_any_locked = True
        axle_states.append({"status": "LOCKED", "class": "wheel-locked", "label": "label-locked", "anim": "0s"})
    else:
        # Dynamic spin speed based on rad/s (capped for visual sanity)
        if spd > 0.1:
            spin_dur = max(0.1, 10.0 / spd)
            axle_states.append({"status": "ROLLING", "class": "wheel-normal", "label": "label-normal", "anim": f"{spin_dur}s"})
        else:
            # Stopped but not a fault (train is stopped)
            axle_states.append({"status": "STOPPED", "class": "wheel-stopped", "label": "label-stopped", "anim": "0s"})

# Determine Banner state
if is_any_locked:
    status_text = "CRITICAL: AXLE LOCK DETECTED"
    color = "#ff0000"
    bg_color = "rgba(255, 0, 0, 0.1)"
    prob = 0.99
else:
    status_text = "NORMAL OPERATION"
    color = "#00ff00"
    bg_color = "rgba(0, 255, 0, 0.05)"
    prob = 0.02

# ==========================================
# MAIN DASHBOARD LAYOUT
# ==========================================
st.markdown(f"""
<div style="
    background-color: {bg_color}; padding: 25px; border-radius: 12px; border: 2px solid {color}; 
    text-align: center; margin-bottom: 25px; box-shadow: 0 0 20px {color}40;
">
    <h1 style="color: {color}; margin: 0; font-family: 'Courier New', Courier, monospace; font-weight: 800; letter-spacing: 4px; text-shadow: 0 0 10px {color};">
        {status_text}
    </h1>
</div>
""", unsafe_allow_html=True)

col_main, col_metrics = st.columns([2.5, 1])

with col_main:
    st.markdown("### 🚂 3D Realistic Live Track Simulation")
    
    # Calculate track speed
    track_anim_dur = "0s"
    if v_loco > 1.0:
        track_anim_dur = f"{max(0.1, 20.0 / v_loco)}s"

    bogie_html = f"""
    <style>
    /* Scene Container */
    .scene-container {{
        background: #0a0a0a;
        border-radius: 12px;
        overflow: hidden;
        border: 2px solid #333;
        position: relative;
        height: 480px;
        width: 100%;
        perspective: 1000px;
        box-shadow: inset 0 0 80px rgba(0,0,0,1);
    }}
    
    /* 3D Realistic Parallax Track */
    .track-layer {{
        position: absolute;
        bottom: 40px;
        width: 200%;
        height: 180px;
        background-color: #111;
        background-image: 
            linear-gradient(90deg, transparent 90%, rgba(255,255,255,0.05) 90%),
            url('data:image/svg+xml;utf8,<svg width="40" height="20" xmlns="http://www.w3.org/2000/svg"><rect x="0" y="5" width="20" height="10" fill="%23222"/></svg>');
        background-size: 60px 100%, 80px 20px;
        border-top: 15px solid #444; /* Back Rail */
        border-bottom: 20px solid #777; /* Front Rail */
        transform: rotateX(60deg) translateY(50px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.8);
    }}
    
    .moving-track {{
        animation: moveTrack {track_anim_dur} linear infinite;
    }}
    
    @keyframes moveTrack {{
        from {{ background-position: 0 0, 0 0; }}
        to {{ background-position: -120px 0, -80px 0; }}
    }}
    
    /* Locomotive Body Section (One Sector) */
    .locomotive-body {{
        position: absolute;
        top: 20px;
        left: 5%;
        width: 90%;
        height: 170px;
        background: linear-gradient(180deg, #d35400 0%, #a04000 70%, #641e16 100%);
        border-radius: 20px 20px 0 0;
        box-shadow: 
            inset 0 15px 15px rgba(255,255,255,0.2),
            inset 0 -15px 30px rgba(0,0,0,0.7),
            0 20px 30px rgba(0,0,0,0.8);
        border: 2px solid #e59866;
        border-bottom: 8px solid #421109;
        z-index: 2;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 40px;
    }}
    .cab-window {{
        width: 120px;
        height: 70px;
        background: linear-gradient(135deg, #aed6f1 0%, #2e86c1 50%, #1b4f72 100%);
        border: 6px solid #222;
        border-radius: 8px;
        box-shadow: inset 5px 5px 15px rgba(255,255,255,0.5), 0 5px 10px rgba(0,0,0,0.5);
    }}
    .vent-grille {{
        width: 180px;
        height: 90px;
        background: repeating-linear-gradient(90deg, #111, #111 8px, #333 8px, #333 16px);
        border: 5px solid #222;
        border-radius: 5px;
        box-shadow: inset 0 0 20px rgba(0,0,0,1);
    }}
    .yellow-stripe {{
        position: absolute;
        bottom: 10px;
        left: 0;
        width: 100%;
        height: 15px;
        background: repeating-linear-gradient(45deg, #f1c40f, #f1c40f 20px, #222 20px, #222 40px);
    }}
    
    /* Chassis / Bogie Frame */
    .bogie-frame {{
        position: absolute;
        top: 190px;
        left: 8%;
        width: 84%;
        height: 80px;
        background: linear-gradient(180deg, #333 0%, #111 100%);
        border-radius: 5px;
        z-index: 4;
        box-shadow: inset 0 5px 10px rgba(255,255,255,0.1), 0 20px 30px rgba(0,0,0,0.8);
        border: 2px solid #444;
    }}
    
    /* 3D Wheel Container */
    .wheels-wrapper {{
        position: absolute;
        top: 200px;
        left: 0;
        width: 100%;
        display: flex;
        justify-content: space-evenly;
        z-index: 5;
    }}
    
    .wheel-unit {{
        display: flex;
        flex-direction: column;
        align-items: center;
        perspective: 500px;
    }}
    
    /* 3D Wheel Design */
    .wheel-3d {{
        width: 130px;
        height: 130px;
        border-radius: 50%;
        background: radial-gradient(circle at 35% 35%, #cd853f 0%, #8b4513 40%, #5c4033 80%, #3e2723 100%);
        box-shadow: 
            inset 0 0 20px rgba(0,0,0,0.9),
            inset 5px 5px 15px rgba(255,255,255,0.4),
            -10px -10px 20px rgba(0,0,0,0.6);
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
        border: 4px solid #a0522d;
        transition: all 0.3s;
    }}
    
    /* Flange (Rim behind the wheel) */
    .wheel-3d::before {{
        content: '';
        position: absolute;
        width: 150px;
        height: 150px;
        border-radius: 50%;
        background: radial-gradient(circle, #8b4513, #5c4033, #2e1a12);
        z-index: -1;
        box-shadow: -5px -5px 10px rgba(0,0,0,0.8);
    }}
    
    /* Hub and Spokes */
    .wheel-3d::after {{
        content: '';
        position: absolute;
        width: 30px;
        height: 30px;
        background: radial-gradient(circle, #d2b48c, #8b4513, #5c4033);
        border-radius: 50%;
        box-shadow: 0 0 10px rgba(0,0,0,0.8);
    }}
    
    .spoke-1, .spoke-2 {{
        position: absolute;
        width: 100%;
        height: 12px;
        background: linear-gradient(90deg, #5c4033, #cd853f, #5c4033);
    }}
    .spoke-2 {{ transform: rotate(90deg); }}
    
    /* States */
    .wheel-normal {{
        border: 4px solid #00ff00;
        box-shadow: inset 0 0 20px rgba(0,255,0,0.4), 0 0 30px rgba(0,255,0,0.6);
    }}
    .wheel-normal::before {{ box-shadow: 0 0 15px rgba(0,255,0,0.4); }}
    
    .wheel-locked {{
        border: 4px solid #ff0000;
        box-shadow: inset 0 0 30px rgba(255,0,0,0.8), 0 0 50px rgba(255,0,0,1);
    }}
    .wheel-locked::before {{ box-shadow: 0 0 25px rgba(255,0,0,0.8); }}
    
    .wheel-stopped {{
        border: 4px solid #555;
    }}

    @keyframes spin {{ 100% {{ transform: rotate(360deg); }} }}
    
    /* Labels */
    .wheel-label {{
        margin-top: 40px;
        padding: 8px 16px;
        border-radius: 6px;
        font-family: 'Orbitron', monospace;
        font-weight: bold;
        font-size: 14px;
        letter-spacing: 1px;
        z-index: 10;
        border-bottom: 3px solid transparent;
        text-align: center;
        background: #111;
    }}
    
    .label-normal {{ color: #00ff00; border-color: #00ff00; box-shadow: 0 5px 15px rgba(0,255,0,0.2); }}
    .label-locked {{ 
        color: #ff0000; 
        border-color: #ff0000; 
        background: #330000;
        animation: pulseAlert 0.8s infinite; 
    }}
    .label-stopped {{ color: #888; border-color: #555; }}
    
    @keyframes pulseAlert {{
        0% {{ box-shadow: 0 0 10px red; }}
        50% {{ box-shadow: 0 0 30px red; transform: scale(1.05); }}
        100% {{ box-shadow: 0 0 10px red; }}
    }}
    </style>
    
    <div class="scene-container">
        <!-- Parallax Track -->
        <div class="track-layer {'moving-track' if track_anim_dur != '0s' else ''}"></div>
        
        <!-- Train Sector Body -->
        <div class="locomotive-body">
            <div class="cab-window"></div>
            <div class="vent-grille"></div>
            <div class="yellow-stripe"></div>
        </div>
        <div class="bogie-frame"></div>
        
        <!-- 4 Axles -->
        <div class="wheels-wrapper">
    """
    
    for i in range(4):
        state = axle_states[i]
        anim_style = f"animation: spin {state['anim']} linear infinite;" if state['anim'] != '0s' else ""
        
        bogie_html += f"""
            <div class="wheel-unit">
                <div class="wheel-3d {state['class']}" style="{anim_style}">
                    <div class="spoke-1"></div>
                    <div class="spoke-2"></div>
                </div>
                <div class="wheel-label {state['label']}">AXLE {i+1}: {state['status']}</div>
            </div>
        """
        
    bogie_html += """
        </div>
    </div>
    """
    
    components.html(bogie_html, height=500)

with col_metrics:
    st.markdown("### 📊 Live Analytics")
    
    st.markdown("""
        <style>
        .metric-container {
            background-color: #1a1c24;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #2a2d3d;
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    delta_color = "inverse" if is_any_locked else "normal"
    st.metric(
        label="Overall Lock Probability", 
        value=f"{prob*100:.1f}%", 
        delta="Risk: HIGH" if is_any_locked else "Risk: LOW", 
        delta_color=delta_color
    )
    
    st.markdown("**Axle Speed Distribution (rad/s)**")
    chart_data = pd.DataFrame(
        {"Speed": [a1, a2, a3, a4]},
        index=["Axle 1", "Axle 2", "Axle 3", "Axle 4"]
    )
    
    st.bar_chart(
        chart_data,
        color="#ff0000" if is_any_locked else "#00ff00",
        height=250
    )