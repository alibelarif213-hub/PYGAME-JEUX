import copy
from .pieces import Pion, Tour, Cavalier, Fou, Dame, Roi


class Plateau:
    def __init__(self):
        self.jeu: object = None
        self.reset()

    def reset(self):
        self.grid: list = [[None] * 8 for _ in range(8)]

        for i in range(8):
            self.grid[6][i] = Pion("JOUEUR")
            self.grid[1][i] = Pion("IA")

        self.grid[7][0] = self.grid[7][7] = Tour("JOUEUR")
        self.grid[0][0] = self.grid[0][7] = Tour("IA")
        self.grid[7][1] = self.grid[7][6] = Cavalier("JOUEUR")
        self.grid[0][1] = self.grid[0][6] = Cavalier("IA")
        self.grid[7][2] = self.grid[7][5] = Fou("JOUEUR")
        self.grid[0][2] = self.grid[0][5] = Fou("IA")
        self.grid[7][3] = Dame("JOUEUR")
        self.grid[0][3] = Dame("IA")
        self.grid[7][4] = Roi("JOUEUR")
        self.grid[0][4] = Roi("IA")

    def est_dans(self, x, y): return 0 <= x < 8 and 0 <= y < 8
    def get(self, x, y):      return self.grid[y][x] if self.est_dans(x, y) else None
    def est_vide(self, x, y): return self.get(x, y) is None

    def move(self, x1, y1, x2, y2):
        p = self.get(x1, y1)
        self.grid[y2][x2] = p
        self.grid[y1][x1] = None
        if p is not None:
            p.a_bouge = True
        return p

    def copie(self):
        return copy.deepcopy(self)
