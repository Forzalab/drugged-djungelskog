#!/usr/bin/env python3
"""Stepper cart sim v2: Barnaby on a gold ball on a dolly cart, geared NEMA17 (17HS15-1684S-PG5).

v2 adds: masses from masses.json, excitation spectrum of the drive profile, base-excited 1-DOF
structural modes from modes.json, a tipping check of the bear+ball stack, and a comparison of
drive profiles (a: main.cc instant start, b: trapezoidal ramp, c: slower step rate).

Run:  python3 cart_sim.py                 (all profiles x low/mid/high mass, plots)
      python3 cart_sim.py --ramp 0.5 --slow-rate 100
Edit: PARAMS (motor/wheel physics, from v1), DEFAULT_MASSES / DEFAULT_MODES (used only when
masses.json / modes.json are missing or lack a key), PROFILES.
v1 is kept unchanged in cart_sim_v1.py.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BRAIN = "projects/cocaine-bear"
MC = "/home/user/tayg-oss/franky-fedbear/main.cc"
U_MOTOR = "https://tindie.com/products/stepperonline/nema-17-stepper-motor-38mm-length-w-51-gearbox/"
U_BEAR = "https://spirit-halloween.fandom.com/wiki/Barnaby_the_Bear"
U_DOLLY = "https://gorillamade.com/product/gfs-1830/"
U_POLOLU = "https://forum.pololu.com/t/what-is-the-correct-method-to-set-the-current-limit/14559"
LAG_BUDGET_STEPS = 2.0     # GUESS: rotor may trail command <2 full steps before losing sync

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
    # --- v2: front casters + load split (Tony) ---
    "rear_load_frac":    (0.5, "-", "GUESS", "static share of weight on the 2 driven rear wheels; masses.json rear_wheel_load_frac_est overrides; swept 0.3-0.7"),
    "cog_h_cart":        (0.52, "m", "GUESS", "whole loaded cart CoM height (load transfer); masses.json cog_h_m_<level>"),
    "wheelbase":         (0.66, "m", "GUESS", "rear axle to caster centres; masses.json wheelbase_m"),
    "caster_trail":      (0.025, "m", "GUESS", "caster offset (trail), 3 in casters 2-3 cm"),
    "caster_patch_r":    (0.01, "m", "GUESS", "effective radius of caster contact patch scrubbing on carpet"),
    "caster_swivel_s":   (2.0, "x trail", "GUESS", "kingpin travel to complete a 180 deg swivel, in trails"),
    "caster_lat_k":      (1.0, "-", "GUESS", "lateral kick / swivel force (1 = both casters swing to the same side, worst case)"),
}

# ===================================================================


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
    N_drv = m * g * P(p, "rear_load_frac")   # v2: static rear share
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




# ============================ v2 INPUTS ============================
# Defaults follow the masses.json / modes.json schemas. A JSON file, when present, overrides
# key by key; anything missing stays at the default and is reported as "default".
DEFAULT_MASSES = {
    "items": {   # kg, low / mid / high
        "bear":         {"low": 9.07, "mid": 9.07, "high": 11.3, "source": f"web:{U_BEAR} (~20 lb); high GUESS"},
        "ball":         {"low": 1.0, "mid": 3.0, "high": 6.0, "source": "GUESS: EPS 60-70 cm"},
        "dolly":        {"low": 6.0, "mid": 10.5, "high": 14.3, "source": f"GUESS frame+deck+carpet; web:{U_DOLLY}"},
        "fog_machine":  {"low": 2.0, "mid": 3.0, "high": 4.5, "source": "GUESS"},
        "anker_solix":  {"low": 3.0, "mid": 7.0, "high": 11.0, "source": "GUESS (model unknown)"},
        "drive_elec":   {"low": 1.4, "mid": 1.5, "high": 1.7, "source": f"web:{U_MOTOR} 0.46 kg/motor + GUESS"},
    },
    "buffer_kg": 2.0,
    "rear_wheel_load_frac_est": {"low": 0.5, "mid": 0.5, "high": 0.5},
    "geometry": {
        "cog_height_m": 1.30,       # bear+ball stack CoM above floor, GUESS
        "track_m": 0.45,            # GUESS (18x30 dolly)
        "wheelbase_m": 0.76,        # GUESS
        "rear_load_frac": 0.5,      # share of weight on the 2 driven rear wheels (Tony default)
    },
}
DEFAULT_MODES = {
    "modes": [   # f in Hz, damping = zeta
        {"name": "bear rocking on ball", "f_low": 0.8, "f_mid": 1.5, "f_high": 2.5, "damping": 0.05},
        {"name": "bear body sway",       "f_low": 2.0, "f_mid": 4.0, "f_high": 6.0, "damping": 0.04},
        {"name": "ball on deck",         "f_low": 3.0, "f_mid": 6.0, "f_high": 10.0, "damping": 0.08},
        {"name": "deck/dolly frame",     "f_low": 15.0, "f_mid": 30.0, "f_high": 50.0, "damping": 0.03},
    ],
    "excitations": [],
    "forbidden_bands_hz": [[0.8, 2.5], [2.0, 6.0]],
    "cog_height_m": 1.30,
    "base_halfwidth_m": 0.20,
    "tip_accel_ms2": None,          # None -> g * base_halfwidth / cog_height
}
LEVELS = ("low", "mid", "high")

PROFILES = {   # name -> builder kwargs; rates in full steps/s
    "a: main.cc instant": dict(kind="instant", rate=250.0),
    "b: trapezoid ramp":  dict(kind="trapezoid", rate=250.0, ramp_s=0.3),
    "c: slower instant":  dict(kind="instant", rate=125.0),
}
DT_SIM, DT_REC = 5e-6, 2e-4      # integration step, record step (5 kHz record)
TIP_LP_HZ = 10.0                 # rigid-body tipping uses cart accel low-passed here
TIP_MODE_FMAX = 10.0             # only modes <= this (Hz) can rock the bear+ball stack over
SWEEP_REAR = (0.3, 0.4, 0.5, 0.6, 0.7)
DOM_REL = 0.10                   # a spectral peak >= 10% of the max counts as dominant
# ===================================================================


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def load_inputs():
    """Load masses.json / modes.json if present; return (masses, modes, provenance)."""
    prov = {}
    masses = json.loads(json.dumps(DEFAULT_MASSES))
    modes = json.loads(json.dumps(DEFAULT_MODES))
    for fname, tgt, keys in (("masses.json", masses, ("items", "buffer_kg", "geometry", "rear_wheel_load_frac_est")),
                             ("modes.json", modes, ("modes", "excitations", "forbidden_bands_hz",
                                                     "cog_height_m", "base_halfwidth_m", "tip_accel_ms2"))):
        path = os.path.join(HERE, fname)
        data = None
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
            except Exception as e:
                print(f"  WARNING: {fname} unreadable ({e}); using defaults")
        for k in keys:
            prov[f"{fname}:{k}"] = "default"
        if not isinstance(data, dict):
            continue
        for k in keys:
            if k in data and data[k] is not None:
                tgt[k] = data[k]
                prov[f"{fname}:{k}"] = "json"
        if fname == "masses.json":
            # tolerate alternative spellings
            for alt in ("buffer", "buffer_mass_kg", "buffer_X_kg"):
                if alt in data and _num(data[alt]):
                    tgt["buffer_kg"] = data[alt]; prov["masses.json:buffer_kg"] = "json"
            if "geometry" not in data:
                for gk in ("cog_height_m", "track_m", "wheelbase_m", "rear_load_frac"):
                    if gk in data:
                        tgt["geometry"][gk] = data[gk]; prov["masses.json:geometry"] = "json"
            if "items" not in data and "masses" in data:
                tgt["items"] = data["masses"]; prov["masses.json:items"] = "json"
        else:
            g = data.get("geometry") or data.get("tipping") or {}
            for gk in ("cog_height_m", "base_halfwidth_m", "tip_accel_ms2"):
                if gk in g and g[gk] is not None and prov[f"modes.json:{gk}"] == "default":
                    tgt[gk] = g[gk]; prov[f"modes.json:{gk}"] = "json"
    masses["items"] = _norm_items(masses["items"])
    modes["modes"] = _norm_modes(modes["modes"])
    modes["forbidden_bands_hz"] = _norm_bands(modes["forbidden_bands_hz"])
    return masses, modes, prov


def _norm_items(items):
    out = {}
    if isinstance(items, list):
        items = {it.get("name", f"item{i}"): it for i, it in enumerate(items)}
    for name, v in items.items():
        if _num(v):
            lo = mi = hi = float(v); src = ""
        elif isinstance(v, (list, tuple)):
            lo, mi, hi = (float(x) for x in v[:3]); src = str(v[3]) if len(v) > 3 else ""
        elif isinstance(v, dict):
            mi = v.get("mid", v.get("mid_kg", v.get("kg_mid", v.get("kg", v.get("mass_kg")))))
            lo = v.get("low", v.get("low_kg", v.get("kg_low", mi)))
            hi = v.get("high", v.get("high_kg", v.get("kg_high", mi)))
            if not all(_num(x) for x in (lo, mi, hi)):
                continue
            lo, mi, hi = float(lo), float(mi), float(hi); src = str(v.get("source", ""))
        else:
            continue
        out[name] = {"low": lo, "mid": mi, "high": hi, "source": src}
    return out


def _norm_modes(modes):
    out = []
    if isinstance(modes, dict):
        modes = [dict(name=k, **v) if isinstance(v, dict) else {"name": k} for k, v in modes.items()]
    for i, md in enumerate(modes):
        fm = md.get("f_mid", md.get("f_mid_hz", md.get("f_hz", md.get("f"))))
        fl = md.get("f_low", md.get("f_low_hz", fm)); fh = md.get("f_high", md.get("f_high_hz", fm))
        z = md.get("damping", md.get("zeta", md.get("damping_ratio", 0.05)))
        if not all(_num(x) for x in (fl, fm, fh)):
            continue
        out.append(dict(name=str(md.get("name", f"mode{i}")), f_low=float(fl), f_mid=float(fm),
                        f_high=float(fh), damping=float(z) if _num(z) else 0.05))
    return out


def _norm_bands(bands):
    out = []
    for b in bands or []:
        if isinstance(b, dict):
            b = (b.get("lo", b.get("f_low", b.get("low"))), b.get("hi", b.get("f_high", b.get("high"))))
        if isinstance(b, (list, tuple)) and len(b) >= 2 and _num(b[0]) and _num(b[1]):
            out.append((float(b[0]), float(b[1])))
    return out


def total_mass(masses, level):
    """Sum of items; buffer_kg is added unless the item list already holds a 'buffer' item."""
    tot = sum(v[level] for v in masses["items"].values())
    if not any("buffer" in k.lower() for k in masses["items"]):
        tot += float(masses.get("buffer_kg") or 0.0)
    return tot


def level_geometry(masses, lvl):
    """Per-level cart geometry from masses.json (falls back to PARAMS defaults)."""
    geo, out = masses.get("geometry", {}), {}
    rl = masses.get("rear_wheel_load_frac_est", geo.get("rear_wheel_load_frac_est"))
    if isinstance(rl, dict) and _num(rl.get(lvl)):
        out["rear_load_frac"] = float(rl[lvl])
    elif _num(geo.get("rear_load_frac")):
        out["rear_load_frac"] = float(geo["rear_load_frac"])
    for key, pk in ((f"cog_h_m_{lvl}", "cog_h_cart"), ("wheelbase_m", "wheelbase")):
        if _num(geo.get(key)):
            out[pk] = float(geo[key])
    if _num(geo.get("caster_trail_m")):
        out["caster_trail"] = float(geo["caster_trail_m"])
    return out


# ------------------------- drive profiles -------------------------
def segment_steps(kind, rate, n, ramp_s=0.0):
    """Step times within one segment (s, from segment start) and segment duration."""
    if kind == "instant":
        ts = np.arange(n) / rate
        return ts, n / rate
    # trapezoidal velocity in steps: accel ramp_s, cruise at rate, decel ramp_s; same n steps
    Tr = ramp_s
    T = n / rate + Tr
    if n / rate < Tr:
        raise ValueError("ramp too long for this distance")
    a = rate / Tr
    x_acc = 0.5 * a * Tr * Tr

    def t_of(x):
        if x <= x_acc:
            return math.sqrt(2 * x / a)
        if x <= n - x_acc:
            return Tr + (x - x_acc) / rate
        return T - math.sqrt(2 * (n - x) / a)
    ts = np.array([t_of(k + 0.5) for k in range(n)])   # step k fires when the ideal path crosses k+0.5
    return ts, T


def build_events(p, prof, cycles=1):
    n = int(P(p, "steps_per_segment"))
    ts, seg_T = segment_steps(prof["kind"], prof["rate"], n, prof.get("ramp_s", 0.0))
    pause = P(p, "pause_s")
    ev, t0 = [], 0.0
    for _ in range(cycles):
        for direction in (+1, -1):
            ev += [(t0 + t, direction) for t in ts]
            t0 += seg_T + pause
    return ev, t0, seg_T


def dynamic_sim(p, ev, t_end, dt=DT_SIM, v_eps=0.005, rec=DT_REC):
    """v1 2-DOF model (rotor with detent torque toward command + cart, Coulomb-regularized
    wheel slip), driven by an arbitrary step-event list. Returns arrays t, x_cmd, x, v."""
    d = analyse(p)
    G, eta, r, n, m = d["G"], d["eta"], d["r"], d["n"], d["m"]
    Nr = math.pi / 2 / d["step"] / P(p, "microstep")
    Jm = P(p, "rotor_inertia") + P(p, "wheel_inertia") / (G * G)
    b, T0 = P(p, "rotor_damping"), d["T0"]
    wz = P(p, "zero_torque_rate") * d["step"] * P(p, "microstep")
    mu, g = P(p, "mu"), P(p, "g")
    W = m * g
    f_rear, h_cg, L = P(p, "rear_load_frac"), P(p, "cog_h_cart"), P(p, "wheelbase")
    e = P(p, "caster_trail")
    s_sw = P(p, "caster_swivel_s") * e
    # peak swivel resistance at the kingpin: contact-patch scrub torque / trail
    k_sw = mu * P(p, "caster_patch_r") / e
    k_lat = P(p, "caster_lat_k")
    Frr = d["F_rr"]
    caster_dir, s_prog = -1.0, 0.0        # worst case: casters start aligned for the other direction
    a_f, tau_a = 0.0, 1 / (2 * math.pi * 50.0)
    fl, nr = [], []
    th = w = cmd = x = v = 0.0
    i, t, k, every = 0, 0.0, 0, max(1, int(round(rec / dt)))
    ts, xc, xs, vs = [], [], [], []
    sin, tanh = math.sin, math.tanh
    nev = len(ev)
    while t < t_end:
        while i < nev and ev[i][0] <= t:
            cmd += ev[i][1] * d["step"]
            i += 1
        aw = w if w >= 0 else -w
        Tm = (T0 * (1 - aw / wz) if aw < wz else 0.0) * sin(Nr * (cmd - th))
        Nr_ = W * f_rear + m * a_f * h_cg / L        # load transfer: accel forward -> rear
        Nr_ = 0.0 if Nr_ < 0 else (W if Nr_ > W else Nr_)
        Nf = W - Nr_
        F = (mu * Nr_ / n) * tanh((w * r / G - v) / v_eps)
        # caster swivel: while moving against the caster alignment, the casters scrub through 180 deg
        F_sw = F_lat = 0.0
        if v * caster_dir < -1e-4:
            s_prog += (v if v > 0 else -v) * dt
            shp = sin(math.pi * min(s_prog, s_sw) / s_sw)
            F_sw = k_sw * Nf * max(shp, 0.3)
            F_lat = k_lat * k_sw * Nf * shp
            if s_prog >= s_sw:
                caster_dir, s_prog = -caster_dir, 0.0
        elif v * caster_dir > 1e-4 and s_prog > 0:     # moving back: caster swings back toward alignment
            s_prog = max(0.0, s_prog - (v if v > 0 else -v) * dt)
        w += (Tm - F * r / (G * eta) - b * w) / Jm * dt
        acc = (n * F - (Frr + F_sw) * tanh(v / 1e-3)) / m
        v += acc * dt
        a_f += (acc - a_f) * dt / tau_a
        th += w * dt
        x += v * dt
        if k % every == 0:
            ts.append(t); xc.append(cmd * r / G); xs.append(x); vs.append(v)
            fl.append(F_lat); nr.append(Nr_ / W)
        t += dt; k += 1
    return np.array(ts), np.array(xc), np.array(xs), np.array(vs), np.array(fl), np.array(nr)


# ------------------------- spectrum -------------------------
def lowpass(x, fc, dt):
    """Zero-phase 2-pole low-pass (forward-backward 1st-order x2)."""
    a = dt / (dt + 1 / (2 * math.pi * fc))
    y = np.asarray(x, float).copy()
    for _ in range(2):
        for arr in (y, y[::-1]):
            acc = arr[0]
            for j in range(len(arr)):
                acc += a * (arr[j] - acc)
                arr[j] = acc
    return y


def cmd_spectrum(ev, seg_dx, freqs):
    """Exact spectrum of the step-quantized commanded motion: velocity = sum dx*delta(t-tk),
    so V(f) = sum dx*exp(-j2pi f tk), A(f) = j2pi f V(f). Returns |A| (m/s^2 per Hz-bin units)."""
    tk = np.array([e[0] for e in ev]); sk = np.array([e[1] for e in ev]) * seg_dx
    V = np.array([np.sum(sk * np.exp(-2j * np.pi * f * tk)) for f in freqs])
    return np.abs(2 * np.pi * freqs * V)


def fft_amp(sig, dt, pad=4):
    nfft = int(2 ** math.ceil(math.log2(len(sig) * pad)))
    S = np.abs(np.fft.rfft(sig - np.mean(sig), nfft)) * dt
    f = np.fft.rfftfreq(nfft, dt)
    return f, S


def dominant(f, S, fmin=0.1, fmax=1000.0, k=6):
    m = (f >= fmin) & (f <= fmax)
    f, S = f[m], S[m]
    pk = np.where((S[1:-1] > S[:-2]) & (S[1:-1] >= S[2:]))[0] + 1
    pk = pk[S[pk] >= DOM_REL * S.max()]
    pk = pk[np.argsort(-S[pk])]
    picked = []
    for j in pk:   # skip near-duplicates (within 3% of a stronger peak)
        if all(abs(f[j] - f[q]) > 0.03 * f[q] + 0.05 for q in picked):
            picked.append(j)
        if len(picked) >= k:
            break
    return [(float(f[j]), float(S[j] / S.max())) for j in picked]


# ------------------------- structure -------------------------
def base_excited(a_base, dt, freqs, zetas):
    """Vectorized 1-DOF base-excited oscillators, Newmark average acceleration.
    z'' + 2 zeta w z' + w^2 z = -a_base.  Returns peak |z|, peak |absolute accel|."""
    w = 2 * np.pi * np.asarray(freqs, float); zt = np.asarray(zetas, float)
    c, kk = 2 * zt * w, w * w
    z = np.zeros_like(w); zd = np.zeros_like(w); zdd = -a_base[0] - c * zd - kk * z
    keff = kk + 2 * c / dt + 4 / dt ** 2
    zmax = np.zeros_like(w); amax = np.zeros_like(w)
    for ab in a_base[1:]:
        rhs = -ab + (4 / dt ** 2) * z + (4 / dt) * zd + zdd + c * ((2 / dt) * z + zd)
        zn = rhs / keff
        zdn = 2 * (zn - z) / dt - zd
        zddn = 4 * (zn - z) / dt ** 2 - 4 * zd / dt - zdd
        z, zd, zdd = zn, zdn, zddn
        aabs = np.abs(c * zd + kk * z)       # = |z'' + a_base|
        np.maximum(zmax, np.abs(z), out=zmax); np.maximum(amax, aabs, out=amax)
    return zmax, amax


def in_bands(f, bands):
    return [b for b in bands if b[0] <= f <= b[1]]


# ------------------------- run one case -------------------------
def run_case(p, prof, masses, modes):
    ev, t_end, seg_T = build_events(p, prof, cycles=1)
    t, xc, x, v, flat, nrear = dynamic_sim(p, ev, t_end + 0.5)
    a = np.gradient(v, DT_REC)
    a_lp = lowpass(a, TIP_LP_HZ, DT_REC)
    seg_end = int(seg_T / DT_REC)
    i2 = int((seg_T + P(p, "pause_s")) / DT_REC)
    fwd = float(np.max(x[: seg_end + int(0.9 / DT_REC)]))
    rev = float(x[i2] - np.min(x[i2:]))
    # lateral kick from caster swivel
    a_lat = flat / P(p, "mass_total")
    f_rev = 1.0 / (seg_T + P(p, "pause_s"))          # one reversal per segment+pause
    sw_idx = np.where(flat > 0)[0]
    lat = dict(a_pk=float(np.max(a_lat)), f_rev=f_rev, flags=[])
    if len(sw_idx):
        # swivel pulse duration (first contiguous run) -> pulse frequency ~ 1/(2*duration)
        run = np.split(sw_idx, np.where(np.diff(sw_idx) > 1)[0] + 1)
        dur = max(len(rr) for rr in run) * DT_REC
        lat["dur"] = dur; lat["f_pulse"] = 1 / (2 * dur)
    else:
        lat["dur"] = 0.0; lat["f_pulse"] = float("nan")
    d = analyse(p)
    cmd_dist = int(P(p, "steps_per_segment")) * d["step"] / d["G"] * d["r"]
    f, S = fft_amp(a, DT_REC)
    dom = dominant(f, S)
    # structural modes at f_low / f_mid / f_high
    fs, zs, lab = [], [], []
    for md in modes["modes"]:
        for tag in ("f_low", "f_mid", "f_high"):
            fs.append(md[tag]); zs.append(md["damping"]); lab.append((md["name"], tag))
    zmax, amax = base_excited(a, DT_REC, fs, zs) if fs else (np.array([]), np.array([]))
    a_pk, a_lp_pk = float(np.max(np.abs(a))), float(np.max(np.abs(a_lp)))
    if fs and lat["a_pk"] > 0:
        _, amax_lat = base_excited(a_lat, DT_REC, fs, zs)
        j = int(np.argmax(amax_lat))
        lat["a_tipdem"] = max([float(np.max(a_lat))] + [float(am) for am, fr in zip(amax_lat, fs) if fr <= TIP_MODE_FMAX])
        lat["a_struct"] = float(amax_lat[j]); lat["worst"] = f"{lab[j][0]} @{fs[j]:g} Hz"
    else:
        lat["a_struct"] = 0.0; lat["worst"] = "-"
    mode_res = []
    for (name, tag), fr, zm, am in zip(lab, fs, zmax, amax):
        mode_res.append(dict(mode=name, tag=tag, f=fr, z_mm=zm * 1e3, a=am, daf=am / a_lp_pk))
    worst = max(mode_res, key=lambda r: r["a"]) if mode_res else None
    # tipping: stack CoM sees max(rigid-body LP accel, worst structural absolute accel)
    g = P(p, "g")
    h, bw = modes["cog_height_m"], modes["base_halfwidth_m"]
    a_tip = modes["tip_accel_ms2"] if _num(modes.get("tip_accel_ms2")) else g * bw / h
    tip_modes = [mr["a"] for mr in mode_res if mr["f"] <= TIP_MODE_FMAX]
    demand = max([a_lp_pk] + tip_modes)
    lat_demand = lat.get("a_tipdem", lat["a_pk"])
    lat["tip_margin"] = a_tip / lat_demand if lat_demand > 0 else float("inf")
    for nh in range(1, 6):
        for bnd in in_bands(nh * f_rev, modes["forbidden_bands_hz"]):
            lat["flags"].append(f"reversal x{nh} = {nh*f_rev:.2f} Hz in {bnd[0]:g}-{bnd[1]:g}")
    if lat["f_pulse"] == lat["f_pulse"]:
        for bnd in in_bands(lat["f_pulse"], modes["forbidden_bands_hz"]):
            lat["flags"].append(f"swivel pulse {lat['f_pulse']:.2f} Hz in {bnd[0]:g}-{bnd[1]:g}")
    flags = []
    for fd, rel in dom:
        for bnd in in_bands(fd, modes["forbidden_bands_hz"]):
            flags.append(f"{fd:.2f} Hz ({rel:.0%}) in forbidden {bnd[0]:g}-{bnd[1]:g} Hz")
    # also flag broadband energy: share of spectrum (0.1-1000 Hz) inside forbidden bands
    band_frac = 0.0
    m = (f >= 0.1) & (f <= 1000)
    tot = np.sum(S[m] ** 2)
    for lo, hi in modes["forbidden_bands_hz"]:
        mb = (f >= lo) & (f <= hi)
        band_frac += np.sum(S[mb] ** 2) / tot if tot > 0 else 0.0
    return dict(t=t, xc=xc, x=x, v=v, a=a, a_lp=a_lp, f=f, S=S, ev=ev, seg_T=seg_T, cmd_dist=cmd_dist,
                rear_frac=P(p, "rear_load_frac"), fwd=fwd, rev=rev, lat=lat, nrear=(float(nrear.min()), float(nrear.max())), drift=float(x[min(len(x) - 1, int(t_end / DT_REC) - 1)]), dom=dom,
                modes=mode_res, worst=worst, a_pk=a_pk, a_lp_pk=a_lp_pk, a_tip=a_tip,
                demand=demand, tip_margin=a_tip / demand if demand > 0 else float("inf"),
                flags=flags, band_frac=band_frac, cycle_T=t_end)


def parse_args():
    a = sys.argv[1:]
    def opt(name, default):
        return float(a[a.index(name) + 1]) if name in a else default
    PROFILES["b: trapezoid ramp"]["ramp_s"] = opt("--ramp", 0.3)
    PROFILES["c: slower instant"]["rate"] = opt("--slow-rate", 125.0)
    PROFILES["b: trapezoid ramp"]["name_extra"] = f"{PROFILES['b: trapezoid ramp']['ramp_s']:g} s ramp"
    PROFILES["c: slower instant"]["name_extra"] = f"{PROFILES['c: slower instant']['rate']:g} steps/s"
    PROFILES["a: main.cc instant"]["name_extra"] = "250 steps/s"


def main():
    parse_args()
    masses, modes, prov = load_inputs()
    print("=== INPUT FILES ===")
    for k, s in prov.items():
        print(f"  {k:34s} {s}")
    geo = masses["geometry"]
    base = with_case(PARAMS, driven_wheels=2)
    # stack CoM for tipping: modes.json, else masses.json bear_on_ball_cog_h_m_mid
    if prov.get("modes.json:cog_height_m") == "default" and _num(geo.get("bear_on_ball_cog_h_m_mid")):
        modes["cog_height_m"] = float(geo["bear_on_ball_cog_h_m_mid"]); prov["modes.json:cog_height_m"] = "masses.json"
    print("\n=== MASS (kg) ===   low / mid / high")
    for k, v in masses["items"].items():
        print(f"  {k:14s} {v['low']:6.2f} {v['mid']:6.2f} {v['high']:6.2f}  {v['source']}")
    if not any("buffer" in k.lower() for k in masses["items"]):
        print(f"  {'buffer':14s} {masses['buffer_kg']:6.2f} (added to every level)")
    print("  " + f"{'TOTAL':14s} " + " ".join(f"{total_mass(masses, l):6.2f}" for l in LEVELS))
    print(f"  geometry: {geo}")
    print("\n=== STRUCTURE (modes.json) ===")
    for md in modes["modes"]:
        print(f"  {md['name']:24s} f {md['f_low']:g}/{md['f_mid']:g}/{md['f_high']:g} Hz  zeta {md['damping']:g}")
    print(f"  forbidden bands: {modes['forbidden_bands_hz']}")
    if modes.get("excitations"):
        print(f"  excitations listed by modes.json: {modes['excitations']}")
    print(f"  stack CoM {modes['cog_height_m']} m, base half-width {modes['base_halfwidth_m']} m, "
          f"tip accel {modes['tip_accel_ms2'] if _num(modes.get('tip_accel_ms2')) else 'g*b/h'}")

    res = {}
    for pname, prof in PROFILES.items():
        for lvl in LEVELS:
            q = with_case(base, mass_total=total_mass(masses, lvl), **level_geometry(masses, lvl))
            res[(pname, lvl)] = run_case(q, prof, masses, modes)

    print("\n=== EXCITATION SPECTRUM (mid mass; simulated cart accel, 1 cycle; dominant peaks, rel. amplitude) ===")
    fgrid = np.linspace(0.05, 1000, 20000)
    cmd_specs = {}
    for pname, prof in PROFILES.items():
        r = res[(pname, "mid")]
        seg_dx = r["cmd_dist"] / int(P(base, "steps_per_segment"))
        Sc = cmd_spectrum(r["ev"], seg_dx, fgrid)
        cmd_specs[pname] = Sc
        dc = dominant(fgrid, Sc)
        print(f"  {pname} ({prof['name_extra']})")
        print("    commanded (step-quantized): " + ", ".join(f"{fq:.2f} Hz {a:.0%}" for fq, a in dc))
        print("    simulated cart accel:       " + ", ".join(f"{fq:.2f} Hz {a:.0%}" for fq, a in r["dom"]))
        print(f"    share of accel energy inside forbidden bands: {r['band_frac']:.1%}")
        print("    forbidden-band hits: " + ("; ".join(r["flags"]) or "none among dominant peaks"))

    print("\n=== STRUCTURAL RESPONSE (mid mass; base accel = simulated cart accel) ===")
    print(f"  {'profile':22s} {'mode':24s} {'f':>6s} {'z_pk mm':>8s} {'a_pk m/s2':>9s} {'DAF':>6s}")
    for pname in PROFILES:
        r = res[(pname, "mid")]
        for mr in r["modes"]:
            if mr["tag"] == "f_low" or True:
                print(f"  {pname:22s} {mr['mode']:24s} {mr['f']:6.2f} {mr['z_mm']:8.3f} {mr['a']:9.3f} {mr['daf']:6.2f}")
    print(f"  DAF = mode peak absolute accel / peak cart accel low-passed at {TIP_LP_HZ:g} Hz")

    print("\n=== PROFILE COMPARISON (all masses; casters + load transfer on) ===")
    print(f"  {'profile':20s} {'mass':4s} {'kg':>5s} {'rear':>5s} {'fwd cm':>6s} {'rev cm':>6s} {'cmd':>5s} "
          f"{'a_LP':>5s} {'a_str':>6s} {'worst mode':26s} {'tipX':>5s} {'latPk':>5s} {'tipY':>5s} {'Nrear range':>11s}")
    for (pname, lvl), r in res.items():
        w, L = r["worst"], r["lat"]
        print(f"  {pname:20s} {lvl:4s} {total_mass(masses, lvl):5.1f} {r['rear_frac']:5.2f} {r['fwd']*100:6.2f} "
              f"{r['rev']*100:6.2f} {r['cmd_dist']*100:5.2f} {r['a_lp_pk']:5.2f} {w['a']:6.2f} "
              f"{(w['mode'] + ' @' + format(w['f'], 'g')):26s} {r['tip_margin']:5.2f} {L['a_pk']:5.2f} "
              f"{L['tip_margin']:5.2f} {r['nrear'][0]:5.2f}-{r['nrear'][1]:4.2f}")
    print("  fwd/rev = travel of segment 1 / segment 2 (v1 slip model + caster swivel + load transfer); cmd = commanded")
    print(f"  a_LP = cart accel low-passed {TIP_LP_HZ:g} Hz; a_str = worst mode absolute accel (fore-aft);")
    print(f"  tipX/tipY = a_tip / max(a_LP, modes <= {TIP_MODE_FMAX:g} Hz) fore-aft / lateral (<1 tips); latPk = caster swivel lateral kick (m/s^2);")
    print(f"  a_tip = {res[next(iter(res))]['a_tip']:.2f} m/s^2; Nrear range = dynamic share of weight on rear wheels")
    print("\n=== CASTER SWIVEL (mid mass) ===")
    for pname in PROFILES:
        L = res[(pname, "mid")]["lat"]
        print(f"  {pname:20s} reversal rate {L['f_rev']:.3f} Hz, swivel pulse {L['dur']:.2f} s (~{L['f_pulse']:.2f} Hz), "
              f"lateral kick {L['a_pk']:.2f} m/s^2, worst lateral mode {L['worst']} {L['a_struct']:.2f} m/s^2")
        print("    lateral flags: " + ("; ".join(L["flags"]) or "none"))

    print("\n=== REAR LOAD SWEEP (mid mass; static rear_load_frac, load transfer on) ===")
    print(f"  {'profile':20s} " + " ".join(f"{fr:>13.1f}" for fr in SWEEP_REAR))
    print(f"  {'':20s} " + " ".join(f"{'fwd/rev cm':>13s}" for _ in SWEEP_REAR))
    for pname, prof in PROFILES.items():
        cells = []
        for fr in SWEEP_REAR:
            geo_l = level_geometry(masses, "mid"); geo_l["rear_load_frac"] = fr
            q = with_case(base, mass_total=total_mass(masses, "mid"), **geo_l)
            r = run_case(q, prof, masses, modes)
            cells.append(f"{r['fwd']*100:5.2f}/{r['rev']*100:5.2f}")
        print(f"  {pname:20s} " + " ".join(f"{c:>13s}" for c in cells))
    print(f"  commanded {res[next(iter(res))]['cmd_dist']*100:.2f} cm per segment; traction = mu*N_rear, "
          "drive accelerates total mass")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  matplotlib missing; no plots")
        return
    cols = {"a: main.cc instant": "#dc2626", "b: trapezoid ramp": "#2563eb", "c: slower instant": "#16a34a"}
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for pname, prof in PROFILES.items():
        r = res[(pname, "mid")]
        c = cols[pname]
        ax1.plot(r["t"], r["xc"] * 100, color=c, lw=1.0, ls="--", alpha=0.7)
        ax1.plot(r["t"], r["x"] * 100, color=c, lw=1.6, label=f"{pname} ({prof['name_extra']})")
        ax2.plot(r["t"], r["a_lp"], color=c, lw=1.3)
    ax1.set_ylabel("cart position (cm)"); ax1.set_title("Bear cart v2, mid mass: sim (solid) vs commanded (dashed)")
    ax1.legend(frameon=False, fontsize=8, loc="upper right")
    ax2.set_ylabel(f"cart accel, LP {TIP_LP_HZ:g} Hz (m/s²)"); ax2.set_xlabel("time (s)")
    a_tip = res[next(iter(res))]["a_tip"]
    for s in (1, -1):
        ax2.axhline(s * a_tip, color="#64748b", lw=1, ls=":")
    ax2.text(0.01, a_tip, " tip threshold", color="#64748b", fontsize=8, va="bottom")
    for ax in (ax1, ax2):
        ax.grid(alpha=0.3)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "cart_sim_v2.png"), dpi=120); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    for md in modes["modes"]:
        ax.axvspan(md["f_low"], md["f_high"], color="#f59e0b", alpha=0.12)
        ax.text(md["f_mid"], 1.15, md["name"], rotation=90, fontsize=7, ha="center", va="bottom",
                transform=ax.get_xaxis_transform(), clip_on=False)
    for lo, hi in modes["forbidden_bands_hz"]:
        ax.axvspan(lo, hi, facecolor="none", edgecolor="#b91c1c", hatch="//", lw=0, alpha=0.5)
    for pname, prof in PROFILES.items():
        r = res[(pname, "mid")]
        m = (r["f"] >= 0.1) & (r["f"] <= 1000)
        ax.loglog(r["f"][m], r["S"][m], color=cols[pname], lw=1.0, label=f"{pname} sim")
        Sc = cmd_specs[pname]
        ax.loglog(fgrid, Sc * DT_REC / DT_REC * (r["S"][m].max() / max(Sc.max(), 1e-12)), color=cols[pname],
                  lw=0.7, ls=":", alpha=0.8)
    ax.set_xlim(0.1, 1000)
    ax.set_xlabel("frequency (Hz)"); ax.set_ylabel("|A(f)| cart accel (m/s), mid mass")
    ax.set_title("Excitation spectrum: sim (solid), commanded step train (dotted, scaled); "
                 "modes shaded, forbidden hatched", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="lower right"); ax.grid(alpha=0.3, which="both")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "spectrum.png"), dpi=120); plt.close(fig)
    print(f"\n  plots -> {HERE}/cart_sim_v2.png, {HERE}/spectrum.png")


if __name__ == "__main__":
    main()
