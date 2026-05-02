import json
import os
import copy

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "savegame.json")

_DEFAULT = {
    "bosses_vaincus": [],           # ["Arène_1", "Arène_2", "Arène_3", "Arène_4"]
    "types_debloque": ["normal"],   # types disponibles pour la selection de pieces
    "types_joueur": {               # derniere selection de types de pieces
        "p":   "normal",
        "r_g": "normal", "r_d": "normal",
        "n_g": "normal", "n_d": "normal",
        "b_g": "normal", "b_d": "normal",
        "q":   "normal",
        "k":   "normal",
    },
    "personnage": None,
}


def charger() -> dict:
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in _DEFAULT.items():
                data.setdefault(k, copy.deepcopy(v))
            return data
        except Exception:
            pass
    return copy.deepcopy(_DEFAULT)


def sauvegarder(data: dict) -> None:
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def reset() -> dict:
    data = copy.deepcopy(_DEFAULT)
    sauvegarder(data)
    return data
