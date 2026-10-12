#!/usr/bin/env python3
"""Stepper cart sim, rev 2: Barnaby on a gold ball on a dolly cart, geared NEMA17 (17HS15-1684S-PG5).

Run:  python3 cart_sim.py            (all cases + sensitivity + time-domain sim + cart_sim.png)
      python3 cart_sim.py --no-dyn   (skip time-domain sim, ~instant)
Edit: only the PARAMS / MASS / CASES blocks. Every entry = (value, unit, source, note).
Source tags: "web:<url>", "brain:<file:line>", "code:<file:line>", "user/photo", "derived", "GUESS".
"""
import math
import sys

BRAIN = "projects/cocaine-bear"
MC = "/home/user/tayg-oss/franky-fedbear/main.cc"
U_MOTOR = "https://tindie.com/products/stepperonline/nema-17-stepper-motor-38mm-length-w-51-gearbox/"
U_BEAR = "https://spirit-halloween.fandom.com/wiki/Barnaby_the_Bear"
U_DOLLY = "https://gorillamade.com/product/gfs-1830/"
U_POLOLU = "https://forum.pololu.com/t/what-is-the-correct-method-to-set-the-current-limit/14559"

# ============================== PARAMS ==============================
PARAMS = {
    # --- drive profile (exactly main.cc) ---
    "steps_per_segment": (200, "steps", f"code:{MC}:12,36", "STEPS_PER_REV loop count"),
    "step_high_us":      (2000, "us", f"code:{MC}:13,39", ""),
    "step_low_us":       (2000, "us", f"code:{MC}:13,42", ""),
    "pause_s":           (1.0, "s", f"code:{MC}:45,59", "delay(1000)"),
    # --- motor + gearbox: 17HS15-1684S-PG5 (label: user/photo) ---
    "step_angle_deg":    (1.8, "deg", f"web:{U_MOTOR}", "0.35 deg at output / 5.18"),
    "microstep":         (1, "-", "user", "MS pins unconnected -> pulled LOW on A4988 & DRV8825 = full step"),
    "gear_ratio":        (5.18, "-", f"web:{U_MOTOR}", "planetary, sold as 5:1"),
    "gear_eff":          (0.90, "-", f"web:{U_MOTOR}", ""),
    "gear_max_torque":   (2.0, "N*m", f"web:{U_MOTOR}", "max permissible (continuous) at output"),
    "gear_moment_torque": (4.0, "N*m", f"web:{U_MOTOR}", "moment (peak) permissible at output"),
    "holding_torque":    (0.36, "N*m", "derived", "1.68 N*m listed (geared, web) / (5.18*0.90) at motor shaft"),
    "rated_current":     (1.68, "A", f"web:{U_MOTOR}", "per phase"),
    "phase_R":           (1.65, "ohm", f"web:{U_MOTOR}", ""),
    "phase_L":           (3.2e-3, "H", f"web:{U_MOTOR}", ""),
    "current_limit":     (1.25, "A", "GUESS", "driver trim pot, range 1.0-1.5 A; Vref not measured; chip unidentified"),
    "fullstep_coil_factor": (0.707, "-", f"web:{U_POLOLU}", "full step: both coils at ~70% of the set limit"),
    "zero_torque_rate":  (1500.0, "full steps/s", "GUESS", "linear falloff; ~V/(2*L*I)=1500 at 12 V, 1.25 A"),
    "rotor_inertia":     (43e-7, "kg*m^2", "GUESS", "~38 g*cm^2 rotor (38 mm body) + ~5 gearbox input; not published"),
    "unloaded_pullin":   (1000.0, "full steps/s", "GUESS", "start-stop rate, no load"),
    "rotor_damping":     (2e-4, "N*m*s/rad", "GUESS", "dynamic sim only"),
    "supply_V":          (12.0, "V", f"brain:{BRAIN}/topics/motor-hardware-2026-10-09.md:20", "Anker SOLIX car socket"),
    # --- wheels / floor ---
    "wheel_diameter":    (0.060, "m", "user/photo", "WHEELTEC, on gearbox output via clamp hub"),
    "wheel_inertia":     (3e-5, "kg*m^2", "GUESS", "per driven wheel + hub"),
    "crr":               (0.05, "-", "GUESS", "rolling resistance, small wheels/casters on carpet"),
    "mu":                (0.6, "-", "GUESS", "tyre-carpet friction"),
    "g":                 (9.81, "m/s^2", "const", ""),
    # --- per-case (overridden by CASES) ---
    "driven_wheels":     (2, "-", "case", "user/photo: one per rear side, mirrored"),
    "driven_load_frac":  (0.33, "-", "case", "GUESS"),
    "mass_total":        (24.0, "kg", "case", ""),
}

# Mass build-up, kg: (low, mid, high, source)
MASS = {
    "bear":        (9.07, 9.07, 11.3, f"web:{U_BEAR} + brain:{BRAIN}/_files/council/S0/S0-facts.md:601 ('about 20 lb'; high = 25 lb GUESS)"),
    "ball_60_70cm": (1.0, 3.0, 6.0, "GUESS: EPS 15-30 kg/m^3 x 0.11-0.18 m^3 solid; hollow/painted shell lower"),
    "dolly_frame": (4.0, 7.0, 9.3, f"GUESS; high = steel 18x30 dolly 20.4 lb web:{U_DOLLY}"),
    "wood_carpet": (2.0, 3.5, 5.0, "GUESS: plywood deck + carpet"),
    "drive_elec":  (1.4, 1.5, 1.7, f"motors 0.46 kg each web:{U_MOTOR} + wheels/board GUESS"),
}
LEVELS = {"low": 0, "mid": 1, "high": 2}

# Layout (user/photo, resolved): TWO driven rear wheels, one per side, motors mirrored -> PRIMARY.
# "1 driven" kept only as a footnote (Tony's first description).
CASES = {
    "2 driven": dict(driven_wheels=2, driven_load_frac=0.33),  # GUESS: 2 driven of ~6 contact points (casters carry rest)
    "1 driven": dict(driven_wheels=1, driven_load_frac=0.2),   # footnote; GUESS 1 of ~5
}
SENS_KEYS = ["current_limit", "holding_torque", "gear_ratio", "wheel_diameter", "mass_total",
             "rotor_inertia", "zero_torque_rate", "unloaded_pullin", "driven_load_frac", "mu", "crr",
             "wheel_inertia", "step_high_us"]
LAG_BUDGET_STEPS = 2.0     # GUESS: rotor may trail command <2 full steps before losing sync
# ===================================================================


def mass(level):
    return sum(v[LEVELS[level]] for v in MASS.values())


def P(p, k):
    return p[k][0]


def with_case(p, **kw):
    q = dict(p)
    for k, v in kw.items():
        q[k] = (v,) + tuple(p[k][1:])
    return q


def analyse(p):
    d = {}
    G, eta = P(p, "gear_ratio"), P(p, "gear_eff")
    step = math.radians(P(p, "step_angle_deg")) / P(p, "microstep")
    t_step = (P(p, "step_high_us") + P(p, "step_low_us")) * 1e-6
    full_rate = 1 / t_step / P(p, "microstep")
    w_m = step / t_step
    r = P(p, "wheel_diameter") / 2
    m, n, g = P(p, "mass_total"), P(p, "driven_wheels"), P(p, "g")
    seg_t = P(p, "steps_per_segment") * t_step
    v = w_m / G * r
    d.update(G=G, eta=eta, step=step, t_step=t_step, full_rate=full_rate, w_m=w_m, r=r, m=m, n=n,
             rpm_wheel=w_m / G * 60 / (2 * math.pi), v=v, seg_t=seg_t, seg_dist=v * seg_t,
             cycle_t=2 * seg_t + 2 * P(p, "pause_s"))
    # motor-side torque available (per motor)
    T0 = P(p, "holding_torque") * min(1.0, P(p, "current_limit") / P(p, "rated_current")) * P(p, "fullstep_coil_factor")
    T_spd = max(0.0, T0 * (1 - full_rate / P(p, "zero_torque_rate")))
    # loads per motor referred to motor shaft
    J_load = (P(p, "wheel_inertia") + (m / n) * r * r) / (G * G * eta)
    J_eq = P(p, "rotor_inertia") + J_load
    F_rr = P(p, "crr") * m * g
    T_rr = (F_rr / n) * r / (G * eta)
    d.update(T0=T0, T_spd=T_spd, J_load=J_load, J_eq=J_eq, F_rr=F_rr, T_rr=T_rr)
    # start models
    a1 = w_m / t_step                                              # one step to full speed
    a2 = w_m ** 2 / (2 * LAG_BUDGET_STEPS * step * P(p, "microstep"))  # lag budget
    for tag, a in (("one", a1), ("lag", a2)):
        T_req = T_rr + J_eq * a
        d[f"T_start_{tag}"] = T_req
        d[f"m_start_{tag}"] = T_spd / T_req
        d[f"F_start_{tag}"] = F_rr + m * a * r / G
    d["m_cruise"] = T_spd / T_rr
    d["f_pullin"] = P(p, "unloaded_pullin") / math.sqrt(1 + J_load / P(p, "rotor_inertia"))
    d["m_pullin"] = d["f_pullin"] / full_rate
    N_drv = m * g * P(p, "driven_load_frac")
    d["traction"] = P(p, "mu") * N_drv
    d["m_slip_cruise"] = d["traction"] / F_rr
    d["m_slip_start"] = d["traction"] / d["F_start_lag"]
    # gearbox: worst output torque = max the motor can push through it, and torque needed at lag-budget start
    d["gear_out_max"] = T0 * G * eta
    d["gear_out_start"] = d["T_start_lag"] * G * eta
    # torque the motor needs just to spin the wheel against carpet friction (slipping start)
    d["T_slipping"] = (d["traction"] / n) * r / (G * eta)
    d["m_slipping"] = T_spd / d["T_slipping"]
    d["margin"] = min(d["m_cruise"], d["m_start_lag"], d["m_pullin"])
    d["verdict"] = "OK" if d["margin"] >= 1 else "STALL"
    return d


def drive_profile(p, cycles):
    th, tl = P(p, "step_high_us") * 1e-6, P(p, "step_low_us") * 1e-6
    t, ev = 0.0, []
    for _ in range(cycles):
        for direction in (+1, -1):
            for _ in range(int(P(p, "steps_per_segment"))):
                ev.append((t, direction))
                t += th + tl
            t += P(p, "pause_s")
    return ev, t


def dynamic_sim(p, cycles=1, dt=5e-6, v_eps=0.005, rec=1e-3):
    """2-DOF: motor rotor (sinusoidal detent torque toward command, linear torque-speed falloff)
    and cart, coupled through the driven wheel(s) by regularized Coulomb friction (wheel CAN slip)."""
    d = analyse(p)
    ev, t_end = drive_profile(p, cycles)
    G, eta, r, n, m = d["G"], d["eta"], d["r"], d["n"], d["m"]
    Nr = math.pi / 2 / d["step"] / P(p, "microstep")
    Jm = P(p, "rotor_inertia") + P(p, "wheel_inertia") / (G * G)
    b, T0 = P(p, "rotor_damping"), d["T0"]
    wz = P(p, "zero_torque_rate") * d["step"] * P(p, "microstep")
    muN = d["traction"] / n                    # per driven wheel
    Frr = d["F_rr"]
    th = w = cmd = x = v = 0.0
    i, t, k, every = 0, 0.0, 0, max(1, int(rec / dt))
    ts, xc, xs = [], [], []
    sin, tanh = math.sin, math.tanh
    while t < t_end:
        while i < len(ev) and ev[i][0] <= t:
            cmd += ev[i][1] * d["step"]
            i += 1
        aw = w if w >= 0 else -w
        Tm = (T0 * (1 - aw / wz) if aw < wz else 0.0) * sin(Nr * (cmd - th))
        F = muN * tanh((w * r / G - v) / v_eps)          # ground force per driven wheel
        w += (Tm - F * r / (G * eta) - b * w) / Jm * dt
        v += (n * F - Frr * tanh(v / 1e-3)) / m * dt
        th += w * dt
        x += v * dt
        if k % every == 0:
            ts.append(t); xc.append(cmd * r / G); xs.append(x)
        t += dt; k += 1
    return ts, xc, xs


def main():
    base = PARAMS
    dyn = "--no-dyn" not in sys.argv
    print("=== PARAMS ===")
    for k, (v, u, s, note) in base.items():
        if s != "case":
            print(f"  {k:20s} {v!s:>9} {u:13s} [{s}] {note}")
    print("\n=== MASS (kg) ===   low / mid / high")
    for k, (lo, mi, hi, s) in MASS.items():
        print(f"  {k:13s} {lo:5.2f} {mi:5.2f} {hi:5.2f}  [{s}]")
    print(f"  {'TOTAL':13s} {mass('low'):5.2f} {mass('mid'):5.2f} {mass('high'):5.2f}")

    d0 = analyse(with_case(base, mass_total=mass("mid"), **CASES["2 driven"]))
    print("\n=== KINEMATICS (ideal, no missed steps) ===")
    print(f"  step rate {d0['full_rate']:.0f} full steps/s; wheel {d0['rpm_wheel']:.2f} RPM; speed {d0['v']*100:.2f} cm/s")
    print(f"  per segment {d0['seg_t']:.2f} s -> {d0['seg_dist']*100:.2f} cm wheel travel; cycle {d0['cycle_t']:.1f} s; net drift 0")
    print(f"  one motor full step = {d0['step']/d0['G']*d0['r']*1000:.3f} mm of cart travel")
    print(f"  motor torque avail: {d0['T0']:.3f} N*m at 0 speed, {d0['T_spd']:.3f} at {d0['full_rate']:.0f} steps/s")

    print("\n=== CASES (margins = available/required, <1 fails) ===")
    hdr = (f"  {'case':9s} {'mass':5s} {'kg':>5s} {'cruise':>7s} {'start1':>7s} {'startL':>7s} {'pullin':>7s} "
           f"{'slipCr':>7s} {'slipSt':>7s} {'spinW':>6s} {'gearOut':>8s} verdict")
    print(hdr)
    results = {}
    for cname, cv in CASES.items():
        for lvl in LEVELS:
            q = with_case(base, mass_total=mass(lvl), **cv)
            d = analyse(q)
            results[(cname, lvl)] = (q, d)
            print(f"  {cname:9s} {lvl:5s} {d['m']:5.1f} {d['m_cruise']:7.2f} {d['m_start_one']:7.3f} {d['m_start_lag']:7.3f} "
                  f"{d['m_pullin']:7.3f} {d['m_slip_cruise']:7.2f} {d['m_slip_start']:7.3f} {d['m_slipping']:6.2f} "
                  f"{d['gear_out_max']:8.2f} {d['verdict']}")
    print("  start1 = full speed within one step; startL = rotor may lag 2 steps (verdict uses startL, cruise, pullin)")
    print("  slipCr/slipSt = traction / force needed at cruise / at lag-budget start")
    print("  spinW = motor torque / torque to spin the driven wheel against carpet friction (>1: wheel can spin, motor keeps sync)")
    print(f"  gearOut = max output torque the motor can put through the gearbox, N*m (limit {P(base,'gear_max_torque')} cont, {P(base,'gear_moment_torque')} peak)")

    print("\n=== SENSITIVITY (2 driven, mid mass; each input x0.5 / x1.5) ===")
    q0, dref = results[("2 driven", "mid")]
    rows = []
    for k in SENS_KEYS:
        outs = [analyse(with_case(q0, **{k: P(q0, k) * f})) for f in (0.5, 1.5)]
        sw = abs(math.log(outs[1]["margin"] / outs[0]["margin"])) if min(o["margin"] for o in outs) > 0 else float("inf")
        sl = abs(math.log(outs[1]["m_slip_start"] / outs[0]["m_slip_start"]))
        flips = [f"x{f}" for f, o in zip((0.5, 1.5), outs) if o["verdict"] != dref["verdict"]]
        rows.append((sw, k, outs, sl, flips))
    rows.sort(key=lambda r: -r[0])
    print(f"  {'#':2s} {'input':20s} {'margin x0.5':>11s} {'x1.5':>7s} {'|ln|':>6s} {'slip|ln|':>8s} flips")
    for j, (sw, k, (lo, hi), sl, fl) in enumerate(rows, 1):
        print(f"  {j:<2d} {k:20s} {lo['margin']:11.3f} {hi['margin']:7.3f} {sw:6.2f} {sl:8.2f} {','.join(fl) or '-'}")
    print(f"  baseline margin {dref['margin']:.3f}")

    if not dyn:
        return
    print("\n=== TIME-DOMAIN SIM (1 cycle each; wheel slip allowed) ===")
    plots = []
    for key in results:
        q, d = results[key]
        cyc = 2 if key[1] == "mid" else 1
        ts, xc, xs = dynamic_sim(q, cycles=cyc)
        seg_end = int(d["seg_t"] / 1e-3)
        fwd = max(xs[: seg_end + 900])
        print(f"  {key[0]:9s} {key[1]:5s}: fwd travel {fwd*100:6.2f} cm (cmd {d['seg_dist']*100:.2f}), "
              f"end-of-cycle drift {xs[int(d['cycle_t']/1e-3)-1]*100:+6.2f} cm")
        if cyc == 2:
            plots.append((key, ts, xc, xs))
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(plots[0][1], [x * 100 for x in plots[0][2]], color="#64748b", lw=2.2, label="commanded (main.cc)")
        for (key, ts, xc, xs), col in zip(plots, ("#dc2626", "#2563eb")):
            ax.plot(ts, [x * 100 for x in xs], color=col, lw=1.3, label=f"sim: {key[0]}, mid mass")
        ax.set_xlabel("time (s)"); ax.set_ylabel("cart position (cm)")
        ax.set_title("Bear cart, geared stepper: position vs time, 2 cycles")
        ax.grid(alpha=0.3); ax.legend(frameon=False, loc="upper right")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        fig.tight_layout()
        out = (__file__.rsplit("/", 1)[0] + "/") if "/" in __file__ else ""
        fig.savefig(out + "cart_sim.png", dpi=120)
        print(f"  plot -> {out}cart_sim.png")
    except ImportError:
        print("  matplotlib missing; no plot")


if __name__ == "__main__":
    main()
