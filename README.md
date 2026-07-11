# Sistema de Control Térmico de Lazo Cerrado para Data Center (PID)

Este proyecto consiste en el diseño, modelado, simulación y validación de un sistema de control automático en lazo cerrado para regular la temperatura del pasillo frío de un Centro de Datos (Data Center). El trabajo fue desarrollado para el Trabajo Final Integrador (TFI) de la materia **Teoría de Control (Comisión K-4011)** de la **Universidad Tecnológica Nacional (UTN - FRBA)**, correspondiente a **Julio de 2026**.

El sistema controla dinámicamente la velocidad de los ventiladores EC de una unidad de aire acondicionado de precisión (CRAC) para contrarrestar la carga térmica disipada por los servidores y rechazar perturbaciones térmicas severas como ataques de denegación de servicio (DoS) térmicos.

---

##  Cómo Ejecutar el Simulador Interactivo

El simulador interactivo está desarrollado en **Python** utilizando **Streamlit**. Permite interactuar en tiempo real con las ganancias del controlador ($K_p$, $K_i$, $K_d$), el setpoint dinámico de temperatura, la velocidad de refresco y la inyección de la perturbación DoS.

### Requisitos Previos
Tener instalado **Python 3.8+** en su sistema (Linux/macOS/Windows).

### Ejecución (Linux / macOS)
Solo debe abrir una terminal en la carpeta del proyecto y correr el script automatizado:
```bash
./run_sim.sh
```
*Este script creará automáticamente el entorno virtual (`.venv`), instalará las dependencias necesarias (`requirements.txt`) de forma silenciosa e iniciará el servidor.*

Si el navegador no se abre automáticamente, ingrese a:
**[http://localhost:8501](http://localhost:8501)**

---

##  Estructura del Proyecto

*   **`app.py`**: Código fuente de la aplicación interactiva Streamlit (simulación dinámica en tiempo real y offline).
*   **`run_sim.sh`**: Script Bash autogestionado para inicializar el entorno virtual y lanzar el simulador.
*   **`informe_final.pdf`**: Reporte académico completo formateado bajo normativas IEEE. **¡Consúltelo para leer el análisis matemático detallado!**
*   **`informe_final.tex`**: Código fuente en LaTeX del informe, incluyendo diagramas de bloques vectoriales en TikZ.
*   **`generate_plots.py`**: Script de Python para generar de forma estática los gráficos de validación del informe.
*   **Modelos de Scilab/Xcos** (Validación analítica):
    *   `abrir_xcos.sce` / `Seguimiento_al_Escalon_PID_FOPTD.zcos`: Diagrama de simulación gráfica en Xcos.
    *   `simulacion_seguimiento.sce` y `simulacion_perturbacion.sce`: Scripts de simulación matemática.
*   **`requirements.txt`**: Dependencias de Python (`streamlit`, `control`, `matplotlib`, `numpy`, `scipy`).

---

##  Parámetros del Sistema de Control

### 1. Modelo de la Planta (Pasillo Frío)
Se modela como un sistema de primer orden con tiempo muerto (FOPTD) que representa la inercia térmica del volumen de aire y el retardo de transporte:
$$G_p(s) = \frac{-0.25 \cdot e^{-4.5s}}{35s + 1}$$
*   **Ganancia estática ($K_{plant}$):** $-0.25$ °C/% (ganancia negativa debido a que aumentar la apertura/velocidad del CRAC disminuye la temperatura).
*   **Constante de tiempo ($\tau$):** $35$ segundos.
*   **Tiempo muerto ($\theta$):** $4.5$ segundos.

### 2. Sensor (Tensión de Realimentación)
Termorresistencia Pt100 con transmisor calibrado de $18$ °C a $28$ °C en rango de $0.2$ V a $1.0$ V (ganancia de transductor $H = 0.2$ V/°C):
$$H(s) = 0.2 \text{ V/°C}$$

### 3. Parámetros del Controlador PID (Sintonización Cohen-Coon)
El controlador implementado es de tipo PID paralelo en paralelo con lazo de realimentación unitaria de tensión ($H_r = 0.2$ V/°C):
*   **Ganancias Físicas (Hardware):**
    *   $K_p = 12.5$ %/V
    *   $K_i = 0.4$ %/(V·s)
    *   $K_d = 2.5$ %·s/V
*   **Ganancias de Software (Compensando H):**
    *   $K_{p,\text{sw}} = 2.5$ %/°C
    *   $K_{i,\text{sw}} = 0.08$ %/(°C·s)
    *   $K_{d,\text{sw}} = 0.5$ %·s/°C

---

##  Características del Simulador en Tiempo Real

La pestaña **"Simulación Dinámica Segundo a Segundo"** cuenta con las siguientes características avanzadas de diseño:
*   **Gráficos Interactivos de Alta Velocidad:** Implementados mediante gráficos nativos web en el cliente para máxima fluidez y tasa de refresco a 15+ FPS.
*   **Velocidad de Simulación Variable:** Dos sliders permiten configurar de forma interactiva la velocidad del reloj:
    *   *Intervalo de refresco [ms]:* Controla cada cuántos milisegundos se actualiza la interfaz.
    *   *Pasos por cuadro:* Multiplica la velocidad temporal de la simulación (hasta 10 segundos virtuales por paso real) para ver la estabilización en segundos.
*   **Ataque DoS Térmico Variable:** Permite simular una inyección de calor variable (de $0$ a $10$ °C) mediante un slider dinámico para evaluar la capacidad de rechazo de perturbaciones de la acción integral del lazo. Un sombreado naranja de fondo en el gráfico alerta del período bajo ataque.

---

##  Autores y Cátedra
*   **Estudiante:** Matias Ezequiel Pormi
*   **Cátedra:** Teoría de Control (K-4011) - UTN FRBA
*   **Profesor:** Ing. Omar Oscár Civale
*   **Fecha de Finalización:** Julio de 2026
