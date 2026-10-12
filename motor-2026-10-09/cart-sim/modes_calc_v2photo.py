#!/usr/bin/env python3
"""v2 (photo-based) earthquake-engineer pass on the Barnaby bear cart.
LOAD PATH (from the 2026-10-09 photos + Tony's sketch, see PHOTOS.md):
  bear (hollow frame, ~6 kg) -> square steel POST (~22 mm, telescoping, wing-nut lock at ball top)
  -> post bottom with fixity = FIXITY case (fixed / pinned_gap / velcro_only)
  ball = light HOLLOW SHELL (2 halves screwed at a seam) hung on the post through a SLOT in its top,
  velcro at the feet and at the ball bottom; the slot has clearance -> impact/rattle.
Writes modes.json next to this file. All inputs (low, mid, high). Run: python3 modes_calc.py
v1 (solid EPS ball, bear resting/strapped on it) is kept as modes_v1.json / modes_calc in git history.
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
g = 9.81
TWO_PI = 2 * math.pi

def f_of(k, m):
    return math.sqrt(max(k / m, 0.0)) / TWO_PI

# ---------------- geometry (PHOTO v2 scale check, see PHOTOS.md) ----------------
H_BEAR = (1.10, 1.20, 1.30)          # feet to head top, MEASURED from photo +-0.1 m (listing 70 in includes the stand)
D_BALL = (0.42, 0.47, 0.52)          # MEASURED from photo via sugar box / sticky note rulers
H_DECK = (0.155, 0.17, 0.19)
CM_FRAC = (0.35, 0.45, 0.55)         # bear-body CoM as fraction of H_BEAR above the feet (hollow frame, motors low)
POST_SIDE = (0.019, 0.022, 0.028)    # square tube side [m], scale-estimated
POST_WALL = (0.0010, 0.0012, 0.0015)
SLOT_CLEAR_ACROSS = (0.001, 0.002, 0.004)   # m, post-to-slot clearance across the slot (rattle)
SLOT_CLEAR_ALONG = (0.05, 0.10, 0.12)       # m, free length of the slot beside the post
REAR_FRAC = 0.33
WHEELBASE = 0.66
CASTER_TRAIL = (0.03, 0.04, 0.05)
CRADLE_B = (0.08, 0.12, 0.16)        # half-width of the ball's contact ring on the wooden cradle [m], GUESS from image 1
VELCRO_PEEL_N = (5.0, 20.0, 40.0)    # peel capacity of the ball-bottom velcro at the far edge [N], GUESS (2 N/cm x 2.5-20 cm)

M = dict(bear=(5.0, 6.0, 7.5), post=(1.0, 1.5, 2.0), plate=(0.0, 1.5, 2.5), ball=(1.0, 1.5, 2.5),
         dolly=(8.79, 9.25, 9.72), wood=(1.5, 3.0, 4.5), drive=(1.4, 1.5, 1.8), fog=(1.4, 2.5, 4.5),
         solix=(4.13, 10.9, 12.9), buffer=(5.0, 5.0, 5.0), pi=(0.15, 0.3, 0.6))
mj = os.path.join(HERE, "masses.json")
masses_src = "placeholders (masses.json not present)"
if os.path.exists(mj):
    try:
        raw = json.load(open(mj))
        alias = {"dolly": "dolly", "wood": "wood", "drive": "drive", "ball": "ball", "barnaby": "bear", "post": "post",
                 "base_plate": "plate", "fog": "fog", "solix": "solix", "raspberry": "pi", "buffer": "buffer"}
        for it in raw["items"]:
            key = next((v for a, v in alias.items() if a in it["name"].lower()), it["name"].lower())
            M[key] = (float(it["kg_low"]), float(it["kg_mid"]), float(it["kg_high"]))
        geo = raw.get("geometry", {})
        if "deck_h_m_range" in geo:
            H_DECK = (geo["deck_h_m_range"][0], geo["deck_h_m"], geo["deck_h_m_range"][1])
        if "ball_d_m_range" in geo:
            D_BALL = (geo["ball_d_m_range"][0], geo["ball_d_m"], geo["ball_d_m_range"][1])
        if "bear_h_m_range" in geo:
            H_BEAR = (geo["bear_h_m_range"][0], geo["bear_h_m"], geo["bear_h_m_range"][1])
        if "post_side_m_range" in geo:
            POST_SIDE = (geo["post_side_m_range"][0], geo["post_side_m"], geo["post_side_m_range"][1])
        if "bear_com_frac_of_height" in geo:
            c = geo["bear_com_frac_of_height"]; CM_FRAC = (c["low"], c["mid"], c["high"])
        REAR_FRAC = raw.get("rear_wheel_load_frac_est", {}).get("mid", 0.33)
        WHEELBASE = geo.get("wheelbase_m", WHEELBASE)
        masses_src = "masses.json v2 (photo-based) total mid %.1f kg" % raw.get("total_kg_mid", 0)
    except Exception as e:
        masses_src = f"masses.json unreadable ({e}); placeholders"

CART_B_LONG, CART_B_TRANS = 0.33, 0.20   # half wheelbase / half track (masses.json: 0.66 / 0.40 m)
IDX = {"low": 0, "mid": 1, "high": 2}
E_STEEL = 200e9

def post_EI(i):
    s, t = POST_SIDE[i], POST_WALL[i]
    I = (s**4 - (s - 2 * t)**4) / 12
    return E_STEEL * I, I

def stack(level):
    """bear body + post + shell above the deck (base plate excluded: it is at deck level)."""
    i = IDX[level]
    R = D_BALL[i] / 2
    h_bear = D_BALL[i] + CM_FRAC[i] * H_BEAR[i]          # bear-body CoM above deck
    h_post = 0.5 * (D_BALL[i] + 0.45 * H_BEAR[i])         # post from deck to crotch, CoM at mid-height
    L_post = D_BALL[i] + 0.45 * H_BEAR[i]                 # post length deck -> crotch
    mb, mp, ms = M["bear"][i], M["post"][i], M["ball"][i]
    m = mb + mp + ms
    h_cm = (mb * h_bear + mp * h_post + ms * R) / m
    I_base = mb * h_bear**2 + mp * L_post**2 / 3 + ms * (2 / 3 * R * R + R * R)   # about deck contact line; thin shell 2/3 m R^2
    I_bear_post = mb * h_bear**2 + mp * L_post**2 / 3       # bear + post alone about the post bottom
    return dict(m=m, h_cm=h_cm, h_bear=h_bear, I=I_base, I_bp=I_bear_post, R=R, L_post=L_post, m_bp=mb + mp,
                h_bp=(mb * h_bear + mp * h_post) / (mb + mp))

def whole_cart(level):
    i = IDX[level]
    hd = H_DECK[i]
    s = stack(level)
    parts = [("bear", hd + s["h_bear"]), ("post", hd + s["L_post"] / 2), ("plate", hd + 0.01), ("ball", hd + s["R"]),
             ("dolly", 0.10), ("wood", hd - 0.02), ("drive", 0.05), ("fog", hd + 0.12), ("solix", hd + 0.12),
             ("buffer", hd + 0.15), ("pi", hd + 0.05)]
    mt = sum(M[n][i] for n, _ in parts)
    h = sum(M[n][i] * z for n, z in parts) / mt
    return dict(m=mt, h_cm=h)

# ---------------- natural frequencies ----------------
modes = []
def add(name, lo, mid, hi, zeta, basis):
    modes.append(dict(name=name, f_low_hz=round(lo, 2), f_mid_hz=round(mid, 2), f_high_hz=round(hi, 2),
                      damping=zeta, basis=basis))

# M1 bear on post, post bottom FIXED: cantilever to the bear CoM, gravity-softened, telescoping-joint factor
sway_fixed = []
for lvl, joint in [("low", 0.5), ("mid", 0.75), ("high", 1.0)]:
    i = IDX[lvl]; s = stack(lvl)
    EI, _ = post_EI(i)
    L = s["h_bear"]
    k = 3 * EI / L**3 * joint
    m_eff = M["bear"][i] + 0.24 * M["post"][i]
    w2 = k / m_eff - g / L
    sway_fixed.append(math.sqrt(max(w2, 0.01)) / TWO_PI)
# low/mid/high of the inputs do not sort the frequency monotonically (stiff small post vs tall bear); sort them
sway_fixed.sort()
add("bear_on_post_sway_FIXED_base", sway_fixed[0], sway_fixed[1], sway_fixed[2], 0.03,
    "post bottom bolted to deck/base plate: steel square tube %.0f mm x %.1f mm wall (EI=%.0f N m2) cantilever to bear CoM L=%.2f m, m_eff=bear+0.24 post, x0.5-1.0 for the wing-nut telescoping joint, gravity softening -g/L. PHOTO v2" % (
        POST_SIDE[1] * 1e3, POST_WALL[1] * 1e3, post_EI(1)[0], stack("mid")["h_bear"]))

# M2 bear on post, post bottom PINNED WITH GAP: rotation restrained only by the shell at the slot + feet velcro
sway_pin = []
for lvl, k_shell in [("low", 1e3), ("mid", 3e3), ("high", 8e3)]:
    i = IDX[lvl]; s = stack(lvl)
    k_th = k_shell * D_BALL[i]**2 - s["m_bp"] * g * s["h_bp"]
    sway_pin.append(f_of(k_th, s["I_bp"]))
add("bear_on_post_sway_PINNED_gap", max(sway_pin[0], 0.3), sway_pin[1], sway_pin[2], 0.05,
    "post bottom captive but free to rotate through the gap; restoring stiffness only from the hollow shell at the slot edge + feet velcro, k=1-8 kN/m at r=ball diameter, minus m g h of bear+post. Amplitude-dependent: inside the gap the stiffness is ZERO and the post hits the slot edge (impact). PHOTO v2 + sketch 'gap'")

# M3 whole stack (bear+post+shell) rocking on the cradle/velcro, post bottom in NOTHING (velcro only)
rock_v = []
for lvl, k_lin in [("low", 2e3), ("mid", 6e3), ("high", 15e3)]:
    i = IDX[lvl]; s = stack(lvl)
    k_th = 2 * k_lin * CRADLE_B[i]**2 - s["m"] * g * s["h_cm"]
    rock_v.append(f_of(k_th, s["I"]))
add("stack_rocking_VELCRO_only", max(rock_v[0], 0.3), max(rock_v[1], 0.3), rock_v[2], 0.08,
    "bear+post+shell as one rigid body on the ball-bottom velcro/cradle springs, k=2-15 kN/m at r=%.2f m minus m g h_cm; k_th<=0 (statically unstable, only velcro peel holds it) for the soft case -> floored at 0.3 Hz. PHOTO v2 sketch 'velcro' at ball bottom" % CRADLE_B[1])

# M4 post rattling across the slot clearance (impact mode on the shell wall)
add("post_in_slot_rattle_impact", 6.0, 10.0, 25.0, 0.10,
    "post hits the slot edge across %.0f-%.0f mm clearance; hollow shell local stiffness 3-20 kN/m vs ~3 kg effective post+bear mass at the slot -> 6-25 Hz, strongly nonlinear (impact, chatter), excited by every start/stop and by cart pitch. SEEN slot clearance" % (SLOT_CLEAR_ACROSS[0] * 1e3, SLOT_CLEAR_ACROSS[2] * 1e3))

# M5 hollow shell ovalling / seam flap
add("ball_shell_ovalling_seam", 15.0, 30.0, 60.0, 0.05,
    "thin hollow sphere ~0.47 m, two halves screwed at a seam: ovalling/seam-flap modes 15-60 Hz (ASSUMED wall 2-5 mm plastic/paper-mache); excited by 250 Hz step buzz subharmonics and by the post rattle; drums (noise), fatigue at the screw holes")

# cart modes (same formulas as v1, lighter cart)
bounce = [f_of(15e3 * 6, whole_cart("high")["m"]), f_of(25e3 * 6, whole_cart("mid")["m"]), f_of(40e3 * 6, whole_cart("low")["m"])]
add("cart_bounce_vertical", bounce[0], bounce[1], bounce[2], 0.08,
    "6 contacts, caster PU + carpet/pad in series 15-40 kN/m each; m = whole cart v2 (%.0f-%.0f kg)" % (whole_cart("low")["m"], whole_cart("high")["m"]))
add("cart_pitch_roll_on_casters", bounce[0] * 0.7, bounce[1] * 0.8, bounce[2] * 0.9, 0.08,
    "same springs, rotational: f_rot ~ 0.7-0.9 f_bounce (ASSUMED)")
add("cart_horizontal_on_carpet", f_of(5e3 * 6, whole_cart("high")["m"]), f_of(12e3 * 6, whole_cart("mid")["m"]),
    f_of(25e3 * 6, whole_cart("low")["m"]), 0.10, "tyre sidewall + carpet pile shear 5-25 kN/m per contact, 6 contacts; stick-slip")

T_h = 0.36 * 0.707 * (1.25 / 1.68)
k_m = T_h * 50
J_rot = 43e-7
def J_load(mass, G=5.18, eta=0.9, r=0.03, n=2, Jw=3e-5):
    return (Jw + (mass / n) * r * r) / (G * G * eta)
loaded = [f_of(k_m * 0.8, J_rot + J_load(whole_cart("high")["m"])), f_of(k_m, J_rot + J_load(whole_cart("mid")["m"])),
          f_of(k_m * 1.3, J_rot + J_load(whole_cart("low")["m"]))]
add("drivetrain_loaded_stepper_spring", loaded[0], loaded[1], loaded[2], 0.03,
    "rotor + cart mass (via r^2/G^2) on the stepper's magnetic spring k=T_h*50 (T_h=0.21 Nm at 1.25 A)")
unl = [f_of(k_m * 0.7, J_rot * 1.2), f_of(k_m, J_rot), f_of(k_m * 1.4, J_rot * 0.85)]
add("stepper_rotor_midband_resonance", unl[0], unl[1], unl[2], 0.02,
    "rotor alone: f=(1/2pi)sqrt(k_m/J_rot); classic full-step resonance 100-300 Hz")

# bear sub-modes, hollow light frame (Tony)
add("arm_cantilever_hollow_frame", 1.5, 3.5, 7.0, 0.06,
    "light hollow arm (~0.3 kg eff.) on a thin rod/plastic shoulder joint, 0.45 m; one arm raised, one horizontal (SEEN) -> asymmetric, lateral CoM offset ~2-4 cm")
add("head_on_neck", 2.5, 4.5, 8.0, 0.06, "~1 kg head + jaw motor on a short neck joint, k 0.3-2.5 kN/m (ASSUMED)")
add("torso_on_dance_pivot", 0.5, 1.2, 2.5, 0.05,
    "torso ~2-3 kg at ~0.3 m above the hip pivot restrained by the dance gear train; backlash rattles (ASSUMED mechanism)")
add("caster_swivel_kinematic_trail", 0.14, 0.18, 0.24, 0.5, "f=V/(2 pi e), V=0.0455 m/s, e=3-5 cm; swivel friction ~overdamped")
add("caster_swivel_rattle_play", 8.0, 15.0, 30.0, 0.08, "swivel bearing + axle play with lateral tyre stiffness, excited at reversals and by the 250 Hz buzz")
add("cart_pitch_load_transfer", 4.0, 7.0, 12.0, 0.08, "cart pitching on the contact springs when the jerk shifts dN=m a h/L")

# ---------------- excitations (unchanged from v1 except masses) ----------------
v = 0.0455; seg = 0.8; pause = 1.0; T = 2 * seg + 2 * pause
f0 = 1 / T
mc = whole_cart("mid")["m"]
T_spd = T_h * (1 - 250 / 1500)
F_torque = 2 * T_spd * 5.18 * 0.9 / 0.03
F_torque0 = 2 * T_h * 5.18 * 0.9 / 0.03
F_trac = 0.6 * REAR_FRAC * mc * g
F_rr = 0.05 * mc * g
a_real = (min(F_torque, F_trac) - F_rr) / mc
a_real_hi = (min(F_torque0, F_trac) - F_rr) / mc
wc_mid = whole_cart("mid")
N_rear0 = REAR_FRAC * mc * g
dN = lambda a: mc * a * wc_mid["h_cm"] / WHEELBASE
load_transfer = {}
for tag, a in [("real", a_real), ("real_hi", a_real_hi)]:
    d = dN(a)
    load_transfer[tag] = dict(a_ms2=round(a, 2), dN_N=round(d, 1), rear_static_N=round(N_rear0, 1),
                              rear_frac_change=round(d / N_rear0, 2),
                              traction_fwd_accel_N=round(0.6 * (N_rear0 + d), 1), traction_rev_accel_N=round(0.6 * (N_rear0 - d), 1))
k_contact = 25e3
pitch_static_rad = (dN(a_real) / k_contact) / WHEELBASE
caster = dict(
    kinematic_mode_hz=[round(v / (TWO_PI * e), 3) for e in CASTER_TRAIL[::-1]],
    flip_distance_m=[round(math.pi * e / 2, 3) for e in CASTER_TRAIL],
    segment_travel_m=[0.001, 0.016, 0.034],
    scrub_force_per_caster_N=round(0.6 * (1 - REAR_FRAC) * mc * g / 4, 1),
    lateral_cart_accel_if_two_casters_scrub_ms2=round(2 * 0.6 * (1 - REAR_FRAC) * mc * g / 4 / mc, 2),
)
a_cmd = v / 0.004
def harm_amp(n, tau=0.0):
    w = TWO_PI * n * f0
    s = abs(1 - math.e**(-1j * w * seg) - math.e**(-1j * w * (seg + pause)) + math.e**(-1j * w * (2 * seg + pause)))
    amp = 2 * v / T * s
    if tau > 0:
        x = math.pi * n * f0 * tau
        amp *= abs(math.sin(x) / x) if x else 1
    return amp
comb = [{"n": n, "f_hz": round(n * f0, 3), "a_amp_ms2_noramp": round(harm_amp(n), 4),
         "a_amp_ms2_ramp1s": round(harm_amp(n, 1.0), 4)} for n in range(1, 25)]
excitations = [
    dict(name="segment_pattern_fundamental", f_hz=round(f0, 3), harmonics_hz=[round(n * f0, 2) for n in range(1, 25)],
         note="0.8 s on / 1 s pause / 0.8 s reverse / 1 s pause; velocity-step impulses -> flat comb to >10 Hz without a ramp", comb=comb),
    dict(name="start_stop_jerk", f_hz=None, a_cmd_ms2=round(a_cmd, 1), a_real_ms2=[round(a_real, 2), round(a_real_hi, 2)],
         note="commanded: full speed in one 4 ms step; real: torque/traction-limited (mid masses v2)"),
    dict(name="full_step_rate", f_hz=250.0, harmonics_hz=[250, 500, 750, 1000], note="1.8 deg/step; torque ripple; buzz; drums the hollow shell"),
    dict(name="stepper_midband_overlap", f_hz=250.0, note="250 steps/s inside the rotor's 170-330 Hz resonance band"),
    dict(name="gearbox_mesh", f_hz=11.1, f_range_hz=[8, 14], note="planetary ring teeth x output speed (ASSUMED tooth counts)"),
    dict(name="reversal_backlash_impact", f_hz=round(2 / T, 3), note="2 reversals per 3.6 s cycle; gearbox/hub backlash impacts AND post-in-slot impacts (v2)"),
    dict(name="post_slot_gap_closure", f_hz=None, note="NEW v2: every start/stop first moves the cart through the slot clearance (1-4 mm across, ~10 cm along!) before the shell can push the post -> impact; along the slot the shell gives NO restraint at all, only the feet velcro"),
    dict(name="carpet_stick_slip", f_hz=None, f_range_hz=[2, 30], note="tyre creep/stick on carpet"),
    dict(name="caster_flip_at_reversal", f_hz=round(2 / T, 3), note="casters never finish the 180 deg swing in a 0.1-3.4 cm segment -> scrub: ~%.0f N per caster, up to %.1f m/s2 lateral kick" % (caster["scrub_force_per_caster_N"], caster["lateral_cart_accel_if_two_casters_scrub_ms2"])),
    dict(name="longitudinal_load_transfer", f_hz=None, detail=load_transfer, note="dN=m a h_cm/L, L=%.2f m" % WHEELBASE),
    dict(name="try_me_dance_torso_sway", f_hz=0.75, f_range_hz=[0.4, 1.5], note="'torso moves side-to-side', 20 s cycle (MEASURED); sits in the sway band; with a pinned/velcro post bottom the dance itself rocks the stack"),
]

# ---------------- tipping by post-bottom FIXITY ----------------
s = stack("mid"); i = 1
EI, I_post = post_EI(i)
Z_post = I_post / (POST_SIDE[i] / 2)
M_yield = 250e6 * Z_post
a_post_yield = M_yield / (s["m_bp"] * s["h_bp"])
# velcro-only: stack rocks about the cradle contact edge b; velcro peel at the far edge adds M = F_peel * 2b
tip_velcro = {}
for lvl in ("low", "mid", "high"):
    j = IDX[lvl]; sl = stack(lvl); b = CRADLE_B[j]
    tip_velcro[lvl] = dict(b_m=b, a_tip_no_velcro=round(g * b / sl["h_cm"], 2),
                           a_tip_with_velcro_peel=round((sl["m"] * g * b + VELCRO_PEEL_N[j] * 2 * b) / (sl["m"] * sl["h_cm"]), 2))
a_tip_velcro_mid = tip_velcro["mid"]["a_tip_no_velcro"]
IMPACT_FACTOR = 2.0   # gap closure: free flight through the gap then impact -> dynamic factor ~2 on the restraint demand
fixity = {
    "fixed": dict(description="post bottom bolted/screwed to the deck or to a base plate screwed to the deck",
                  a_tip_ms2=round(min(g * CART_B_TRANS / whole_cart("mid")["h_cm"], a_post_yield), 2),
                  governing="whole-cart transverse tip (%.2f m/s2); post yield at %.1f m/s2 is not governing" % (g * CART_B_TRANS / whole_cart("mid")["h_cm"], a_post_yield),
                  sway_mode_hz=[round(x, 2) for x in sway_fixed]),
    "pinned_gap": dict(description="post bottom captive (socket/hole/base plate with play) but free to rotate through a gap; shell + velcro take the moment after the gap closes",
                       a_tip_ms2=round(tip_velcro["mid"]["a_tip_with_velcro_peel"] / IMPACT_FACTOR, 2),
                       governing="velcro/cradle tip accel divided by impact factor %.1f (gap closure); the shell wall at the slot can also crush (hollow shell, local load ~m a h / R)" % IMPACT_FACTOR,
                       sway_mode_hz=[round(x, 2) for x in sway_pin]),
    "velcro_only": dict(description="post bottom reaches nothing (sketch 'gap'); bear+post hang on the shell via the slot and feet velcro; shell held by bottom velcro on the cradle",
                        a_tip_ms2=a_tip_velcro_mid,
                        governing="rigid stack about the cradle contact edge b=%.2f m, h_cm=%.2f m; velcro peel would raise it to %.2f m/s2 but velcro fatigues under 2 Hz cyclic peel -> no credit; feet-velcro peel lets the bear+post fall THROUGH the gap" % (CRADLE_B[1], s["h_cm"], tip_velcro["mid"]["a_tip_with_velcro_peel"]),
                        sway_mode_hz=[round(max(x, 0.3), 2) for x in rock_v]),
}
tip = {k: v_["a_tip_ms2"] for k, v_ in fixity.items()}
wc = whole_cart("mid")
tip_cart = dict(longitudinal=round(g * CART_B_LONG / wc["h_cm"], 2), transverse=round(g * CART_B_TRANS / wc["h_cm"], 2))
L_ang = s["m"] * s["h_cm"] * v
ke = 0.5 * L_ang**2 / s["I"]
energy = {"velcro_only": dict(E_tip_J=round(s["m"] * g * CRADLE_B[1]**2 / (2 * s["h_cm"]), 3), KE_pulse_J=round(ke, 4),
                              single_pulse_overturns=bool(ke > s["m"] * g * CRADLE_B[1]**2 / (2 * s["h_cm"])))}
Q = {"3%": 17, "5%": 10}
a_h = max(c["a_amp_ms2_noramp"] for c in comb[2:13])
res = {}
for case, f_sw in [("fixed", sway_fixed[1]), ("pinned_gap", sway_pin[1]), ("velcro_only", max(rock_v[1], 0.3))]:
    res[case] = {z: dict(a_rel_ms2=round(q * a_h, 2), x_cm_at_com_cm=round(100 * q * a_h / (TWO_PI * f_sw)**2, 1), cycles_to_build=q)
                 for z, q in Q.items()}

DEFAULT_CASE = "velcro_only"   # most likely per Tony's sketch ('velcro' + 'gap' at the bottom); cart_sim.py uses these top-level values
forbidden = [[0.3, 6.0], [6.0, 30.0], [150.0, 330.0]]
out = dict(
    generated_by="modes_calc.py v2 (photo-based load path: bear on post, hollow shell, fixity cases)", masses_source=masses_src,
    load_path_case_used_for_tip=DEFAULT_CASE, fixity_cases=fixity,
    modes=modes, excitations=excitations,
    forbidden_bands_hz=forbidden,
    forbidden_bands_note=["0.3-6 Hz: bear-on-post sway (all fixities), stack rocking on velcro, torso pivot, arms -> no un-ramped periodic start/stop; ramp >= 1 s",
                          "6-30 Hz: post-in-slot rattle, cart bounce/pitch, gear mesh, loaded drivetrain ring -> rise times < 80 ms excite the slot impact",
                          "150-330 Hz: stepper rotor mid-band; 250 full steps/s is INSIDE; also drums the hollow shell"],
    cog_height_m=round(s["h_cm"], 3), cog_height_note="bear+post+shell stack CoM above the deck (mid, v2 photo geometry); whole cart CoM above floor = %.2f m" % wc["h_cm"],
    base_halfwidth_m=CRADLE_B[1], base_halfwidth_note="ball-on-cradle contact half-width (velcro_only / pinned_gap); fixed case has no rigid-body tip",
    tip_accel_ms2=tip[DEFAULT_CASE], tip_accel_by_case_ms2=tip, tip_velcro_detail=tip_velcro, tip_accel_whole_cart_ms2=tip_cart,
    post=dict(side_m=POST_SIDE[1], wall_m=POST_WALL[1], EI_Nm2=round(EI, 1), M_yield_Nm=round(M_yield, 1), a_yield_ms2=round(a_post_yield, 1),
              slot_clear_across_m=SLOT_CLEAR_ACROSS, slot_clear_along_m=SLOT_CLEAR_ALONG),
    jerk_accel_ms2=dict(commanded=round(a_cmd, 1), realistic_low=round(a_real, 2), realistic_high=round(a_real_hi, 2)),
    load_transfer=load_transfer, cart_pitch_static_rad=round(pitch_static_rad, 5), caster=caster,
    single_pulse_energy_check=energy,
    resonant_buildup_at_sway_mode=dict(per_harmonic_base_accel_ms2=round(a_h, 3), response_by_case=res),
    stack=dict(m_kg=round(s["m"], 2), I_base_kgm2=round(s["I"], 2), h_bear_com_m=round(s["h_bear"], 2), h_cm_m=round(s["h_cm"], 3)),
    whole_cart=dict(m_kg=round(wc["m"], 1), h_cm_m=round(wc["h_cm"], 3)),
    recommended_profile=dict(microstep=16, ramp_s=1.0, ramp_shape="S-curve (sin^2)", cruise_full_steps_per_s_max=250,
                             min_dwell_s=2.0, dwell_jitter="uniform 2-4 s, never periodic", no_drive_during_try_me=True,
                             max_segment_accel_ms2=round(min(tip.values()) / 3, 2),
                             note="keep every start/stop acceleration below 1/3 of the worst-case fixity tip accel; FIX THE POST BOTTOM FIRST (fixed case) and shim the slot"),
)
json.dump(out, open(os.path.join(HERE, "modes.json"), "w"), indent=1)
print(json.dumps({k: out[k] for k in ["cog_height_m", "tip_accel_by_case_ms2", "tip_velcro_detail", "tip_accel_whole_cart_ms2", "post",
                                      "jerk_accel_ms2", "single_pulse_energy_check", "resonant_buildup_at_sway_mode", "stack", "whole_cart", "masses_source"]}, indent=1))
for m in modes:
    print(f'{m["name"]:38s} {m["f_low_hz"]:7.2f} {m["f_mid_hz"]:7.2f} {m["f_high_hz"]:7.2f}  z={m["damping"]}')
