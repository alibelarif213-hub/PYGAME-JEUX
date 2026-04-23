import pygame
import sys
import copy
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets_pieces")

UI_DIR = os.path.join(BASE_DIR, "assets_bordures")

pygame.init()

TAILLE_CASE = 80

pokeball = pygame.image.load(os.path.join(UI_DIR, "pokeball.png"))
pokeball = pygame.transform.smoothscale(pokeball, (30, 30))

WIDTH, HEIGHT = 1400, 900

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

BACKGROUND = pygame.image.load(os.path.join(BASE_DIR, "assets_pokemons_fond", "bg2.png")).convert_alpha()
BACKGROUND = pygame.transform.smoothscale(BACKGROUND, (WIDTH, HEIGHT))

TYPES = {
    "feu": {
        "p": "rattata",
        "r": "reptincelle",
        "n": "galopa_f",
        "b": "salameche",
        "q": "drakofeu",
        "k": "drakofeu"
    },
    "eau": {
        "p": "rattata",
        "r": "carabaffe",
        "n": "galopa_e",
        "b": "carapuce",
        "q": "tortank",
        "k": "tortank"
    },
    "plante": {
        "p": "rattata",
        "r": "herbizarre",
        "n": "galopa_h",
        "b": "bulbizarre",
        "q": "florizarre",
        "k": "florizarre"
    }
}

TYPES_IMAGES = {
    "feu": pygame.transform.smoothscale(
        pygame.image.load(os.path.join(UI_DIR, "feu.png")).convert_alpha(), (120,120)
    ),
    "eau": pygame.transform.smoothscale(
        pygame.image.load(os.path.join(UI_DIR, "eau.png")).convert_alpha(), (120,120)
    ),
    "plante": pygame.transform.smoothscale(
        pygame.image.load(os.path.join(UI_DIR, "plante.png")).convert_alpha(), (120,120)
    )
}

# Charger images
def load_type_image(name, max_size=120):
    img = pygame.image.load(os.path.join(UI_DIR, f"{name}.png")).convert_alpha()
    w, h = img.get_size()

    scale = min(max_size / w, max_size / h)
    new_size = (int(w * scale), int(h * scale))

    return pygame.transform.smoothscale(img, new_size)

def load_images():
    images = {}
    noms = [
        "rattata","reptincelle","salameche","drakofeu",
        "carapuce","carabaffe","tortank",
        "galopa_f","galopa_e","galopa_h",
        "bulbizarre","herbizarre","florizarre"
    ]

    for nom in noms:
        img = pygame.image.load(os.path.join(ASSETS_DIR, f"{nom}.png")).convert_alpha()
        images[nom] = pygame.transform.smoothscale(img, (TAILLE_CASE, TAILLE_CASE))

    return images


TYPES_IMAGES = {
    "feu": load_type_image("feu"),
    "eau": load_type_image("eau"),
    "plante": load_type_image("plante")
}

IMAGES = load_images()

font = pygame.font.SysFont(None, 30)

# ------------------------
# PIECES
# ------------------------

class Piece:
    def __init__(self, couleur):
        self.couleur = couleur
        self.a_bouge = False

    def ennemie(self, autre):
        return autre and autre.couleur != self.couleur

    def attaques(self, x, y, plateau):
        return self.mouvements_valides(x, y, plateau)


class Pion(Piece):
    def mouvements_valides(self, x, y, plateau):
        moves = []
        dir = -1 if self.couleur == "JOUEUR" else 1

        # 1 case
        if plateau.est_vide(x, y+dir):
            moves.append((x, y+dir))

            # 2 cases si premier coup
            if not self.a_bouge and plateau.est_vide(x, y+2*dir):
                moves.append((x, y+2*dir))

        # captures
        for dx in [-1,1]:
            nx, ny = x+dx, y+dir
            if plateau.est_dans(nx, ny):
                if self.ennemie(plateau.get(nx, ny)):
                    moves.append((nx, ny))

        # PRISE EN PASSANT
        if hasattr(plateau, "jeu") and plateau.jeu.dernier_coup:
            x1,y1,x2,y2,piece = plateau.jeu.dernier_coup

            # pion adverse qui vient de faire 2 cases
            if isinstance(piece, Pion) and abs(y2 - y1) == 2:
                if y == y2 and abs(x - x2) == 1:
                    moves.append((x2, y + dir))

        return moves


class Tour(Piece):
    def mouvements_valides(self, x, y, p):
        return lignes(x,y,p,[(1,0),(-1,0),(0,1),(0,-1)], self)


class Fou(Piece):
    def mouvements_valides(self, x, y, p):
        return lignes(x,y,p,[(1,1),(-1,-1),(1,-1),(-1,1)], self)


class Dame(Piece):
    def mouvements_valides(self, x, y, p):
        return lignes(x,y,p,[(1,0),(-1,0),(0,1),(0,-1),
                             (1,1),(-1,-1),(1,-1),(-1,1)], self)


class Cavalier(Piece):
    def mouvements_valides(self, x, y, p):
        moves = []
        for dx,dy in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
            nx, ny = x+dx, y+dy
            if p.est_dans(nx, ny):
                if p.est_vide(nx, ny) or self.ennemie(p.get(nx, ny)):
                    moves.append((nx, ny))
        return moves


class Roi(Piece):
    def attaques(self, x, y, p):
        moves = []
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x+dx, y+dy
                if p.est_dans(nx, ny):
                    moves.append((nx, ny))
        return moves
    
    def mouvements_valides(self, x, y, p, ignore_roque=False):
        moves = []
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if dx==0 and dy==0: continue
                nx, ny = x+dx, y+dy
                if p.est_dans(nx, ny):
                    if p.est_vide(nx, ny) or self.ennemie(p.get(nx, ny)):
                        moves.append((nx, ny))

        # ROQUE
        if not ignore_roque and not self.a_bouge and hasattr(p, "jeu"):
            jeu = p.jeu

            # interdit si roi en échec
            if not jeu.roi_en_echec(self.couleur):
                
                # =====================
                # PETIT ROQUE (0-0)
                # =====================
                tour_droite = p.get(7, y)

                if (
                    isinstance(tour_droite, Tour)
                    and not tour_droite.a_bouge
                    and p.est_vide(5, y)
                    and p.est_vide(6, y)
                    and not jeu.case_attaquee(5, y, self.couleur)
                    and not jeu.case_attaquee(6, y, self.couleur)
                ):
                    moves.append((6, y))

                # =====================
                # GRAND ROQUE (0-0-0)
                # =====================
                tour_gauche = p.get(0, y)

                if (
                    isinstance(tour_gauche, Tour)
                    and not tour_gauche.a_bouge
                    and p.est_vide(1, y)
                    and p.est_vide(2, y)
                    and p.est_vide(3, y)
                    and not jeu.case_attaquee(3, y, self.couleur)
                    and not jeu.case_attaquee(2, y, self.couleur)
                ):
                    moves.append((2, y))
                
        return moves


# ------------------------
# UTIL
# ------------------------

def lignes(x,y,p,dirs,piece):
    moves = []
    for dx,dy in dirs:
        nx, ny = x,y
        while True:
            nx += dx
            ny += dy
            if not p.est_dans(nx,ny): break
            if p.est_vide(nx,ny):
                moves.append((nx,ny))
            else:
                if piece.ennemie(p.get(nx,ny)):
                    moves.append((nx,ny))
                break
    return moves


# ------------------------
# PLATEAU
# ------------------------

class Plateau:
    def __init__(self):
        self.reset()

    def reset(self):
        self.grid = [[None]*8 for _ in range(8)]

        for i in range(8):
            self.grid[6][i] = Pion("JOUEUR")
            self.grid[1][i] = Pion("IA")

        self.grid[7][0]=self.grid[7][7]=Tour("JOUEUR")
        self.grid[0][0]=self.grid[0][7]=Tour("IA")

        self.grid[7][1]=self.grid[7][6]=Cavalier("JOUEUR")
        self.grid[0][1]=self.grid[0][6]=Cavalier("IA")

        self.grid[7][2]=self.grid[7][5]=Fou("JOUEUR")
        self.grid[0][2]=self.grid[0][5]=Fou("IA")

        self.grid[7][3]=Dame("JOUEUR")
        self.grid[0][3]=Dame("IA")

        self.grid[7][4]=Roi("JOUEUR")
        self.grid[0][4]=Roi("IA")

    def get(self,x,y): return self.grid[y][x]
    def est_vide(self,x,y): return self.get(x,y) is None
    def est_dans(self,x,y): return 0<=x<8 and 0<=y<8


    def move(self,x1,y1,x2,y2):
        p = self.get(x1,y1)
        self.grid[y2][x2] = p
        self.grid[y1][x1] = None
        p.a_bouge = True
        return p

    def copie(self):
        return copy.deepcopy(self)


# ------------------------
# JEU
# ------------------------

class Jeu:
    def __init__(self):
        self.p = Plateau()
        self.sel = None
        self.tour = "JOUEUR"
        self.message = ""
        self.partie_terminee = False
        self.message_timer = 0
        self.duree_message = 2000  # en millisecondes (2 secondes)
        self.message_permanent = False
        self.dernier_coup = None  # (x1, y1, x2, y2, piece)
        self.p.jeu = self
        self.etat = "menu"
        self.type_joueur = None
        self.type_ia = None

    def choisir_type(self):
        print("Choisis ton type : feu ou eau")
        choix = input().lower()
        if choix not in ["feu", "eau"]:
            return "feu"
        return choix

    def set_message(self, texte, permanent = False):
        # si la partie est finie, on ne remplace pas le message
        if self.partie_terminee:
            return
        self.message = texte
        self.message_timer = pygame.time.get_ticks()
        self.message_permanent = permanent

    def roi_en_echec(self, couleur, plateau=None):
        if plateau is None:
            plateau = self.p

        roi_pos = None

        # Trouver le roi
        for y in range(8):
            for x in range(8):
                piece = plateau.get(x, y)
                if isinstance(piece, Roi) and piece.couleur == couleur:
                    roi_pos = (x, y)

        # Vérifier attaques ennemies
        for y in range(8):
            for x in range(8):
                piece = plateau.get(x, y)

                if piece and piece.couleur != couleur:

                    # CAS SPÉCIAL : ROI
                    if isinstance(piece, Roi):
                        moves = piece.attaques(x, y, plateau)
                    else:
                        moves = piece.mouvements_valides(x, y, plateau)

                    if roi_pos in moves:
                        return True
        return False
    
    def coup_legal(self,x1,y1,x2,y2):
        test = self.p.copie()
        test.move(x1,y1,x2,y2)

        return not self.roi_en_echec(self.tour, test)

    def click(self,pos,offset):
        mx,my = pos

        #Bloquer uniquement les coups après fin de partie
        if my < 8*TAILLE_CASE and self.partie_terminee :
            return
        
        x = (mx-offset)//TAILLE_CASE
        y = (my-20)//TAILLE_CASE

        if not self.p.est_dans(x,y): return

        if self.sel:
            x1,y1 = self.sel
            piece = self.p.get(x1,y1)

            if (x,y) in piece.mouvements_valides(x1,y1,self.p):
                if self.coup_legal(x1,y1,x,y):
                    # prise en passant
                    if isinstance(piece, Pion):
                        if x != x1 and self.p.est_vide(x,y):
                            # pion capturé derrière
                            self.p.grid[y1][x] = None
                    piece_jouee = self.p.move(x1,y1,x,y)
                    # PROMOTION DU PION
                    if isinstance(piece_jouee, Pion):
                        if (piece_jouee.couleur == "JOUEUR" and y == 0) or (piece_jouee.couleur == "IA" and y == 7):
                            # remplacer le pion par une dame
                            self.p.grid[y][x] = Dame(piece_jouee.couleur)
                            
                    self.dernier_coup = (x1,y1,x,y,piece_jouee)
                    self.tour = "IA" if self.tour=="JOUEUR" else "JOUEUR"
                    # Vérifier échec et mat
                    if self.est_mat(self.tour):
                        self.message = (f"ÉCHEC ET MAT ! {('JOUEUR' if self.tour=='IA' else 'IA')} gagne !")
                        self.message_permanent = True
                        self.partie_terminee = True
                    
                    # ROQUE
                    if isinstance(piece, Roi):
                        # petit roque
                        if x == 6:
                            self.p.move(7, y, 5, y)
                        # grand roque
                        elif x == 2:
                            self.p.move(0, y, 3, y)

                else:
                    self.set_message("Roi en danger !")
            else:
                self.set_message("Mouvement interdit !")

            self.sel = None

        else:
            piece = self.p.get(x,y)
            if piece and piece.couleur == self.tour:
                self.sel = (x,y)
            
    def a_coup_legal(self, couleur):
        for y in range(8):
            for x in range(8):
                piece = self.p.get(x, y)

                if piece and piece.couleur == couleur:
                    mouvements = piece.mouvements_valides(x, y, self.p)

                    for (nx, ny) in mouvements:
                        # simuler le coup
                        test = self.p.copie()
                        test.move(x, y, nx, ny)

                        # si le roi n'est plus en échec → coup légal
                        if not self.roi_en_echec(couleur, test):
                            return True

        return False
    
    def case_attaquee(self, x, y, couleur):
        """
        Retourne True si la case (x, y) est attaquée par une pièce ennemie.
        IMPORTANT : cette fonction NE DOIT PAS appeler mouvements_valides
        pour éviter les boucles de récursion infinie.
        """

        for j in range(8):
            for i in range(8):
                piece = self.p.get(i, j)

                # ignore les cases vides et les pièces alliées
                if not piece or piece.couleur == couleur:
                    continue

                # =====================================================
                # ROI : attaque sur les 8 cases adjacentes
                # =====================================================
                if isinstance(piece, Roi):
                    if max(abs(i - x), abs(j - y)) == 1:
                        return True
                    continue

                # =====================================================
                # PION : attaque uniquement en diagonale (spécifique)
                # =====================================================
                if isinstance(piece, Pion):
                    direction = -1 if piece.couleur == "JOUEUR" else 1

                    # les pions attaquent en diagonale AVANT
                    if (j + direction == y) and (abs(i - x) == 1):
                        return True
                    continue

                # =====================================================
                # CAVALIER : déplacement en L (pattern fixe)
                # =====================================================
                if isinstance(piece, Cavalier):
                    if (abs(i - x), abs(j - y)) in [(1, 2), (2, 1)]:
                        return True
                    continue

                # =====================================================
                # TOUR / FOU / DAME : attaque par ligne
                # sans utiliser mouvements_valides (IMPORTANT)
                # =====================================================

                dx = x - i
                dy = y - j

                # vérifier si la pièce peut attaquer selon sa géométrie
                is_rook_line = (dx == 0 or dy == 0)
                is_bishop_line = (abs(dx) == abs(dy))

                if is_rook_line or is_bishop_line:

                    step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
                    step_y = 0 if dy == 0 else (1 if dy > 0 else -1)

                    cx, cy = i + step_x, j + step_y

                    # on avance jusqu'à la case cible
                    blocked = False
                    while (cx, cy) != (x, y):

                        # si une pièce bloque le chemin → pas d'attaque possible
                        if not self.p.est_vide(cx, cy):
                            blocked = True
                            break

                        cx += step_x
                        cy += step_y

                    # si chemin libre → attaque valide
                    if not blocked:
                        return True

        return False
    
    def est_mat(self, couleur):
        return self.roi_en_echec(couleur) and not self.a_coup_legal(couleur)

# ------------------------
# AFFICHAGE
# ------------------------

def draw(jeu):
    WIDTH, HEIGHT = screen.get_size()
    bg = pygame.transform.smoothscale(BACKGROUND, (WIDTH, HEIGHT))
    screen.blit(bg, (0,0))

    offset = (WIDTH//2) - 320

    for y in range(8):
        for x in range(8):
            couleur = (240,217,181) if (x+y)%2==0 else (181,136,99)
            rect = pygame.Rect(offset + x*TAILLE_CASE, y*TAILLE_CASE+20, TAILLE_CASE, TAILLE_CASE)
            pygame.draw.rect(screen, couleur, rect)

            # sélection
            if jeu.sel == (x,y):
                pygame.draw.rect(screen,(0,0,0),rect,3)

            piece = jeu.p.get(x,y)
            if piece:
                mapping = {
                    Pion: "p",
                    Tour: "r",
                    Cavalier: "n",
                    Fou: "b",
                    Dame: "q",
                    Roi: "k"
                }

                type_piece = mapping[type(piece)]

                if piece.couleur == "JOUEUR":
                    pokemon = TYPES[jeu.type_joueur][type_piece]
                else:
                    pokemon = TYPES[jeu.type_ia][type_piece]

                screen.blit(IMAGES[pokemon], rect)

    # contour rouge si roi en échec
    for y in range(8):
        for x in range(8):
            piece = jeu.p.get(x,y)
            if isinstance(piece, Roi):
                if jeu.roi_en_echec(piece.couleur):
                    rect = pygame.Rect(offset+x*TAILLE_CASE, y*TAILLE_CASE+20, TAILLE_CASE, TAILLE_CASE)
                    pygame.draw.rect(screen,(255,0,0),rect,4)

    pygame.draw.rect(screen,(0,0,0),((WIDTH//2)-90,690,180,40))
    txt = font.render(f"Tour : {jeu.tour}", True, (255,255,255) )
    screen.blit(txt,((WIDTH//2)-74,700))

    bouton_rect = pygame.Rect((WIDTH//2)-90, 760, 185, 40)
    pygame.draw.rect(screen,(0,0,0), bouton_rect)
    screen.blit(font.render("Nouvelle partie",True,(255,255,255)),((WIDTH//2)-74,770))

    temps_actuel = pygame.time.get_ticks()

    if jeu.message :
        if jeu.message_permanent or (temps_actuel - jeu.message_timer < jeu.duree_message):
            txt = font.render(jeu.message, True, (200,0,0))
            screen.blit(txt,(20,380))

    board_rect = pygame.Rect(offset - 11, 20 - 11, 8 * TAILLE_CASE + 25, 8 * TAILLE_CASE + 25)

    pygame.draw.rect(screen, (20, 20, 20), board_rect, 20)

    screen.blit(pokeball, (board_rect.left-5, board_rect.top-5))
    screen.blit(pokeball, (board_rect.right-25, board_rect.top-5))
    screen.blit(pokeball, (board_rect.left -5, board_rect.bottom -25))
    screen.blit(pokeball, (board_rect.right -25, board_rect.bottom -25))
    
    screen.blit(pokeball, (board_rect.left +315, board_rect.top-5))
    screen.blit(pokeball, (board_rect.left -5, board_rect.top +315))
    screen.blit(pokeball, (board_rect.right -350, board_rect.bottom -25))
    screen.blit(pokeball, (board_rect.right -25, board_rect.bottom -350))

    # Texte Player / IA

    pygame.draw.rect(screen,(0,0,0),(WIDTH//10,90,100,40))
    txt_ia = font.render("IA (Noir)", True, (255,255,255))
    screen.blit(txt_ia, (WIDTH//10+10, 100))

    pygame.draw.rect(screen,(0,0,0),(WIDTH-(WIDTH*(1/6)),90,180,40))
    txt_player = font.render("JOUEUR (Blanc)", True, (255,255,255))
    screen.blit(txt_player, (WIDTH-(WIDTH*(1/6))+10, 100))

    return offset, bouton_rect

def draw_menu(jeu):
    WIDTH, HEIGHT = screen.get_size()

    # fond assombri
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0,0,0))
    screen.blit(overlay, (0,0))

    # fenêtre centrale (petite)
    menu_width = 500
    menu_height = 300
    menu_x = WIDTH//2 - menu_width//2
    menu_y = HEIGHT//2 - menu_height//2

    pygame.draw.rect(screen, (40,40,40), (menu_x, menu_y, menu_width, menu_height), border_radius=15)
    pygame.draw.rect(screen, (255,255,255), (menu_x, menu_y, menu_width, menu_height), 2, border_radius=15)

    # titre
    title = font.render("Choisis ton type", True, (255,255,255))
    screen.blit(title, (menu_x + 150, menu_y + 20))

    rects = {}

    types = ["feu", "eau", "plante"]

    # positions centrées
    spacing = 140
    start_x = menu_x + 70

    mouse_pos = pygame.mouse.get_pos()

    for i, t in enumerate(types):
        x = start_x + i * spacing
        y = menu_y + 100

        img = TYPES_IMAGES[t]
        rect = pygame.Rect(0, 0, 120, 120)
        rect.center = (x, y)
        img_rect = img.get_rect(center=rect.center)
        screen.blit(img, img_rect)

        # texte en dessous
        label = font.render(t.capitalize(), True, (255,255,255))
        label_y = y + 80  # valeur fixe propre
        screen.blit(label, (rect.centerx - label.get_width()//2, label_y))

        rects[t] = rect
        if rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (255,255,255), rect, 3, border_radius=10)

    return rects

# ------------------------
# MAIN
# ------------------------

jeu = Jeu()

while True:

    if jeu.etat == "menu":
        rects_types = draw_menu(jeu)
    else:
        offset, bouton_rect = draw(jeu)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if e.type == pygame.MOUSEBUTTONDOWN:

            # CAS MENU
            if jeu.etat == "menu":
                for t, rect in rects_types.items():
                    if rect.collidepoint(e.pos):
                        jeu.type_joueur = t

                        if t == "feu":
                            jeu.type_ia = "eau"
                        elif t == "eau":
                            jeu.type_ia = "feu"
                        else:
                            jeu.type_ia = "feu"

                        jeu.etat = "jeu"

            # CAS JEU NORMAL
            else:
                if bouton_rect.collidepoint(e.pos):
                    jeu = Jeu()
                else:
                    jeu.click(e.pos, offset)

    pygame.display.flip()