import os
import random
import shutil

# python-chess + Stockfish (optionnel : fallback aléatoire si absent)
try:
    import chess as _chess
    import chess.engine as _chess_engine
    _CHESS_OK = True
except ImportError:
    _CHESS_OK = False
    print("[IA] python-chess introuvable — IA en mode aléatoire. Installez : pip install chess")

from .pieces import Pion, Tour, Cavalier, Fou, Dame, Roi

_LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stockfish", "stockfish.exe")
STOCKFISH_PATH = _LOCAL if os.path.exists(_LOCAL) else (shutil.which("stockfish") or "stockfish")

SKILL_LEVEL     = {"Facile": 0, "Moyen": 0, "Difficile": 0,  "Expert": 2}
TEMPS_REFLEXION = {"Facile": 0.02, "Moyen": 0.04, "Difficile": 0.08, "Expert": 0.32}
PIECE_FEN       = {Pion: "p", Tour: "r", Cavalier: "n", Fou: "b", Dame: "q", Roi: "k"}

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = _chess_engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    return _engine


def _coords_uci(x, y):
    return f"{chr(97 + x)}{8 - y}"


def _uci_coords(uci):
    return (ord(uci[0]) - 97, 8 - int(uci[1]), ord(uci[2]) - 97, 8 - int(uci[3]))


def _coup_aleatoire(jeu, ignorer_statuts=False):
    """Fallback : retourne un coup légal aléatoire (sans Stockfish)."""
    tous = []
    for y in range(8):
        for x in range(8):
            p = jeu.p.get(x, y)
            if not p or p.couleur != jeu.tour:
                continue
            if not ignorer_statuts and p.statut == "poison":
                continue
            for nx, ny in p.mouvements_valides(x, y, jeu.p):
                if not ignorer_statuts and p.statut == "brulure" and jeu.p.get(nx, ny):
                    continue
                if jeu.coup_legal(x, y, nx, ny):
                    tous.append((x, y, nx, ny))
    return random.choice(tous) if tous else None


def plateau_vers_fen(jeu):
    rows = []
    for y in range(8):
        vide = 0
        row  = ""
        for x in range(8):
            p = jeu.p.get(x, y)
            if p is None:
                vide += 1
            else:
                if vide:
                    row += str(vide)
                    vide = 0
                letter = PIECE_FEN[type(p)]
                row += letter.upper() if p.couleur == "JOUEUR" else letter
        if vide:
            row += str(vide)
        rows.append(row)

    trait = "w" if jeu.tour == "JOUEUR" else "b"
    roque = ""
    roi_j = jeu.p.get(4, 7)
    if isinstance(roi_j, Roi) and not roi_j.a_bouge:
        t = jeu.p.get(7, 7)
        if isinstance(t, Tour) and not t.a_bouge: roque += "K"
        t = jeu.p.get(0, 7)
        if isinstance(t, Tour) and not t.a_bouge: roque += "Q"
    roi_ia = jeu.p.get(4, 0)
    if isinstance(roi_ia, Roi) and not roi_ia.a_bouge:
        t = jeu.p.get(7, 0)
        if isinstance(t, Tour) and not t.a_bouge: roque += "k"
        t = jeu.p.get(0, 0)
        if isinstance(t, Tour) and not t.a_bouge: roque += "q"
    if not roque:
        roque = "-"

    ep = "-"
    if jeu.dernier_coup:
        _, y1, x2, y2, piece = jeu.dernier_coup
        if isinstance(piece, Pion) and abs(y2 - y1) == 2:
            ep = _coords_uci(x2, (y1 + y2) // 2)

    return f"{'/'.join(rows)} {trait} {roque} {ep} 0 1"


def coups_pokemon_legaux(jeu, ignorer_statuts=False):
    coups = []
    for y in range(8):
        for x in range(8):
            piece = jeu.p.get(x, y)
            if not piece or piece.couleur != jeu.tour:
                continue
            if not ignorer_statuts and piece.statut == "poison":
                continue
            for nx, ny in piece.mouvements_valides(x, y, jeu.p):
                if not ignorer_statuts and piece.statut == "brulure":
                    if jeu.p.get(nx, ny) is not None:
                        continue
                if not jeu.coup_legal(x, y, nx, ny):
                    continue
                base = _coords_uci(x, y) + _coords_uci(nx, ny)
                if isinstance(piece, Pion) and (ny == 0 or ny == 7):
                    for promo in "qrbn":
                        coups.append(base + promo)
                else:
                    coups.append(base)
    return coups


def meilleur_coup(jeu):
    if not _CHESS_OK:
        return _coup_aleatoire(jeu, ignorer_statuts=True)
    try:
        engine = _get_engine()
        engine.configure({"Skill Level": SKILL_LEVEL[jeu.niveau_ia]})
        fen    = plateau_vers_fen(jeu)
        board  = _chess.Board(fen)
        coups  = coups_pokemon_legaux(jeu, ignorer_statuts=True)
        if not coups:
            return None
        root_moves = [_chess.Move.from_uci(c) for c in coups]
        result = engine.play(board, _chess_engine.Limit(time=TEMPS_REFLEXION[jeu.niveau_ia]),
                             root_moves=root_moves)
        return _uci_coords(result.move.uci()) if result.move else None
    except Exception as e:
        print(f"[IA] Erreur Stockfish : {e}")
        return _coup_aleatoire(jeu, ignorer_statuts=True)


def meilleur_coup_avec_statuts(jeu):
    # Confusion → coup aléatoire prioritaire
    for y in range(8):
        for x in range(8):
            p = jeu.p.get(x, y)
            if p and p.couleur == jeu.tour and p.statut == "confusion":
                moves = [m for m in p.mouvements_valides(x, y, jeu.p) if jeu.coup_legal(x, y, *m)]
                if moves:
                    tx, ty = random.choice(moves)
                    return (x, y, tx, ty)

    if not _CHESS_OK:
        return _coup_aleatoire(jeu, ignorer_statuts=False)
    try:
        engine = _get_engine()
        engine.configure({"Skill Level": SKILL_LEVEL[jeu.niveau_ia]})
        fen    = plateau_vers_fen(jeu)
        board  = _chess.Board(fen)
        coups  = coups_pokemon_legaux(jeu, ignorer_statuts=False)
        if not coups:
            return None
        root_moves = [_chess.Move.from_uci(c) for c in coups]
        result = engine.play(board, _chess_engine.Limit(time=TEMPS_REFLEXION[jeu.niveau_ia]),
                             root_moves=root_moves)
        return _uci_coords(result.move.uci()) if result.move else None
    except Exception as e:
        print(f"[IA] Erreur Stockfish : {e}")
        return _coup_aleatoire(jeu, ignorer_statuts=False)
