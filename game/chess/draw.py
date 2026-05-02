import math
import textwrap
import pygame
from .assets import screen, BACKGROUND, TAILLE_CASE, TYPES, IMAGES, font, pokeball
from .pieces import Pion, Tour, Cavalier, Fou, Dame, Roi
from .campaign import PIECES_SELECTION, TYPES_DISPONIBLES, COULEURS_TYPES

PIECE_MAPPING = {Pion: "p", Tour: "r", Cavalier: "n", Fou: "b", Dame: "q", Roi: "k"}

NIVEAUX_IA = ["Facile", "Moyen", "Difficile", "Expert"]
COULEURS_NIVEAUX = {
    "Facile":    (60, 180, 60),
    "Moyen":     (200, 180, 40),
    "Difficile": (200, 100, 40),
    "Expert":    (180, 40, 40),
}
COULEURS_STATUT = {
    "brulure":   (230, 100, 20),
    "poison":    (160, 40,  200),
    "confusion": (60,  160, 230),
}

font_grand = pygame.font.SysFont(None, 52)
font_titre = pygame.font.SysFont(None, 72)
font_petit = pygame.font.SysFont("Arial", 17)

_TYPE_ICONS = {
    "feu":    ("FEU",    (220, 80, 30)),
    "eau":    ("EAU",    (50, 140, 220)),
    "plante": ("PLANTE", (60, 180, 60)),
    "normal": ("NOR",    (150, 150, 150)),
}


_STATUT_INFO = [
    ("brulure",   (230, 100,  20), "Brulee  : ne peut pas capturer"),
    ("poison",    (160,  40, 200), "Empois. : ne peut pas bouger"),
    ("confusion", ( 60, 160, 230), "Confuse : coup aleatoire"),
]

def _draw_side_panel(jeu):
    """Panneau gauche : types du joueur + légende des statuts."""
    WIDTH, HEIGHT = screen.get_size()
    px, py = 14, 140

    # ── Types du joueur ──────────────────────────────────────
    lbl = font_petit.render("Vos types", True, (180, 180, 180))
    screen.blit(lbl, (px, py - 20))

    counts: dict[str, int] = {}
    for y in range(8):
        for x in range(8):
            p = jeu.p.get(x, y)
            if p and p.couleur == "JOUEUR":
                t = p.type_pokemon or "normal"
                counts[t] = counts.get(t, 0) + 1

    for i, (t, cnt) in enumerate(sorted(counts.items())):
        name, col = _TYPE_ICONS.get(t, (t.upper()[:3], (140, 140, 140)))
        bar_w = max(10, min(cnt * 8, 110))
        bar_rect = pygame.Rect(px, py + i * 26, bar_w, 18)
        pygame.draw.rect(screen, col, bar_rect, border_radius=4)
        txt = font_petit.render(f"{name} x{cnt}", True, (255, 255, 255))
        screen.blit(txt, (px + bar_w + 4, py + i * 26))

    # ── Légende des statuts ──────────────────────────────────
    legend_y = py + len(counts) * 26 + 20
    lbl2 = font_petit.render("Statuts", True, (180, 180, 180))
    screen.blit(lbl2, (px, legend_y))
    for i, (_, col, desc) in enumerate(_STATUT_INFO):
        cy = legend_y + 18 + i * 22
        pygame.draw.circle(screen, col, (px + 7, cy + 7), 6)
        pygame.draw.circle(screen, (255, 255, 255), (px + 7, cy + 7), 6, 1)
        screen.blit(font_petit.render(desc, True, (210, 210, 210)), (px + 18, cy))


def draw(jeu, en_campagne=False, boss_name=""):
    WIDTH, HEIGHT = screen.get_size()
    screen.blit(pygame.transform.smoothscale(BACKGROUND, (WIDTH, HEIGHT)), (0, 0))
    offset = (WIDTH // 2) - 320

    # Fond sombre centré sur le plateau — améliore la lisibilité
    board_dark = pygame.Surface((8 * TAILLE_CASE + 56, HEIGHT), pygame.SRCALPHA)
    board_dark.fill((0, 0, 0, 135))
    screen.blit(board_dark, (offset - 28, 0))

    for y in range(8):
        for x in range(8):
            couleur = (240, 217, 181) if (x + y) % 2 == 0 else (181, 136, 99)
            rect = pygame.Rect(offset + x * TAILLE_CASE, y * TAILLE_CASE + 20, TAILLE_CASE, TAILLE_CASE)
            pygame.draw.rect(screen, couleur, rect)
            if jeu.sel == (x, y):
                pygame.draw.rect(screen, (220, 190, 40), rect, 4)

    if jeu.sel:
        sx, sy = jeu.sel
        sel_piece = jeu.p.get(sx, sy)
        if sel_piece:
            moves = sel_piece.mouvements_valides(sx, sy, jeu.p)
            if sel_piece.statut == "brulure":
                moves = [(nx, ny) for nx, ny in moves if jeu.p.est_vide(nx, ny)]
            for (mx, my) in moves:
                if jeu.coup_legal(sx, sy, mx, my):
                    mrect = pygame.Rect(offset + mx * TAILLE_CASE, my * TAILLE_CASE + 20, TAILLE_CASE, TAILLE_CASE)
                    if jeu.p.est_vide(mx, my):
                        pygame.draw.circle(screen, (60, 160, 60), mrect.center, TAILLE_CASE // 6)
                    else:
                        pygame.draw.rect(screen, (180, 50, 50), mrect, 4)

    for y in range(8):
        for x in range(8):
            piece = jeu.p.get(x, y)
            if piece:
                rect = pygame.Rect(offset + x * TAILLE_CASE, y * TAILLE_CASE + 20, TAILLE_CASE, TAILLE_CASE)
                type_piece = PIECE_MAPPING[type(piece)]
                type_poke = piece.type_pokemon if piece.type_pokemon in TYPES else "normal"
                screen.blit(IMAGES[TYPES[type_poke][type_piece]], rect)
                badge_couleur = COULEURS_TYPES.get(piece.type_pokemon, (140, 140, 140))
                badge = pygame.Rect(rect.left + 2, rect.bottom - 14, 12, 12)
                pygame.draw.rect(screen, badge_couleur, badge, border_radius=3)
                pygame.draw.rect(screen, (255, 255, 255), badge, 1, border_radius=3)
                if piece.statut and piece.statut in COULEURS_STATUT:
                    col_s  = COULEURS_STATUT[piece.statut]
                    pulse  = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 280)
                    # Teinte colorée sur toute la case
                    ov = pygame.Surface((TAILLE_CASE, TAILLE_CASE), pygame.SRCALPHA)
                    ov.fill((*col_s, int(35 + 45 * pulse)))
                    screen.blit(ov, rect)
                    # Bordure pulsante
                    pygame.draw.rect(screen, col_s, rect, 3 + int(2 * pulse))
                    # Cercle avec lettre initiale (coin haut-droit)
                    r  = 13
                    cx = rect.right - r - 2
                    cy = rect.top   + r + 2
                    pygame.draw.circle(screen, col_s,           (cx, cy), r)
                    pygame.draw.circle(screen, (255, 255, 255), (cx, cy), r, 2)
                    init = {"brulure": "B", "poison": "P", "confusion": "C"}
                    lbl  = font_petit.render(init.get(piece.statut, "?"), True, (255, 255, 255))
                    screen.blit(lbl, (cx - lbl.get_width() // 2, cy - lbl.get_height() // 2))

    for y in range(8):
        for x in range(8):
            piece = jeu.p.get(x, y)
            if isinstance(piece, Roi) and jeu.roi_en_echec(piece.couleur):
                rect = pygame.Rect(offset + x * TAILLE_CASE, y * TAILLE_CASE + 20, TAILLE_CASE, TAILLE_CASE)
                pygame.draw.rect(screen, (255, 0, 0), rect, 4)

    board_rect = pygame.Rect(offset - 11, 20 - 11, 8 * TAILLE_CASE + 25, 8 * TAILLE_CASE + 25)
    pygame.draw.rect(screen, (20, 20, 20), board_rect, 20)
    for pos in [
        (board_rect.left - 5,    board_rect.top - 5),
        (board_rect.right - 25,  board_rect.top - 5),
        (board_rect.left - 5,    board_rect.bottom - 25),
        (board_rect.right - 25,  board_rect.bottom - 25),
        (board_rect.left + 315,  board_rect.top - 5),
        (board_rect.left - 5,    board_rect.top + 315),
        (board_rect.right - 350, board_rect.bottom - 25),
        (board_rect.right - 25,  board_rect.bottom - 350),
    ]:
        screen.blit(pokeball, pos)

    # Panneau gauche : résumé des types du joueur
    _draw_side_panel(jeu)

    rects_niveaux = {}  # Plus de boutons difficulté pendant le combat

    if jeu.ia_en_cours:
        thinking = font.render("IA reflechit...", True, (255, 220, 50))
        screen.blit(thinking, (WIDTH // 2 - thinking.get_width() // 2, 673))

    # Indicateur de tour (coin bas-gauche, plus discret)
    tour_col = (100, 200, 255) if jeu.tour == "JOUEUR" else (255, 130, 80)
    tour_lbl = font.render(f"Tour : {jeu.tour}", True, tour_col)
    bg_tour  = pygame.Surface((tour_lbl.get_width() + 16, tour_lbl.get_height() + 8), pygame.SRCALPHA)
    bg_tour.fill((0, 0, 0, 180))
    screen.blit(bg_tour,  (12, HEIGHT - bg_tour.get_height() - 8))
    screen.blit(tour_lbl, (20, HEIGHT - tour_lbl.get_height() - 12))

    if not en_campagne:
        bouton_rect = pygame.Rect((WIDTH // 2) - 90, 750, 185, 40)
        pygame.draw.rect(screen, (0, 0, 0), bouton_rect)
        screen.blit(font.render("Nouvelle partie", True, (255, 255, 255)), ((WIDTH // 2) - 74, 760))
    else:
        bouton_rect = None

    if jeu.message:
        temps_actuel = pygame.time.get_ticks()
        if jeu.message_permanent or (temps_actuel - jeu.message_timer < jeu.duree_message):
            couleur_msg = (255, 220, 50) if jeu.message_permanent else (255, 80, 80)
            msg_surf = font.render(jeu.message, True, couleur_msg)
            mx = WIDTH // 2 - msg_surf.get_width() // 2
            bg = pygame.Surface((msg_surf.get_width() + 14, msg_surf.get_height() + 8), pygame.SRCALPHA)
            bg.fill((20, 20, 20, 200))
            screen.blit(bg,       (mx - 7, 648))
            screen.blit(msg_surf, (mx,     652))

    # Les hints (A/T) sont gérés par _BattleDialogue.draw() dans integration.py

    return offset, bouton_rect, rects_niveaux


def _fond_overlay(titre, sous_titre=""):
    WIDTH, HEIGHT = screen.get_size()
    screen.blit(pygame.transform.smoothscale(BACKGROUND, (WIDTH, HEIGHT)), (0, 0))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))
    titre_surf = font_titre.render(titre, True, (255, 220, 50))
    screen.blit(titre_surf, (WIDTH // 2 - titre_surf.get_width() // 2, 40))
    if sous_titre:
        ss = font_grand.render(sous_titre, True, (200, 200, 200))
        screen.blit(ss, (WIDTH // 2 - ss.get_width() // 2, 110))
    return WIDTH, HEIGHT


def _bouton(label, rect, couleur=(60, 60, 180), couleur_texte=(255, 255, 255)):
    pygame.draw.rect(screen, couleur, rect, border_radius=8)
    pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=8)
    txt = font_grand.render(label, True, couleur_texte)
    screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))


def draw_accueil():
    WIDTH, _ = _fond_overlay("PokeChess", "Choisissez un mode de jeu")
    btn_campagne = pygame.Rect(WIDTH // 2 - 140, 260, 280, 65)
    btn_libre    = pygame.Rect(WIDTH // 2 - 140, 360, 280, 65)
    _bouton("Campagne",    btn_campagne, (180, 40, 40))
    _bouton("Partie libre", btn_libre,   (40, 100, 180))
    pygame.display.flip()
    return {"campagne": btn_campagne, "libre": btn_libre}


def draw_choix_type(campagne, prochain_combat=None, types_disponibles=None):
    if types_disponibles is None:
        types_disponibles = TYPES_DISPONIBLES
    WIDTH, HEIGHT = screen.get_size()
    screen.blit(pygame.transform.smoothscale(BACKGROUND, (WIDTH, HEIGHT)), (0, 0))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    titre = font_grand.render("Choisissez vos types de pieces", True, (255, 220, 50))
    screen.blit(titre, (WIDTH // 2 - titre.get_width() // 2, 20))

    if prochain_combat:
        type_ia = prochain_combat["type_ia"]
        type_ia_label = type_ia if isinstance(type_ia, str) else "Mixte"
        info = font.render(
            f"Adversaire : {prochain_combat['arene']}  —  IA : {type_ia_label.upper()}",
            True, (200, 200, 200))
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, 70))

    rects = {}
    col_label = 80
    col_types_start = 280
    btn_w, btn_h = 110, 34
    gap = 8
    row_h = 46
    start_y = 110

    screen.blit(font.render("Piece", True, (180, 180, 180)), (col_label, start_y - 30))
    for ti, t in enumerate(TYPES_DISPONIBLES):
        hx = col_types_start + ti * (btn_w + gap)
        th = font.render(t.capitalize(), True, COULEURS_TYPES[t] if t in types_disponibles else (80, 80, 80))
        screen.blit(th, (hx + btn_w // 2 - th.get_width() // 2, start_y - 30))

    for ri, (cle, nom) in enumerate(PIECES_SELECTION):
        y = start_y + ri * row_h
        screen.blit(font.render(nom, True, (255, 255, 255)), (col_label, y + btn_h // 2 - font.get_height() // 2))
        type_actuel = campagne.types_joueur.get(cle, "normal")
        for ti, t in enumerate(TYPES_DISPONIBLES):
            bx = col_types_start + ti * (btn_w + gap)
            rect = pygame.Rect(bx, y, btn_w, btn_h)
            disponible = t in types_disponibles
            actif = type_actuel == t and disponible
            if disponible:
                pygame.draw.rect(screen, COULEURS_TYPES[t] if actif else (50, 50, 50), rect, border_radius=6)
                pygame.draw.rect(screen, (255, 255, 255), rect, 2 if actif else 1, border_radius=6)
                rects[(cle, t)] = rect
            else:
                pygame.draw.rect(screen, (28, 28, 28), rect, border_radius=6)
                pygame.draw.rect(screen, (65, 65, 65), rect, 1, border_radius=6)
            txt = font.render(t.capitalize(), True, (255, 255, 255) if disponible else (70, 70, 70))
            screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

    bottom_y = start_y + len(PIECES_SELECTION) * row_h + 20
    btn_normal    = pygame.Rect(col_label, bottom_y, 180, 42)
    btn_confirmer = pygame.Rect(WIDTH // 2 + 60, bottom_y, 200, 42)
    _bouton("Tout Normal", btn_normal,    (80, 80, 80))
    _bouton("Combattre !",  btn_confirmer, (40, 160, 40))
    rects["tout_normal"] = btn_normal
    rects["confirmer"]   = btn_confirmer
    pygame.display.flip()
    return rects


def draw_intro_combat(campagne):
    config = campagne.combat_actuel
    if not config:
        return {}
    type_ia_label = config["type_ia"].upper() if isinstance(config["type_ia"], str) else "MIXTE"
    WIDTH, HEIGHT = _fond_overlay(config["arene"], config["label"])
    for i, ligne in enumerate([f"Adversaire : {type_ia_label}", f"Difficulte : {config['difficulte']}"]):
        txt = font_grand.render(ligne, True, (220, 220, 220))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 200 + i * 60))
    btn = pygame.Rect(WIDTH // 2 - 120, HEIGHT - 160, 240, 60)
    _bouton("Commencer !", btn, (180, 40, 40))
    pygame.display.flip()
    return {"commencer": btn}


def draw_intro_boss(boss_name, type_ia, difficulte, boss_message="..."):
    WIDTH, HEIGHT = screen.get_size()
    screen.blit(pygame.transform.smoothscale(BACKGROUND, (WIDTH, HEIGHT)), (0, 0))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    type_label = type_ia.upper() if isinstance(type_ia, str) else "MIXTE"
    titre = font_titre.render(f"COMBAT — {boss_name}", True, (255, 80, 50))
    screen.blit(titre, (WIDTH // 2 - titre.get_width() // 2, 35))
    info = font_grand.render(f"Type : {type_label}   ·   Difficulté : {difficulte}", True, (210, 210, 210))
    screen.blit(info, (WIDTH // 2 - info.get_width() // 2, 115))

    box = pygame.Rect(WIDTH // 4, 180, WIDTH // 2, 130)
    surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    surf.fill((15, 15, 35, 220))
    screen.blit(surf, (box.x, box.y))
    pygame.draw.rect(screen, (255, 180, 50), box, 2, border_radius=10)

    btn_rect = None
    if boss_message == "...":
        wait = font_grand.render("L'adversaire prépare ses mots...", True, (140, 140, 140))
        screen.blit(wait, (box.centerx - wait.get_width() // 2, box.centery - wait.get_height() // 2))
    else:
        lines = textwrap.wrap(f'"{boss_message}"', 46)[:4]
        for i, line in enumerate(lines):
            txt = font.render(line, True, (255, 240, 180))
            screen.blit(txt, (box.x + 14, box.y + 14 + i * 28))
        btn_rect = pygame.Rect(WIDTH // 2 - 130, HEIGHT - 130, 260, 58)
        _bouton("COMBATTRE !", btn_rect, (200, 30, 30))
        hint = font_petit.render("Clic ou ENTRÉE pour commencer", True, (120, 120, 120))
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 55))

    pygame.display.flip()
    return {"commencer": btn_rect}


def draw_menu_victoire(campagne):
    config = campagne.combat_actuel
    label = config["label"] if config else ""
    WIDTH, _ = _fond_overlay("Victoire !", label + " remportee !")
    btn_continuer = pygame.Rect(WIDTH // 2 - 140, 250, 280, 58)
    btn_rejouer   = pygame.Rect(WIDTH // 2 - 140, 330, 280, 58)
    btn_quitter   = pygame.Rect(WIDTH // 2 - 140, 410, 280, 58)
    _bouton("Continuer",          btn_continuer, (40, 160, 40))
    _bouton("Rejouer ce combat",  btn_rejouer,   (160, 120, 30))
    _bouton("Quitter la campagne", btn_quitter,  (140, 30, 30))
    pygame.display.flip()
    return {"continuer": btn_continuer, "rejouer": btn_rejouer, "quitter": btn_quitter}


def draw_game_over():
    WIDTH, _ = _fond_overlay("Defaite...", "Votre armee a ete vaincue.")
    btn_menu = pygame.Rect(WIDTH // 2 - 120, 320, 240, 58)
    _bouton("Menu principal", btn_menu, (140, 30, 30))
    pygame.display.flip()
    return {"menu": btn_menu}


def draw_victoire_finale():
    WIDTH, _ = _fond_overlay("Champion !", "Vous avez vaincu les 4 arenes !")
    for i, l in enumerate(["Votre legende est ecrite.", "Vous etes le Maitre PokeChess !"]):
        txt = font_grand.render(l, True, (255, 220, 50))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 260 + i * 60))
    btn_menu = pygame.Rect(WIDTH // 2 - 120, 420, 240, 58)
    _bouton("Menu principal", btn_menu, (40, 100, 180))
    pygame.display.flip()
    return {"menu": btn_menu}
