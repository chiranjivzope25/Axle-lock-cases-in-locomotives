import streamlit as st
import requests
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Dual-Bogie Chassis Mechanical Digital Twin",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Dual 2-Axle Bogie Chassis Real-Time Digital Twin")
st.markdown("Under-Carriage Mechanical Structure with Independent Heating, Brakes, and Vibration for All 4 Axles")

# Friendly tip for mobile users regarding sidebar


FASTAPI_URL = "https://backend-for-locomotive.vercel.app"

# -------------------------------------------------------------
# SIDEBAR: SENSOR TELEMETRY INPUT CONTROLS (ALL 4 AXLES)
# -------------------------------------------------------------
st.sidebar.header("📊 Locomotive Sensor Inputs")

# 1. Kinematics
st.sidebar.subheader("1. Train Kinematics")
v_loco_kmh = st.sidebar.slider("Locomotive Speed (km/h)", 0.0, 160.0, 80.0, 1.0)
axle1_speed = st.sidebar.slider("Axle 1 Speed (rad/s)", 0.0, 200.0, 55.1, 0.5)
axle2_speed = st.sidebar.slider("Axle 2 Speed (rad/s)", 0.0, 200.0, 55.2, 0.5)
axle3_speed = st.sidebar.slider("Axle 3 Speed (rad/s)", 0.0, 200.0, 55.0, 0.5)
axle4_speed = st.sidebar.slider("Axle 4 Speed (rad/s)", 0.0, 200.0, 54.8, 0.5)
axle1_slip = st.sidebar.slider("Axle 1 Slip Ratio", 0.0, 1.0, 0.01, 0.01)

# 2. Axle 1 Physical Sensors
st.sidebar.subheader("2. Axle 1 Sensors (Front Bogie)")
axle1_temp = st.sidebar.slider("Axle 1 Temp (°C)", 20.0, 150.0, 45.0)
axle1_vib = st.sidebar.slider("Axle 1 Vib (G)", 0.0, 10.0, 0.3)
axle1_amp = st.sidebar.slider("Axle 1 Current (A)", 0.0, 700.0, 300.0)

# 3. Axle 2 Physical Sensors
st.sidebar.subheader("3. Axle 2 Sensors (Front Bogie)")
axle2_temp = st.sidebar.slider("Axle 2 Temp (°C)", 20.0, 150.0, 45.0)
axle2_vib = st.sidebar.slider("Axle 2 Vib (G)", 0.0, 10.0, 0.3)
axle2_amp = st.sidebar.slider("Axle 2 Current (A)", 0.0, 700.0, 300.0)

# 4. Axle 3 Physical Sensors
st.sidebar.subheader("4. Axle 3 Sensors (Rear Bogie)")
axle3_temp = st.sidebar.slider("Axle 3 Temp (°C)", 20.0, 150.0, 46.2)
axle3_vib = st.sidebar.slider("Axle 3 Vib (G)", 0.0, 10.0, 0.35)
axle3_amp = st.sidebar.slider("Axle 3 Current (A)", 0.0, 700.0, 305.0)

# 5. Axle 4 Physical Sensors
st.sidebar.subheader("5. Axle 4 Sensors (Rear Bogie)")
axle4_temp = st.sidebar.slider("Axle 4 Temp (°C)", 20.0, 150.0, 44.8)
axle4_vib = st.sidebar.slider("Axle 4 Vib (G)", 0.0, 10.0, 0.28)
axle4_amp = st.sidebar.slider("Axle 4 Current (A)", 0.0, 700.0, 298.0)

# Request Payload Construction
payload = {
    "data_axel": {
        "v_loco_kmh": float(v_loco_kmh),
        "axle1_speed_rads": float(axle1_speed),
        "axle2_speed_rads": float(axle2_speed),
        "axle3_speed_rads": float(axle3_speed),
        "axle4_speed_rads": float(axle4_speed),
        "axle1_slip_ratio": float(axle1_slip)
    },
    "data_phy": {
        "axle1_bearing_temp_c": float(axle1_temp),
        "axle1_vibration_g": float(axle1_vib),
        "axle1_motor_current_amp": float(axle1_amp),
        "axle2_bearing_temp_c": float(axle2_temp),
        "axle2_vibration_g": float(axle2_vib),
        "axle2_motor_current_amp": float(axle2_amp),
        "axle3_bearing_temp_c": float(axle3_temp),
        "axle3_vibration_g": float(axle3_vib),
        "axle3_motor_current_amp": float(axle3_amp),
        "axle4_bearing_temp_c": float(axle4_temp),
        "axle4_vibration_g": float(axle4_vib),
        "axle4_motor_current_amp": float(axle4_amp)
    }
}

# Physical Kinematic Lock Override
lock_threshold = 5.0 if v_loco_kmh > 15.0 else -1.0
is_locked1 = 1 if axle1_speed < lock_threshold else 0
is_locked2 = 1 if axle2_speed < lock_threshold else 0
is_locked3 = 1 if axle3_speed < lock_threshold else 0
is_locked4 = 1 if axle4_speed < lock_threshold else 0

# Backend Request
alert_status = "SYSTEM NORMAL"
display_color = "green"
risk_level = "NORMAL"
prob_kin, prob_phy = 0.0, 0.0

try:
    response = requests.post(FASTAPI_URL, json=payload, timeout=3)
    if response.status_code == 200:
        res_json = response.json()
        alert_status = res_json.get("overall_status", "NORMAL")
        display_color = res_json.get("display_color", "green")
        risk_level = res_json.get("risk_level", "NORMAL")
        models_res = res_json.get("model_outputs", {})
        prob_kin = models_res.get("kinematic_model", {}).get("confidence_score", 0.0)
        prob_phy = models_res.get("physical_model", {}).get("confidence_score", 0.0)
except Exception as e:
    st.warning(f"FastAPI Offline: Operating in local 3D preview mode. Detail: {e}")
    if any([is_locked1, is_locked2, is_locked3, is_locked4]):
        alert_status = "CAUTION: AXLE LOCK DETECTED"
        display_color = "yellow"
        risk_level = "MEDIUM"

color_hex_map = {"green": "#28a745", "yellow": "#ffc107", "orange": "#fd7e14", "red": "#dc3545"}
banner_color = color_hex_map.get(display_color, "#28a745")

st.markdown(
    f"""
    <div style="background-color: {banner_color}; padding: 16px; border-radius: 10px; color: white; text-align: center; font-size: 20px; font-weight: bold; margin-bottom: 20px;">
        {alert_status}
    </div>
    """,
    unsafe_allow_html=True
)

c1, c2, c3 = st.columns(3)
c1.metric("Risk Level", risk_level)
c2.metric("Kinematic Anomaly Score", f"{prob_kin:.1%}")
c3.metric("Physical Hazard Score", f"{prob_phy:.1%}")

st.divider()

# Color mappings helper (Returns Clean CSS Hex & JS Hex)
def get_sensor_hex(temp, vib, is_locked):
    if is_locked or temp > 90 or vib > 2.5:
        return "#ff2222"  # Red
    elif temp > 70 or vib > 1.2:
        return "#ff8800"  # Orange
    else:
        return "#00ff66"  # Green

# CSS Color Variables
c_a1 = get_sensor_hex(axle1_temp, axle1_vib, is_locked1)
c_a2 = get_sensor_hex(axle2_temp, axle2_vib, is_locked2)
c_a3 = get_sensor_hex(axle3_temp, axle3_vib, is_locked3)
c_a4 = get_sensor_hex(axle4_temp, axle4_vib, is_locked4)

# JavaScript Hex String Conversions (0xff2222)
js_c_a1 = c_a1.replace("#", "0x")
js_c_a2 = c_a2.replace("#", "0x")
js_c_a3 = c_a3.replace("#", "0x")
js_c_a4 = c_a4.replace("#", "0x")

track_speed_factor = float(v_loco_kmh) * 0.003

# -------------------------------------------------------------
# THREE.JS 3D DUAL-BOGIE DIGITAL TWIN (MOBILE RESPONSIVE)
# -------------------------------------------------------------
three_js_code = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ margin: 0; overflow: hidden; background: #080a0f; font-family: 'Segoe UI', Arial, sans-serif; }}
        canvas {{ width: 100vw; height: 100vh; display: block; }}
        #hud {{
            position: absolute;
            top: 10px;
            left: 10px;
            right: 10px;
            max-width: 330px;
            width: auto;
            color: #ffffff;
            background: rgba(10, 14, 23, 0.92);
            border: 1px solid rgba(0, 210, 255, 0.3);
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 11px;
            backdrop-filter: blur(8px);
        }}
        .axle-box {{
            margin-bottom: 4px;
            padding: 4px 8px;
            background: rgba(255,255,255,0.05);
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
        }}
        .tag {{ padding: 2px 5px; border-radius: 3px; font-weight: bold; color: #000; }}

        /* Mobile Viewport Optimizations */
        @media (max-width: 600px) {{
            #hud {{
                font-size: 10px;
                padding: 8px;
                top: 8px;
                left: 8px;
            }}
            .axle-box {{
                font-size: 9px;
                padding: 3px 6px;
            }}
        }}
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
    <div id="hud">
        <div style="font-weight: bold; font-size: 13px; margin-bottom: 6px; color: #00d2ff;">
            🛠️ DUAL 2-AXLE BOGIE MECHANICAL CHASSIS
        </div>
        <div style="margin-bottom: 6px;"><strong>Track Speed:</strong> {v_loco_kmh} km/h</div>
        
        <div class="axle-box">
            <span><strong>Axle 1 (Front):</strong> {axle1_temp}°C | {axle1_vib}G | {axle1_amp}A</span>
            <span class="tag" style="background: {c_a1};">{'LOCKED' if is_locked1 else 'OK'}</span>
        </div>
        <div class="axle-box">
            <span><strong>Axle 2 (Front):</strong> {axle2_temp}°C | {axle2_vib}G | {axle2_amp}A</span>
            <span class="tag" style="background: {c_a2};">{'LOCKED' if is_locked2 else 'OK'}</span>
        </div>
        <div class="axle-box">
            <span><strong>Axle 3 (Rear):</strong> {axle3_temp}°C | {axle3_vib}G | {axle3_amp}A</span>
            <span class="tag" style="background: {c_a3};">{'LOCKED' if is_locked3 else 'OK'}</span>
        </div>
        <div class="axle-box">
            <span><strong>Axle 4 (Rear):</strong> {axle4_temp}°C | {axle4_vib}G | {axle4_amp}A</span>
            <span class="tag" style="background: {c_a4};">{'LOCKED' if is_locked4 else 'OK'}</span>
        </div>
        <div style="margin-top: 6px; color: #8a9ba8;">🖱️ Touch/Drag: Rotate | Pinch: Zoom</div>
    </div>

    <script>
        const scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x080a0f, 0.018);

        const camera = new THREE.PerspectiveCamera(40, window.innerWidth / window.innerHeight, 0.1, 1000);

        // Adjust camera zoom for mobile screen aspect ratios
        const aspect = window.innerWidth / window.innerHeight;
        if (aspect < 1.0) {{
            camera.position.set(18, 10, 18); // Mobile Portrait Mode (Zoom Out)
        }} else {{
            camera.position.set(11, 6, 11);  // Widescreen Desktop View
        }}

        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.shadowMap.enabled = true;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        document.body.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;

        scene.add(new THREE.AmbientLight(0xffffff, 0.7));
        const sun = new THREE.DirectionalLight(0xffffff, 2.0);
        sun.position.set(15, 22, 12);
        sun.castShadow = true;
        scene.add(sun);

        // --- INDUSTRIAL METALLIC MATERIALS ---
        const darkChassisMat = new THREE.MeshStandardMaterial({{ color: 0x1f242c, metalness: 0.8, roughness: 0.3 }});
        const steelReflect = new THREE.MeshStandardMaterial({{ color: 0xcccccc, metalness: 0.95, roughness: 0.15 }});
        const darkMetal = new THREE.MeshStandardMaterial({{ color: 0x22252a, metalness: 0.7, roughness: 0.4 }});
        const railMat = new THREE.MeshStandardMaterial({{ color: 0x777a80, metalness: 0.95, roughness: 0.1 }});
        const sleeperMat = new THREE.MeshStandardMaterial({{ color: 0x303338, roughness: 0.9 }});

        function createCableMat(ampVal) {{
            const intensity = ampVal / 700.0;
            return new THREE.MeshStandardMaterial({{
                color: 0x00d2ff,
                emissive: 0x00a2ff,
                emissiveIntensity: 0.2 + intensity * 1.5
            }});
        }}

        // Track & Sleepers
        const sleeperGroup = new THREE.Group();
        const sleeperGeo = new THREE.BoxGeometry(2.8, 0.16, 0.4);

        for (let z = -25; z <= 25; z += 0.85) {{
            const sleeper = new THREE.Mesh(sleeperGeo, sleeperMat);
            sleeper.position.set(0, -0.3, z);
            sleeper.receiveShadow = true;
            sleeperGroup.add(sleeper);
        }}
        scene.add(sleeperGroup);

        // Rails
        const railShape = new THREE.Shape();
        railShape.moveTo(-0.08, 0); railShape.lineTo(0.08, 0);
        railShape.lineTo(0.08, 0.04); railShape.lineTo(0.03, 0.1);
        railShape.lineTo(0.04, 0.2); railShape.lineTo(-0.04, 0.2);
        railShape.lineTo(-0.03, 0.1); railShape.lineTo(-0.08, 0.04);

        const railExtrude = new THREE.ExtrudeGeometry(railShape, {{ depth: 52, bevelEnabled: false }});
        const railL = new THREE.Mesh(railExtrude, railMat);
        railL.position.set(-1.1, -0.22, -26);
        scene.add(railL);

        const railR = railL.clone();
        railR.position.set(1.1, -0.22, -26);
        scene.add(railR);

        // Frame Spine
        const centerSpineGeo = new THREE.BoxGeometry(1.2, 0.25, 9.0);
        const centerSpine = new THREE.Mesh(centerSpineGeo, darkChassisMat);
        centerSpine.position.set(0, 0.55, 0);
        centerSpine.castShadow = true;
        scene.add(centerSpine);

        function createBogieBlock(centerZ) {{
            const bogie = new THREE.Group();

            const transomGeo = new THREE.BoxGeometry(2.2, 0.28, 0.9);
            const transom = new THREE.Mesh(transomGeo, darkChassisMat);
            transom.position.set(0, 0.45, 0);
            transom.castShadow = true;
            bogie.add(transom);

            const sideBeamGeo = new THREE.BoxGeometry(0.2, 0.3, 2.8);
            const sideL = new THREE.Mesh(sideBeamGeo, darkChassisMat);
            sideL.position.set(-1.25, 0.35, 0);
            sideL.castShadow = true;
            bogie.add(sideL);

            const sideR = sideL.clone();
            sideR.position.set(1.25, 0.35, 0);
            bogie.add(sideR);

            bogie.position.set(0, 0, centerZ);
            scene.add(bogie);
            return bogie;
        }}

        createBogieBlock(-3.35);
        createBogieBlock(3.35);

        // Individual Axle Assemblies
        function createAxle(colorHex, isLocked, tempVal, vibVal, ampVal, speedVal, posZ) {{
            const group = new THREE.Group();

            const axleGeo = new THREE.CylinderGeometry(0.08, 0.08, 2.3, 32);
            axleGeo.rotateZ(Math.PI / 2);
            const axleMesh = new THREE.Mesh(axleGeo, steelReflect);
            group.add(axleMesh);

            const wheelGeo = new THREE.CylinderGeometry(0.5, 0.5, 0.12, 32);
            wheelGeo.rotateZ(Math.PI / 2);

            const wL = new THREE.Mesh(wheelGeo, steelReflect);
            wL.position.set(-1.1, 0, 0);
            group.add(wL);

            const wR = new THREE.Mesh(wheelGeo, steelReflect);
            wR.position.set(1.1, 0, 0);
            group.add(wR);

            // Brakes
            const isBraking = (speedVal < 30.0 || isLocked == 1);
            const brakeMat = new THREE.MeshStandardMaterial({{
                color: isBraking ? 0xff4400 : 0x222222,
                emissive: isBraking ? 0xff2200 : 0x000000,
                emissiveIntensity: isBraking ? 0.8 : 0.0,
                metalness: 0.8
            }});
            const shoeGeo = new THREE.BoxGeometry(0.12, 0.22, 0.16);

            const shoeL = new THREE.Mesh(shoeGeo, brakeMat);
            shoeL.position.set(-1.1, 0.1, isBraking ? -0.52 : -0.6);
            group.add(shoeL);

            const shoeR = shoeL.clone();
            shoeR.position.set(1.1, 0.1, isBraking ? -0.52 : -0.6);
            group.add(shoeR);

            // Traction Motor & Cable
            const motorGeo = new THREE.CylinderGeometry(0.25, 0.25, 0.6, 24);
            motorGeo.rotateZ(Math.PI / 2);
            const motor = new THREE.Mesh(motorGeo, darkMetal);
            motor.position.set(0, 0, -0.2);
            group.add(motor);

            const cableGeo = new THREE.CylinderGeometry(0.02, 0.02, 0.5, 12);
            const cable = new THREE.Mesh(cableGeo, createCableMat(ampVal));
            cable.position.set(0, 0.28, -0.2);
            group.add(cable);

            // Bearing Box
            const boxGeo = new THREE.BoxGeometry(0.28, 0.3, 0.28);
            const boxMat = new THREE.MeshStandardMaterial({{
                color: parseInt(colorHex),
                emissive: parseInt(colorHex),
                emissiveIntensity: (tempVal > 70 || isLocked == 1) ? 0.95 : 0.15,
                roughness: 0.2
            }});

            const boxL = new THREE.Mesh(boxGeo, boxMat);
            boxL.position.set(-1.3, 0, 0);
            group.add(boxL);

            const boxR = new THREE.Mesh(boxGeo, boxMat);
            boxR.position.set(1.3, 0, 0);
            group.add(boxR);

            group.position.set(0, 0.28, posZ);
            scene.add(group);

            // Thermal Smoke Particles
            let particles = null;
            if (tempVal > 70) {{
                const pCount = 25;
                const pGeo = new THREE.BufferGeometry();
                const pPos = new Float32Array(pCount * 3);
                for(let i = 0; i < pCount * 3; i += 3) {{
                    pPos[i] = (Math.random() - 0.5) * 2.6;
                    pPos[i+1] = 0.3 + Math.random() * 0.4;
                    pPos[i+2] = posZ + (Math.random() - 0.5) * 0.2;
                }}
                pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
                const pMat = new THREE.PointsMaterial({{ color: 0xff4400, size: 0.08, transparent: true, opacity: 0.8 }});
                particles = new THREE.Points(pGeo, pMat);
                scene.add(particles);
            }}

            return {{ group, wL, wR, isLocked, vibVal, tempVal, speedVal, particles }};
        }}

        // Axle Assemblies
        const axle1 = createAxle("{js_c_a1}", {is_locked1}, {axle1_temp}, {axle1_vib}, {axle1_amp}, {axle1_speed}, -4.5);
        const axle2 = createAxle("{js_c_a2}", {is_locked2}, {axle2_temp}, {axle2_vib}, {axle2_amp}, {axle2_speed}, -2.2);
        const axle3 = createAxle("{js_c_a3}", {is_locked3}, {axle3_temp}, {axle3_vib}, {axle3_amp}, {axle3_speed}, 2.2);
        const axle4 = createAxle("{js_c_a4}", {is_locked4}, {axle4_temp}, {axle4_vib}, {axle4_amp}, {axle4_speed}, 4.5);

        const axlesList = [axle1, axle2, axle3, axle4];

        // Animation Loop
        const trackSpeed = {track_speed_factor};
        const speeds = [
            {float(axle1_speed) * 0.0012},
            {float(axle2_speed) * 0.0012},
            {float(axle3_speed) * 0.0012},
            {float(axle4_speed) * 0.0012}
        ];

        function animate() {{
            requestAnimationFrame(animate);

            // Move Sleepers
            sleeperGroup.children.forEach(s => {{
                s.position.z += trackSpeed;
                if (s.position.z > 25) s.position.z -= 50;
            }});

            axlesList.forEach((ax, idx) => {{
                if (!ax.isLocked) {{
                    ax.wL.rotation.x += speeds[idx];
                    ax.wR.rotation.x += speeds[idx];
                }}

                if (ax.vibVal > 0.5 || ax.isLocked) {{
                    const shakeFactor = (ax.isLocked ? 1.5 : 1.0) * ax.vibVal * 0.006;
                    ax.group.position.x = (Math.random() - 0.5) * shakeFactor;
                    ax.group.position.y = 0.28 + (Math.random() - 0.5) * shakeFactor;
                }} else {{
                    ax.group.position.x = 0;
                    ax.group.position.y = 0.28;
                }}

                if (ax.particles) {{
                    const pos = ax.particles.geometry.attributes.position.array;
                    for(let i=1; i<pos.length; i+=3) {{
                        pos[i] += 0.009;
                        if (pos[i] > 1.3) pos[i] = 0.3;
                    }}
                    ax.particles.geometry.attributes.position.needsUpdate = true;
                }}
            }});

            controls.update();
            renderer.render(scene, camera);
        }}

        animate();

        window.addEventListener('resize', () => {{
            const newAspect = window.innerWidth / window.innerHeight;
            camera.aspect = newAspect;
            if (newAspect < 1.0) {{
                camera.position.set(18, 10, 18);
            }} else {{
                camera.position.set(11, 6, 11);
            }}
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});
    </script>
</body>
</html>
"""

components.html(three_js_code, height=520)