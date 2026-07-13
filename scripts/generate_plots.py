import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import control as ct

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
figures_dir = os.path.join(project_dir, "report/figures")

# Parameters from the paper (Shi, Liu et al., 2026)
K = -0.25
tau = 35
theta = 4.5

# Sensor feedback gain H(s)
H = 0.2

# PID Tuning (Conservative for stability, physical gains in %/V)
kp = 12.5
ki = 0.4
kd = 2.5

# Time vector
t = np.linspace(0, 500, 2000)

# Plant Model
num_p = [K]
den_p = [tau, 1]
gp_no_delay = ct.TransferFunction(num_p, den_p)

# Pade Approximation
num_d, den_d = ct.pade(theta, n=2)
delay_link = ct.TransferFunction(num_d, den_d)
gp = ct.series(delay_link, gp_no_delay)

# Controller
gc = ct.TransferFunction([kd, kp, ki], [1, 0])

# Systems
go = -ct.series(gc, gp) * H
sys_cl = ct.feedback(go, 1)
sys_dist = ct.feedback(1, go)

# Disturbance model: FOPTD with same tau and theta as the plant
Gd_base = ct.TransferFunction([1], [tau, 1])
Gd = ct.series(delay_link, Gd_base)
T_dist_combined = ct.series(sys_dist, Gd)

# Simulation
setpoint = 22
initial_temp = 28
dist_start_time = 200
dos_magnitude = 5.0

t_out, y_step = ct.step_response(sys_cl, t)
y_final = initial_temp + (setpoint - initial_temp) * y_step

# Disturbance
t_dist_mask = t >= dist_start_time
t_dist = t[t_dist_mask] - dist_start_time
_, y_dist = ct.step_response(T_dist_combined, t_dist)
y_final[t_dist_mask] += y_dist * dos_magnitude

# Error Signal
error_signal = setpoint - y_final

# --- Plot 1: Temperature and Error ---
plt.style.use('seaborn-v0_8-paper')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 10), sharex=True)

# Cálculo de puntos clave para anotaciones
t_after_200_mask = t >= dist_start_time
y_after_200 = y_final[t_after_200_mask]
t_after_200 = t[t_after_200_mask]
peak_val_dos = y_after_200.max()
peak_idx_dos = np.argmax(y_after_200)
peak_t_dos = t_after_200[peak_idx_dos]

t_track_mask = t < dist_start_time
t_track_only = t[t_track_mask]
y_track_only = y_final[t_track_mask]
error_track_only = error_signal[t_track_mask]
band = 6.0 * 0.02  # 2% de banda sobre un escalón de 6°C = 0.12°C
inside_band = np.abs(error_track_only) <= band
ts = 0.0
ts_idx = 0
if np.any(inside_band):
    ts_idx = np.where(inside_band)[0][0]
    ts = t_track_only[ts_idx]

# Subplot 1: Temperatura
ax1.plot(t, y_final, label=r"Temperatura Medida $T_{out}(t)$", color="#1f77b4", linewidth=2.5)
ax1.axhline(setpoint, color="#d62728", linestyle="--", linewidth=1.5, label=f"Setpoint ({setpoint}°C)")
ax1.axhspan(setpoint - band, setpoint + band, color="green", alpha=0.08, label=f"Banda de Tolerancia ±2% (±{band:.2f}°C)")
ax1.axvline(dist_start_time, color="#ff7f0e", linestyle=":", linewidth=2, label=f"Ataque DoS (t={dist_start_time}s)")
ax1.axvspan(dist_start_time, 500, color="#ff7f0e", alpha=0.04, label="Período bajo Perturbación (DoS)")

# Anotación T0
ax1.annotate(r"$T_0 = 28^\circ$C", xy=(0, initial_temp), xytext=(20, initial_temp + 0.8),
             arrowprops=dict(arrowstyle="->", color="black", lw=1),
             fontsize=10, color="black", weight="bold")

# Anotación Pico DoS
ax1.annotate(f"Pico Térmico DoS: {peak_val_dos:.2f}°C\nt = {peak_t_dos:.0f} s",
             xy=(peak_t_dos, peak_val_dos), xytext=(peak_t_dos + 30, peak_val_dos + 0.8),
             arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.5),
             fontsize=10, color="#d62728", weight="bold")

ax1.set_ylabel("Temperatura [°C]", fontsize=11)
ax1.set_title("Respuesta Temporal y Rechazo de Perturbaciones", fontsize=14, fontweight="bold")
ax1.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="none", shadow=True)
ax1.grid(True, alpha=0.3, linestyle="--")
ax1.set_ylim(21, 30)

# Subplot 2: Señal de Error
ax2.plot(t, error_signal, label=r"Señal de Error $e(t) = T_{sp} - T_{out}$", color="#2ca02c", linewidth=2)
ax2.fill_between(t, error_signal, 0, where=(error_signal >= 0), alpha=0.1, color="#2ca02c")
ax2.fill_between(t, error_signal, 0, where=(error_signal < 0), alpha=0.1, color="#d62728")
ax2.axhline(0, color="black", linestyle="-", linewidth=1, alpha=0.5)
ax2.axvline(dist_start_time, color="#ff7f0e", linestyle=":", linewidth=2)

# Anotación ts (Tiempo de asentamiento)
if ts > 0:
    ax2.annotate(f"Asentamiento $t_s \\approx {ts:.0f}$ s", xy=(ts, error_signal[ts_idx]),
                 xytext=(ts - 20, error_signal[ts_idx] - 1.8),
                 arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=1.2),
                 fontsize=10, color="#2ca02c", weight="bold")

# Anotación Pico de Error DoS
peak_err_dos = error_signal[t_after_200_mask].min()
ax2.annotate(f"Error Pico: {peak_err_dos:.2f}°C\nt = {peak_t_dos:.0f} s",
             xy=(peak_t_dos, peak_err_dos), xytext=(peak_t_dos + 40, peak_err_dos - 1.0),
             arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.2),
             fontsize=10, color="#d62728", weight="bold")

ax2.set_xlabel("Tiempo [s]", fontsize=11)
ax2.set_ylabel("Error [°C]", fontsize=11)
ax2.legend(loc="lower right", frameon=True, facecolor="white", edgecolor="none", shadow=True)
ax2.grid(True, alpha=0.3, linestyle="--")
ax2.set_ylim(-6.8, 0.8)

plt.tight_layout()
plt.savefig(os.path.join(figures_dir, "respuesta_temporal.png"), dpi=300)
plt.close()

# --- Plot 2: Reference Tracking Only (D = 0) ---
t_track = np.linspace(0, 300, 1500)
_, y_track_step = ct.step_response(sys_cl, t_track)
y_tracking = initial_temp + (setpoint - initial_temp) * y_track_step
error_tracking = setpoint - y_tracking

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)

ax1.plot(t_track, y_tracking, label=r"$T_{out}(t)$", color="#1f77b4", linewidth=2)
ax1.axhline(setpoint, color="#d62728", linestyle="--", label=f"Setpoint ({setpoint}°C)")
ax1.axhline(initial_temp, color="gray", linestyle=":", alpha=0.5, label=f"$T_0$ ({initial_temp}°C)")
band = abs(setpoint - initial_temp) * 0.02
ax1.axhspan(setpoint - band, setpoint + band, color="green", alpha=0.08, label=f"Banda ±2% ({band:.2f}°C)")
ax1.set_ylabel("Temperatura [°C]")
ax1.set_title("Respuesta al Escalón de Referencia ($D = 0$)", fontsize=14, fontweight="bold")
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

ax2.plot(t_track, error_tracking, label=r"$e(t) = T_{sp} - T_{out}$", color="#2ca02c", linewidth=2)
ax2.axhline(0, color="black", linewidth=0.8)
ax2.set_xlabel("Tiempo [s]")
ax2.set_ylabel("Error [°C]")
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3)

inside_band = np.abs(error_tracking) <= band
if np.any(inside_band):
    ts_idx = np.where(inside_band)[0][0]
    ts = t_track[ts_idx]
    ax2.annotate(f"$t_s \\approx {ts:.0f}$ s", xy=(ts, 0), xytext=(ts + 30, 0.5),
                arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.2),
                fontsize=9, color="#d62728")

plt.tight_layout()
plt.savefig(os.path.join(figures_dir, "respuesta_seguimiento.png"), dpi=300)
plt.close()

# --- Plot 3: Bode Plot ---
mag, phase, omega = ct.bode(go, omega=np.logspace(-2, 1, 500), plot=False)
gm, pm, wg, wp = ct.margin(go)

fig, (ax_mag, ax_phase) = plt.subplots(2, 1, figsize=(8, 8))

ax_mag.semilogx(omega, 20*np.log10(mag), color="blue")
ax_mag.axhline(0, color="red", linestyle="--")
ax_mag.set_ylabel("Magnitud [dB]")
ax_mag.set_title(f"Diagrama de Bode (Margen de Fase: {pm:.2f}°)", fontsize=14)
ax_mag.grid(True, which="both", alpha=0.3)

ax_phase.semilogx(omega, np.degrees(phase), color="purple")
ax_phase.axhline(-180, color="red", linestyle="--")
if not np.isnan(wp):
    ax_phase.plot(wp, pm-180, 'ro')
ax_phase.set_ylabel("Fase [deg]")
ax_phase.set_xlabel("Frecuencia [rad/s]")
ax_phase.grid(True, which="both", alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(figures_dir, "diagrama_bode.png"), dpi=300)
plt.close()

# --- Plot 4: Perturbation Rejection Only (R=0) ---
t_dist_only = np.linspace(0, 400, 2000)
_, y_dist_step = ct.step_response(T_dist_combined, t_dist_only)
dist_scale = dos_magnitude / abs(K)
y_dist_only = setpoint + y_dist_step * dos_magnitude
error_dist = setpoint - y_dist_only

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)

ax1.plot(t_dist_only, y_dist_only, label=r"$T_{out}(t)$", color="#1f77b4", linewidth=2)
ax1.axhline(setpoint, color="#d62728", linestyle="--", label=f"Setpoint ({setpoint}°C)")
peak_val = y_dist_only.max()
peak_idx = np.argmax(y_dist_only)
peak_t = t_dist_only[peak_idx]
ax1.annotate(f"Pico: {peak_val:.2f}°C\nt = {peak_t:.0f} s",
             xy=(peak_t, peak_val), xytext=(peak_t + 60, peak_val - 0.5),
             arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.5),
             fontsize=9, color="#d62728", fontweight="bold")
band_dist = abs(dos_magnitude) * 0.02
ax1.axhspan(setpoint - band_dist, setpoint + band_dist, color="green", alpha=0.08,
            label=f"Banda ±2% ({band_dist:.2f}°C)")
ax1.set_ylabel("Temperatura [°C]")
ax1.set_title(f"Rechazo de Perturbación — DoS +{dos_magnitude}°C  ($R = 0$)", fontsize=14, fontweight="bold")
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

ax2.plot(t_dist_only, error_dist, label=r"$e(t) = T_{sp} - T_{out}$", color="#2ca02c", linewidth=2)
ax2.axhline(0, color="black", linewidth=0.8)
ax2.fill_between(t_dist_only, error_dist, 0, alpha=0.15, color="#2ca02c")
ax2.set_xlabel("Tiempo [s]")
ax2.set_ylabel("Error [°C]")
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(figures_dir, "respuesta_perturbacion.png"), dpi=300)
plt.close()

print("Plots generated successfully.")
