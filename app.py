import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import control as ct
import time

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Simulador TFI – Control Térmico Data Center",
    layout="wide",
    page_icon="🌡️",
)

st.title("🌡️ Simulador de Control Térmico — Data Center")
st.caption("**TFI — Teoría de Control (K-4011) · UTN FRBA · Julio 2026**")
st.markdown(
    "Programa de simulación del sistema de control **PID** en lazo cerrado para la "
    "estabilización térmica del pasillo frío de un Data Center, basado en un modelo "
    "de planta **FOPTD** y una unidad CRAC Schneider Electric Uniflair™ (Serie LE/DX).  \n"
    "Permite verificar la funcionalidad del sistema mediante la **interrelación de "
    "las señales y variables** en tiempo real."
)

# ═══════════════════════════════════════════════════════════════
# BARRA LATERAL — PARÁMETROS DEL SISTEMA
# ═══════════════════════════════════════════════════════════════
st.sidebar.header("⚙️ Parámetros del Sistema")

# --- Planta FOPTD ---
st.sidebar.subheader("🏭 Planta FOPTD")
st.sidebar.latex(r"G_p(s) = \frac{K \, e^{-\theta s}}{\tau s + 1}")
K_p = st.sidebar.number_input(
    "K — Ganancia estática [°C/%]", value=-0.25, step=0.01, format="%.2f",
    help="Ganancia inversa: +1 % esfuerzo de enfriamiento → K °C",
)
tau = st.sidebar.number_input(
    "τ — Constante de tiempo [s]", value=35.0, step=1.0, format="%.1f",
    help="Inercia térmica de la zona confinada del pasillo frío",
)
theta = st.sidebar.number_input(
    "θ — Tiempo muerto [s]", value=4.5, step=0.5, format="%.1f",
    help="Retardo de transporte del aire desde CRAC al plano de servidores",
)

# --- Controlador PID ---
st.sidebar.subheader("🎛️ Controlador PID")
st.sidebar.latex(r"G_c(s) = K_p + \frac{K_i}{s} + K_d \cdot s")
Kp = st.sidebar.number_input("Kp [%/V]", value=12.5, step=0.5, format="%.1f")
Ki = st.sidebar.number_input("Ki [%/(V·s)]", value=0.4, step=0.1, format="%.1f")
Kd = st.sidebar.number_input("Kd [%·s/V]", value=2.5, step=0.5, format="%.1f")

# --- Instrumentación ---
H = 0.2   # V/°C — Sensor RTD Pt100 (realimentación)
Hr = 0.2  # V/°C — Transmisor de referencia
st.sidebar.subheader("📡 Instrumentación")
st.sidebar.markdown(
    f"| Elemento | Valor |\n"
    f"|---|---|\n"
    f"| Sensor Pt100 H(s) | **{H} V/°C** |\n"
    f"| Transmisor ref. Hr(s) | **{Hr} V/°C** |\n"
    f"| Rango sensor | 0–50 °C → 0–10 V |\n"
    f"| ADC (lectura) | 10 bits |\n"
    f"| DAC (actuador) | 8 bits (PWM) |"
)
st.sidebar.caption(
    f"**Equivalencias dominio software (÷ H):**  \n"
    f"Kp_sw = {Kp * H:.2f} %/°C · Ki_sw = {Ki * H:.3f} %/(°C·s) · "
    f"Kd_sw = {Kd * H:.2f} %·s/°C"
)

# --- Escenario ---
st.sidebar.subheader("🌡️ Escenario Operativo")
T0 = st.sidebar.number_input(
    "T₀ — Temperatura inicial [°C]", value=28.0, step=0.5, format="%.1f",
)
Tsp = st.sidebar.number_input(
    "T_sp — Setpoint [°C]", value=22.0, step=0.5, format="%.1f",
)
t_sim = st.sidebar.slider("Tiempo de simulación [s]", 200, 1000, 600)

# --- Perturbación ---
st.sidebar.subheader("⚠️ Perturbación Térmica")
dist_on = st.sidebar.checkbox("Habilitar perturbación (Ataque DoS)", value=True)
t_dist = (
    st.sidebar.number_input("Instante de inyección [s]", value=200.0, step=10.0, format="%.0f")
    if dist_on else 200.0
)
D_mag = (
    st.sidebar.number_input("Magnitud ΔT [°C]", value=5.0, step=0.5, format="%.1f")
    if dist_on else 0.0
)

# ═══════════════════════════════════════════════════════════════
# CONSTRUCCIÓN DEL SISTEMA DE CONTROL
# ═══════════════════════════════════════════════════════════════

# 1. Planta sin retardo: Gp_base(s) = K / (τs + 1)
gp_base = ct.TransferFunction([K_p], [tau, 1])

# 2. Aproximación de Padé (orden 2) para e^{-θs}
if theta > 0:
    num_pade, den_pade = ct.pade(theta, n=2)
    delay_tf = ct.TransferFunction(num_pade, den_pade)
    gp = ct.series(delay_tf, gp_base)
else:
    gp = gp_base

# 3. PID paralelo: Gc(s) = (Kd·s² + Kp·s + Ki) / s
gc = ct.TransferFunction([Kd, Kp, Ki], [1, 0])

# 4. Trayectoria directa con corrección de signo: Gd(s) = −Gc(s)·Gp(s)
gd = -ct.series(gc, gp)

# 5. Lazo abierto: Gol(s) = Gd(s)·H(s) = −Gc(s)·Gp(s)·H(s)
gol = gd * H

# 6. Lazo cerrado — seguimiento: T(s) = Gol/(1+Gol)
T_cl = ct.feedback(gol, 1)

# 7. Rechazo de perturbaciones: Td(s) = 1 / (1 + Gol)
T_dist = ct.feedback(1, gol)

# Perturbación modelada como FOPTD (misma inercia y retardo que la planta)
Gd_base = ct.TransferFunction([1], [tau, 1])
Gd = ct.series(delay_tf, Gd_base)
T_dist_combined = ct.series(T_dist, Gd)

# 8. Sensibilidad: S(s) = 1/(1+Gol)
one_tf = ct.TransferFunction([1], [1])
S_tf = ct.feedback(one_tf, gol)

# 9. R→U (señal de control ante referencia)
try:
    T_ru = ct.minreal(ct.series(-gc * Hr, S_tf))
except Exception:
    T_ru = ct.series(-gc * Hr, S_tf)

# 10. D→U (señal de control ante perturbación)
try:
    T_du = ct.minreal(ct.series(gc * H, T_dist))
except Exception:
    T_du = ct.series(gc * H, T_dist)

# ═══════════════════════════════════════════════════════════════
# SIMULACIÓN NUMÉRICA
# ═══════════════════════════════════════════════════════════════
N_pts = 3000
t = np.linspace(0, t_sim, N_pts)
delta_R = Tsp - T0  # Cambio de referencia (ej: −6 °C)

# Respuesta de seguimiento
_, y_cl_step = ct.step_response(T_cl, t)
y_tracking = T0 + delta_R * y_cl_step

# Error de seguimiento
err_tracking = Tsp - y_tracking

# Señal de control u(t) — seguimiento
try:
    _, u_step_resp = ct.step_response(T_ru, t)
    u_tracking = np.clip(u_step_resp * delta_R, 0, 100)
    u_available = True
except Exception:
    u_tracking = np.zeros_like(t)
    u_available = False

# Respuesta combinada: seguimiento + perturbación
y_combined = y_tracking.copy()
u_combined = u_tracking.copy()
if dist_on and D_mag > 0:
    dist_scale = D_mag / abs(K_p)
    idx_d = t >= t_dist
    t_shifted = t[idx_d] - t_dist
    _, y_d_resp = ct.step_response(T_dist_combined, t_shifted)
    y_combined[idx_d] += y_d_resp * D_mag
    try:
        _, u_d_resp = ct.step_response(T_du, t_shifted)
        u_dist_full = np.zeros_like(t)
        u_dist_full[idx_d] = u_d_resp * dist_scale
        u_combined = np.clip(u_tracking + u_dist_full, 0, 100)
    except Exception:
        pass

err_combined = Tsp - y_combined

# Señales de tensión del sensor y del transmisor
v_sensor_combined = H * y_combined       # V_sensor(t) = H · T_out(t)
v_setpoint = Hr * Tsp                    # V_sp = Hr · T_sp (constante)
e_voltage = v_setpoint - v_sensor_combined  # Error en voltaje

# ═══════════════════════════════════════════════════════════════
# MÉTRICAS DE RESPUESTA
# ═══════════════════════════════════════════════════════════════
def calc_metrics(t_arr, y_arr, sp, y0):
    """Sobreimpulso, tiempo de asentamiento, tiempo de subida, e_ss."""
    delta = sp - y0
    if abs(delta) < 0.01:
        return 0, 0, 0, abs(sp - y_arr[-1]), "N/A"

    # Sobreimpulso
    if delta < 0:
        y_ext = y_arr.min()
        os_abs = sp - y_ext
    else:
        y_ext = y_arr.max()
        os_abs = y_ext - sp
    os_pct = max(0, os_abs / abs(delta) * 100)

    # Tiempo de asentamiento (±2 %)
    band = abs(delta) * 0.02
    inside = np.abs(y_arr - sp) <= band
    out_idx = np.where(~inside)[0]
    if len(out_idx) > 0 and out_idx[-1] + 1 < len(t_arr):
        ts = t_arr[out_idx[-1] + 1]
    elif len(out_idx) > 0:
        ts = t_arr[-1]
    else:
        ts = t_arr[0]

    # Tiempo de subida (10 %–90 %)
    y10 = y0 + 0.1 * delta
    y90 = y0 + 0.9 * delta
    if delta < 0:
        i10 = np.where(y_arr <= y10)[0]
        i90 = np.where(y_arr <= y90)[0]
    else:
        i10 = np.where(y_arr >= y10)[0]
        i90 = np.where(y_arr >= y90)[0]
    tr = (t_arr[i90[0]] - t_arr[i10[0]]) if len(i10) > 0 and len(i90) > 0 else 0

    ess = abs(sp - y_arr[-1])
    regime = "Sobreamortiguado" if os_pct < 0.5 else "Subamortiguado"
    return os_pct, ts, tr, ess, regime


os_pct, ts_val, tr_val, ess_val, regime = calc_metrics(t, y_tracking, Tsp, T0)


# ═══════════════════════════════════════════════════════════════
# PESTAÑAS
# ═══════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs([
    "📈 Respuesta Temporal y Señales",
    "🏭 Identificación del Sistema",
    "⏱️ Simulación en Tiempo Real",
])

# ─────────────────────────────────────────────────────────────
# TAB 1: RESPUESTA TEMPORAL — INTERRELACIÓN DE SEÑALES
# ─────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Respuesta del Sistema en Lazo Cerrado")
    st.markdown(
        "Interrelación de todas las señales del lazo de control: "
        "**temperatura** $T_{out}(t)$, **error** $e(t)$, **señal de control** "
        "$u(t)$, y **señales de tensión** del sensor/transmisor."
    )

    # Métricas de respuesta
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Sobreimpulso", f"{os_pct:.1f} %")
    m2.metric("T. asentamiento (±2 %)", f"{ts_val:.1f} s")
    m3.metric("T. subida (10–90 %)", f"{tr_val:.1f} s")
    m4.metric("Error estacionario", f"{ess_val:.4f} °C")
    m5.metric("Régimen", regime)

    st.markdown("---")

    # --- Gráfico: T(t), e(t), u(t), señales de tensión ---
    plt.rcParams.update({"font.size": 11, "figure.dpi": 130})

    n_sub = 4 if u_available else 3
    ratios = [3, 1.5, 1.5, 1.5] if u_available else [3, 1.5, 1.5]
    fig, axes = plt.subplots(
        n_sub, 1, figsize=(12, 3.2 * n_sub),
        sharex=True, gridspec_kw={"height_ratios": ratios},
    )
    ax_T = axes[0]
    ax_e = axes[1]
    ax_v = axes[2]
    ax_u = axes[3] if u_available else None

    # ─── 1. Temperatura T_out(t) ───
    y_plot = y_combined if dist_on else y_tracking
    ax_T.plot(t, y_plot, label="Temperatura T_out(t) — Variable controlada", color="#1f77b4", linewidth=2.5)
    if dist_on:
        ax_T.plot(t, y_tracking, color="#1f77b4", linewidth=1, linestyle=":", alpha=0.4,
                  label="Temperatura T_out(t) sin perturbación")
        ax_T.axvline(t_dist, color="orange", linestyle=":", linewidth=2,
                     label=f"Perturbación +{D_mag} °C (t = {t_dist:.0f} s)")
        idx_after = t >= t_dist
        if np.any(idx_after):
            peak_val = y_combined[idx_after].max()
            peak_idx = np.argmax(y_combined[idx_after])
            peak_t = t[idx_after][peak_idx]
            ax_T.annotate(
                f"Pico: {peak_val:.2f} °C", xy=(peak_t, peak_val),
                xytext=(peak_t + 40, peak_val + 0.8),
                arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.5),
                fontsize=10, color="#d62728", fontweight="bold",
            )

    ax_T.axhline(Tsp, color="#d62728", linestyle="--", linewidth=1.5, label=f"Setpoint = {Tsp} °C")
    ax_T.axhline(T0, color="gray", linestyle=":", linewidth=1, alpha=0.5, label=f"T₀ = {T0} °C")
    band_2 = abs(delta_R) * 0.02
    ax_T.axhspan(Tsp - band_2, Tsp + band_2, color="green", alpha=0.07,
                 label=f"Banda ±2 % ({band_2:.2f} °C)")
    ax_T.set_ylabel("Temperatura [°C]")
    ax_T.set_title("Interrelación de Señales del Sistema de Control Térmico", fontweight="bold", fontsize=13)
    ax_T.legend(loc="upper right", fontsize=8, frameon=True, shadow=True)
    ax_T.grid(True, linestyle="--", alpha=0.4)
    ymin = min(y_plot.min(), Tsp) - 1.5
    ymax = max(y_plot.max(), T0) + 1.5
    ax_T.set_ylim(ymin, ymax)

    # ─── 2. Error e(t) en °C ───
    err_plot = err_combined if dist_on else err_tracking
    ax_e.plot(t, err_plot, label="Error e(t) = T_sp - T_out(t) [°C]", color="#2ca02c", linewidth=2)
    ax_e.axhline(0, color="black", linewidth=0.8)
    ax_e.set_ylabel("Error [°C]")
    ax_e.legend(loc="upper right", fontsize=9)
    ax_e.grid(True, linestyle="--", alpha=0.4)

    # ─── 3. Señales de tensión: V_sensor, V_sp, E_v ───
    ax_v.plot(t, v_sensor_combined, label="Medición V_sensor(t) = H · T_out [V]",
              color="#ff7f0e", linewidth=2)
    ax_v.axhline(v_setpoint, color="#d62728", linestyle="--", linewidth=1.5,
                 label=f"Referencia V_sp = H · T_sp = {v_setpoint:.1f} V")
    ax_v.plot(t, e_voltage, label="Error E_v(t) = V_sp - V_sensor [V]",
              color="#17becf", linewidth=1.5, linestyle="-.")
    ax_v.axhline(0, color="black", linewidth=0.8)
    ax_v.set_ylabel("Tensión [V]")
    ax_v.legend(loc="upper right", fontsize=8)
    ax_v.grid(True, linestyle="--", alpha=0.4)

    # ─── 4. Señal de control u(t) ───
    if ax_u is not None:
        u_plot = u_combined if dist_on else u_tracking
        ax_u.plot(t, u_plot, label="Control u(t) — Variable manipulada [%]",
                  color="#9467bd", linewidth=2)
        ax_u.axhline(0, color="black", linewidth=0.8)
        ax_u.axhline(100, color="gray", linestyle=":", linewidth=0.8, alpha=0.5)
        ax_u.set_ylabel("Control [%]")
        ax_u.set_xlabel("Tiempo [s]")
        ax_u.legend(loc="upper right", fontsize=9)
        ax_u.grid(True, linestyle="--", alpha=0.4)
        ax_u.set_ylim(-5, max(u_plot.max() * 1.3, 30))
    else:
        ax_v.set_xlabel("Tiempo [s]")

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Métricas de perturbación
    if dist_on and D_mag > 0:
        st.markdown("#### Rechazo de Perturbación")
        idx_after = t >= t_dist
        if np.any(idx_after):
            peak_val = y_combined[idx_after].max()
            peak_t = t[idx_after][np.argmax(y_combined[idx_after])]
            recovered = np.abs(y_combined[idx_after] - Tsp) <= band_2
            t_recovery = t[-1]
            for ri in range(len(recovered)):
                if recovered[ri] and np.all(recovered[ri:]):
                    t_recovery = t[idx_after][ri]
                    break

            pc1, pc2, pc3, pc4 = st.columns(4)
            pc1.metric("Pico de temperatura", f"{peak_val:.2f} °C")
            pc2.metric("Instante del pico", f"{peak_t:.1f} s")
            pc3.metric("Desviación máx. del SP", f"+{peak_val - Tsp:.2f} °C")
            pc4.metric("Recuperación (±2 %)", f"≈ {t_recovery:.0f} s")

    st.markdown("---")
    st.caption(
        "💡 Clic derecho sobre cualquier gráfico → *Guardar imagen como…* "
        "para exportar en alta resolución."
    )


# ─────────────────────────────────────────────────────────────
# TAB 2: IDENTIFICACIÓN DEL SISTEMA
# ─────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Identificación y Estructura del Sistema de Control")

    col_p1, col_p2 = st.columns([1, 1])

    with col_p1:
        st.markdown("#### Modelo de la Planta")
        st.latex(
            r"G_p(s) = \frac{K \cdot e^{-\theta s}}{\tau s + 1} = "
            r"\frac{" + f"{K_p}" + r" \cdot e^{-" + f"{theta}" + r"\,s}}{"
            + f"{tau}" + r"\,s + 1}"
        )

        st.markdown("**Parámetros identificados:**")
        st.markdown(
            f"| Parámetro | Símbolo | Valor | Unidad |\n"
            f"|---|---|---|---|\n"
            f"| Ganancia estática | K | **{K_p}** | °C/% |\n"
            f"| Constante de tiempo | τ | **{tau}** | s |\n"
            f"| Tiempo muerto | θ | **{theta}** | s |"
        )
        st.caption("*Fuente: Liu et al. (2026), DOI: 10.3390/buildings16091752*")

        st.markdown("#### Aproximación de Padé (Orden 2)")
        st.latex(
            r"e^{-\theta s} \approx "
            r"\frac{\theta^2 s^2 - 6\theta s + 12}"
            r"{\theta^2 s^2 + 6\theta s + 12}"
        )

        st.markdown("#### Controlador PID — Ley de Control")
        st.latex(r"G_c(s) = K_p + \frac{K_i}{s} + K_d \cdot s")
        st.markdown(
            f"| Parámetro | Físico (%/V) | Software (%/°C) |\n"
            f"|---|---|---|\n"
            f"| Kp | **{Kp}** | {Kp * H:.2f} |\n"
            f"| Ki | **{Ki}** | {Ki * H:.3f} |\n"
            f"| Kd | **{Kd}** | {Kd * H:.2f} |"
        )

    with col_p2:
        st.markdown("#### Respuesta al Escalón — Lazo Abierto")
        t_ol = np.linspace(0, 250, 1000)
        _, y_ol = ct.step_response(gp, t_ol)

        fig_ol, ax_ol = plt.subplots(figsize=(7, 5))
        ax_ol.plot(t_ol, y_ol, color="#1f77b4", linewidth=2.5,
                   label="Salida y_OL(t) para escalón u = 1 %")
        ax_ol.axhline(K_p, color="red", linestyle="--", alpha=0.7, label=f"K = {K_p} °C/%")
        ax_ol.axhline(0.632 * K_p, color="gray", linestyle=":", alpha=0.5,
                      label=f"63.2 % K = {0.632 * K_p:.3f}")
        ax_ol.axvline(theta, color="orange", linestyle=":", alpha=0.7, label=f"θ = {theta} s")
        ax_ol.axvline(theta + tau, color="green", linestyle=":", alpha=0.7,
                      label=f"θ + τ = {theta + tau} s")
        ax_ol.set_xlabel("Tiempo [s]")
        ax_ol.set_ylabel("ΔTemperatura [°C]")
        ax_ol.set_title("Respuesta al Escalón Unitario — Planta en Lazo Abierto", fontweight="bold")
        ax_ol.legend(fontsize=8, loc="lower right")
        ax_ol.grid(True, linestyle="--", alpha=0.4)
        plt.tight_layout()
        st.pyplot(fig_ol)
        plt.close(fig_ol)

    # Variables del sistema
    st.markdown("---")
    st.markdown("#### Variables, Unidades y Rangos")
    vc1, vc2 = st.columns(2)
    with vc1:
        st.markdown(
            "| Variable | Símbolo | Unidad | Rango |\n"
            "|---|---|---|---|\n"
            "| Controlada (salida) | y(t) | °C | 15–30 |\n"
            "| Referencia (setpoint) | r(t) | °C | 18–27 (ASHRAE) |\n"
            "| Manipulada (actuador) | u(t) | % | 0–100 |\n"
            "| Perturbación | d(t) | °C | — |"
        )
    with vc2:
        st.markdown(
            "| Señal | Expresión | Rango |\n"
            "|---|---|---|\n"
            f"| Tensión sensor | V_sensor = H·T = {H}·T | 0–10 V |\n"
            f"| Tensión setpoint | V_sp = Hr·T_sp = {Hr}·T_sp | 0–10 V |\n"
            f"| Error en tensión | E_v = V_sp − V_sensor | ± V |\n"
            f"| Realimentación | H(s) = {H} V/°C | — |"
        )

    # Funciones de transferencia
    st.markdown("---")
    st.markdown("#### Funciones de Transferencia")
    tf1, tf2 = st.columns(2)
    with tf1:
        st.markdown("**Trayectoria directa** (con corrección de signo)")
        st.latex(r"G_d(s) = -G_c(s) \cdot G_p(s)")

        st.markdown("**Lazo abierto**")
        st.latex(r"G_{ol}(s) = G_d(s) \cdot H(s) = -G_c(s) \cdot G_p(s) \cdot H(s)")

        st.markdown("**Seguimiento en lazo cerrado**")
        st.latex(
            r"T(s) = \frac{Y(s)}{R(s)} = "
            r"\frac{-0.2\, G_c(s)\, G_p(s)}{1 - 0.2\, G_c(s)\, G_p(s)}"
        )

    with tf2:
        st.markdown("**Rechazo de perturbaciones**")
        st.latex(
            r"T_d(s) = \frac{Y(s)}{D(s)} = "
            r"\frac{-G_p(s)}{1 - G_c(s) \cdot G_p(s) \cdot H(s)}"
        )

        st.markdown("**Error en estado estable** (T. del Valor Final)")
        st.latex(r"e_{ss} = 0")
        st.caption(
            "La acción integral ($K_i/s$) en $G_c(s)$ garantiza "
            "$G_{ol}(0) \\to \\infty$, eliminando el error estacionario."
        )

        st.markdown("**Corrección de signo**")
        st.caption(
            "La planta tiene K < 0 (ganancia inversa). El signo negativo en "
            "$G_d(s) = -G_c \\cdot G_p$ restaura la realimentación negativa "
            "y garantiza $G_{ol}(0) > 0$."
        )


# ─────────────────────────────────────────────────────────────
# TAB 3: SIMULACIÓN EN TIEMPO REAL
# ─────────────────────────────────────────────────────────────
with tab3:
    st.subheader("⏱️ Simulación Dinámica Segundo a Segundo")
    st.markdown(
        "Simulación discreta del lazo cerrado PID en tiempo real. "
        "Iniciá la simulación y usá los controles para interactuar "
        "(cambiar setpoint o inyectar perturbaciones) y observar la respuesta."
    )

    # Inicializar estado en session_state para que la UI no se bloquee
    if "rt_running" not in st.session_state:
        st.session_state.rt_running = False
    if "rt_step" not in st.session_state:
        st.session_state.rt_step = 1
    if "rt_state" not in st.session_state:
        st.session_state.rt_state = {
            "y_dev": 0.0, "integral_e": 0.0, "prev_ev": Hr * float(Tsp) - H * T0,
            "u_buf": [0.0] * max(1, int(round(theta / 1.0)) + 1),
            "dist_buf": [0.0] * max(1, int(round(theta / 1.0)) + 1),
            "hist_t": [0.0], "hist_T": [T0], "hist_sp": [float(Tsp)], "hist_u": [0.0], 
            "hist_e": [float(Tsp) - T0], "hist_vsensor": [H * T0], "hist_ev": [Hr * float(Tsp) - H * T0], "hist_dist": [0.0],
            "dist_val": 0.0
        }

    cr1, cr2, cr3, cr4 = st.columns(4)
    with cr1:
        if st.button("▶️ Iniciar / ⏸️ Pausar", type="primary"):
            st.session_state.rt_running = not st.session_state.rt_running
            st.rerun()
        if st.button("🔄 Reiniciar"):
            st.session_state.rt_running = False
            st.session_state.rt_step = 1
            if "rt_dist_slider" in st.session_state:
                st.session_state.rt_dist_slider = 0.0
            st.session_state.rt_state = {
                "y_dev": 0.0, "integral_e": 0.0, "prev_ev": Hr * float(Tsp) - H * T0,
                "u_buf": [0.0] * max(1, int(round(theta / 1.0)) + 1),
                "dist_buf": [0.0] * max(1, int(round(theta / 1.0)) + 1),
                "hist_t": [0.0], "hist_T": [T0], "hist_sp": [float(Tsp)], "hist_u": [0.0], 
                "hist_e": [float(Tsp) - T0], "hist_vsensor": [H * T0], "hist_ev": [Hr * float(Tsp) - H * T0], "hist_dist": [0.0],
                "dist_val": 0.0
            }
            st.rerun()
    with cr2:
        rt_sp = st.slider("Setpoint dinámico [°C]", 18.0, 27.0, float(Tsp), 0.5, key="rt_sp_slider")
    with cr3:
        def clear_dist():
            st.session_state.rt_dist_slider = 0.0
            st.session_state.rt_state["dist_val"] = 0.0

        rt_dist = st.slider("Perturbación DoS [°C]", 0.0, 10.0, 0.0, 0.5, key="rt_dist_slider")
        st.session_state.rt_state["dist_val"] = rt_dist
        st.button("✅ Quitar Perturbación", on_click=clear_dist)
    with cr4:
        rt_speed = st.slider("Intervalo de refresco [ms]", 50, 500, 100, 50, key="rt_speed_slider")
        steps_per_frame = st.slider("Pasos por cuadro (Velocidad)", 1, 10, 4, 1, key="rt_steps_slider")

    state = st.session_state.rt_state
    # Parche de seguridad para sesiones existentes
    if "dist_buf" not in state:
        state["dist_buf"] = [0.0] * max(1, int(round(theta / 1.0)) + 1)
    if "hist_dist" not in state:
        state["hist_dist"] = [0.0] * len(state["hist_t"])
    dt = 1.0

    # Ejecutar pasos de simulación si está corriendo
    if st.session_state.rt_running:
        for _ in range(steps_per_frame):
            k = st.session_state.rt_step
            t_k = k * dt

            # La perturbación ingresa en el buffer para simular el retardo de transporte
            state["dist_buf"].append(state["dist_val"])
            dist_delayed = state["dist_buf"].pop(0)

            # La temperatura medida T_k evoluciona a través de la inercia del sistema
            T_k = T0 + state["y_dev"]

            e_k = rt_sp - T_k
            v_sens = H * T_k
            v_sp_rt = Hr * rt_sp
            e_v = v_sp_rt - v_sens

            state["integral_e"] += e_v * dt
            state["integral_e"] = float(np.clip(state["integral_e"], -200, 200))
            deriv = (e_v - state["prev_ev"]) / dt if k > 0 else 0.0
            state["prev_ev"] = e_v

            u_k = -(Kp * e_v + Ki * state["integral_e"] + Kd * deriv)
            u_k = float(np.clip(u_k, 0, 100))

            state["u_buf"].append(u_k)
            u_delayed = state["u_buf"].pop(0)

            # Ecuación diferencial con perturbación y control sumados antes de la inercia:
            # τ · dy/dt + y = K_p · u(t - θ) + d(t - θ)
            dy = (K_p * u_delayed + dist_delayed - state["y_dev"]) / tau
            state["y_dev"] += dy * dt

            state["hist_t"].append(t_k)
            state["hist_T"].append(T_k)
            state["hist_sp"].append(rt_sp)
            state["hist_u"].append(u_k)
            state["hist_e"].append(e_k)
            state["hist_vsensor"].append(v_sens)
            state["hist_ev"].append(e_v)
            state["hist_dist"].append(state["dist_val"])

            st.session_state.rt_step += 1

            # Límite de historia para mantener rendimiento
            if len(state["hist_t"]) > 300:
                for key in ["hist_t", "hist_T", "hist_sp", "hist_u", "hist_e", "hist_vsensor", "hist_ev", "hist_dist"]:
                    state[key].pop(0)

    # Renderizar UI con el estado actual
    ph_metrics = st.empty()
    ph_chart = st.empty()

    if len(state["hist_t"]) > 0:
        with ph_metrics.container():
            rm1, rm2, rm3, rm4, rm5 = st.columns(5)
            rm1.metric("🌡️ Sensor Pt100", f"{state['hist_T'][-1]:.2f} °C")
            rm2.metric("📏 Error", f"{state['hist_e'][-1]:.2f} °C")
            rm3.metric("⚡ V_sensor", f"{state['hist_vsensor'][-1]:.2f} V")
            rm4.metric("🔧 Actuador CRAC", f"{state['hist_u'][-1]:.1f} %")
            rm5.metric("⏰ Tiempo", f"{state['hist_t'][-1]:.0f} s")

        import pandas as pd
        df = pd.DataFrame({
            "Temperatura": state["hist_T"],
            "Setpoint": state["hist_sp"],
            "V_sensor": state["hist_vsensor"],
            "E_v": state["hist_ev"],
            "Apertura CRAC": state["hist_u"]
        }, index=state["hist_t"])

        with ph_chart.container():
            st.markdown("#### 🌡️ Temperatura de Salida y Setpoint [°C]")
            st.line_chart(df[["Temperatura", "Setpoint"]], height=240)
            
            st.markdown("#### ⚡ Señales Eléctricas de Entrada/Sensor [V]")
            st.line_chart(df[["V_sensor", "E_v"]], height=160)
            
            st.markdown("#### 🔧 Esfuerzo de Control (Apertura de Válvula CRAC) [%]")
            st.line_chart(df[["Apertura CRAC"]], height=160)

    # Volver a correr el script si la simulación está activa
    if st.session_state.rt_running:
        time.sleep(rt_speed / 1000.0)
        st.rerun()


# ═══════════════════════════════════════════════════════════════
# PIE DE PÁGINA
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.caption(
    "TFI — Teoría de Control K-4011 · UTN Facultad Regional Buenos Aires "
    "· Matias Ezequiel Pormi · Julio 2026"
)
