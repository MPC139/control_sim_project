#!/usr/bin/env python3
"""
Simulador de Control Térmico — Data Center
Interfaz de escritorio con PyQt6 + pyqtgraph
TFI Teoría de Control K-4011 · UTN FRBA
"""

import sys
import numpy as np
from collections import deque

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QSlider, QDoubleSpinBox, QPushButton, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

import pyqtgraph as pg

# ═════════════════════════════════════════════════════════════════════════════
# PARÁMETROS DEL SISTEMA
# ═════════════════════════════════════════════════════════════════════════════
K_PLANTA  = -0.25
TAU       = 35.0
THETA     = 4.5
H_SENSOR  = 0.2
HR        = 0.2

# ═════════════════════════════════════════════════════════════════════════════
# VENTANA PRINCIPAL
# ═════════════════════════════════════════════════════════════════════════════
class Simulador(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador de Control Térmico — Data Center")
        self.setMinimumSize(1200, 750)

        # ── Estado de simulación ───────────────────────────────────────
        self.running = False
        self.t = 0.0
        self.dt = 0.1          # paso de integración [s]
        self.speed = 5          # pasos por tick del timer

        # Estado del sistema
        self.y_dev = 0.0
        self.integral = 0.0
        self.prev_ev = 0.0

        # Buffers de retardo (theta = 4.5 s → 45 muestras con dt=0.1)
        buf_len = max(1, int(THETA / self.dt) + 1)
        self.u_buf = deque([0.0] * buf_len, maxlen=buf_len)
        self.dist_buf = deque([0.0] * buf_len, maxlen=buf_len)

        # Parámetros
        self.Kp = 12.5
        self.Ki = 0.4
        self.Kd = 2.5
        self.T0 = 28.0
        self.Tsp = 22.0
        self.t_sim = 600.0     # tiempo total de simulación [s]
        self.dist_val = 0.0    # magnitud DoS actual

        # ── Métricas de QoS térmica ────────────────────────────────────
        self.error_area      = 0.0   # integral de e(t) > 0 [°C·s]
        self.time_above_27   = 0.0   # tiempo sobre 27 °C (ASHRAE max) [s]
        self.time_above_32   = 0.0   # tiempo sobre 32 °C (absoluto) [s]
        self.time_saturated  = 0.0   # tiempo con actuador al 100 % [s]
        self.dos_injected    = False # si ya se inyectó DoS
        self.time_saturated_continuous = 0.0 # tiempo de saturación continua [s]

        # Buffers de historial
        self._init_buffers()

        # ── Construir UI ────────────────────────────────────────────────
        self._build_ui()

        # ── Timer de simulación ─────────────────────────────────────────
        self.timer = QTimer()
        self.timer.timeout.connect(self._step)

        # ── Color de fondo ──────────────────────────────────────────────
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; }
            QGroupBox {
                color: #cdd6f4; font-weight: bold; border: 1px solid #45475a;
                border-radius: 6px; margin-top: 10px; padding-top: 8px;
                background-color: #181825;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 10px; padding: 0 5px;
            }
            QLabel { color: #cdd6f4; font-size: 13px; }
            QPushButton {
                background-color: #89b4fa; color: #1e1e2e; font-weight: bold;
                border-radius: 6px; padding: 6px 14px; font-size: 13px;
            }
            QPushButton:hover { background-color: #b4d0fb; }
            QDoubleSpinBox {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 4px; padding: 3px;
            }
        """)

    def _init_buffers(self):
        self.max_pts = int(self.t_sim / self.dt) + 10
        self.hist_t  = deque(maxlen=self.max_pts)
        self.hist_T  = deque(maxlen=self.max_pts)
        self.hist_sp = deque(maxlen=self.max_pts)
        self.hist_u  = deque(maxlen=self.max_pts)
        self.hist_e  = deque(maxlen=self.max_pts)
        self.hist_vs = deque(maxlen=self.max_pts)

    # ═════════════════════════════════════════════════════════════════════
    # CONSTRUCCIÓN DE LA UI
    # ═════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # ── Panel izquierdo: controles ──────────────────────────────────
        left = QWidget()
        left.setFixedWidth(280)
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(6)

        # -- PID --
        gb_pid = QGroupBox("Controlador PID")
        gb_pid.setFont(QFont("", 11))
        g_pid = QGridLayout(gb_pid)
        g_pid.setSpacing(4)

        self.spin_Kp = self._add_spin(g_pid, 0, "Kp [%/V]", 0, 50, 12.5, 0.5)
        self.spin_Ki = self._add_spin(g_pid, 1, "Ki [%/(V·s)]", 0, 5, 0.4, 0.05)
        self.spin_Kd = self._add_spin(g_pid, 2, "Kd [%·s/V]", 0, 20, 2.5, 0.5)

        def on_pid():
            self.Kp = self.spin_Kp.value()
            self.Ki = self.spin_Ki.value()
            self.Kd = self.spin_Kd.value()
            self._restart()
        self.spin_Kp.valueChanged.connect(on_pid)
        self.spin_Ki.valueChanged.connect(on_pid)
        self.spin_Kd.valueChanged.connect(on_pid)
        left_layout.addWidget(gb_pid)

        # -- Escenario --
        gb_env = QGroupBox("Escenario")
        gb_env.setFont(QFont("", 11))
        g_env = QGridLayout(gb_env)
        g_env.setSpacing(4)

        self.spin_T0 = self._add_spin(g_env, 0, "T₀ [°C]", 15, 35, 28.0, 0.5)
        self.spin_sp = self._add_spin(g_env, 1, "Setpoint [°C]", 18, 27, 22.0, 0.5)
        self.spin_T0.valueChanged.connect(lambda: self._restart())
        self.spin_sp.valueChanged.connect(lambda: self._restart())
        left_layout.addWidget(gb_env)

        # -- Perturbación --
        gb_dist = QGroupBox("Ataque DoS")
        gb_dist.setFont(QFont("", 11))
        g_dist = QGridLayout(gb_dist)
        g_dist.setSpacing(4)

        self.spin_dos = self._add_spin(g_dist, 0, "Magnitud [°C]", 0, 100, 0, 0.5)
        btn_inject = QPushButton("Inyectar DoS")
        btn_inject.clicked.connect(self._inject_dos)
        g_dist.addWidget(btn_inject, 1, 0, 1, 2)

        btn_clear = QPushButton("Quitar DoS")
        btn_clear.clicked.connect(self._clear_dos)
        g_dist.addWidget(btn_clear, 2, 0, 1, 2)
        left_layout.addWidget(gb_dist)

        # -- Control de simulación --
        gb_ctrl = QGroupBox("Control")
        gb_ctrl.setFont(QFont("", 11))
        g_ctrl = QGridLayout(gb_ctrl)

        self.btn_run = QPushButton("▶ Iniciar")
        self.btn_run.clicked.connect(self._toggle_run)
        g_ctrl.addWidget(self.btn_run, 0, 0, 1, 2)

        btn_reset = QPushButton("↺ Reiniciar")
        btn_reset.clicked.connect(self._restart)
        g_ctrl.addWidget(btn_reset, 1, 0)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 20)
        self.speed_slider.setValue(5)
        self.speed_slider.valueChanged.connect(lambda v: setattr(self, 'speed', v))
        g_ctrl.addWidget(QLabel("Velocidad"), 2, 0)
        g_ctrl.addWidget(self.speed_slider, 2, 1)

        self.spin_tsim = QDoubleSpinBox()
        self.spin_tsim.setRange(60, 2000)
        self.spin_tsim.setSingleStep(60)
        self.spin_tsim.setValue(600)
        self.spin_tsim.setDecimals(0)
        self.spin_tsim.valueChanged.connect(lambda v: setattr(self, 't_sim', v))
        g_ctrl.addWidget(QLabel("t_sim [s]"), 3, 0)
        g_ctrl.addWidget(self.spin_tsim, 3, 1)
        left_layout.addWidget(gb_ctrl)

        # -- Indicador de falla --
        gb_status = QGroupBox("Estado del Sistema")
        gb_status.setFont(QFont("", 11))
        g_status = QGridLayout(gb_status)
        g_status.setSpacing(2)

        self.lbl_status = QLabel("● OPERACIÓN NORMAL")
        self.lbl_status.setStyleSheet(
            "QLabel { color: #a6e3a1; font-weight: bold; font-size: 14px; "
            "border: 2px solid #a6e3a1; border-radius: 8px; "
            "padding: 8px; background-color: rgba(166,227,161,0.08); }"
        )
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        g_status.addWidget(self.lbl_status, 0, 0, 1, 2)

        self.lbl_limit = QLabel("Límite: — °C")
        g_status.addWidget(self.lbl_limit, 1, 0)
        g_status.addWidget(QLabel(""), 1, 1)
        left_layout.addWidget(gb_status)

        # -- Métricas --
        gb_met = QGroupBox("Métricas (último valor)")
        gb_met.setFont(QFont("", 11))
        g_met = QGridLayout(gb_met)
        g_met.setSpacing(4)
        self.lbl_T = QLabel("🌡 T_out = — °C"); g_met.addWidget(self.lbl_T, 0, 0)
        self.lbl_E = QLabel("📏 Error = — °C"); g_met.addWidget(self.lbl_E, 1, 0)
        self.lbl_U = QLabel("🔧 CRAC = — %");  g_met.addWidget(self.lbl_U, 2, 0)
        self.lbl_t = QLabel("⏰ t = — s");              g_met.addWidget(self.lbl_t, 3, 0)
        left_layout.addWidget(gb_met)

        # -- QoS Térmica (visible solo tras DoS) --
        gb_qos = QGroupBox("QoS Térmica (tras inyección DoS)")
        gb_qos.setFont(QFont("", 11))
        g_qos = QGridLayout(gb_qos)
        g_qos.setSpacing(4)
        self.lbl_area = QLabel("∫ error = — °C·s")
        g_qos.addWidget(self.lbl_area, 0, 0)
        self.lbl_t27 = QLabel("t > 27 °C  = — s")
        g_qos.addWidget(self.lbl_t27, 1, 0)
        self.lbl_t32 = QLabel("t > 32 °C  = — s")
        g_qos.addWidget(self.lbl_t32, 2, 0)
        self.lbl_sat = QLabel("Saturación = — s")
        g_qos.addWidget(self.lbl_sat, 3, 0)
        left_layout.addWidget(gb_qos)

        left_layout.addStretch()

        # ── Panel derecho: gráficos pyqtgraph ───────────────────────────
        self._build_plots()
        right = self.plot_widget
        root.addWidget(left, 0)
        root.addWidget(right, 1)

    def _add_spin(self, grid, row, label, vmin, vmax, val, step):
        lbl = QLabel(label)
        box = QDoubleSpinBox()
        box.setRange(vmin, vmax)
        box.setSingleStep(step)
        box.setValue(val)
        box.setDecimals(2)
        grid.addWidget(lbl, row, 0)
        grid.addWidget(box, row, 1)
        return box

    # ═════════════════════════════════════════════════════════════════════
    # GRÁFICOS (pyqtgraph)
    # ═════════════════════════════════════════════════════════════════════
    def _build_plots(self):
        pw = pg.GraphicsLayoutWidget()
        pw.setBackground("#1e1e2e")

        # Colores Catppuccin Mocha
        C_TEMP  = (137, 180, 250)   # blue
        C_SP    = (243, 139, 168)   # red
        C_VS    = (250, 179, 135)   # peach
        C_EV    = (148, 226, 213)   # teal
        C_U     = (203, 166, 247)   # mauve
        C_GRID  = (69, 71, 90)      # surface1
        C_LABEL = (205, 214, 244)   # text

        def _style(axis):
            axis.setPen(pg.mkPen(color=C_LABEL, width=1))
            axis.setTextPen(pg.mkPen(color=C_LABEL))

        # ── 1. Temperatura ──────────────────────────────────────────────
        p1 = pw.addPlot(row=0, col=0, title="Temperatura de Salida")
        p1.setLabel("left", "°C")
        p1.showGrid(x=True, y=True, alpha=0.3)
        _style(p1.getAxis("left"))
        _style(p1.getAxis("bottom"))
        p1.setTitle("Temperatura de Salida", color=C_LABEL, size="12pt")

        self.curve_T  = p1.plot(pen=pg.mkPen(color=C_TEMP, width=2.5), name="T_out(t)  [°C]")
        self.curve_sp = p1.plot(pen=pg.mkPen(color=C_SP, width=2, style=Qt.PenStyle.DashLine), name="Setpoint  [°C]")
        p1.addLegend(offset=(5, 5), labelTextColor=C_LABEL)

        # ── 2. Señales de Tensión ───────────────────────────────────────
        p2 = pw.addPlot(row=1, col=0, title="Señales de Tensión")
        p2.setLabel("left", "V")
        p2.showGrid(x=True, y=True, alpha=0.3)
        _style(p2.getAxis("left"))
        _style(p2.getAxis("bottom"))
        p2.setTitle("Señales de Tensión", color=C_LABEL, size="12pt")

        self.curve_vs = p2.plot(pen=pg.mkPen(color=C_VS, width=2.2), name="V_sensor(t) = H·T_out  [V]")
        self.curve_ev = p2.plot(pen=pg.mkPen(color=C_EV, width=1.6, style=Qt.PenStyle.DashDotLine), name="E_v(t) = V_sp − V_sensor  [V]")
        p2.addLegend(offset=(5, 5), labelTextColor=C_LABEL)

        # ── 3. Señal de Control ─────────────────────────────────────────
        p3 = pw.addPlot(row=2, col=0, title="Esfuerzo de Control")
        p3.setLabel("left", "%")
        p3.setLabel("bottom", "Tiempo [s]")
        p3.showGrid(x=True, y=True, alpha=0.3)
        _style(p3.getAxis("left"))
        _style(p3.getAxis("bottom"))
        p3.setTitle("Esfuerzo de Control — Apertura CRAC", color=C_LABEL, size="12pt")
        p3.setYRange(-5, 105)

        curve_u_fill = p3.plot(pen=pg.mkPen(color=C_U, width=0), fillLevel=0,
                                brush=(203, 166, 247, 40), name="")
        self.curve_u = p3.plot(pen=pg.mkPen(color=C_U, width=2.2), name="u(t) — Apertura CRAC  [%]")

        self.plot_widget = pw

    # ═════════════════════════════════════════════════════════════════════
    # BOTONES
    # ═════════════════════════════════════════════════════════════════════
    def _toggle_run(self):
        self.running = not self.running
        if self.running:
            self.T0 = self.spin_T0.value()
            self.Tsp = self.spin_sp.value()
            if self.t == 0.0:
                pass  # ya inicializado en _restart si t==0
            self.btn_run.setText("⏸ Pausar")
            self.timer.start(20)  # ~50 Hz
        else:
            self.btn_run.setText("▶ Iniciar")
            self.timer.stop()

    def _restart(self):
        self.running = False
        self.timer.stop()
        self.t = 0.0
        self.y_dev = 0.0
        self.integral = 0.0
        self.prev_ev = 0.0
        buf_len = max(1, int(THETA / self.dt) + 1)
        self.u_buf = deque([0.0] * buf_len, maxlen=buf_len)
        self.dist_buf = deque([0.0] * buf_len, maxlen=buf_len)
        self.dist_val = 0.0
        self.spin_dos.setValue(0.0)
        self.dos_injected = False

        # Reset métricas QoS
        self.error_area     = 0.0
        self.time_above_27  = 0.0
        self.time_above_32  = 0.0
        self.time_saturated = 0.0
        self.time_saturated_continuous = 0.0

        self.T0 = self.spin_T0.value()
        self.Tsp = self.spin_sp.value()

        self._init_buffers()
        self._update_metrics(reset=True)
        self._update_plots()
        self.btn_run.setText("▶ Iniciar")

    def _inject_dos(self):
        self.dist_val = self.spin_dos.value()
        self.dos_injected = True

    def _clear_dos(self):
        self.dist_val = 0.0
        self.spin_dos.setValue(0.0)
        self.dos_injected = False

    # ═════════════════════════════════════════════════════════════════════
    # PASO DE SIMULACIÓN (Euler)
    # ═════════════════════════════════════════════════════════════════════
    def _step(self):
        if not self.running:
            return

        for _ in range(self.speed):
            # -- Perturbación con retardo --
            self.dist_buf.append(self.dist_val)
            dist_delayed = self.dist_buf[0]

            # -- Temperatura actual --
            T_k = self.T0 + self.y_dev

            # -- Error en voltaje --
            v_sens = H_SENSOR * T_k
            v_sp   = HR * self.Tsp
            e_v    = v_sp - v_sens
            e_C    = self.Tsp - T_k  # error en °C

            # -- Métricas de QoS térmica --
            if self.dos_injected and T_k > self.Tsp:
                self.error_area += (T_k - self.Tsp) * self.dt
            if self.dos_injected and T_k > 27:
                self.time_above_27 += self.dt
            if self.dos_injected and T_k > 32:
                self.time_above_32 += self.dt

            # -- PID --
            self.integral += e_v * self.dt
            self.integral = float(np.clip(self.integral, -500, 500))
            deriv = (e_v - self.prev_ev) / self.dt if self.t > 0 else 0.0
            self.prev_ev = e_v

            u_k = -(self.Kp * e_v + self.Ki * self.integral + self.Kd * deriv)
            u_k = float(np.clip(u_k, 0, 100))

            if u_k >= 99.9:
                self.time_saturated_continuous += self.dt
                if self.dos_injected:
                    self.time_saturated += self.dt
            else:
                self.time_saturated_continuous = 0.0

            # -- Retardo de control --
            self.u_buf.append(u_k)
            u_delayed = self.u_buf[0]

            # -- Ecuación del proceso: τ · dy/dt + y = K · u(t-θ) --
            dy = (K_PLANTA * u_delayed + dist_delayed - self.y_dev) / TAU
            self.y_dev += dy * self.dt
            self.t += self.dt

        # -- Registrar --
        self.hist_t.append(self.t)
        self.hist_T.append(T_k)
        self.hist_sp.append(self.Tsp)
        self.hist_u.append(u_k)
        self.hist_e.append(e_C)
        self.hist_vs.append(v_sens)

        self._update_metrics()
        self._update_plots()

        if self.t >= self.t_sim:
            self.timer.stop()
            self.running = False
            self.btn_run.setText("▶ Iniciar")

    # ═════════════════════════════════════════════════════════════════════
    # ACTUALIZACIÓN DE UI
    # ═════════════════════════════════════════════════════════════════════
    def _update_metrics(self, reset=False):
        if reset or len(self.hist_T) == 0:
            self.lbl_T.setText("🌡 T_out = — °C")
            self.lbl_E.setText("📏 Error = — °C")
            self.lbl_U.setText("🔧 CRAC = — %")
            self.lbl_t.setText("⏰ t = — s")
            self.lbl_limit.setText("Límite: — °C")
            self.lbl_status.setText("● OPERACIÓN NORMAL")
            self.lbl_area.setText("∫ error = — °C·s")
            self.lbl_t27.setText("t > 27 °C = — s")
            self.lbl_t32.setText("t > 32 °C = — s")
            self.lbl_sat.setText("Saturación = — s")
        else:
            self.lbl_T.setText(f"🌡 T_out = {self.hist_T[-1]:.2f} °C")
            self.lbl_E.setText(f"📏 Error = {self.hist_e[-1]:.2f} °C")
            self.lbl_U.setText(f"🔧 CRAC = {self.hist_u[-1]:.1f} %")
            self.lbl_t.setText(f"⏰ t = {self.hist_t[-1]:.0f} s")
            self.lbl_area.setText(f"∫ error = {self.error_area:.1f} °C·s")
            self.lbl_t27.setText(f"t > 27 °C = {self.time_above_27:.1f} s")
            self.lbl_t32.setText(f"t > 32 °C = {self.time_above_32:.1f} s")
            self.lbl_sat.setText(f"Saturación = {self.time_saturated:.1f} s")

        # Indicador de estado
        self._update_status()

    def _update_status(self):
        T_k = self.hist_T[-1] if len(self.hist_T) > 0 else self.T0

        # Límite de perturbación teórica en régimen permanente
        d_limit = 25.0 - (self.T0 - self.Tsp)
        self.lbl_limit.setText(f"Límite Teórico: D ≤ {d_limit:.1f} °C")

        green  = "QLabel { color: #a6e3a1; font-weight: bold; font-size: 13px; border: 2px solid #a6e3a1; border-radius: 8px; padding: 8px; background-color: rgba(166,227,161,0.08); }"
        yellow = "QLabel { color: #f9e2af; font-weight: bold; font-size: 13px; border: 2px solid #f9e2af; border-radius: 8px; padding: 8px; background-color: rgba(249,226,175,0.08); }"
        red    = "QLabel { color: #f38ba8; font-weight: bold; font-size: 13px; border: 2px solid #f38ba8; border-radius: 8px; padding: 8px; background-color: rgba(243,139,168,0.1); }"

        # Clasificación de fallas y advertencias dinámicas basadas en variables de estado
        if T_k > 32.0:
            self.lbl_status.setText(f"● FALLA: TEMP. CRÍTICA ({T_k:.1f} °C)")
            self.lbl_status.setStyleSheet(red)
        elif self.time_saturated_continuous >= 30.0 and T_k > 27.0:
            self.lbl_status.setText(f"● FALLA: CAPACIDAD EXCEDIDA ({self.time_saturated_continuous:.0f}s)")
            self.lbl_status.setStyleSheet(red)
        elif T_k > 27.0:
            self.lbl_status.setText(f"⚠ DEGRADACIÓN: T > 27 °C ({T_k:.1f} °C)")
            self.lbl_status.setStyleSheet(yellow)
        elif self.time_saturated_continuous > 0.0:
            self.lbl_status.setText(f"⚠ CRAC SATURADO - SIN RESERVA ({self.time_saturated_continuous:.1f}s)")
            self.lbl_status.setStyleSheet(yellow)
        else:
            self.lbl_status.setText("● OPERACIÓN NORMAL (SEGURO)")
            self.lbl_status.setStyleSheet(green)

    def _update_plots(self):
        if len(self.hist_t) < 2:
            return
        tt = list(self.hist_t)
        self.curve_T.setData(tt, list(self.hist_T))
        self.curve_sp.setData(tt, list(self.hist_sp))
        self.curve_vs.setData(tt, list(self.hist_vs))
        ev = [HR * self.Tsp - v for v in self.hist_vs]
        self.curve_ev.setData(tt, ev)
        self.curve_u.setData(tt, list(self.hist_u))


# ═════════════════════════════════════════════════════════════════════════════
# EJECUCIÓN
# ═════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = Simulador()
    win.show()
    sys.exit(app.exec())
