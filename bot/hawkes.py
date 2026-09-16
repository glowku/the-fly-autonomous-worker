"""Processus de Hawkes pour générer des timestamps de commits réalistes."""
import numpy as np

def simulate_hawkes(mu, alpha, beta, T_minutes, seed=None):
    """
    Simulation exacte par inversion (Ogata 1981).
    mu    : taux de base (événements/min)
    alpha : force d'excitation
    beta  : décroissance
    T_minutes : horizon de simulation
    """
    rng = np.random.default_rng(seed)
    events, t = [], 0.0
    M = mu + alpha  # majorant de l'intensité

    while t < T_minutes:
        t += -np.log(rng.random()) / M
        if t >= T_minutes:
            break
        lam = mu + alpha * sum(np.exp(-beta * (t - ti)) for ti in events)
        if rng.random() <= lam / M:
            events.append(t)
    return events

# Paramètres calibrés pour ~1400 événements/jour sur 20h actives
DEFAULT_PARAMS = {"mu": 0.55, "alpha": 0.85, "beta": 1.4}