import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

# Reproducibility seed
np.random.seed(42)

# ==========================================
# 1. LOCOMOTIVE PHYSICAL & THERMAL CONSTANTS
# ==========================================
M_total = 120000.0        # Locomotive mass (120 tonnes)
N_axles = 4               # 4 axles total
M_axle = M_total / N_axles # Mass per axle (30 tonnes)
g = 9.81                  # Acceleration due to gravity (m/s^2)
N_normal = M_axle * g     # Normal force per axle (N)

r_wheel = 0.54            # Wheel radius (m)
J_axle = 120.0            # Rotational inertia per axle (kg*m^2)
B_normal = 0.5            # Baseline bearing friction coefficient

# Physical Thermal Dynamics Parameters
C_thermal = 8500.0        # Heat capacity of axle box assembly (J/°C)
R_cooling = 0.15          # Heat dissipation rate to ambient air
T_ambient = 30.0          # Ambient temperature (°C)

# Electrical Motor Parameters
K_e = 2.5                 # Back-EMF constant
R_armature = 0.12         # Armature resistance (Ohms)
V_supply = 600.0          # Line supply voltage (V)

# Creep Model Constants (Polach)
mu_0 = 0.38               # Max adhesion coefficient
k_a = 1.0                 # Adhesion reduction factor
k_s = 0.4                 # Slip reduction factor

# ==========================================
# 2. POLACH WHEEL-RAIL CREEP FORCE MODEL
# ==========================================
def polach_creep_force(v_loco, omega_axle, N_norm):
    v_wheel = omega_axle * r_wheel
    v_ref = max(abs(v_loco), abs(v_wheel), 0.1)
    s_x = (v_wheel - v_loco) / v_ref
    
    if abs(s_x) < 1e-6:
        return 0.0, s_x

    mu_max = mu_0 * (1.0 - k_a * abs(s_x))
    mu_inf = mu_0 * k_s
    mu_eff = mu_max + (mu_inf - mu_max) * (1.0 - np.exp(-10.0 * abs(s_x)))
    
    C = 12000.0 * N_norm
    epsilon = (C * abs(s_x)) / (3.0 * max(mu_eff, 0.01) * N_norm)
    
    f_s = epsilon - (epsilon**2 / 3.0) + (epsilon**3 / 27.0) if epsilon <= 1.0 else 1.0
    F_x = np.sign(s_x) * mu_eff * N_norm * f_s
    return F_x, s_x

# ==========================================
# 3. ODE PHYSICAL SYSTEM
# ==========================================
def physical_quantities_dynamics(t, y):
    v_loco = y[0]
    omegas = y[1:5]
    temps = y[5:9]
    
    T_motor_base = 3500.0 if v_loco < (80.0 / 3.6) else 1000.0
    
    # Fault Torques simulating physical friction spikes
    T_fault_axle1 = 65000.0 if (30.0 <= t <= 45.0) else 0.0  # Axle 1 Bearing seizure
    T_fault_axle3 = 45000.0 if (65.0 <= t <= 80.0) else 0.0  # Axle 3 Brake drag
    
    fault_torques = [T_fault_axle1, 0.0, T_fault_axle3, 0.0]
    
    F_x_total = 0.0
    d_omegas = np.zeros(4)
    d_temps = np.zeros(4)
    
    for i in range(4):
        T_f = fault_torques[i]
        F_x, _ = polach_creep_force(v_loco, omegas[i], N_normal)
        F_x_total += F_x
        
        d_omegas[i] = (T_motor_base - T_f - (F_x * r_wheel) - (B_normal * omegas[i])) / J_axle
        
        friction_power = (T_f * omegas[i]) + (B_normal * (omegas[i]**2))
        heat_dissipated = R_cooling * (temps[i] - T_ambient)
        d_temps[i] = (friction_power - heat_dissipated) / C_thermal
        
    F_drag = 0.5 * 1.2 * 10.0 * 0.35 * (v_loco**2)
    d_v_loco = (F_x_total - F_drag) / M_total
    
    return [d_v_loco, *d_omegas, *d_temps]

# ==========================================
# 4. SIMULATION EXECUTION & DATA EXTRACT
# ==========================================
print("Simulating physical quantities dataset...")

t_span = (0.0, 100.0)
t_eval = np.linspace(0.0, 100.0, 10000)

v_init = 30.0 / 3.6
omega_init = v_init / r_wheel
temp_init = 45.0

y0 = [v_init] + [omega_init]*4 + [temp_init]*4

sol = solve_ivp(physical_quantities_dynamics, t_span, y0, t_eval=t_eval, method='RK45')

data = {}

# Individual Axle Fault Tracker
axle1_active = ((sol.t >= 30.0) & (sol.t <= 45.0)).astype(int)
axle3_active = ((sol.t >= 65.0) & (sol.t <= 80.0)).astype(int)

# Generate sensor columns for each axle
for i in range(1, 5):
    axle_id = i
    raw_omega = sol.y[i]
    raw_temp = sol.y[i + 4]
    
    axle_fault_active = axle1_active if axle_id == 1 else (axle3_active if axle_id == 3 else 0)
    
    # 1. Temperature Stream
    data[f'axle{axle_id}_bearing_temp_c'] = raw_temp + np.random.normal(0, 0.25, len(sol.t))
    
    # 2. Vibration G-Force Stream
    baseline_vib = 0.2 + (raw_omega * 0.004)
    vib_shocks = axle_fault_active * np.random.uniform(2.2, 4.5, len(sol.t))
    data[f'axle{axle_id}_vibration_g'] = baseline_vib + vib_shocks + np.random.normal(0, 0.05, len(sol.t))
    
    # 3. Motor Current Stream
    back_emf_current = (V_supply - K_e * raw_omega) / R_armature
    current_surge = axle_fault_active * 230.0
    data[f'axle{axle_id}_motor_current_amp'] = np.clip(back_emf_current + current_surge + np.random.normal(0, 3.5, len(sol.t)), 10, 650)

# SINGLE OVERALL TARGET OUTPUT
# 1 if ANY axle is experiencing a lock/fault, 0 otherwise
data['axle_lock_label'] = np.where((axle1_active == 1) | (axle3_active == 1), 1, 0)

df = pd.DataFrame(data)

# Export Dataset
output_file = "locomotive_physical_sensors_single_label.csv"
df.to_csv(output_file, index=False)
print(f"Dataset successfully saved as '{output_file}'!")
print(f"Total Columns ({len(df.columns)}):\n{list(df.columns)}")