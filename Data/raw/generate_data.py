import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

# ==========================================
# 1. LOCOMOTIVE & RAIL PHYSICAL PARAMETERS
# ==========================================
M_total = 120000.0       # Locomotive mass (kg) = 120 tonnes
N_axles = 4              # Number of axles
M_axle = M_total / N_axles # Mass per axle (30 tonnes)
g = 9.81                 # Acceleration due to gravity (m/s^2)
N_normal = M_axle * g    # Normal force per wheelset (N)

r_wheel = 0.54           # Wheel radius (m)
J_axle = 120.0           # Axle + motor rotational inertia (kg*m^2)
B_normal = 0.5           # Baseline bearing friction coefficient

# Polach Wheel-Rail Creep Model Constants
mu_0 = 0.38              # Maximum adhesion coefficient (dry rail)
k_a = 1.0                # Reduction factor in adhesion zone
k_s = 0.4                # Reduction factor in slip zone

# ==========================================
# 2. POLACH NON-LINEAR CREEP FORCE FUNCTION
# ==========================================
def polach_creep_force(v_loco, omega_axle, N_norm):
    """Calculates non-linear longitudinal tractive/braking force between wheel & rail."""
    v_wheel = omega_axle * r_wheel
    v_ref = max(abs(v_loco), abs(v_wheel), 0.1) # Prevent division by zero
    s_x = (v_wheel - v_loco) / v_ref  # Longitudinal Creepage (Slip Ratio)
    
    if abs(s_x) < 1e-6:
        return 0.0, s_x

    # Polach Adhesion Dynamics
    mu_max = mu_0 * (1.0 - k_a * abs(s_x))
    mu_inf = mu_0 * k_s
    mu_eff = mu_max + (mu_inf - mu_max) * (1.0 - np.exp(-10.0 * abs(s_x)))
    
    C = 12000.0 * N_norm  # Contact stiffness factor
    epsilon = (C * abs(s_x)) / (3.0 * max(mu_eff, 0.01) * N_norm)
    
    if epsilon <= 1.0:
        f_s = epsilon - (epsilon**2 / 3.0) + (epsilon**3 / 27.0)
    else:
        f_s = 1.0
        
    F_x = np.sign(s_x) * mu_eff * N_norm * f_s
    return F_x, s_x

# ==========================================
# 3. DIFFERENTIAL EQUATIONS OF MOTION
# ==========================================
def locomotive_dynamics(t, y):
    """
    State Vector y:
    y[0] = v_loco (m/s)
    y[1] = omega1 (rad/s)
    y[2] = omega2 (rad/s)
    y[3] = omega3 (rad/s)
    y[4] = omega4 (rad/s)
    """
    v_loco = y[0]
    omegas = y[1:5]
    
    # Motor Torque (Constant tractive effort up to cruise speed)
    T_motor = 3500.0 if v_loco < (80.0 / 3.6) else 1000.0  # N*m per axle
    
    # FAULT INJECTION: At t = 15s to 25s, Axle 1 suffers a massive bearing seizure
    T_fault_axle1 = 65000.0 if (15.0 <= t <= 25.0) else 0.0
    
    # Calculate forces and derivative rates for each axle
    F_x_total = 0.0
    d_omegas = np.zeros(4)
    
    for i in range(4):
        T_f = T_fault_axle1 if i == 0 else 0.0
        
        # Compute creep force from Polach model
        F_x, _ = polach_creep_force(v_loco, omegas[i], N_normal)
        F_x_total += F_x
        
        # Axle Rotational Acceleration: J * d(omega)/dt = T_motor - T_fault - (F_x * r) - B*omega
        d_omegas[i] = (T_motor - T_f - (F_x * r_wheel) - (B_normal * omegas[i])) / J_axle
        
    # Locomotive Acceleration: M * dv/dt = Sum(F_x) - Drag
    F_drag = 0.5 * 1.2 * 10.0 * 0.35 * (v_loco**2)  # Aerodynamic Drag Force
    d_v_loco = (F_x_total - F_drag) / M_total
    
    return [d_v_loco, d_omegas[0], d_omegas[1], d_omegas[2], d_omegas[3]]

# ==========================================
# 4. RUN SIMULATION & EXPORT DATASET
# ==========================================
print("Running Python Physics Simulation...")

# Time Span: 40 seconds at 100 Hz resolution
t_span = (0.0, 40.0)
t_eval = np.linspace(0.0, 40.0, 4000)

# Initial conditions: Loco starting at 30 km/h (8.33 m/s) with wheels rolling at equivalent speed
v_init = 30.0 / 3.6
omega_init = v_init / r_wheel
y0 = [v_init, omega_init, omega_init, omega_init, omega_init]

# Solve IVP (Ordinary Differential Equations)
sol = solve_ivp(locomotive_dynamics, t_span, y0, t_eval=t_eval, method='RK45')

# Parse Results into Pandas DataFrame
data = {
    'time_s': sol.t,
    'v_loco_kmh': sol.y[0] * 3.6,
    'axle1_speed_rads': sol.y[1],
    'axle2_speed_rads': sol.y[2],
    'axle3_speed_rads': sol.y[3],
    'axle4_speed_rads': sol.y[4],
}

df = pd.DataFrame(data)

# Compute Features & Fault Labels
df['axle1_slip_ratio'] = ( (df['v_loco_kmh']/3.6/r_wheel) - df['axle1_speed_rads'] ) / np.maximum(df['v_loco_kmh']/3.6/r_wheel, 0.1)
df['axle_lock_label'] = ((df['time_s'] >= 15.0) & (df['time_s'] <= 25.0)).astype(int)

# Add Synthetic Sensor Noise
df['axle1_speed_noisy'] = df['axle1_speed_rads'] + np.random.normal(0, 0.1, len(df))

# Save to CSV
output_filename = "locomotive_axle_lock_python_sim.csv"
df.to_csv(output_filename, index=False)
print(f"Dataset successfully created and exported to '{output_filename}'!")