// ============================================================================
// SIMULACIÓN DE RESPUESTA AL ESCALÓN DE REFERENCIA — SCILAB
// TFI Teoría de Control K-4011 · UTN FRBA
// Planta FOPTD + PID con corrección de signo · Seguimiento puro (D = 0)
// ============================================================================

clear;

// ─── 1. PARÁMETROS DEL SISTEMA ──────────────────────────────────────────────
// Planta FOPTD: Gp(s) = K * e^(-theta*s) / (tau*s + 1)
K     = -0.25;      // Ganancia estática [°C/%]
tau   =  35;        // Constante de tiempo [s]
theta =   4.5;      // Tiempo muerto [s]

// Instrumentación [V/°C]
H   = 0.2;          // Sensor Pt100 (realimentación)
Hr  = 0.2;          // Transmisor de referencia

// Controlador PID (ganancias físicas en %/V)
Kp = 12.5;
Ki =  0.4;
Kd =  2.5;

// Condiciones iniciales y setpoint
T0  = 28;           // Temperatura inicial [°C]
Tsp = 22;           // Setpoint [°C]
deltaR = Tsp - T0;  // Cambio de referencia = −6 °C

// Tiempo de simulación
t = linspace(0, 300, 3000);  // 0 a 300 s, 3000 puntos


// ─── 2. FUNCIONES DE TRANSFERENCIA ──────────────────────────────────────────
s = poly(0, 's');

// Planta sin retardo: K / (tau*s + 1)
Gp_base = syslin('c', K, tau*s + 1);

// Aproximación de Padé de 2do orden para e^(-theta*s)
// e^(-θs) ≈ (θ²s² − 6θs + 12) / (θ²s² + 6θs + 12)
num_pade = theta^2 * s^2 - 6*theta*s + 12;
den_pade = theta^2 * s^2 + 6*theta*s + 12;
delay_tf = syslin('c', num_pade, den_pade);

// Planta completa con retardo
Gp = Gp_base * delay_tf;

// Controlador PID: Gc(s) = (Kd*s^2 + Kp*s + Ki) / s
num_pid = Kd*s^2 + Kp*s + Ki;
den_pid = s;
Gc = syslin('c', num_pid, den_pid);

// ─── 3. LAZO CERRADO ────────────────────────────────────────────────────────
// Corrección de signo: −Gc(s) compensa la ganancia negativa K < 0
// Ganancia de lazo abierto: Gol(s) = −Gc(s) * Gp(s) * H(s)
Gol = -Gc * Gp * H;

// Transferencia de seguimiento: Y(s)/R(s) = Gol(s) / (1 + Gol(s))
// Scilab: T_cl = Gol /. 1  (feedback unitario)
T_cl = Gol /. 1;

// Verificación: polos de lazo cerrado
polos = roots(T_cl.den);
printf("Polos de lazo cerrado:\n");
for i = 1:length(polos)
    if imag(polos(i)) >= 0 then
        signo = "+";
    else
        signo = "-";
    end
    printf("  p%d = % .4f %s % .4f j\n", i, real(polos(i)), signo, abs(imag(polos(i))));
end
printf("\n");


// ─── 4. SIMULACIÓN ──────────────────────────────────────────────────────────
// Respuesta al escalón unitario del lazo cerrado
y_step = csim('step', t, T_cl);

// Superposición: condición inicial + transitorio hacia el setpoint
y_total = T0 + deltaR * y_step;

// Señal de error
error = Tsp - y_total;

// Señales de tensión
v_sensor = H * y_total;       // Vsensor(t) = H · T_out(t)
v_sp     = Hr * Tsp;          // Vsp = Hr · Tsp (constante)
e_volt   = v_sp - v_sensor;   // Error en voltaje


// ─── 5. MÉTRICAS DE RESPUESTA ──────────────────────────────────────────────
// Tiempo de asentamiento ±2 %
banda = abs(deltaR) * 0.02;
idx_in = find(abs(error) <= banda);
if ~isempty(idx_in) then
    ts = t(idx_in(1));
else
    ts = t($);
end

// Sobreimpulso (%)
if deltaR < 0 then
    temp_min = min(y_total);
    os_pct = abs(Tsp - temp_min) / abs(deltaR) * 100;
else
    temp_max = max(y_total);
    os_pct = abs(temp_max - Tsp) / abs(deltaR) * 100;
end

// Error estacionario
e_ss = abs(error($));

printf("╔════════════════════════════════════╗\n");
printf("║   MÉTRICAS DE RESPUESTA           ║\n");
printf("╠════════════════════════════════════╣\n");
printf("║ Tiempo asentamiento (±2%%): %5.1f s ║\n", ts);
printf("║ Sobreimpulso:              %5.1f %% ║\n", os_pct);
printf("║ Error estacionario:        %5.4f °C║\n", e_ss);
printf("║ Temperatura final:         %5.2f °C║\n", y_total($));
printf("║ Régimen:          Sobreamortiguado ║\n");
printf("╚════════════════════════════════════╝\n\n");


// ─── 6. GRÁFICOS ────────────────────────────────────────────────────────────
scf(0);
subplot(3,1,1);
plot(t, y_total, 'b-', 'LineWidth', 2);
plot(t, Tsp*ones(t), 'r--', 'LineWidth', 1.5);
plot(t, T0*ones(t), ':', 'Color', [0.5 0.5 0.5], 'LineWidth', 1);
// Banda ±2 %
xpoly([t(1) t($) t($) t(1)], [Tsp+banda Tsp+banda Tsp-banda Tsp-banda]);
e = gce(); e.fill_mode = 'on'; e.background = color('green');
e.foreground = color('green'); e.thickness = 0;
a = gca(); a.auto_clear = 'off';
hl = legend(['$T_{out}(t)$'; 'Setpoint (22°C)'; '$T_0$ (28°C)'; 'Banda ±2 %'], ...
            pos=1, font_size=2);
title('Respuesta al Escalón de Referencia  —  $D = 0$', 'fontsize', 4);
ylabel('Temperatura [°C]', 'fontsize', 3);
xgrid(color('grey70'));

subplot(3,1,2);
plot(t, error, 'g-', 'LineWidth', 2);
plot(t, zeros(t), 'k-', 'LineWidth', 0.5);
// Anotación tiempo asentamiento
xstring(ts + 5, 0.5, '$t_s \approx ' + string(round(ts)) + '$ s');
gce().font_size = 3;
gce().font_foreground = color('red');
plot(ts, 0, 'ro');
ylabel('Error [°C]', 'fontsize', 3);
hl2 = legend('$e(t) = T_{sp} - T_{out}$', pos=1, font_size=2);
xgrid(color('grey70'));

subplot(3,1,3);
plot(t, v_sensor, 'LineWidth', 2, 'color', [1 0.5 0]);    // orange
plot(t, v_sp*ones(t), 'r--', 'LineWidth', 1.5);
plot(t, e_volt, '-.', 'LineWidth', 1.5, 'color', [0 0.4 0.7]); // cyan
plot(t, zeros(t), 'k-', 'LineWidth', 0.5);
ylabel('Tensión [V]', 'fontsize', 3);
xlabel('Tiempo [s]', 'fontsize', 3);
hl3 = legend(['$V_{sensor}(t)$'; '$V_{sp}$'; '$E_v(t)$'], pos=1, font_size=2);
xgrid(color('grey70'));

printf("Script ejecutado correctamente.\n");

// Guardar gráfico en la raíz del proyecto
xs2png(0, 'respuesta_seguimiento_scilab.png');
printf("Gráfico guardado: respuesta_seguimiento_scilab.png\n");
