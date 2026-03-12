import pygame
import sys
import subprocess

pygame.init()

# Fenetre
WIDTH, HEIGHT = 1080, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mon jeux")

# Couleurs
WHITE = (255, 255, 255)
TRANSLUCENT_BLUE = (0, 80, 200, 180)
HOVER_BLUE = (0, 140, 255, 220)
SHADOW = (0, 0, 0)
YELLOW = (255, 255, 0)
GOLD = (255, 215, 0)



background = pygame.image.load("assets/bg.png")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))


elon_img = pygame.image.load("assets/elon_crying.png")
elon_img = pygame.transform.scale(elon_img, (WIDTH, HEIGHT))

FONT_TITLE = pygame.font.Font("assets/Minecraft.ttf", 72)
FONT_BUTTON = pygame.font.Font("assets/Minecraft.ttf", 36)


class Button:
    def __init__(self, text, center_y, action):
        self.text = text 
        self.action = action 
        self.center_y = center_y
        self.width, self.height = 320, 70
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

    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]
    
# Listes des boutons 
buttons = [
    Button("Voulez voir la suite ?", 320, "new"),
    Button("Quitter", 560, "quit")
]

running = True
clock = pygame.time.Clock()

current_scene = "menu"
user_text = ""  # Variable pour stocker la réponse du joueur

while running:
    clock.tick(60)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # --- GESTION DU CLAVIER POUR LA QUESTION ---
        if event.type == pygame.KEYDOWN and current_scene == "question_elon":
            if event.key == pygame.K_RETURN:
                # L'utilisateur appuie sur Entrée : on vérifie sa réponse
                if user_text.strip().lower() == "oui":
                    current_scene = "image_elon"
                    
                    pygame.mixer.music.load("assets/caca.mp3")
                    pygame.mixer.music.set_volume(0.1)
                    pygame.mixer.music.play(-1)
                   
                else:
                    # Mauvaise réponse, on retourne au menu
                    current_scene = "menu"
            elif event.key == pygame.K_BACKSPACE:
                # Effacer la dernière lettre
                user_text = user_text[:-1]
            else:
                # Ajouter la lettre tapée (on limite la longueur pour ne pas sortir de l'écran)
                if len(user_text) < 15:
                    user_text += event.unicode
        # -------------------------------------------

    # SCÈNE 1 : LE MENU 
    if current_scene == "menu":
        screen.blit(background, (0, 0))

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        title = FONT_TITLE.render("POKEMON CHESS", True, GOLD)
        shadow = FONT_TITLE.render("POKEMON CHESS", True, SHADOW)
        
        screen.blit(shadow, (WIDTH // 2 - title.get_width() // 2 + 4, 104))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        for btn in buttons:
            btn.draw(screen, mouse_pos)
            
            if btn.is_clicked(mouse_pos, mouse_pressed):
                pygame.time.delay(200)
                if btn.action == "new":
                    pygame.quit()
                    subprocess.run(['python', "new_game.py"])
                    sys.exit()
                elif btn.action == "load":
                    print("Charger Partie")
                elif btn.action == "options":
                    current_scene = "question_elon"
                    user_text = "" # On réinitialise le texte à chaque fois
                elif btn.action == "quit":
                    running = False 

    # -------------------------------------
    # SCÈNE 2 : LA QUESTION (Saisie clavier)
    # -------------------------------------
    elif current_scene == "question_elon":
        screen.blit(background, (0, 0))

        # Afficher la question
        question_text = FONT_BUTTON.render("Es-tu sur ? Tape OUI pour confirmer :", True, WHITE)
        screen.blit(question_text, (WIDTH // 2 - question_text.get_width() // 2, 200))

        # Curseur clignotant
        cursor = "|" if pygame.time.get_ticks() % 1000 < 500 else ""
        
        # Préparer le texte tapé par le joueur + le curseur
        input_text = FONT_TITLE.render(user_text + cursor, True, GOLD)
        
        # Dessiner la boîte semi-transparente
        box_width = max(300, input_text.get_width() + 50)
        box_height = 90
        input_box_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(input_box_surface, (0, 0, 0, 150), (0, 0, box_width, box_height), border_radius=12)
        
        box_x = WIDTH // 2 - box_width // 2
        box_y = 350 - 10
        screen.blit(input_box_surface, (box_x, box_y))

        # Afficher le texte par-dessus la boîte
        screen.blit(input_text, (WIDTH // 2 - input_text.get_width() // 2, 350))

        # Indication
        info_text = FONT_BUTTON.render("Appuie sur Entree pour valider", True, WHITE)
        screen.blit(info_text, (WIDTH // 2 - info_text.get_width() // 2, 500))

    # -------------------------------------
    # SCÈNE 3 : IMAGE D'ELON QUI PLEURE
    # -------------------------------------
    elif current_scene == "image_elon":
        screen.blit(elon_img, (0, 0))
        
        retour_text = FONT_BUTTON.render("Cliquez pour retourner au menu", True, WHITE)
        retour_shadow = FONT_BUTTON.render("Cliquez pour retourner au menu", True, SHADOW)
        
        text_x = WIDTH // 2 - retour_text.get_width() // 2
        text_y = HEIGHT - 50
        
        screen.blit(retour_shadow, (text_x + 2, text_y + 2))
        screen.blit(retour_text, (text_x, text_y))
        
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]: 
            pygame.time.delay(200) 
            current_scene = "menu"
            try:
                pygame.mixer.music.load("assets/music.mp3")
                pygame.mixer.music.set_volume(0.1)
                pygame.mixer.music.play(-1)
            except:
                pass

    pygame.display.flip()

pygame.quit()
sys.exit()


