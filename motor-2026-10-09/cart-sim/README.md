# cart-sim v2 (structural + casters)

`cart_sim.py` is now v2. v1 is kept unchanged in `cart_sim_v1.py` (its notes follow below).

## Run v2
```
python3 cart_sim.py                          # 3 profiles x low/mid/high mass + rear-load sweep, ~45 s
python3 cart_sim.py --ramp 0.5 --slow-rate 100   # change profile b ramp time / profile c step rate
```
Needs Python 3, numpy, matplotlib. Writes `cart_sim_v2.png` (position + low-passed accel, mid mass) and `spectrum.png` (cart-accel FFT, mode bands shaded, forbidden bands hatched). Full output of the last run: `run_v2.log`.

## Inputs and where they come from
| input | file | fallback |
|---|---|---|
| item masses low/mid/high, buffer (`buffer_X` item or `buffer_kg`, never both) | `masses.json` (agent B) | `DEFAULT_MASSES` |
| rear_load_frac per level (`rear_wheel_load_frac_est`), cart CoM `cog_h_m_<level>`, `wheelbase_m` | `masses.json` | PARAMS: 0.5, 0.52 m, 0.66 m |
| modes (f_low/mid/high, damping), forbidden_bands_hz, cog_height_m, base_halfwidth_m, tip_accel_ms2 | `modes.json` (agent A) | `DEFAULT_MODES` |
| motor, gearbox, wheel, mu, crr | PARAMS (v1) | - |
| caster_trail 2.5 cm, caster_patch_r 1 cm, swivel travel 2 trails, lateral factor 1 | PARAMS (GUESS) | - |

The run prints `=== INPUT FILES ===` with `json` or `default` for every key.

## What v2 computes
- **Profiles:** (a) main.cc, 200 steps @250/s, instant start; (b) trapezoid, same 200 steps, 0.3 s ramp; (c) instant start @125/s. 1 s pauses, reverse.
- **Drive:** v1 rotor + cart model with wheel slip. Traction = mu x N_rear only. The drive accelerates the total mass. Load transfer: N_rear = m(g f_rear + a h_cg / L), so accelerating forward loads the rear wheels and braking or reversing unloads them.
- **Casters:** on each reversal the front casters scrub through 180 deg. Resistance = mu N_front r_patch / trail, sine-shaped over 2 x trail of travel. The lateral kick has the same size (worst case: both casters swing to the same side). If the cart moves less than 2 x trail, the casters never finish the swivel, and the swivel-resisted direction stays the weak one.
- **Spectrum:** the exact spectrum of the step-quantized commanded motion, plus an FFT of the simulated cart acceleration. Dominant peaks are listed and checked against the forbidden bands.
- **Structure:** each mode at f_low, f_mid and f_high is a 1-DOF base-excited oscillator (Newmark) driven by the simulated cart acceleration. The run reports peak relative displacement, absolute acceleration, and DAF (relative to cart acceleration low-passed at 10 Hz).
- **Tipping:** margin = tip_accel / max(cart accel low-passed at 10 Hz, modes <= 10 Hz), checked fore-aft and lateral (caster kick). Below 1, the stack tips.

## Results (final run, both JSON files present, mid mass 44.5 kg, rear frac 0.40)
| profile | fwd / rev travel (cmd 3.64 cm) | worst mode (all f) | tip margin fore-aft | caster lateral kick | tip margin lateral |
|---|---|---|---|---|---|
| a main.cc 250/s instant | 0.00 / 0.08 cm (stall) | rotor midband @180 Hz, 5.8 m/s^2 | 1.64 | 0.02 m/s^2 | >10 |
| b 0.3 s ramp | 0.55 / 3.52 cm | rotor midband @236 Hz, 8.1 m/s^2 | **0.84** | 0.60 m/s^2 | 2.03 |
| c 125/s instant | 0.00 / 0.56 cm | drivetrain spring @23 Hz, 4.9 m/s^2 | 3.60 | 0.01 m/s^2 | >10 |

Rear-load sweep (mid mass, fwd/rev cm): with profile b, forward travel goes 0.03 / 0.55 / 0.79 / 1.16 / 1.59 for rear_frac 0.3 / 0.4 / 0.5 / 0.6 / 0.7, and reverse travel stays about 3.5. Profiles a and c stall at every split. See `run_v2.log` for low and high mass, the spectra, the per-mode table and the forbidden-band flags. Every profile puts excitation in a forbidden band: 250 steps/s sits in the 150-330 Hz rotor band, 125 steps/s rings the 15-40 Hz drivetrain band, and the reversal-rate harmonics fall in 0.5-6 Hz.

---

# cart-sim v1 (rev 2): the Barnaby bear cart on a geared stepper

This simulates the bear cart running the drive profile in `franky-fedbear/main.cc`. The profile is 200 full steps at 2 ms high + 2 ms low each, starting instantly with no ramp. It then pauses 1 s, runs the same steps in reverse, pauses 1 s and repeats.

The drive is two 17HS15-1684S-PG5 geared NEMA17 motors (5.18:1), each turning a 6 cm WHEELTEC wheel. There are **two driven rear wheels, mounted mirrored**, and casters carry the rest of the load. The 1-driven-wheel case is a footnote only.

## Run
```
python3 cart_sim.py          # runs all cases, sensitivity, the 2-DOF time-domain sim, and writes cart_sim.png (~4 s)
python3 cart_sim.py --no-dyn # analytic results only
```
Needs Python 3 and matplotlib (optional, used only for the plot).

## Edit
- **PARAMS:** physical inputs, as `(value, unit, source, note)`.
- **MASS:** low, mid and high mass for each part.
- **CASES:** driven-wheel count and the share of weight on the driven wheels.

When you measure a value, change it and set its source to `"user"`.

## Checks
- **cruise:** rolling resistance against torque at 250 steps/s.
- **start1:** reaches full speed within one step (worst case).
- **startL:** the rotor may trail the command by up to 2 steps. The verdict uses this one.
- **pullin:** start-stop rate with the load inertia.
- **slip:** at cruise and at start.
- **spinW:** whether the motor can spin a slipping wheel and so keep sync.
- **gearbox:** output torque checked against the gearbox limits (2 N·m continuous, 4 N·m peak).
- **time-domain sim:** wheel slip is allowed, so it can show partial travel.

## GUESS values
| param | value | meaning |
|---|---|---|
| current_limit | 1.25 A | trim-pot setting, range 1.0–1.5 A; Vref not measured |
| zero_torque_rate | 1500 steps/s | linear torque-speed falloff, from V/(2LI) |
| rotor_inertia | 43 g·cm² | rotor plus gearbox input; not published |
| unloaded_pullin | 1000 steps/s | start-stop rate with no load |
| wheel_inertia | 3e-5 kg·m² | per driven wheel |
| crr / mu | 0.05 / 0.6 | carpet rolling resistance / tyre grip |
| driven_load_frac | 0.33 | share of weight on the 2 driven wheels |
| ball / dolly / wood / bear-high | see MASS | ball estimated from EPS density × volume |

## Measure first
1. **Weight on the driven wheels** (bathroom scale under one rear wheel). This sets slip, and slip decides whether the cart moves at all.
2. **Total mass.** You do not have to weigh the bear: weigh the cart with the ball and estimate the rest.
3. **Vref on each driver, plus the chip marking** to tell A4988 from DRV8825. Current limit is Vref × 2 for a DRV8825 and about Vref / 0.8 (0.1 Ω sense) for an A4988. Clones vary.
4. **Wheel diameter**, measured exactly.
5. **Gear ratio**: count output turns for 1000 steps.

The code levers rank alongside these: adding an acceleration ramp, or a longer `STEP_DELAY_US`, is the cheapest fix.
