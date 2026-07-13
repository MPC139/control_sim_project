# Sistema de Control Térmico de Lazo Cerrado para Data Center (PID)

Este proyecto consiste en el diseño, modelado, simulación y validación de un sistema de control automático en lazo cerrado para regular la temperatura del pasillo frío de un Centro de Datos (Data Center). El trabajo fue desarrollado para el Trabajo Final Integrador (TFI) de la materia **Teoría de Control (Comisión K-4011)** de la **Universidad Tecnológica Nacional (UTN - FRBA)**, correspondiente a **Julio de 2026**.

El sistema controla dinámicamente la velocidad de los ventiladores EC de una unidad de aire acondicionado de precisión (CRAC) para contrarrestar la carga térmica disipada por los servidores y rechazar perturbaciones térmicas severas como ataques de denegación de servicio (DoS) térmicos.

---

## 📖 Guía de Lectura del Informe y Ejecución de Pruebas

Esta guía detalla los pasos para consultar el informe final académico, ejecutar los simuladores dinámicos y reproducir los ensayos analíticos del sistema de control.

### 📋 Requisitos Previos

Tener instalado **Python 3.8+** en su sistema (Linux/macOS/Windows) y, opcionalmente, **Scilab / Xcos 6.1+** para las simulaciones complementarias en Xcos.

---

### 1. Lectura del Informe Final (PDF y LaTeX)
El informe académico formal del TFI, formateado bajo las normativas oficiales IEEE (16 páginas con marcos teóricos, desarrollos matemáticos y resultados), se encuentra disponible en:
👉 **[report/informe_final.pdf](report/informe_final.pdf)** *(Haz clic para abrir el reporte completo).*

Si deseas recompilar el código fuente en LaTeX, navega a la carpeta correspondiente y ejecuta tu compilador (por ejemplo, con `pdflatex`):
```bash
cd report
pdflatex informe_final.tex
pdflatex informe_final.tex
```

---

### 2. Ejecución de los Simuladores Interactivos (Python)

El proyecto incluye dos plataformas de simulación interactiva que inicializan su propio entorno virtual e instalan todas las dependencias (`requirements.txt`) de forma silenciosa al ejecutarse:

#### A. Simulador Web (Streamlit)
Ideal para explorar rápidamente el lazo de control, visualizar el análisis de respuesta temporal y sintonizar en una interfaz web.
```bash
./run_sim.sh
```
*Si la aplicación no se abre automáticamente en tu navegador, ingresa a: **[http://localhost:8501](http://localhost:8501)***

#### B. Simulador de Escritorio en Tiempo Real (PyQt6 + pyqtgraph)
Diseñado para reproducir la dinámica física en tiempo real de alta velocidad (15+ FPS), registrar métricas de calidad de servicio (QoS) térmica y diagnosticar fallas de capacidad y saturación PID.
```bash
./run_desktop_sim.sh
```

---

### 3. Ejecución de Ensayos Analíticos y Scripts
En la carpeta `scripts/` se ubican utilidades en Python para regenerar las figuras y datos documentados en el informe:

*   **Regenerar Gráficos del Informe (Bode y Respuestas Temporales):**
    Genera de forma analítica las curvas de respuesta al escalón de referencia, rechazo de perturbaciones y el diagrama de estabilidad de Bode:
    ```bash
    .venv/bin/python scripts/generate_plots.py
    ```
    *Los resultados se guardan directamente en `report/figures/`.*

*   **Regenerar Capturas de Ensayo del Simulador de Escritorio:**
    Simula programáticamente y captura en memoria (modo offscreen) las tres situaciones clave (límite de capacidad, falla crítica y bug de clamping anti-windup) para actualizar los gráficos del apéndice del reporte:
    ```bash
    .venv/bin/python scripts/generate_screenshots.py
    ```
    *Los resultados actualizan los gráficos de la aplicación en `report/figures/`.*

*   **Regenerar Diagramas de Bloques Draw.io:**
    Reconstruye el archivo XML Draw.io editable del diagrama de bloques de control:
    ```bash
    .venv/bin/python scripts/generate_drawio.py
    ```
    *El archivo se guarda en `docs/diagrama_bloques_general.drawio`.*

---

### 4. Simulación Analítica en Scilab / Xcos
Para abrir el modelo gráfico de bloques de Scilab/Xcos y correr las simulaciones del TFI:
1. Abre **Scilab**.
2. Dirígete a la carpeta `scilab/` dentro de la consola de Scilab.
3. Ejecuta el script `abrir_xcos.sce` para cargar los bloques:
   ```scilab
   exec('abrir_xcos.sce', -1)
   ```
4. El simulador abrirá el archivo `Seguimiento_al_Escalon_PID_FOPTD.zcos`. Presiona **Play** en Xcos para iniciar la simulación.
5. De manera alternativa, puedes correr los scripts analíticos de respuesta temporal `simulacion_seguimiento.sce` y `simulacion_perturbacion.sce` desde la consola de Scilab.

---

##  Estructura del Proyecto

El repositorio se encuentra organizado de la siguiente manera:
*   **`src/`**: Código fuente de las aplicaciones.
    *   `app.py`: Simulador interactivo web (Streamlit).
    *   `app_escritorio.py`: Simulador interactivo de escritorio (PyQt6 + pyqtgraph).
*   **`report/`**: Informe final formal del proyecto.
    *   `informe_final.pdf`: Reporte académico completo en PDF listo para entregar.
    *   `informe_final.tex`: Código fuente LaTeX del reporte, incluyendo diagramas vectoriales TikZ.
    *   `figures/`: Gráficos analíticos y capturas del simulador en tiempo real utilizados en el reporte.
*   **`scilab/`**: Archivos de simulación y validación en Scilab / Xcos.
    *   `Seguimiento_al_Escalon_PID_FOPTD.zcos`: Diagrama de bloques gráfico en Xcos.
    *   `abrir_xcos.sce`, `simulacion_seguimiento.sce`, `simulacion_perturbacion.sce`: Scripts complementarios.
*   **`scripts/`**: Utilidades y scripts generadores de recursos.
    *   `generate_plots.py`: Generador de gráficos analíticos de control.
    *   `generate_drawio.py`: Generador de diagramas de bloques drawio.
    *   `generate_screenshots.py`: Generador de capturas de pantalla de la app de escritorio en modo offscreen.
*   **`docs/`**: Documentación adicional de soporte del proyecto.
*   **`run_sim.sh`**: Script Bash autogestionado para inicializar el entorno virtual y lanzar el simulador web.
*   **`run_desktop_sim.sh`**: Script Bash autogestionado para inicializar el entorno virtual y lanzar el simulador de escritorio (PyQt6).
*   **`requirements.txt`**: Dependencias de Python (`streamlit`, `pyqt6`, `pyqtgraph`, `control`, `matplotlib`, `numpy`, `scipy`).

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
