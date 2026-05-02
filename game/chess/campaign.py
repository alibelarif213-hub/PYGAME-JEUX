from .jeu import Jeu

COMBATS = [
    {"type_ia": "eau",    "difficulte": "Facile", "label": "Combat 1", "arene": "Arène Eau"},
    {"type_ia": "plante", "difficulte": "Facile", "label": "Combat 2", "arene": "Arène Plante"},
    {"type_ia": "feu",    "difficulte": "Facile", "label": "Combat 3", "arene": "Arène Feu"},
    {
        "type_ia": {"p": "eau", "r_g": "feu", "r_d": "plante",
                    "n_g": "plante", "n_d": "feu", "b_g": "eau", "b_d": "feu",
                    "q": "plante", "k": "eau"},
        "difficulte": "Difficile",
        "label": "Combat Final",
        "arene": "Arène Légendaire",
    },
]

PIECES_SELECTION = [
    ("p",   "Pions"),
    ("r_g", "Tour Gauche"),
    ("r_d", "Tour Droite"),
    ("n_g", "Cavalier Gauche"),
    ("n_d", "Cavalier Droite"),
    ("b_g", "Fou Gauche"),
    ("b_d", "Fou Droite"),
    ("q",   "Dame"),
    ("k",   "Roi"),
]

TYPES_DISPONIBLES = ["normal", "feu", "eau", "plante"]

COULEURS_TYPES = {
    "normal": (160, 160, 160),
    "feu":    (220, 80,  30),
    "eau":    (50,  140, 220),
    "plante": (60,  180, 60),
}


class Campagne:
    def __init__(self):
        self.etape = 0
        self.types_joueur = {key: "eau" for key, _ in PIECES_SELECTION}
        self._jeu_courant = None

    @property
    def combat_actuel(self):
        idx = self.etape - 1
        if 0 <= idx < len(COMBATS):
            return COMBATS[idx]
        return None

    @property
    def est_termine(self):
        return self.etape > len(COMBATS)

    def avancer(self):
        self.etape += 1

    def creer_jeu(self):
        config = self.combat_actuel
        if not config:
            return None
        jeu = Jeu()
        jeu.niveau_ia = config["difficulte"]
        jeu.appliquer_types(self.types_joueur, config["type_ia"])
        self._jeu_courant = jeu
        return jeu

    def rejouer_jeu(self):
        return self.creer_jeu()
