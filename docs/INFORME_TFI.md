# TRABAJO PRÁCTICO INTEGRADOR: TEORÍA DE CONTROL (K-4011)

**TEMA:** Sistema de Control de Lazo Cerrado para la Temperatura de un Data Center (Aire de Precisión)  
**PROFESOR:** Omar Oscár Civale  
**ALUMNOS:** Matias Ezequiel Pormi  
**COMISIÓN:** K4011  
**FECHA:** 11/07/2026

---

## ÍNDICE
1. [Introducción](#introducción)
2. [Objetivos](#objetivos)
3. [Alcance y Estructura del Sistema](#alcance-y-estructura-del-sistema)
    - Contexto y Mercado
    - Diagrama de Bloques
    - Variables y Unidades
    - Transductores y Elementos de Medición
    - Ley de Control y Actuación
4. [Modelado Matemático y Transferencias](#modelado-matemático-y-transferencias)
5. [Análisis de Estabilidad y Respuesta](#análisis-de-estabilidad-y-respuesta)
6. [Perturbaciones y Error](#perturbaciones-y-error)
7. [Simulación Computacional (Python)](#simulación-computacional-python)
8. [Conclusión](#conclusión)
9. [Bibliografía](#bibliografía)

---

## 1. INTRODUCCIÓN
El presente trabajo se encuadra en el mercado de la infraestructura de centros de datos (Data Centers). En la actualidad, la densidad de potencia de los servidores ha aumentado drásticamente, lo que genera una gran cantidad de calor en espacios reducidos. El control preciso de la temperatura en el "pasillo frío" no es solo una cuestión de operatividad, sino de eficiencia energética y prevención de fallas catastróficas del hardware. Se analiza un sistema de enfriamiento de precisión (CRAC/CRAH) que actúa sobre el flujo de aire para mantener las condiciones ambientales dentro de los estándares de la normativa ASHRAE.

## 2. OBJETIVOS
*   **Objetivo de Control:** Mantener la temperatura de entrada de aire a los servidores (Rack Inlet Temperature) en un valor constante de 22°C (Setpoint), independientemente de las variaciones en la carga de procesamiento (calor generado) o condiciones externas.
*   **Solución Planteada:** Implementación de un sistema de lazo cerrado con un controlador PID que regule la potencia de enfriamiento de la unidad CRAC basándose en la retroalimentación de sensores de temperatura distribuidos en el pasillo frío.

## 3. ALCANCE Y ESTRUCTURA DEL SISTEMA

### Contexto y Mercado
El sistema se sitúa en el mercado de infraestructura crítica para centros de datos. Se toma como referencia tecnológica las unidades de enfriamiento de precisión **Schneider Electric Uniflair™ (Serie LE/DX)**. Estos sistemas están diseñados para operar 24/7 y gestionar cargas térmicas de alta densidad en entornos de cloud computing y colocation.

### Carga del Sistema
La carga está constituida por la **Carga Térmica de IT (IT Load)**, generada por los racks de servidores. Esta carga es variable y depende del uso de CPU/GPU. Se modela como una inyección de energía térmica ($Q_{IT}$) en el flujo de aire, expresada en kilowatts (kW).

### Puntos de Interconexión con el Mundo Exterior
- **Suministro Eléctrico:** Alimentación trifásica para los ventiladores y compresores.
- **Red de Datos (BMS/DCIM):** Conexión vía protocolo **Modbus TCP/IP o SNMP** para el monitoreo remoto y ajuste de Setpoint.
- **Entorno Físico:** El aire caliente expulsado por los servidores hacia el "Pasillo Caliente" (Hot Aisle) y el aire frío inyectado al "Pasillo Frío" (Cold Aisle).

### Transductores y Elementos de Medición
Se identifican dos transductores críticos en el lazo de realimentación:
1.  **Sensor de Temperatura de Aire de Suministro (Supply Air Sensor):** Utiliza termistores tipo **NTC de alta precisión** (10k ohm @ 25°C) con un rango de operación de -10°C a 50°C. Convierte la temperatura física en una resistencia eléctrica, que el microprocesador de la unidad traduce a un valor digital.
2.  **Sensores de Rack (Opcionales):** Sensores inalámbricos o cableados ubicados en la cara frontal de los racks para medir la temperatura real de entrada a los servidores.

### Actuadores y Elementos de Acción
1.  **Ventiladores EC (Electronically Commutated):** Ventiladores de velocidad variable integrados que reciben una señal de control de **0-10V DC** desde el controlador. Permiten modular el caudal de aire ($\dot{m}$) de forma continua.
2.  **Válvula de Expansión Electrónica (EEV):** En sistemas DX (Direct Expansion), modula el flujo de refrigerante para ajustar la capacidad de enfriamiento con alta precisión.

### Variables, Unidades y Rangos
- **Referencia (Setpoint):** Rango típico 18°C - 27°C (Recomendado ASHRAE: 22°C).
- **Entrada Analógica (Sensor):** Señal de 0-10V o 4-20mA escalada a temperatura.
- **Salida de Control (Actuador):** 0-100% de la capacidad nominal del ventilador/compresor.

### Señales de Error y Realimentación
- **Señal de Realimentación ($y_f(t)$):** Valor medido por el sensor de suministro, convertido a voltios para su comparación.
- **Señal de Error ($e(t)$):** Diferencia instantánea entre el Setpoint y la realimentación ($e = Setpoint - T_{medida}$). Esta señal es procesada por el algoritmo PID para generar la corrección necesaria.

### Perturbaciones a Considerar
1.  **Ataque DoS / Picos de Tráfico:** Generan un aumento súbito de la carga térmica ($Q_{IT}$), actuando como una perturbación de tipo escalón o rampa en el proceso.
2.  **Apertura de Puertas:** Pérdida de contención en el pasillo frío, lo que introduce aire caliente del resto del edificio (perturbación externa).
3.  **Falla de una Unidad CRAC Adyacente:** Aumento de la carga sobre las unidades restantes en una configuración redundante (N+1).

### Caracterización de la Estabilidad
El sistema debe ser **estable en lazo cerrado** para todos los rangos de operación. Se utilizarán los criterios de **Bode (Margen de Fase > 45°)** y **Nyquist** para asegurar que el sistema no entre en oscilaciones divergentes ante cambios bruscos de carga.

### Relación entre Señales Analógicas y Digitales
Aunque el proceso térmico es analógico, el controlador es un **Microprocesador Digital**. Esto implica:
- **ADC (Analog-to-Digital Converter):** De 10 o 12 bits para leer los sensores NTC.
- **DAC (Digital-to-Analog Converter) / PWM:** Para generar la señal de 0-10V que comanda los ventiladores EC.
- **Tiempo de Muestreo ($T_s$):** El lazo se ejecuta a intervalos discretos (ej. cada 100ms), lo cual se modelará en la simulación.

## 4. MODELADO MATEMÁTICO Y TRANSFERENCIAS

### Metodología de Identificación de la Planta
Para determinar la dinámica del proceso térmico, se utiliza el método de **Identificación Experimental mediante Respuesta al Escalón**. Este procedimiento consiste en llevar el sistema a un punto de operación estable y aplicar un cambio súbito (escalón) en la señal de control (porcentaje de enfriamiento), registrando la evolución de la temperatura de salida ($T_{out}$) hasta alcanzar un nuevo estado estacionario.

El modelo resultante se ajusta a una estructura de **Primer Orden con Tiempo Muerto (FOPTD)**:
$$ G_p(s) = \frac{K e^{-\theta s}}{\tau s + 1} $$

Donde:
1.  **Ganancia del Proceso ($K$):** Define la magnitud del cambio en la temperatura por cada unidad de cambio en la señal de control.
2.  **Constante de Tiempo ($\tau$):** Representa la inercia térmica del aire y los componentes del rack (tiempo necesario para alcanzar el 63.2% de la respuesta final).
3.  **Tiempo Muerto ($\theta$):** Representa el retardo de transporte del flujo de aire desde la unidad CRAC hasta el sensor NTC.

### Parámetros de Referencia Académica
Para este trabajo, se toman como base los resultados experimentales presentados en el paper **"Optimizing Control Chain Latency in Liquid Cooled Data Center for Load Responsive Operation"** (Shi, Liu et al., 2026), publicado en la revista *Buildings*.

Basado en este estudio y adaptado a un sistema de aire de precisión (CRAC) de la línea Schneider Uniflair, se establecen los siguientes parámetros nominales para la simulación:
- **Ganancia ($K$):** $-0.25 \, \text{°C/\%}$ (Un aumento del 1% en la potencia de enfriamiento reduce la temperatura en 0.25°C).
- **Constante de Tiempo ($\tau$):** $35 \, \text{s}$.
- **Tiempo Muerto ($\theta$):** $4.5 \, \text{s}$.

La Función de Transferencia de la Planta resulta:
$$ G_p(s) = \frac{-0.25 e^{-4.5 s}}{35 s + 1} $$

## 5. LEY DE CONTROL

### Estructura del Controlador PID
Se implementa un controlador con algoritmo Proporcional-Integral-Derivativo en su forma paralela:
$$ G_c(s) = K_p + \frac{K_i}{s} + K_d s = K_p \left( 1 + \frac{1}{T_i s} + T_d s \right) $$

- **Acción Proporcional ($K_p$):** Proporciona una respuesta inmediata al error actual.
- **Acción Integral ($K_i$):** Elimina el error en estado estable acumulando el error histórico (fundamental ante perturbaciones de carga de CPU).
- **Acción Derivativa ($K_d$):** Proporciona amortiguamiento al sistema, anticipando la velocidad de cambio de la temperatura y reduciendo el sobreimpulso (*overshoot*).

## 6. PERTURBACIONES Y ERROR

### Análisis de Perturbaciones
En un Data Center, el sistema de control de temperatura se enfrenta a perturbaciones constantes que intentan desviar la variable controlada de su Setpoint. En este trabajo, modelamos el **Ataque de Denegación de Servicio (DoS)** como la perturbación principal.

1.  **Naturaleza de la Perturbación:** Un ataque DoS incrementa súbitamente la carga de trabajo en todos los servidores del rack. Esto se traduce en un aumento inmediato de la potencia térmica disipada ($Q_{IT}$), actuando como una entrada tipo **Escalón** en el bloque de perturbaciones.
2.  **Transferencia de Perturbación ($T_d(s)$):** La relación entre la perturbación y la salida del sistema en lazo cerrado está dada por:
    $$ T_d(s) = \frac{G_p(s)}{1 + G_c(s)G_p(s)} $$
3.  **Capacidad de Rechazo:** El controlador PID, específicamente a través de su **acción integral ($K_i$)**, detecta el aumento de temperatura causado por el DoS y aumenta la potencia de enfriamiento hasta que el efecto de la perturbación se anula por completo.

### Análisis del Error en Estado Estable ($e_{ss}$)
El error se define como $e(t) = Setpoint - T_{out}(t)$. Según el **Teorema del Valor Final**:
- **Ante un Escalón de Referencia:** Debido a que nuestro controlador tiene una acción integral (un polo en el origen, $1/s$), el sistema es de **Tipo 1**. Esto garantiza que el error en estado estable ante una entrada escalón sea **Cero**.
- **Ante una Perturbación Escalón:** La acción integral también asegura que, tras el transitorio provocado por el ataque DoS, la temperatura regrese exactamente a los 22°C definidos, logrando un rechazo total del error en régimen permanente.

En la simulación realizada, se observa que ante un ataque DoS inyectado en $t=200s$, el error presenta un pico transitorio, pero vuelve a $0 \pm 0.001 °C$ en menos de 100 segundos (dependiendo de la sintonía del PID).

## 7. SIMULACIÓN COMPUTACIONAL (PYTHON)
Se desarrolló una aplicación interactiva utilizando la librería `Streamlit` y el motor de control `python-control`. La herramienta permite:
- Ajustar las ganancias del PID en tiempo real.
- Modificar parámetros de la planta basados en el paper de Shi, Liu et al. (2026).
- Inyectar ataques DoS dinámicos para verificar la robustez del sistema.
- Visualizar automáticamente los márgenes de estabilidad (Bode) y la señal de error.

## 8. CONCLUSIÓN
Tras el desarrollo, modelado y simulación del sistema de control térmico para el Data Center, se han alcanzado las siguientes conclusiones desde una perspectiva de ingeniería:

1.  **Eficacia del Control PID:** Se ha demostrado que el uso de un controlador PID es fundamental para sistemas con inercia térmica. La acción **Integral** resultó ser el componente más crítico, ya que permitió anular el error en estado estable frente a perturbaciones persistentes como el aumento de carga por ataques DoS. Sin esta acción, el sistema presentaría un *offset* permanente que pondría en riesgo la vida útil de los servidores.
2.  **Impacto del Tiempo Muerto:** La incorporación del delay (tiempo muerto) mediante la aproximación de Padé reveló que la estabilidad del sistema es sumamente sensible a la ubicación física de los sensores. Un mayor retardo de transporte reduce drásticamente el Margen de Fase, obligando a reducir las ganancias del controlador para evitar oscilaciones divergentes.
3.  **Compromiso Desempeño vs. Estabilidad:** Se observó un compromiso (*trade-off*) claro: una sintonía agresiva permite una recuperación rápida ante perturbaciones, pero disminuye los márgenes de estabilidad. Para un entorno real de Data Center, se recomienda una sintonía moderada que priorice un Margen de Fase cercano a los 50° para absorber incertidumbres en el modelo.
4.  **Validación mediante Simulación:** El uso de herramientas de alto nivel (Python/Streamlit) permitió validar de forma empírica los conceptos teóricos de la materia. La capacidad de inyectar perturbaciones dinámicas y visualizar la respuesta temporal y en frecuencia simultáneamente proporciona una comprensión profunda de la dinámica del lazo cerrado que el análisis puramente analítico no alcanza a cubrir.

Finalmente, el cumplimiento de las normativas ASHRAE mediante este sistema asegura no solo la operatividad del hardware, sino también una optimización en el consumo energético de las unidades CRAC, demostrando que la Teoría de Control es una pieza angular en la gestión de infraestructuras IT modernas.

## 9. BIBLIOGRAFÍA
1.  **Shi, H., Pan, S., Liu, K., Wan, T., Li, C., \& Niu, B. (2026):** *"Optimizing Control Chain Latency in Liquid Cooled Data Center for Load Responsive Operation"*. Buildings, MDPI, 16(9), 1752. DOI: 10.3390/buildings16091752.
2.  **ASHRAE TC 9.9 (2021):** *"Thermal Guidelines for Data Processing Environments"*. American Society of Heating, Refrigerating and Air-Conditioning Engineers.
3.  **Parolini, L., et al. (2012):** *"A Cyber-Physical Systems Approach to Data Center Modeling and Control"*. Proceedings of the IEEE.
4.  **Ogata, K. (2010):** *"Ingeniería de Control Moderna"*. Pearson Education.
5.  **Schneider Electric (2023):** *"Technical Specifications: Uniflair™ Direct Expansion Room Cooling Solutions"*. White Paper.
