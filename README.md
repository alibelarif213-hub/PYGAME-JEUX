# PokeChess

Jeu de rôle / RPG en vue de dessus mêlant exploration Pokémon et combats d'échecs.
Le joueur explore un monde, affronte des boss en parties d'échecs et peut les vaincre
par la force **ou par le dialogue** (style Undertale).

---

## Prérequis

- **Python 3.10+**
- **Ollama** avec le modèle `mistral` (pour les dialogues IA des boss)

---

## Installation

### 1. Cloner / télécharger le projet

Placer le dossier `PokeChess/` où vous souhaitez.

### 2. Créer un environnement virtuel et installer les dépendances

```bash
cd PokeChess
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install pygame pyscroll pytmx requests
```

### 3. Installer python-chess + Stockfish (moteur d'IA pour les échecs)

```bash
pip install chess
```

Télécharger **Stockfish** : https://stockfishchess.org/download/
Placer l'exécutable dans `game/chess/stockfish/stockfish.exe` (Windows)
ou dans le PATH système.

### 4. Installer Ollama + le modèle mistral (dialogues boss)

```bash
# Installer Ollama : https://ollama.com
ollama pull mistral
ollama serve        # lancer le serveur local (port 11434)
```

> Sans Ollama, le jeu fonctionne normalement mais les boss répondent
> par des phrases génériques au lieu de réponses générées.

---

## Lancement

```bash
# Depuis la racine du projet, avec le venv activé :
python main.py
```

---

## Contrôles

### Overworld (exploration)
| Touche | Action |
|--------|--------|
| Flèches / ZQSD | Déplacer le personnage |
| A | Interagir avec un PNJ ou lancer un combat boss |
| Entrée | Fermer un dialogue |

### Combat d'échecs
| Touche / Action | Effet |
|-----------------|-------|
| Clic gauche | Sélectionner / déplacer une pièce |
| T | Parler au boss (1 fois par tour) |
| A | Provoquer le boss |
| Entrée / Clic | Fermer la boîte de dialogue |

### Système de dialogue Undertale
- Appuyer sur **T** ouvre une saisie libre : tapez ce que vous voulez dire au boss.
- Si votre argument ébranle ses convictions, il répond **DOUTE:** → son moral baisse.
- Quand le moral atteint **0**, il abandonne → **victoire par le dialogue**.
- Le moral est représenté par des cercles en haut à droite de l'écran.

---

## Mécaniques de types Pokémon

| Avantage | Défenseur dégradé | Effet de statut |
|----------|------------------|-----------------|
| Feu > Plante | Pièce attaquante affaiblie (Dame→Tour→...) | Brûlure : ne peut pas capturer |
| Plante > Eau | idem | Poison : ne peut pas bouger |
| Eau > Feu | idem | Confusion : mouvement aléatoire |

Chaque victoire contre un boss débloque son type pour la sélection de pièces.

---

## Progression de la campagne

| Arène | Boss | Type | Difficulté |
|-------|------|------|------------|
| Arène Eau | DJ Mary | EAU | Facile |
| Arène Plante | Mafieuse Banquière | PLANTE | Moyen |
| Arène Feu | Membre du FSE | FEU | Difficile |
| Arène Finale | Bessière | MIXTE | Difficile |

Les trois premières arènes doivent être complétées avant d'accéder à l'arène finale.

---

## Modifier les personnages et dialogues

### Personnalité des boss (prompts LLM)

Dans `game/engine/game.py`, le dictionnaire `BOSS_CONFIG` en haut du fichier
contient la clé `"battle_prompt"` pour chaque boss :

```python
BOSS_CONFIG = {
    "arena_eau": {
        "npc_name": "DJ Mary",
        "battle_prompt": "Tu es DJ Mary, une DJ rebelle...",  # <-- modifier ici
        ...
    },
    "arena_plante": {
        "npc_name": "Mafieuse Banquière",
        "battle_prompt": "Tu es une mafieuse banquière...",   # <-- modifier ici
        ...
    },
    ...
}
```

### Personnalité des PNJ du monde (Samouraï, M. Delbot)

Dans `game/engine/game.py`, la méthode `_setup_npcs()` :

```python
self.samurai = _add("world", "Samurai", "samurai.png", 850, 700,
    "Tu es un maitre samourai sarcastique...",  # <-- modifier ici
    speed=0.8)
self.delbot  = _add("world", "M. Delbot", "delbot.png", 600, 500,
    "Tu es un professeur enthousiaste...",       # <-- modifier ici
    speed=0)
```

---

## Structure du projet

```
PokeChess/
├── main.py                    # Point d'entrée
├── save.py                    # Sauvegarde JSON
├── savegame.json              # Fichier de sauvegarde (généré automatiquement)
├── game/
│   ├── engine/
│   │   ├── game.py            # Logique RPG overworld + boss config
│   │   ├── map.py             # Gestion des cartes (pyscroll/pytmx)
│   │   ├── player.py          # Joueur
│   │   ├── npc.py             # PNJ
│   │   └── entity.py          # Entité de base
│   ├── chess/
│   │   ├── integration.py     # Pont RPG ↔ combat + dialogues Undertale
│   │   ├── jeu.py             # Logique des échecs + types Pokémon
│   │   ├── ia.py              # IA Stockfish + niveaux de difficulté
│   │   ├── draw.py            # Rendu du plateau et des menus
│   │   ├── pieces.py          # Pièces d'échecs + statuts
│   │   ├── plateau.py         # Grille 8×8
│   │   ├── campaign.py        # Configuration campagne
│   │   ├── assets.py          # Chargement images / configuration écran
│   │   └── stockfish/         # Placer stockfish.exe ici
│   └── assets/
│       ├── images/            # Sprites, pokémons, UI
│       ├── maps/              # Cartes TMX (Tiled)
│       ├── music/             # Musiques
│       └── fonts/             # Police Minecraft.ttf
└── README.md
```

---

## Réinitialiser la sauvegarde

Supprimer le fichier `savegame.json` ou choisir "Nouvelle Partie" dans le menu.
