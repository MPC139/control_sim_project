# PLAN DE SPRINTS: TFI - SISTEMA DE CONTROL DE TEMPERATURA DE DATA CENTER

**Herramientas Seleccionadas:** Python, Streamlit, librerías `control` y `scipy`.
**Enfoque Teórico:** Modelado matemático FOPTD (First-Order Plus Dead-Time) basado en papers académicos.

## SPRINT 1: Concepción, Definición Teórica y Diagrama de Bloques (ACTUAL)
*   **Objetivo:** Definir la arquitectura del sistema, el modelo matemático sustentado en bibliografía académica y el diagrama de bloques.
*   **Entregables:** 
    *   Definición de Entradas, Salidas y Perturbaciones basadas en el estándar ASHRAE.
    *   Ecuaciones matemáticas del sistema térmico (FOPTD y Ley de Enfriamiento de Newton).
    *   Diagrama de Bloques detallado.

## SPRINT 2: Definición de Alcance y Arquitectura (DEDICADO A DOCUMENTACIÓN)
*   **Objetivo:** Completar el esqueleto oficial del informe según las pautas reglamentarias.
*   **Entregables:** 
    *   Sección de "Alcance" completa con hardware real (Sensores NTC, Ventiladores EC, Unidades Uniflair).
    *   Definición técnica de Carga, Transductores y Actuadores.
    *   Primer borrador del Diagrama de Bloques detallado.

## SPRINT 3: Desarrollo del Tablero de Control y Motor de Simulación
*   **Objetivo:** Configurar el entorno visual (Streamlit) e implementar el modelo FOPTD.
*   **Entregables:** 
    *   Simulación funcional del lazo cerrado.
    *   Sliders para sintonía PID y parámetros físicos.

## SPRINT 4: Análisis de Estabilidad y Perturbaciones (CONTENIDO TÉCNICO)
*   **Objetivo:** Realizar el análisis de Margen de Fase, Ganancia y respuesta ante Ataque DoS.
*   **Entregables:** 
    *   Gráficos de estabilidad (Bode/Root Locus).
    *   Sección de "Análisis de Estabilidad" en el informe final.

## SPRINT 5: Pulido del Informe Final y Validación
*   **Objetivo:** Revisión final del documento entregable frente a las pautas del .doc original.
*   **Entregables:** 
    *   Informe final (.pdf) con todas las secciones completas.
    *   Conclusiones con criterio ingenieril.
