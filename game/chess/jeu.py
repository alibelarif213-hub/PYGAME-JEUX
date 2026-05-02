import random
import pygame
from .plateau import Plateau
from .pieces import Pion, Cavalier, Dame, Roi, downgrade
from .assets import TAILLE_CASE, AVANTAGES, EFFETS_DE_STATUT

_POS_JOUEUR = {
    "r_g": (0, 7), "r_d": (7, 7),
    "n_g": (1, 7), "n_d": (6, 7),
    "b_g": (2, 7), "b_d": (5, 7),
    "q":   (3, 7), "k":   (4, 7),
}
_POS_IA = {
    "r_g": (0, 0), "r_d": (7, 0),
    "n_g": (1, 0), "n_d": (6, 0),
    "b_g": (2, 0), "b_d": (5, 0),
    "q":   (3, 0), "k":   (4, 0),
}


class Jeu:
    def __init__(self):
        self.p = Plateau()
        self.sel = None
        self.tour = "JOUEUR"
        self.message = ""
        self.partie_terminee = False
        self.message_timer = 0
        self.duree_message = 2000
        self.message_permanent = False
        self.dernier_coup = None
        self.type_joueur = "feu"
        self.type_ia = "eau"
        self.ia_en_cours = False
        self.niveau_ia = "Moyen"
        self.gagnant = None
        self.p.jeu = self
        self.appliquer_types(
            {k: "feu" for k in list(_POS_JOUEUR) + ["p"]},
            "eau",
        )

    def appliquer_types(self, types_joueur: dict, type_ia):
        for x in range(8):
            p = self.p.get(x, 6)
            if p:
                p.type_pokemon = types_joueur.get("p", "normal")
        for key, (x, y) in _POS_JOUEUR.items():
            p = self.p.get(x, y)
            if p:
                p.type_pokemon = types_joueur.get(key, "normal")
        ia_type_p = type_ia if isinstance(type_ia, str) else type_ia.get("p", "normal")
        for x in range(8):
            p = self.p.get(x, 1)
            if p:
                p.type_pokemon = ia_type_p
        for key, (x, y) in _POS_IA.items():
            p = self.p.get(x, y)
            if p:
                p.type_pokemon = type_ia if isinstance(type_ia, str) else type_ia.get(key, "normal")
        self.type_joueur = types_joueur.get("p", "normal")
        self.type_ia = type_ia if isinstance(type_ia, str) else "mixte"

    def set_message(self, texte, permanent=False):
        if self.partie_terminee:
            return
        self.message = texte
        self.message_timer = pygame.time.get_ticks()
        self.message_permanent = permanent

    def roi_en_echec(self, couleur, plateau=None):
        if plateau is None:
            plateau = self.p
        roi_pos = None
        for y in range(8):
            for x in range(8):
                piece = plateau.get(x, y)
                if isinstance(piece, Roi) and piece.couleur == couleur:
                    roi_pos = (x, y)
        for y in range(8):
            for x in range(8):
                piece = plateau.get(x, y)
                if piece and piece.couleur != couleur:
                    if isinstance(piece, Roi):
                        moves = piece.attaques(x, y, plateau)
                    else:
                        moves = piece.mouvements_valides(x, y, plateau)
                    if roi_pos in moves:
                        return True
        return False

    def coup_legal(self, x1, y1, x2, y2):
        test = self.p.copie()
        test.move(x1, y1, x2, y2)
        return not self.roi_en_echec(self.tour, test)

    def a_coup_legal(self, couleur):
        for y in range(8):
            for x in range(8):
                piece = self.p.get(x, y)
                if piece and piece.couleur == couleur:
                    for (nx, ny) in piece.mouvements_valides(x, y, self.p):
                        test = self.p.copie()
                        test.move(x, y, nx, ny)
                        if not self.roi_en_echec(couleur, test):
                            return True
        return False

    def case_attaquee(self, x, y, couleur):
        for j in range(8):
            for i in range(8):
                piece = self.p.get(i, j)
                if not piece or piece.couleur == couleur:
                    continue
                if isinstance(piece, Roi):
                    if max(abs(i - x), abs(j - y)) == 1:
                        return True
                    continue
                if isinstance(piece, Pion):
                    direction = -1 if piece.couleur == "JOUEUR" else 1
                    if (j + direction == y) and (abs(i - x) == 1):
                        return True
                    continue
                if isinstance(piece, Cavalier):
                    if (abs(i - x), abs(j - y)) in [(1, 2), (2, 1)]:
                        return True
                    continue
                dx = x - i
                dy = y - j
                is_rook_line  = (dx == 0 or dy == 0)
                is_bishop_line = (abs(dx) == abs(dy))
                if is_rook_line or is_bishop_line:
                    step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
                    step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
                    cx, cy = i + step_x, j + step_y
                    blocked = False
                    while (cx, cy) != (x, y):
                        if not self.p.est_vide(cx, cy):
                            blocked = True
                            break
                        cx += step_x
                        cy += step_y
                    if not blocked:
                        return True
        return False

    def est_mat(self, couleur):
        return self.roi_en_echec(couleur) and not self.a_coup_legal(couleur)

    def _traiter_effets_capture(self, attaquant, capturee, x2, y2):
        type_att = attaquant.type_pokemon
        type_cap = capturee.type_pokemon
        if type_att in AVANTAGES.get(type_cap, []):
            if isinstance(attaquant, Roi):
                return
            degradee = downgrade(attaquant)
            if degradee is None:
                self.p.grid[y2][x2] = None
                self.set_message("Désavantage de type ! Pièce perdue !")
            else:
                self.p.grid[y2][x2] = degradee
                self.set_message("Désavantage de type ! Pièce affaiblie !")
            return
        if type_cap in AVANTAGES.get(type_att, []):
            effet = EFFETS_DE_STATUT.get(type_att)
            if not effet:
                return
            couleur_ennemie = capturee.couleur
            adjacentes = []
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x2 + dx, y2 + dy
                    if self.p.est_dans(nx, ny):
                        p = self.p.get(nx, ny)
                        if p and p.couleur == couleur_ennemie and not isinstance(p, Roi):
                            adjacentes.append(p)
            if adjacentes:
                cible = random.choice(adjacentes)
                cible.statut = effet
                self.set_message(f"Avantage de type ! {effet.capitalize()} infligé !")

    def executer_coup(self, x1, y1, x2, y2):
        piece = self.p.get(x1, y1)
        if not piece:
            return
        if isinstance(piece, Pion) and x2 != x1 and self.p.est_vide(x2, y2):
            self.p.grid[y1][x2] = None
        captured = self.p.get(x2, y2)
        piece_jouee = self.p.move(x1, y1, x2, y2)
        if isinstance(piece_jouee, Pion):
            if (piece_jouee.couleur == "JOUEUR" and y2 == 0) or \
               (piece_jouee.couleur == "IA" and y2 == 7):
                dame = Dame(piece_jouee.couleur)
                dame.type_pokemon = random.choice(["feu", "eau", "plante", "normal"])
                dame.a_bouge = True
                self.p.grid[y2][x2] = dame
                piece_jouee = dame
                self.set_message(f"Promotion ! Type : {dame.type_pokemon} !")
        if isinstance(piece, Roi):
            if x2 == 6:
                self.p.move(7, y2, 5, y2)
            elif x2 == 2:
                self.p.move(0, y2, 3, y2)
        if captured:
            self._traiter_effets_capture(piece_jouee, captured, x2, y2)
        self.dernier_coup = (x1, y1, x2, y2, piece_jouee)
        joueur_qui_vient_de_jouer = self.tour
        for yy in range(8):
            for xx in range(8):
                p = self.p.get(xx, yy)
                if p and p.couleur == joueur_qui_vient_de_jouer:
                    p.statut = None
        self.tour = "IA" if self.tour == "JOUEUR" else "JOUEUR"
        self.ia_en_cours = False
        en_echec = self.roi_en_echec(self.tour)
        a_coups  = self.a_coup_legal(self.tour)
        if en_echec and not a_coups:
            gagnant = "JOUEUR" if self.tour == "IA" else "IA"
            self.gagnant = gagnant
            self.message = f"ÉCHEC ET MAT ! {gagnant} gagne !"
            self.message_permanent = True
            self.partie_terminee = True
        elif not a_coups:
            self.gagnant = None
            self.message = "PAT ! Match nul !"
            self.message_permanent = True
            self.partie_terminee = True

        if not self.partie_terminee:
            non_rois_ia = [
                self.p.get(x, y) for y in range(8) for x in range(8)
                if self.p.get(x, y) and self.p.get(x, y).couleur == "IA"
                and not isinstance(self.p.get(x, y), Roi)
            ]
            if len(non_rois_ia) == 0:
                self.gagnant = "JOUEUR"
                self.message = "L'IA n'a plus que son roi ! Victoire !"
                self.message_permanent = True
                self.partie_terminee = True

    def appliquer_coup(self, x1, y1, x2, y2):
        self.executer_coup(x1, y1, x2, y2)

    def click(self, pos, offset):
        mx, my = pos
        if self.partie_terminee:
            return
        x = (mx - offset) // TAILLE_CASE
        y = (my - 20) // TAILLE_CASE
        if not self.p.est_dans(x, y):
            return
        if self.sel:
            x1, y1 = self.sel
            piece = self.p.get(x1, y1)
            moves = piece.mouvements_valides(x1, y1, self.p)
            if piece.statut == "brulure":
                moves = [(nx, ny) for nx, ny in moves if self.p.est_vide(nx, ny)]
            if (x, y) in moves:
                if self.coup_legal(x1, y1, x, y):
                    self.executer_coup(x1, y1, x, y)
                else:
                    self.set_message("Roi en danger !")
            else:
                if piece.statut == "brulure" and (x, y) in piece.mouvements_valides(x1, y1, self.p):
                    self.set_message("Brûlé ! Impossible de capturer !")
                else:
                    self.set_message("Mouvement interdit !")
            self.sel = None
        else:
            piece = self.p.get(x, y)
            if piece and piece.couleur == self.tour:
                if piece.statut == "confusion":
                    moves_legaux = [m for m in piece.mouvements_valides(x, y, self.p)
                                    if self.coup_legal(x, y, *m)]
                    if moves_legaux:
                        tx, ty = random.choice(moves_legaux)
                        self.set_message("Confus ! Mouvement aléatoire !")
                        self.executer_coup(x, y, tx, ty)
                    else:
                        self.set_message("Confus ! Aucun mouvement possible.")
                elif piece.statut == "poison":
                    self.set_message("Empoisonné ! Cette pièce ne peut pas bouger.")
                else:
                    self.sel = (x, y)
