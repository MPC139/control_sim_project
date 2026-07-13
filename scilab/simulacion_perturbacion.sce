// ============================================================================
// SIMULACIÓN DE RECHAZO DE PERTURBACIÓN (ATAQUE DoS) — SCILAB
// TFI Teoría de Control K-4011 · UTN FRBA
// Planta FOPTD + PID · Análisis de perturbación (R = 0)
// ============================================================================

clear;

// ─── 1. PARÁMETROS DEL SISTEMA ──────────────────────────────────────────────
K     = -0.25;      // Ganancia estática [°C/%]
tau   =  35;        // Constante de tiempo [s]
theta =   4.5;      // Tiempo muerto [s]

H  = 0.2;           // Sensor Pt100 (realimentación) [V/°C]

Kp = 12.5;          // Ganancia proporcional [%/V]
Ki =  0.4;          // Constante integral [%/(V·s)]
Kd =  2.5;          // Constante derivativa [%·s/V]

// Perturbación
d0     = 5.0;       // Magnitud térmica del DoS [°C]
setpoint = 22;      // Temperatura de referencia [°C]

// Tiempo de simulación
t = linspace(0, 400, 2000);


// ─── 2. FUNCIONES DE TRANSFERENCIA ──────────────────────────────────────────
s = poly(0, 's');

// Planta sin retardo
Gp_base = syslin('c', K, tau*s + 1);

// Padé 2do orden
num_pade = theta^2 * s^2 - 6*theta*s + 12;
den_pade = theta^2 * s^2 + 6*theta*s + 12;
delay_tf = syslin('c', num_pade, den_pade);

// Planta completa
Gp = Gp_base * delay_tf;

// Controlador PID
num_pid = Kd*s^2 + Kp*s + Ki;
den_pid = s;
Gc = syslin('c', num_pid, den_pid);

// ─── 3. SISTEMAS EN LAZO CERRADO ───────────────────────────────────────────
// Ganancia de lazo abierto: Gol = −Gc·Gp·H
Gol = -Gc * Gp * H;

// Transferencia de perturbación: Y/D = 1 / (1 - Gc·Gp·H) = 1 / (1 + Gol)
T_dist = 1 / (1 - Gc * Gp * H);

// Perturbación modelada como FOPTD (misma tau y theta que la planta)
Gd = 1 / (tau*s + 1);                  // Primer orden sin retardo
Gd = Gd * delay_tf;                     // Agregar retardo de Padé
T_combined = T_dist * Gd;               // Y(s) = T_dist(s) * Gd(s) * D0/s

// ─── 4. SIMULACIÓN ──────────────────────────────────────────────────────────
// Respuesta al escalón de perturbación: D(s) = d0 / s
y_dist_step = csim('step', t, T_combined);
y_total = setpoint + y_dist_step * d0;

// Señal de error
error = setpoint - y_total;

// ─── 5. MÉTRICAS ────────────────────────────────────────────────────────────
banda = abs(d0) * 0.02;

// Pico máximo (buscar después de t > 0 para evitar el valor inicial)
[pico, idx_pico] = max(y_total(10:$));
t_pico = t(idx_pico + 9);

// Tiempo de recuperación: buscar después del pico
idx_post_pico = find(t > t_pico & abs(error) <= banda);
if ~isempty(idx_post_pico) then
    t_rec = t(idx_post_pico(1));
else
    t_rec = t($);
end

// Error estacionario
e_ss = abs(error($));

printf("\n");
printf("╔══════════════════════════════════════╗\n");
printf("║   MÉTRICAS DE RECHAZO DE DoS        ║\n");
printf("╠══════════════════════════════════════╣\n");
printf("║ Magnitud DoS:             %5.1f °C   ║\n", d0);
printf("║ Pico máximo:              %5.2f °C   ║\n", pico);
printf("║ Instante del pico:        %5.1f s    ║\n", t_pico);
printf("║ Tiempo recuperación (±2%%): %5.1f s  ║\n", t_rec);
printf("║ Error estacionario:       %5.4f °C  ║\n", e_ss);
printf("╚══════════════════════════════════════╝\n\n");


// ─── 6. GRÁFICOS ────────────────────────────────────────────────────────────
scf(0);

subplot(2,1,1);
plot(t, y_total, 'b-', 'LineWidth', 2);
plot(t, setpoint*ones(t), 'r--', 'LineWidth', 1.5);
// Anotación del pico
plot(t_pico, pico, 'ro', 'MarkerSize', 8);
xstring(t_pico + 10, pico - 0.3, sprintf('%.2f °C\nt = %.0f s', pico, t_pico));
gce().font_size = 3;
gce().font_foreground = color('red');
// Banda ±2 %
xpoly([t(1) t($) t($) t(1)], [setpoint+banda setpoint+banda setpoint-banda setpoint-banda]);
gce().fill_mode = 'on'; gce().background = color('green');
gce().foreground = color('green'); gce().thickness = 0;
a = gca(); a.auto_clear = 'off';
legend(['$T_{out}(t)$'; 'Setpoint (22°C)'; 'Banda ±2 %'], pos=1, font_size=2);
title('Rechazo de Perturbación — Ataque DoS +' + string(d0) + '°C', 'fontsize', 4);
ylabel('Temperatura [°C]', 'fontsize', 3);
xgrid(color('grey70'));

subplot(2,1,2);
plot(t, error, 'g-', 'LineWidth', 2);
plot(t, zeros(t), 'k-', 'LineWidth', 0.5);
// Anotación tiempo de recuperación
if ~isempty(idx_rec) then
    plot(t_rec, 0, 'go', 'MarkerSize', 6);
    xstring(t_rec + 10, 0.3, '$t_{rec} \approx ' + string(round(t_rec)) + '$ s');
    gce().font_size = 3;
    gce().font_foreground = color('red');
end
ylabel('Error [°C]', 'fontsize', 3);
xlabel('Tiempo [s]', 'fontsize', 3);
legend('$e(t) = T_{sp} - T_{out}$', pos=1, font_size=2);
xgrid(color('grey70'));

// Guardar gráfico
xs2png(0, 'respuesta_perturbacion_scilab.png');
printf("Gráfico guardado: respuesta_perturbacion_scilab.png\n");
printf("Script ejecutado correctamente.\n");
