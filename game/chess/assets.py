import pygame
import os

pygame.init()

# Racine du projet : game/chess/ → game/ → PokeChess/
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PIECES_DIR = os.path.join(_ROOT, "game", "assets", "images", "chess", "pieces")
UI_DIR     = os.path.join(_ROOT, "game", "assets", "images", "chess")

TAILLE_CASE = 80
WIDTH, HEIGHT = 1400, 900

if pygame.display.get_surface() is None:
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("PokeChess — Échecs")
else:
    screen = pygame.display.get_surface()

BACKGROUND = pygame.image.load(os.path.join(UI_DIR, "bg_chess.png")).convert_alpha()
BACKGROUND = pygame.transform.smoothscale(BACKGROUND, (WIDTH, HEIGHT))

pokeball = pygame.image.load(os.path.join(UI_DIR, "pokeball.png"))
pokeball = pygame.transform.smoothscale(pokeball, (30, 30))

TYPES = {
    "normal": {"p": "rattata", "r": "normal_r", "n": "normal_n", "b": "normal_b", "q": "normal_q", "k": "normal_k"},
    "feu":    {"p": "rattata", "r": "reptincelle", "n": "galopa_f", "b": "salameche", "q": "drakofeu",  "k": "drakofeu"},
    "eau":    {"p": "rattata", "r": "carabaffe",   "n": "galopa_e", "b": "carapuce",  "q": "tortank",   "k": "tortank"},
    "plante": {"p": "rattata", "r": "herbizarre",  "n": "galopa_h", "b": "bulbizarre","q": "florizarre","k": "florizarre"},
}

AVANTAGES = {
    "feu":    ["plante"],
    "plante": ["eau"],
    "eau":    ["feu"],
    "normal": [],
}

EFFETS_DE_STATUT = {
    "feu":    "brulure",
    "plante": "poison",
    "eau":    "confusion",
}


def _to_grayscale(surf):
    gray = surf.copy()
    for y in range(surf.get_height()):
        for x in range(surf.get_width()):
            r, g, b, a = surf.get_at((x, y))
            if a > 0:
                lum = int(0.299 * r + 0.587 * g + 0.114 * b)
                gray.set_at((x, y), (lum, lum, lum, a))
    return gray


def load_images():
    images = {}
    noms = ["rattata", "reptincelle", "salameche", "drakofeu",
            "carapuce", "carabaffe", "tortank",
            "galopa_f", "galopa_e", "galopa_h",
            "bulbizarre", "herbizarre", "florizarre"]
    for nom in noms:
        img = pygame.image.load(os.path.join(PIECES_DIR, f"{nom}.png")).convert_alpha()
        images[nom] = pygame.transform.smoothscale(img, (TAILLE_CASE, TAILLE_CASE))
    images["normal_r"] = _to_grayscale(images["reptincelle"])
    images["normal_n"] = _to_grayscale(images["galopa_f"])
    images["normal_b"] = _to_grayscale(images["salameche"])
    images["normal_q"] = _to_grayscale(images["drakofeu"])
    images["normal_k"] = _to_grayscale(images["drakofeu"])
    return images


IMAGES = load_images()
font = pygame.font.SysFont(None, 30)
