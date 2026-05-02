"""
main.py — Point d'entrée unique de PokeChess.
Lancer depuis la racine : python main.py
"""

import sys
import os
import math
import random

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame
import save as save_module
from game.engine.game import Game

_UI   = "game/assets/images/ui"
_ANIM = "game/assets/images/anim"
_MUS  = "game/assets/music"
_FNT  = "game/assets/fonts"


# ---------------------------------------------------------------------------
# Particules menu
# ---------------------------------------------------------------------------
class _Particle:
    def __init__(self, W, H, img):
        self.img = img
        self.W, self.H = W, H
        self._reset()

    def _reset(self):
        self.x     = random.uniform(0, self.W)
        self.y     = random.uniform(0, self.H)
        self.vy    = random.uniform(-0.35, -1.1)
        self.vx    = random.uniform(-0.18, 0.18)
        self.alpha = random.randint(35, 110)
        self.scale = random.uniform(0.45, 1.15)

    def update(self):
        self.y += self.vy
        self.x += self.vx
        if self.y < -40:
            self._reset()
            self.y = self.H + 5

    def draw(self, surface):
        s   = max(1, int(26 * self.scale))
        img = pygame.transform.smoothscale(self.img, (s, s))
        img.set_alpha(self.alpha)
        surface.blit(img, (int(self.x), int(self.y)))


# ---------------------------------------------------------------------------
# Écran d'intro animé (frames anim/)
# ---------------------------------------------------------------------------
def lancer_intro(screen: pygame.Surface) -> None:
    """Joue l'animation intro et attend ENTRÉE."""
    W, H   = screen.get_size()
    clock  = pygame.time.Clock()

    try:
        font_press = pygame.font.Font(f"{_FNT}/Minecraft.ttf", 22)
    except Exception:
        font_press = pygame.font.SysFont("Arial", 22, bold=True)

    # Charger les frames
    frames = []
    for i in range(1, 6):
        path = f"{_ANIM}/menu_{i:04d}.png"
        raw  = pygame.image.load(path)
        # Mise à l'échelle en letterbox (préserve 16:9)
        scale    = min(W / raw.get_width(), H / raw.get_height())
        new_w    = int(raw.get_width()  * scale)
        new_h    = int(raw.get_height() * scale)
        scaled   = pygame.transform.scale(raw, (new_w, new_h))
        frame_surf = pygame.Surface((W, H))
        frame_surf.fill((0, 0, 0))
        frame_surf.blit(scaled, ((W - new_w) // 2, (H - new_h) // 2))
        frames.append(frame_surf)

    frame_idx   = 0
    frame_timer = 0.0
    FRAME_DUR   = 1 / 3  # 3 fps — animation lente

    while True:
        dt = clock.tick(60) / 1000
        frame_timer += dt

        if frame_timer >= FRAME_DUR:
            frame_timer = 0.0
            frame_idx   = (frame_idx + 1) % len(frames)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                return

        screen.blit(frames[frame_idx], (0, 0))
        pygame.display.flip()


# ---------------------------------------------------------------------------
# Menu principal
# ---------------------------------------------------------------------------
def lancer_menu(screen: pygame.Surface, save_data: dict) -> str | None:
    W, H = screen.get_size()

    try:
        FONT_TITLE = pygame.font.Font(f"{_FNT}/Minecraft.ttf", 58)
        FONT_BTN   = pygame.font.Font(f"{_FNT}/Minecraft.ttf", 28)
        FONT_SMALL = pygame.font.Font(f"{_FNT}/Minecraft.ttf", 17)
    except Exception:
        FONT_TITLE = pygame.font.SysFont("Arial", 58, bold=True)
        FONT_BTN   = pygame.font.SysFont("Arial", 28, bold=True)
        FONT_SMALL = pygame.font.SysFont("Arial", 17)

    WHITE  = (255, 255, 255)
    BLACK  = (0, 0, 0)
    BLUE_T = (0, 80, 200, 170)
    BLUE_H = (0, 150, 255, 220)

    bg_menu  = pygame.transform.scale(pygame.image.load(f"{_UI}/bg_menu.png"),  (W, H))
    bg_intro = pygame.transform.scale(pygame.image.load(f"{_UI}/bg_intro.png"), (W, H))
    elon_img = pygame.transform.scale(pygame.image.load(f"{_UI}/elon.png"),     (W, H))
    pb_raw   = pygame.image.load("game/assets/images/chess/pokeball.png")

    particles = [_Particle(W, H, pb_raw) for _ in range(22)]
    for p in particles:
        p.y = random.uniform(0, H)

    title_tick = 0.0
    has_save   = bool(save_data.get("bosses_vaincus") or save_data.get("personnage"))

    class Button:
        def __init__(self, text, cy, action, w=340, h=62):
            self.text   = text
            self.action = action
            self.rect   = pygame.Rect(0, 0, w, h)
            self.rect.center = (W // 2, cy)

        def draw(self, win, mouse):
            hover = self.rect.collidepoint(mouse)
            col   = BLUE_H if hover else BLUE_T
            surf  = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(surf, col, (0, 0, *self.rect.size), border_radius=14)
            win.blit(surf, self.rect)
            if hover:
                pygame.draw.rect(win, (180, 220, 255, 100), self.rect, 2, border_radius=14)
            tx = FONT_BTN.render(self.text, True, WHITE)
            sh = FONT_BTN.render(self.text, True, BLACK)
            win.blit(sh, tx.get_rect(center=self.rect.center).move(2, 2))
            win.blit(tx, tx.get_rect(center=self.rect.center))

        def clicked(self, mouse, click):
            return self.rect.collidepoint(mouse) and click

    start_y = 300 if has_save else 320
    dy      = 78
    menu_btns = [b for b in [
        Button("Nouvelle Partie", start_y,        "new"),
        Button("Continuer",       start_y + dy,   "load") if has_save else None,
        Button("Tuer Elon ?",     start_y + 2*dy, "kill_elon"),
        Button("Quitter",         start_y + 3*dy, "quit"),
    ] if b]

    choix_btns = [
        Button("Jouer Sacha",   310, "ash.png"),
        Button("Jouer Pikachu", 400, "pikachu.png"),
    ]

    clock   = pygame.time.Clock()
    scene   = "menu"
    is_new  = False   # True si le joueur a cliqué "Nouvelle Partie"

    while True:
        dt    = clock.tick(60) / 1000
        mouse = pygame.mouse.get_pos()
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        # ---- MENU ----
        if scene == "menu":
            screen.blit(bg_menu, (0, 0))
            for p in particles:
                p.update()
                p.draw(screen)

            title_tick += dt * 1.8
            scale  = 1.0 + 0.018 * math.sin(title_tick)
            t_base = FONT_TITLE.render("POKEMON CHESS", True, WHITE)
            t_w    = int(t_base.get_width() * scale)
            t_h    = int(t_base.get_height() * scale)
            t_sc   = pygame.transform.smoothscale(t_base, (t_w, t_h))
            s_base = FONT_TITLE.render("POKEMON CHESS", True, BLACK)
            s_sc   = pygame.transform.smoothscale(s_base, (t_w, t_h))
            tx = W // 2 - t_w // 2
            screen.blit(s_sc, (tx + 3, 100 + 3))
            screen.blit(t_sc, (tx, 100))

            for btn in menu_btns:
                btn.draw(screen, mouse)
                if btn.clicked(mouse, click):
                    if btn.action == "new":
                        is_new = True
                        scene  = "intro"
                    elif btn.action == "load":
                        is_new = False
                        if save_data.get("personnage"):
                            return save_data["personnage"], False
                        scene = "choix_perso"
                    elif btn.action == "kill_elon":
                        pygame.mixer.music.load(f"{_MUS}/elon.mp3")
                        pygame.mixer.music.play(-1)
                        scene = "elon"
                    elif btn.action == "quit":
                        return None

            if has_save:
                nb  = len(save_data.get("bosses_vaincus", []))
                txt = FONT_SMALL.render(f"Progression : {nb}/4 boss vaincus", True, (200, 220, 255))
                screen.blit(txt, (W // 2 - txt.get_width() // 2, H - 36))

        # ---- ELON ----
        elif scene == "elon":
            screen.blit(elon_img, (0, 0))
            txt = FONT_BTN.render("Il est ridicule, retourne au menu !", True, WHITE)
            screen.blit(txt, (W // 2 - txt.get_width() // 2, H - 110))
            if click:
                pygame.mixer.music.load(f"{_MUS}/theme.mp3")
                pygame.mixer.music.play(-1)
                scene = "menu"

        # ---- INTRO ----
        elif scene == "intro":
            screen.blit(bg_intro, (0, 0))
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 80))
            screen.blit(overlay, (0, 0))
            txt = FONT_BTN.render("Bienvenue, jeune dresseur !", True, WHITE)
            screen.blit(FONT_BTN.render("Bienvenue, jeune dresseur !", True, BLACK),
                        (W // 2 - txt.get_width() // 2 + 2, H - 108))
            screen.blit(txt, (W // 2 - txt.get_width() // 2, H - 110))
            sub = FONT_SMALL.render("cliquez pour continuer", True, (180, 180, 180))
            screen.blit(sub, (W // 2 - sub.get_width() // 2, H - 70))
            if click:
                scene = "choix_perso"

        # ---- CHOIX PERSO ----
        elif scene == "choix_perso":
            screen.blit(bg_menu, (0, 0))
            for p in particles:
                p.update()
                p.draw(screen)
            titre = FONT_TITLE.render("CHOISIS TON HÉROS", True, WHITE)
            screen.blit(FONT_TITLE.render("CHOISIS TON HÉROS", True, BLACK),
                        (W // 2 - titre.get_width() // 2 + 3, 103))
            screen.blit(titre, (W // 2 - titre.get_width() // 2, 100))
            for btn in choix_btns:
                btn.draw(screen, mouse)
                if btn.clicked(mouse, click):
                    return btn.action, is_new

        pygame.display.flip()


# ---------------------------------------------------------------------------
def main():
    pygame.init()
    try:
        pygame.mixer.init()
    except pygame.error:
        print("Audio non disponible.")

    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("PokeChess")

    save_data = save_module.charger()

    # Animation intro (frames anim/) avant le menu
    lancer_intro(screen)

    pygame.mixer.music.load(f"{_MUS}/theme.mp3")
    pygame.mixer.music.set_volume(0.05)
    pygame.mixer.music.play(-1)

    result = lancer_menu(screen, save_data)
    if result is None:
        pygame.quit()
        sys.exit()

    sprite, is_new = result

    # Nouvelle Partie → toujours réinitialiser la sauvegarde
    if is_new:
        save_data = save_module.reset()
    elif save_data.get("personnage") != sprite:
        save_data = save_module.reset()

    save_data["personnage"] = sprite
    save_module.sauvegarder(save_data)

    Game(screen, sprite, save_data).run()


if __name__ == "__main__":
    main()
