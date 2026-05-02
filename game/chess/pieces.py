class Piece:
    def __init__(self, couleur):
        self.couleur = couleur
        self.a_bouge = False
        self.type_pokemon = "normal"
        self.statut = None  # None | "brulure" | "poison" | "confusion"

    def ennemie(self, autre):
        return autre and autre.couleur != self.couleur

    def mouvements_valides(self, _x, _y, _plateau):
        return []

    def attaques(self, x, y, plateau):
        return self.mouvements_valides(x, y, plateau)


class Pion(Piece):
    def mouvements_valides(self, x, y, plateau):
        moves = []
        dir = -1 if self.couleur == "JOUEUR" else 1

        if plateau.est_vide(x, y + dir):
            moves.append((x, y + dir))
            if not self.a_bouge and plateau.est_vide(x, y + 2 * dir):
                moves.append((x, y + 2 * dir))

        for dx in [-1, 1]:
            nx, ny = x + dx, y + dir
            if plateau.est_dans(nx, ny) and self.ennemie(plateau.get(nx, ny)):
                moves.append((nx, ny))

        if hasattr(plateau, "jeu") and plateau.jeu.dernier_coup:
            x1, y1, x2, y2, piece = plateau.jeu.dernier_coup
            if isinstance(piece, Pion) and abs(y2 - y1) == 2:
                if y == y2 and abs(x - x2) == 1:
                    moves.append((x2, y + dir))

        return moves


class Tour(Piece):
    def mouvements_valides(self, x, y, p):
        return lignes(x, y, p, [(1, 0), (-1, 0), (0, 1), (0, -1)], self)


class Fou(Piece):
    def mouvements_valides(self, x, y, p):
        return lignes(x, y, p, [(1, 1), (-1, -1), (1, -1), (-1, 1)], self)


class Dame(Piece):
    def mouvements_valides(self, x, y, p):
        return lignes(x, y, p, [(1, 0), (-1, 0), (0, 1), (0, -1),
                                 (1, 1), (-1, -1), (1, -1), (-1, 1)], self)


class Cavalier(Piece):
    def mouvements_valides(self, x, y, p):
        moves = []
        for dx, dy in [(2, 1), (2, -1), (-2, 1), (-2, -1),
                       (1, 2), (1, -2), (-1, 2), (-1, -2)]:
            nx, ny = x + dx, y + dy
            if p.est_dans(nx, ny) and (p.est_vide(nx, ny) or self.ennemie(p.get(nx, ny))):
                moves.append((nx, ny))
        return moves


class Roi(Piece):
    def attaques(self, x, y, p):
        moves = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if p.est_dans(nx, ny):
                    moves.append((nx, ny))
        return moves

    def mouvements_valides(self, x, y, p, ignore_roque=False):
        moves = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if p.est_dans(nx, ny) and (p.est_vide(nx, ny) or self.ennemie(p.get(nx, ny))):
                    moves.append((nx, ny))

        if not ignore_roque and not self.a_bouge and hasattr(p, "jeu"):
            jeu = p.jeu
            if not jeu.roi_en_echec(self.couleur):
                tour_droite = p.get(7, y)
                if (isinstance(tour_droite, Tour) and not tour_droite.a_bouge
                        and p.est_vide(5, y) and p.est_vide(6, y)
                        and not jeu.case_attaquee(5, y, self.couleur)
                        and not jeu.case_attaquee(6, y, self.couleur)):
                    moves.append((6, y))

                tour_gauche = p.get(0, y)
                if (isinstance(tour_gauche, Tour) and not tour_gauche.a_bouge
                        and p.est_vide(1, y) and p.est_vide(2, y) and p.est_vide(3, y)
                        and not jeu.case_attaquee(3, y, self.couleur)
                        and not jeu.case_attaquee(2, y, self.couleur)):
                    moves.append((2, y))

        return moves


def downgrade(piece):
    hierarchy = {Dame: Tour, Tour: Cavalier, Cavalier: Pion, Fou: Pion}
    new_cls = hierarchy.get(type(piece))
    if new_cls is None:
        return None
    p = new_cls(piece.couleur)
    p.type_pokemon = piece.type_pokemon
    p.a_bouge = True
    return p


def lignes(x, y, p, dirs, piece):
    moves = []
    for dx, dy in dirs:
        nx, ny = x, y
        while True:
            nx += dx
            ny += dy
            if not p.est_dans(nx, ny):
                break
            if p.est_vide(nx, ny):
                moves.append((nx, ny))
            else:
                if piece.ennemie(p.get(nx, ny)):
                    moves.append((nx, ny))
                break
    return moves
