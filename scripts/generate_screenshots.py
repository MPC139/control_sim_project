#!/usr/bin/env python3
import os
import sys
import numpy as np

# Run in offscreen mode to avoid launching a physical window
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Agregar src/ al PYTHONPATH para poder importar app_escritorio
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
sys.path.insert(0, os.path.join(project_dir, "src"))

from PyQt6.QtWidgets import QApplication
from app_escritorio import Simulador

def run_simulation(sim, target_t):
    # Set speed to 5 so each step simulates 5 * 0.05 = 0.25 seconds of process time
    sim.speed = 5
    sim.running = True
    while sim.t < target_t:
        sim._step()
    sim.running = False

def create_screenshots():
    # Initialize the Qt Application
    app = QApplication(sys.argv)
    
    # -------------------------------------------------------------------------
    # Caso 1: Perturbación en el Límite de Capacidad (D = 19 °C)
    # -------------------------------------------------------------------------
    print("Simulando Caso 1...")
    sim1 = Simulador()
    sim1.spin_Kp.setValue(12.50)
    sim1.spin_Ki.setValue(0.40)
    sim1.spin_Kd.setValue(2.50)
    sim1.spin_T0.setValue(28.00)
    sim1.spin_sp.setValue(22.00)
    sim1.spin_tsim.setValue(650.0)
    sim1._restart()
    
    # Simular hasta t = 220s sin DoS
    run_simulation(sim1, 220.0)
    # Inyectar DoS de 19.00 °C
    sim1.spin_dos.setValue(19.00)
    sim1._inject_dos()
    # Simular hasta t = 645s
    run_simulation(sim1, 645.0)
    
    # Mostrar y capturar
    sim1.resize(1300, 950)
    sim1.show()
    for _ in range(15):
        QApplication.processEvents()
    sim1.grab().save(os.path.join(project_dir, "report/figures/sim_falla_capacidad.png"))
    sim1.close()
    
    # -------------------------------------------------------------------------
    # Caso 2: Falla por Capacidad Excedida y Falla Térmica Crítica (D = 29.50 °C)
    # -------------------------------------------------------------------------
    print("Simulando Caso 2...")
    sim2 = Simulador()
    sim2.spin_Kp.setValue(12.50)
    sim2.spin_Ki.setValue(0.40)
    sim2.spin_Kd.setValue(2.50)
    sim2.spin_T0.setValue(28.00)
    sim2.spin_sp.setValue(22.00)
    sim2.spin_tsim.setValue(1500.0)
    sim2._restart()
    
    # Simular hasta t = 220s sin DoS
    run_simulation(sim2, 220.0)
    # Inyectar DoS de 29.50 °C
    sim2.spin_dos.setValue(29.50)
    sim2._inject_dos()
    # Simular hasta t = 1493s
    run_simulation(sim2, 1493.0)
    
    # Mostrar y capturar
    sim2.resize(1300, 950)
    sim2.show()
    for _ in range(15):
        QApplication.processEvents()
    sim2.grab().save(os.path.join(project_dir, "report/figures/sim_falla_critica.png"))
    sim2.close()
    
    # -------------------------------------------------------------------------
    # Caso 3: Diagnóstico de bug de anti-windup (D = 25.00 °C, clamp integral a 200)
    # -------------------------------------------------------------------------
    print("Simulando Caso 3 (con clamp integral bug a +/- 200)...")
    sim3 = Simulador()
    sim3.spin_Kp.setValue(12.50)
    sim3.spin_Ki.setValue(0.40)
    sim3.spin_Kd.setValue(2.50)
    sim3.spin_T0.setValue(28.00)
    sim3.spin_sp.setValue(22.00)
    sim3.spin_tsim.setValue(1400.0)
    sim3._restart()
    
    import app_escritorio
    
    def patched_step(self):
        if not self.running:
            return
        for _ in range(self.speed):
            # -- Perturbación con retardo --
            self.dist_buf.append(self.dist_val)
            dist_delayed = self.dist_buf[0]
            # -- Temperatura actual --
            T_k = self.T0 + self.y_dev
            # -- Error en voltaje --
            v_sens = app_escritorio.H_SENSOR * T_k
            v_sp   = app_escritorio.HR * self.Tsp
            e_v    = v_sp - v_sens
            e_C    = self.Tsp - T_k
            
            # QoS metrics
            if self.dos_injected and T_k > self.Tsp:
                self.error_area += (T_k - self.Tsp) * self.dt
            if self.dos_injected and T_k > 27:
                self.time_above_27 += self.dt
            if self.dos_injected and T_k > 32:
                self.time_above_32 += self.dt
                
            # PID (con clamp integral antiguo de +/- 200)
            self.integral += e_v * self.dt
            self.integral = float(np.clip(self.integral, -200.0, 200.0))  # BUG ANTIGUO
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
                
            # Retardo de control
            self.u_buf.append(u_k)
            u_delayed = self.u_buf[0]
            # Proceso
            dy = (app_escritorio.K_PLANTA * u_delayed + dist_delayed - self.y_dev) / app_escritorio.TAU
            self.y_dev += dy * self.dt
            self.t += self.dt
            
        self.hist_t.append(self.t)
        self.hist_T.append(T_k)
        self.hist_sp.append(self.Tsp)
        self.hist_u.append(u_k)
        self.hist_e.append(e_C)
        self.hist_vs.append(v_sens)
        
        self._update_metrics()
        self._update_plots()
        
        if self.t >= self.t_sim:
            self.running = False
            self.btn_run.setText("▶ Iniciar")
            
    # Asignar la función parcheada a la instancia de sim3
    sim3._step = patched_step.__get__(sim3, Simulador)
    
    # Simular hasta t = 60s sin DoS
    run_simulation(sim3, 60.0)
    # Inyectar DoS de 25.00 °C
    sim3.spin_dos.setValue(25.00)
    sim3._inject_dos()
    # Simular hasta t = 1386s
    run_simulation(sim3, 1386.0)
    
    # Mostrar y capturar
    sim3.resize(1300, 950)
    sim3.show()
    for _ in range(15):
        QApplication.processEvents()
    sim3.grab().save(os.path.join(project_dir, "report/figures/sim_bug_saturacion.png"))
    sim3.close()
    
    print("¡Todas las capturas de pantalla de la app actualizadas se generaron con éxito!")

if __name__ == "__main__":
    create_screenshots()
