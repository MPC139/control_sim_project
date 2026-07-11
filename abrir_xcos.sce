// ============================================================================
// CONSTRUIR Y ABRIR DIAGRAMA XCOS — SEGUIMIENTO AL ESCALÓN  
// Ejecutar en Scilab GUI: exec('abrir_xcos.sce')
// ============================================================================

clear;
loadXcosLibs();

function set_pins(block, nin, nout)
    // Calcular posiciones de puertos de entrada y salida
    x  = block.graphics.orig(1);
    y  = block.graphics.orig(2);
    w  = block.graphics.sz(1);
    h  = block.graphics.sz(2);
    
    if nin > 0 then
        block.graphics.pin = zeros(nin, 1);
        if nin == 1 then
            block.graphics.pin(1) = y + h/2;
        else
            for i = 1:nin
                block.graphics.pin(i) = y + h*i/(nin+1);
            end
        end
    end
    
    if nout > 0 then
        block.graphics.pout = zeros(nout, 1);
        if nout == 1 then
            block.graphics.pout(1) = y + h/2;
        else
            for i = 1:nout
                block.graphics.pout(i) = y + h*i/(nout+1);
            end
        end
    end
endfunction

// ─── Layout ─────────────────────────────────────────────────────────────────
w=70; h=40;
x_step=20;   y=180;
x_hr=110;    
x_sum=200;   ysum=y-5;
x_pid=300;   yP=120; yI=y; yD=240;
x_int=380;
x_big=470;   ybig=y-10;
x_ga=550;
x_gp=630;
x_del=740;
x_sumd=820;  
x_sc=890;
x_h=630;     yfb=300;

scs_m = scicos_diagram();
scs_m.props.title = "Seguimiento al Escalon - PID + FOPTD";

idx=0;

// ─── 1. STEP ────────────────────────────────────────────────────────────────
idx=idx+1; b=STEP_FUNCTION("define");
b.graphics.orig=[x_step, y]; b.graphics.sz=[w, h];
b.model.rpar=[0; 28; 22];
set_pins(b, 0, 1);
scs_m.objs(idx)=b; iST=idx;

// ─── 2. GAIN: Hr=0.2 ───────────────────────────────────────────────────────
idx=idx+1; b=GAINBLK_f("define");
b.graphics.orig=[x_hr, y]; b.graphics.sz=[w, h];
b.graphics.exprs="0.2"; b.model.rpar=0.2;
set_pins(b, 1, 1);
scs_m.objs(idx)=b; iHR=idx;

// ─── 3. SUMMATION: comparador de error ─────────────────────────────────────
idx=idx+1; b=SUMMATION("define");
b.graphics.orig=[x_sum, ysum]; b.graphics.sz=[w, h];
b.model.rpar=[1; -1]; b.model.ipar=[2];
b.graphics.exprs=["1";"-1"];
set_pins(b, 2, 1);
scs_m.objs(idx)=b; iSUM=idx;

// ─── 4. GAIN P: -Kp ─────────────────────────────────────────────────────────
idx=idx+1; b=GAINBLK_f("define");
b.graphics.orig=[x_pid, yP]; b.graphics.sz=[w, h];
b.graphics.exprs="-12.5"; b.model.rpar=-12.5;
set_pins(b, 1, 1);
scs_m.objs(idx)=b; iP=idx;

// ─── 5. GAIN I: -Ki ─────────────────────────────────────────────────────────
idx=idx+1; b=GAINBLK_f("define");
b.graphics.orig=[x_pid, yI]; b.graphics.sz=[w, h];
b.graphics.exprs="-0.4"; b.model.rpar=-0.4;
set_pins(b, 1, 1);
scs_m.objs(idx)=b; iIG=idx;

// ─── 6. INTEGRAL ──────────────────────────────────────────────────────────
idx=idx+1; b=INTEGRAL_f("define");
b.graphics.orig=[x_int, yI]; b.graphics.sz=[w, h];
b.model.rpar=0;
set_pins(b, 1, 1);
scs_m.objs(idx)=b; iII=idx;

// ─── 7. DERIV ─────────────────────────────────────────────────────────────
idx=idx+1; b=DERIV("define");
b.graphics.orig=[x_pid, yD]; b.graphics.sz=[w, h];
set_pins(b, 1, 1);
scs_m.objs(idx)=b; iDD=idx;

// ─── 8. GAIN D: -Kd ─────────────────────────────────────────────────────────
idx=idx+1; b=GAINBLK_f("define");
b.graphics.orig=[x_int, yD]; b.graphics.sz=[w, h];
b.graphics.exprs="-2.5"; b.model.rpar=-2.5;
set_pins(b, 1, 1);
scs_m.objs(idx)=b; iDG=idx;

// ─── 9. BIGSOM: sumador PID (3 entradas) ────────────────────────────────────
idx=idx+1; b=BIGSOM_f("define");
b.graphics.orig=[x_big, ybig]; b.graphics.sz=[50, 50];
b.model.ipar=[3];
b.graphics.exprs=["1";"1";"1"];
set_pins(b, 3, 1);
scs_m.objs(idx)=b; iSP=idx;

// ─── 10. GAIN: Ga=1 ───────────────────────────────────────────────────────
idx=idx+1; b=GAINBLK_f("define");
b.graphics.orig=[x_ga, y]; b.graphics.sz=[w, h];
b.graphics.exprs="1"; b.model.rpar=1;
set_pins(b, 1, 1);
scs_m.objs(idx)=b; iGA=idx;

// ─── 11. CLR: Planta K/(tau*s+1) ──────────────────────────────────────────
idx=idx+1; b=CLR("define");
b.graphics.orig=[x_gp, y]; b.graphics.sz=[100, h];
b.graphics.exprs=["-0.25";"1 35"];
b.model.rpar=[-0.25; 1; 35]; b.model.ipar=[1; 2];
set_pins(b, 1, 1);
scs_m.objs(idx)=b; iGP=idx;

// ─── 12. TIME_DELAY: theta=4.5 ────────────────────────────────────────────
idx=idx+1; b=TIME_DELAY("define");
b.graphics.orig=[x_del, y]; b.graphics.sz=[w, h];
b.model.rpar=4.5; b.graphics.exprs="4.5";
set_pins(b, 1, 1);
scs_m.objs(idx)=b; iDL=idx;

// ─── 13. SUMMATION: perturbacion (D=0, abierto) ────────────────────────────
idx=idx+1; b=SUMMATION("define");
b.graphics.orig=[x_sumd, ysum]; b.graphics.sz=[w, h];
b.model.rpar=[1; -1]; b.model.ipar=[2];
b.graphics.exprs=["1";"-1"];
set_pins(b, 2, 1);
scs_m.objs(idx)=b; iSD=idx;

// ─── 14. CSCOPE ────────────────────────────────────────────────────────────
idx=idx+1; b=CSCOPE("define");
b.graphics.orig=[x_sc, y-10]; b.graphics.sz=[80, 80];
b.model.ipar=[1];
set_pins(b, 1, 0);
scs_m.objs(idx)=b; iSC=idx;

// ─── 15. GAIN: H=0.2 (sensor feedback) ─────────────────────────────────────
idx=idx+1; b=GAINBLK_f("define");
b.graphics.orig=[x_h, yfb]; b.graphics.sz=[w, h];
b.graphics.exprs="0.2"; b.model.rpar=0.2;
set_pins(b, 1, 1);
scs_m.objs(idx)=b; iH=idx;

// ─── LINKS ──────────────────────────────────────────────────────────────────
// Creación directa (sin función auxiliar — las funciones pierden el tipo Link)

// STEP → Hr
lk=scicos_link(); lk.from(1)=iST; lk.from(2)=1; lk.from(3)=0; lk.to(1)=iHR; lk.to(2)=1; lk.to(3)=0; scs_m.objs($+1)=lk;
// Hr → SUM(+)
lk=scicos_link(); lk.from(1)=iHR; lk.from(2)=1; lk.from(3)=0; lk.to(1)=iSUM; lk.to(2)=1; lk.to(3)=0; scs_m.objs($+1)=lk;
// Error → P
lk=scicos_link(); lk.from(1)=iSUM; lk.from(2)=1; lk.from(3)=0; lk.to(1)=iP; lk.to(2)=1; lk.to(3)=0; scs_m.objs($+1)=lk;
// Error → I_gain
lk=scicos_link(); lk.from(1)=iSUM; lk.from(2)=1; lk.from(3)=0; lk.to(1)=iIG; lk.to(2)=1; lk.to(3)=0; scs_m.objs($+1)=lk;
// Error → Deriv
lk=scicos_link(); lk.from(1)=iSUM; lk.from(2)=1; lk.from(3)=0; lk.to(1)=iDD; lk.to(2)=1; lk.to(3)=0; scs_m.objs($+1)=lk;
// I_gain → Integ
lk=scicos_link(); lk.from(1)=iIG; lk.from(2)=1; lk.from(3)=0; lk.to(1)=iII; lk.to(2)=1; lk.to(3)=0; scs_m.objs($+1)=lk;
// Deriv → D_gain
lk=scicos_link(); lk.from(1)=iDD; lk.from(2)=1; lk.from(3)=0; lk.to(1)=iDG; lk.to(2)=1; lk.to(3)=0; scs_m.objs($+1)=lk;
// P → BIGSOM(1)
lk=scicos_link(); lk.from(1)=iP; lk.from(2)=1; lk.from(3)=0; lk.to(1)=iSP; lk.to(2)=1; lk.to(3)=0; scs_m.objs($+1)=lk;
// Integ → BIGSOM(2)
lk=scicos_link(); lk.from(1)=iII; lk.from(2)=1; lk.from(3)=0; lk.to(1)=iSP; lk.to(2)=2; lk.to(3)=0; scs_m.objs($+1)=lk;
// D_gain → BIGSOM(3)
lk=scicos_link(); lk.from(1)=iDG; lk.from(2)=1; lk.from(3)=0; lk.to(1)=iSP; lk.to(2)=3; lk.to(3)=0; scs_m.objs($+1)=lk;
// BIGSOM → Ga
lk=scicos_link(); lk.from(1)=iSP; lk.from(2)=1; lk.from(3)=0; lk.to(1)=iGA; lk.to(2)=1; lk.to(3)=0; scs_m.objs($+1)=lk;
// Ga → Planta
lk=scicos_link(); lk.from(1)=iGA; lk.from(2)=1; lk.from(3)=0; lk.to(1)=iGP; lk.to(2)=1; lk.to(3)=0; scs_m.objs($+1)=lk;
// Planta → Delay
lk=scicos_link(); lk.from(1)=iGP; lk.from(2)=1; lk.from(3)=0; lk.to(1)=iDL; lk.to(2)=1; lk.to(3)=0; scs_m.objs($+1)=lk;
// Delay → SumD(1)
lk=scicos_link(); lk.from(1)=iDL; lk.from(2)=1; lk.from(3)=0; lk.to(1)=iSD; lk.to(2)=1; lk.to(3)=0; scs_m.objs($+1)=lk;
// SumD → Scope
lk=scicos_link(); lk.from(1)=iSD; lk.from(2)=1; lk.from(3)=0; lk.to(1)=iSC; lk.to(2)=1; lk.to(3)=0; scs_m.objs($+1)=lk;

// Feedback: SD output → H sensor
lk=scicos_link(); lk.from(1)=iSD; lk.from(2)=1; lk.from(3)=0; lk.to(1)=iH; lk.to(2)=1; lk.to(3)=0;
lk.xx=[x_sumd+w; x_sumd+w; x_h+w]; lk.yy=[ysum+h/2; yfb+h/2; yfb+h/2]; scs_m.objs($+1)=lk;
// H sensor → SUM(2) (neg input)
lk=scicos_link(); lk.from(1)=iH; lk.from(2)=1; lk.from(3)=0; lk.to(1)=iSUM; lk.to(2)=2; lk.to(3)=0;
lk.xx=[x_h; x_sum+w/2]; lk.yy=[yfb+h/2; ysum+h]; scs_m.objs($+1)=lk;

disp("Construido: " + string(length(scs_m.objs)) + " objetos");
disp("Abriendo Xcos...");
xcos(scs_m);
disp("Listo.");
