import pygame
import sys
import cv2
import os
from game import Game  # Import de ton moteur de jeu

def lancer_menu():
    pygame.init()
    
    # --- TA CONFIGURATION EXACTE ---
    try:
        pygame.mixer.init()
    except pygame.error:
        print("Périphérique audio non disponible")

    WIDTH, HEIGHT = 1080, 720
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mon jeux")

    # Couleurs
    WHITE = (255, 255, 255)
    TRANSLUCENT_BLUE = (0, 80, 200, 180)
    HOVER_BLUE = (0, 140, 255, 220)
    SHADOW = (0, 0, 0)

    # Polices
    FONT_TITLE = pygame.font.Font("assets/Minecraft.ttf", 72)
    FONT_BUTTON = pygame.font.Font("assets/Minecraft.ttf", 36)

    # Ressources
    background = pygame.image.load("assets/Bg1.png")
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))
    elon_img = pygame.image.load("assets/elon_crying.png")
    elon_img = pygame.transform.scale(elon_img, (WIDTH, HEIGHT))
    Scène_de_N = pygame.image.load("assets/Bg2.png")
    Scène_de_N = pygame.transform.scale(Scène_de_N, (WIDTH, HEIGHT))
    cinématique = cv2.VideoCapture("assets/cinématique.mp4")

    # Musique initiale
    if os.path.exists("assets/music.mp3"):
        pygame.mixer.music.load("assets/music.mp3")
        pygame.mixer.music.set_volume(0.1)
        pygame.mixer.music.play(-1)

    # --- TA CLASSE BUTTON ---
    class Button:
        def __init__(self, text, center_y, action):
            self.text = text 
            self.action = action 
            self.center_y = center_y
            self.width, self.height = 380, 70 # Légèrement élargi pour les nouveaux textes
            self.rect = pygame.Rect((0, 0, self.width, self.height))
            self.rect.center = (WIDTH // 2, center_y)
        
        def draw(self, win, mouse_pos):
            is_hover = self.rect.collidepoint(mouse_pos)
            color = HOVER_BLUE if is_hover else TRANSLUCENT_BLUE
            button_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.rect(button_surface, color, (0, 0, self.width, self.height), border_radius=16)
            win.blit(button_surface, self.rect)

            text_surf = FONT_BUTTON.render(self.text, True, WHITE)
            text_rect = text_surf.get_rect(center=self.rect.center)
            shadow = FONT_BUTTON.render(self.text, True, SHADOW)
            win.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
            win.blit(text_surf, text_rect)

        def is_clicked(self, mouse_pos, clicked):
            return self.rect.collidepoint(mouse_pos) and clicked

    # --- LISTES DES BOUTONS ---
    buttons_menu = [
        Button("Nouvelle partie", 320, "new"),
        Button("Charger Partie", 400, "load"),
        Button("Tuer Elon Musk ?", 480, "options"),
        Button("Quitter", 560, "quit")
    ]

    buttons_choix = [
        Button("Jouer Sacha", 320, "ash_atchoum_walk.png"),
        Button("Jouer Pikachu", 420, "pikachu.png")
    ]

    running = True
    clock = pygame.time.Clock()
    current_scene = "menu"

    # --- BOUCLE PRINCIPALE ---
    while running:
        clock.tick(60)
        mouse_pos = pygame.mouse.get_pos()
        
        # GESTION DU CLIC UNIQUE
        click_event = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    click_event = True

        # SCÈNE 1 : LE MENU 
        if current_scene == "menu":
            screen.blit(background, (0, 0))
            title = FONT_TITLE.render("POKEMON CHESS", True, WHITE)
            shadow = FONT_TITLE.render("POKEMON CHESS", True, SHADOW)
            screen.blit(shadow, (WIDTH // 2 - title.get_width() // 2 + 4, 104))
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

            for btn in buttons_menu:
                btn.draw(screen, mouse_pos)
                if btn.is_clicked(mouse_pos, click_event):
                    if btn.action == "new":
                        current_scene = "introduction"
                    elif btn.action == "load":
                        print("Charger Partie")
                    elif btn.action == "options":
                        current_scene = "image_elon"
                        pygame.mixer.music.load("assets/caca.mp3")
                        pygame.mixer.music.play(-1)
                    elif btn.action == "quit":
                        pygame.quit()
                        sys.exit()

        # SCÈNE 2 : ELON
        elif current_scene == "image_elon":
            screen.blit(elon_img, (0, 0))
            ligne1 = "Il est ridicule, retourne au menu !"
            txt = FONT_BUTTON.render(ligne1, True, WHITE)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT - 140))
            
            if click_event: 
                current_scene = "menu"
                pygame.mixer.music.load("assets/music.mp3")
                pygame.mixer.music.play(-1)

        # SCÈNE 3 : INTRO
        elif current_scene == "introduction":
            screen.blit(Scène_de_N, (0, 0))
            ligne1 = "Bienvenue jeune dresseur ! (Cliquez pour la suite)"
            txt = FONT_BUTTON.render(ligne1, True, WHITE)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT - 140))

            if click_event:
                current_scene = "cinématique"
                cinématique.set(cv2.CAP_PROP_POS_FRAMES, 0)

        # SCÈNE 4 : CINÉMATIQUE
        elif current_scene == "cinématique":
            ret, frame = cinématique.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (WIDTH, HEIGHT))
                frame_surf = pygame.image.fromstring(frame.tobytes(), frame.shape[1::-1], "RGB")
                screen.blit(frame_surf, (0, 0))
                
                if click_event: # On skip la vidéo et on va au choix du perso
                    
                    current_scene = "choix_perso"
            else:
                # Vidéo finie
                
                current_scene = "choix_perso"
                
        # SCÈNE 5 : CHOIX DU PERSONNAGE
        elif current_scene == "choix_perso":
            screen.blit(background, (0, 0)) # On garde le même fond de menu
            titre = FONT_TITLE.render("CHOISIS TON HEROS", True, WHITE)
            shadow = FONT_TITLE.render("CHOISIS TON HEROS", True, SHADOW)
            screen.blit(shadow, (WIDTH // 2 - titre.get_width() // 2 + 4, 104))
            screen.blit(titre, (WIDTH // 2 - titre.get_width() // 2, 100))

            for btn in buttons_choix:
                btn.draw(screen, mouse_pos)
                if btn.is_clicked(mouse_pos, click_event):
                    # On retourne le nom du fichier image sélectionné
                    return btn.action 

        pygame.display.flip()

# --- EXECUTION FINALE ---
if __name__ == "__main__":
    # resultat contient soit "ash_atchoum_walk.png" soit "pikachu.png"
    resultat = lancer_menu()
    
    if resultat: # Sécurité si on a fermé la fenêtre en plein milieu
        # On passe le sprite choisi à la classe Game
        mon_jeu = Game(resultat)
        mon_jeu.run()