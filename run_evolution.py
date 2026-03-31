"""
KAIROS v3 - Full Evolution Run with Analysis

Runs the self-modifying equation through multiple market regimes,
lets it evolve, and analyzes what it discovered about itself.
"""

import numpy as np
from collections import Counter
from kairos_equation_v3 import (
    KairosEquationV3, MarketState, SyntheticMarket, PhiHierarchy,
    Regime, REGIME_NAMES, PHI, PHI_INV, PHI_SQ, SQRT5
)
from kairos_self_modification import (
    KairosEvolutionEngine, create_self_evolving_kairos
)


class RichSyntheticMarket(SyntheticMarket):
    """Enhanced market with crash events, mean-reversion, and trending phases."""

    def __init__(self, seed=42):
        super().__init__(seed)
        self._crash_cooldown = 0
        self._trend_direction = 0.0
        self._trend_strength = 0.0

    def step(self) -> MarketState:
        self.t += 1
        self._regime_phase += 0.01

        # Regime cycling with distinct phases
        phase = self._regime_phase
        cycle_pos = phase % (2 * np.pi * PHI)

        # Phase 1: Quiet accumulation (OMEGA/DELTA)
        # Phase 2: Trend formation (TAU/PSI)
        # Phase 3: Strong trend (SIGMA)
        # Phase 4: Exhaustion and crash (XI/KAPPA)
        normalized_pos = (cycle_pos / (2 * np.pi * PHI))

        if normalized_pos < 0.3:
            # Quiet phase
            base_vol = 0.008 + 0.005 * self.rng.rand()
            drift = 0.0001 * self.rng.randn()
            sync = 0.2 + 0.15 * self.rng.rand()
        elif normalized_pos < 0.55:
            # Trending phase
            base_vol = 0.015 + 0.01 * self.rng.rand()
            drift = 0.002 * (1 if np.sin(phase) > 0 else -1)
            sync = 0.5 + 0.2 * np.sin(phase * PHI)
        elif normalized_pos < 0.8:
            # Strong trend / sweet spot
            base_vol = 0.025 + 0.015 * self.rng.rand()
            drift = 0.004 * np.sign(np.sin(phase))
            sync = PHI_INV + 0.1 * self.rng.randn()  # Near golden sweet spot
        else:
            # Crash / volatility spike
            base_vol = 0.05 + 0.04 * self.rng.rand()
            drift = -0.008 * self.rng.rand()
            sync = 0.1 + 0.3 * self.rng.rand()

        # Random crash events (5% chance)
        if self.rng.rand() < 0.05 and self._crash_cooldown <= 0:
            base_vol *= 3.0
            drift = -0.02 * self.rng.rand()
            self._crash_cooldown = 20
        self._crash_cooldown = max(0, self._crash_cooldown - 1)

        shock = self.rng.randn() * base_vol
        ret = drift + shock
        self.price *= np.exp(ret)

        # Derived observables
        corr_time = PHI_INV + 0.3 * np.cos(phase * PHI) + 0.1 * self.rng.randn()
        net_risk = np.clip(0.2 + 0.5 * (base_vol / 0.05), 0, 1)
        delta = ret * 10 + 0.1 * self.rng.randn()

        return MarketState(
            price=self.price,
            log_return=ret,
            volatility=max(base_vol, 0.001),
            sync_ratio=np.clip(sync, 0, 1),
            correlation_time=max(0, corr_time),
            network_risk=net_risk,
            delta_val=delta,
            volume=0.3 + 0.7 * self.rng.rand(),
            momentum=ret * 20,
        )


def analyze_evolution(kairos, engine, log):
    """Deep analysis of what the equation discovered."""

    print("\n" + "=" * 72)
    print("  EVOLUTION ANALYSIS - What Did The Equation Learn?")
    print("=" * 72)

    # --- 1. Parameter Trajectory ---
    print("\n  1. PARAMETER TRAJECTORY")
    print("  " + "-" * 40)

    initial_phi = PhiHierarchy()
    h = kairos.phi_h

    params = [
        ("alpha1 (Kuramoto)", initial_phi.alpha1, h.alpha1),
        ("alpha2 (SOC)", initial_phi.alpha2, h.alpha2),
        ("alpha3 (Network)", initial_phi.alpha3, h.alpha3),
        ("alpha4 (Catastrophe)", initial_phi.alpha4, h.alpha4),
        ("mu1 (well pos 1)", initial_phi.mu1, h.mu1),
        ("mu2 (well pos 2)", initial_phi.mu2, h.mu2),
        ("beta (SOC decay)", initial_phi.beta, h.beta),
        ("tau_c (crit time)", initial_phi.tau_c, h.tau_c),
        ("zeta (well depth)", initial_phi.zeta, h.zeta),
    ]

    for name, initial, final in params:
        change_pct = ((final - initial) / max(abs(initial), 1e-8)) * 100
        arrow = ">>>" if abs(change_pct) > 20 else "-->" if abs(change_pct) > 5 else "~~ "
        print(f"    {arrow} {name:<25} {initial:.6f} -> {final:.6f} ({change_pct:+.1f}%)")

    # --- 2. Alpha Sum Evolution (sqrt(5) invariant) ---
    print(f"\n  2. GOLDEN RATIO INVARIANT")
    print("  " + "-" * 40)
    alpha_sums = [g['alpha_sum'] for g in log]
    print(f"    Target (sqrt 5):  {SQRT5:.6f}")
    print(f"    Start:            {alpha_sums[0]:.6f}")
    print(f"    Final:            {alpha_sums[-1]:.6f}")
    print(f"    Min during run:   {min(alpha_sums):.6f}")
    print(f"    Max during run:   {max(alpha_sums):.6f}")
    drift = abs(alpha_sums[-1] - SQRT5)
    print(f"    Final drift:      {drift:.6f} ({drift/SQRT5*100:.2f}%)")

    # --- 3. Fitness Evolution ---
    print(f"\n  3. FITNESS EVOLUTION")
    print("  " + "-" * 40)
    fitnesses = [g['fitness'] for g in log]
    n = len(fitnesses)
    q1 = fitnesses[:n//4]
    q2 = fitnesses[n//4:n//2]
    q3 = fitnesses[n//2:3*n//4]
    q4 = fitnesses[3*n//4:]

    print(f"    Quarter 1 (early):  mean={np.mean(q1):.4f} std={np.std(q1):.4f}")
    print(f"    Quarter 2:          mean={np.mean(q2):.4f} std={np.std(q2):.4f}")
    print(f"    Quarter 3:          mean={np.mean(q3):.4f} std={np.std(q3):.4f}")
    print(f"    Quarter 4 (late):   mean={np.mean(q4):.4f} std={np.std(q4):.4f}")
    print(f"    Overall best:       {max(fitnesses):.4f} (gen {fitnesses.index(max(fitnesses))})")
    print(f"    Overall worst:      {min(fitnesses):.4f} (gen {fitnesses.index(min(fitnesses))})")

    improvement = np.mean(q4) - np.mean(q1)
    print(f"    Q4 vs Q1 change:   {improvement:+.4f} "
          f"({'IMPROVED' if improvement > 0 else 'DEGRADED'})")

    # --- 4. Regime Boundary Evolution ---
    print(f"\n  4. EVOLVED REGIME BOUNDARIES")
    print("  " + "-" * 40)
    original_bounds = [0.0, PHI_INV**3, PHI_INV**2, PHI_INV, 1.0, PHI, PHI_SQ]
    evolved_bounds = list(h.regime_boundaries[:-1])

    for i, (orig, evol) in enumerate(zip(original_bounds, evolved_bounds)):
        if i < len(list(Regime)):
            rname = REGIME_NAMES[Regime(i)]
        else:
            rname = "---"
        shift = evol - orig
        print(f"    {rname:<22} {orig:.4f} -> {evol:.4f} (shift {shift:+.4f})")

    # --- 5. Temperature Exponents ---
    print(f"\n  5. EVOLVED TEMPERATURE EXPONENTS (T = sigma * phi^-n)")
    print("  " + "-" * 40)
    original_n = {
        Regime.OMEGA: 0.0, Regime.DELTA: 1.0, Regime.TAU: PHI_INV,
        Regime.PSI: PHI_INV**2, Regime.SIGMA: -PHI_INV,
        Regime.XI: -1.0, Regime.KAPPA: -PHI,
    }
    for regime in Regime:
        orig = original_n[regime]
        evol = kairos._n_exponents[regime]
        print(f"    {REGIME_NAMES[regime]:<22} n: {orig:.4f} -> {evol:.4f}")
        if evol != orig:
            # What this means for temperature
            T_scale_orig = PHI ** (-orig)
            T_scale_evol = PHI ** (-evol)
            print(f"      T multiplier: {T_scale_orig:.4f} -> {T_scale_evol:.4f} "
                  f"({'more cautious' if T_scale_evol > T_scale_orig else 'more decisive'})")

    # --- 6. Learned Potential ---
    print(f"\n  6. LEARNED POTENTIAL CORRECTION")
    print("  " + "-" * 40)
    weights = kairos._V_learned_weights
    norm = np.linalg.norm(weights)
    print(f"    Weight vector norm: {norm:.6f}")
    if norm > 1e-6:
        centers = kairos._V_learned_centers
        peak_idx = np.argmax(np.abs(weights))
        print(f"    Strongest correction at energy = {centers[peak_idx]:.4f}")
        print(f"    Correction magnitude: {weights[peak_idx]:.6f}")
        print(f"    Interpretation: {'increase risk aversion' if weights[peak_idx] > 0 else 'decrease risk aversion'}"
              f" at H ~ {centers[peak_idx]:.3f}")
    else:
        print(f"    (minimal learned correction - phi-derived landscape sufficient)")

    # --- 7. Learning Rate Evolution ---
    print(f"\n  7. META-LEARNING: Learning Rate Evolution")
    print("  " + "-" * 40)
    initial_lrs = {
        'phi_hierarchy': 0.001, 'V_learned': 0.005,
        'bayesian': 0.01, 'regime_bounds': 0.0005, 'meta': 0.0001
    }
    for key in kairos._learning_rates:
        orig = initial_lrs[key]
        evol = kairos._learning_rates[key]
        ratio = evol / orig
        print(f"    {key:<20} {orig:.6f} -> {evol:.6f} ({ratio:.1f}x)")

    # --- 8. Regime Distribution ---
    print(f"\n  8. REGIME DISTRIBUTION (across all generations)")
    print("  " + "-" * 40)
    if kairos.regime_history:
        counts = Counter(kairos.regime_history)
        total = sum(counts.values())
        for regime in Regime:
            count = counts.get(regime, 0)
            pct = count / total * 100
            bar = "#" * int(pct / 2)
            print(f"    {REGIME_NAMES[regime]:<22} {count:5d} ({pct:5.1f}%) {bar}")

    # --- 9. Convergence Behavior ---
    print(f"\n  9. CONVERGENCE BEHAVIOR")
    print("  " + "-" * 40)
    drifts = [g['drift'] for g in log if g['drift'] != float('inf')]
    if drifts:
        print(f"    Initial drift:  {drifts[0]:.8f}")
        print(f"    Final drift:    {drifts[-1]:.8f}")
        print(f"    Min drift:      {min(drifts):.8f} (gen {drifts.index(min(drifts))})")
        print(f"    Max drift:      {max(drifts):.8f}")

        # Detect oscillation
        sign_changes = sum(1 for i in range(1, len(drifts))
                          if (drifts[i] - drifts[i-1]) * (drifts[i-1] - drifts[max(0,i-2)]) < 0)
        print(f"    Drift direction changes: {sign_changes}")
        if sign_changes > len(drifts) * 0.3:
            print(f"    Pattern: OSCILLATING (exploring parameter space)")
        elif drifts[-1] < drifts[0] * 0.1:
            print(f"    Pattern: CONVERGING toward fixed point")
        else:
            print(f"    Pattern: DRIFTING (still searching)")

    converged = log[-1].get('converged', False)
    print(f"    Final status: {'CONVERGED (fixed point found)' if converged else 'Still evolving'}")

    # --- 10. Key Insights ---
    print(f"\n  10. KEY INSIGHTS")
    print("  " + "=" * 40)

    # What changed most?
    changes = [(name, abs((final-initial)/max(abs(initial),1e-8)))
               for name, initial, final in params]
    changes.sort(key=lambda x: x[1], reverse=True)
    print(f"\n    Most evolved parameter:  {changes[0][0]} ({changes[0][1]*100:.1f}% change)")
    print(f"    Least evolved parameter: {changes[-1][0]} ({changes[-1][1]*100:.1f}% change)")

    # Did it maintain the golden ratio structure?
    final_alphas = [h.alpha1, h.alpha2, h.alpha3, h.alpha4]
    ratios = [final_alphas[i+1]/max(final_alphas[i], 1e-8) for i in range(3)]
    print(f"\n    Alpha ratios (ideal = phi^-1 = {PHI_INV:.4f}):")
    for i, r in enumerate(ratios):
        drift_from_phi = abs(r - PHI_INV) / PHI_INV * 100
        print(f"      alpha{i+2}/alpha{i+1} = {r:.4f} "
              f"({'preserved' if drift_from_phi < 15 else 'BROKEN'} "
              f"- {drift_from_phi:.1f}% from phi)")

    print()


def main():
    print("=" * 72)
    print("  THE KAIROS EQUATION v3")
    print("  Full Self-Evolution Run with Rich Market Dynamics")
    print("=" * 72)
    print()
    print("  The equation will trade a synthetic market with crashes,")
    print("  trends, and quiet periods. After each generation it applies")
    print("  its own mathematics to evolve its parameters.")
    print()
    print("  Free parameters: capital=10000, edge_bias=0.05")
    print("  Everything else starts from phi and evolves.")
    print()

    kairos, engine = create_self_evolving_kairos(
        capital=10000.0,
        edge_bias=0.05,
    )
    market = RichSyntheticMarket(seed=42)

    log = engine.evolve(
        market,
        max_generations=60,
        steps_per_gen=200,
        verbose=True,
    )

    analyze_evolution(kairos, engine, log)


if __name__ == "__main__":
    main()
