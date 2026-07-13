# MARCO TEÓRICO: Control de Temperatura en Data Center

## 1. Referencias Académicas y Contexto
El modelo desarrollado para este trabajo se basa en las investigaciones estándar de la industria sobre control térmico en centros de datos, específicamente:
1.  **Parolini et al. (2012):** *"A Cyber-Physical Systems Approach to Data Center Modeling and Control"*. Define el modelado en espacio de estados acoplando la carga de trabajo de TI (servidores) con la dinámica térmica.
2.  **ASHRAE TC 9.9:** Normativa internacional que establece que la temperatura de entrada a los servidores (Rack Inlet Temperature) debe mantenerse en un *Setpoint* ideal de **22°C (rango permitido de 18°C a 27°C)**.

## 2. Definición de Variables
*   **Variable Controlada (Salida - $Y(s)$):** Temperatura de entrada al rack de servidores ($T_{in}$), medida en °C.
*   **Variable de Referencia (Entrada - $R(s)$ o Setpoint):** Temperatura deseada seteada por el administrador (Ej. 22°C). Representada como escalón.
*   **Señal de Control ($U(s)$):** Porcentaje de apertura de la válvula de agua helada o velocidad del ventilador de la unidad CRAC (0 - 100%).
*   **Señal de Error ($E(s)$):** Diferencia entre la referencia y la temperatura medida: $e(t) = R(t) - Y_{medida}(t)$.
*   **Perturbaciones ($D(s)$):** 
    *   *Internas:* Carga térmica (Calor) generada por los servidores ($Q_{IT}$). Ej: Un aumento brusco de tráfico (ataque DoS) eleva drásticamente $Q_{IT}$.
    *   *Externas:* Apertura de puertas del pasillo frío.

## 3. Modelo Matemático (La Planta)
Para el diseño del controlador se utiliza el modelo empírico **FOPTD (First-Order Plus Dead-Time)**, ampliamente adoptado en la industria HVAC por su precisión y simplicidad para el "tuning" de PIDs:

$$ G_p(s) = \frac{Y(s)}{U(s)} = \frac{K_p e^{-\theta_p s}}{\tau_p s + 1} $$

Donde:
*   $K_p$ (Ganancia del Proceso): Disminución de temperatura por cada 1% de aumento en el enfriamiento.
*   $\tau_p$ (Constante de Tiempo Térmica): Depende de la capacitancia térmica del aire y los metales (inercia).
*   $\theta_p$ (Tiempo Muerto): Retardo de transporte (el tiempo que tarda el aire frío en viajar desde el aire acondicionado hasta los sensores en el rack).

## 4. Ley de Control (Controlador PID)
Se utilizará un controlador **PID** (Proporcional-Integral-Derivativo). 
*   La acción **Integral** garantiza el error nulo en estado estable ante los cambios constantes de carga térmica de los servidores.
*   La acción **Derivativa** ayuda a frenar la inercia térmica, evitando el *overshoot* (que la sala se enfríe demasiado, desperdiciando energía eléctrica).

$$ G_c(s) = K_c \left( 1 + \frac{1}{T_i s} + T_d s \right) $$

## 5. Diagrama de Bloques Estructural
```text
           Perturbación D(s) [Carga CPU / DoS]
                   |
                   v
R(s)   +   E(s)  +---+  U(s)   +-------+   Y(s)
---->(O)-------->|G_c|-------->|  G_p  |----+----> (Temperatura de Salida)
      ^ -        +---+         +-------+    |
      |                                     |
      |             +-------+               |
      +-------------|  H(s) |<--------------+
                    +-------+
                  (Sensor NTC)
```
*   **G_c:** Controlador PID implementado en software.
*   **G_p:** Planta térmica (Unidad CRAC + Pasillo Frío).
*   **H(s):** Transductor de temperatura (ej. termistor NTC), modelado típicamente como una ganancia $K_h = 1$ (sensor rápido respecto a la planta) o un polo rápido.
