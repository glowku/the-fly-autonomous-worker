"""ASCII art de mouches — variations infinies, esthétique cyberpunk."""
import random

# Fragments pour construire des mouches uniques
WINGS = [
    r"  /\\   /\\  ",
    r" //\\\\_//\\\\ ",
    r"  (~)   (~)  ",
    r"  ⌐╦╦═─ ═╦╦¬",
    r"  ◤◥   ◤◥  ",
]

BODY = [
    r"   \_ _/     ",
    r"   (o o)     ",
    r"   /|_|\     ",
    r"   <|•|>     ",
    r"   \\|/      ",
]

LEGS = [
    r"   /   \  ",
    r"  //   \\ ",
    r"  ⌇ ⌇ ⌇ ⌇ ",
    r"  |_| |_| ",
]

TAILS = [
    r"  ~~bzzz~~",
    r"  •·.·´¯`·.·•",
    r"  ⟨⟨⟨⟨⟨⟨⟨⟨⟨",
    r"  ═══════",
    r"  …zZZ…",
]

TAGS = ["bzzz", "fly", "insect", "autonomous", "worker", "commit"]

def generate_fly(seed=None):
    """Génère une mouche ASCII unique."""
    rng = random.Random(seed)
    lines = [
        rng.choice(WINGS),
        rng.choice(BODY),
        rng.choice(LEGS),
        rng.choice(TAILS),
    ]
    # Ajout d'un tag signature sur une ligne aléatoire
    tag_line = rng.randint(0, len(lines) - 1)
    tag = rng.choice(TAGS)
    lines[tag_line] = lines[tag_line] + "  " + tag
    return "\n".join(lines)

def render_commit_panel(fly, metrics):
    """Encadre la mouche avec un HUD cyberpunk."""
    return f"""
╔══════════════════════════════════════════════════╗
║  THE FLY · AUTONOMOUS WORKER                      ║
╠══════════════════════════════════════════════════╣
║ {fly.split(chr(10))[0]:<48} ║
║ {fly.split(chr(10))[1]:<48} ║
║ {fly.split(chr(10))[2]:<48} ║
║ {fly.split(chr(10))[3]:<48} ║
╠══════════════════════════════════════════════════╣
║  state: {metrics['state']:<8}  ·  latent: {metrics['latent']:>4}ms       ║
║  lead_time: {metrics['lead_time']:<10}  ·  ttfr: {metrics['ttfr']:<8}   ║
║  batch: {metrics['batch']:<4}  ·  hawkes_t: {metrics['t']:>6.1f}min      ║
╚══════════════════════════════════════════════════╝
"""