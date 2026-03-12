import pygame
import sys
import subprocess
import cv2
pygame.init()

# Initialiser le mixer avec gestion d'erreur
try:
    pygame.mixer.init()
except pygame.error:
    print("Périphérique audio non disponible - le jeu fonctionnera sans son")

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

# Ressources
background = pygame.image.load("assets/imgs/backgrounds/main_menu_bg.png")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

cinématique = cv2.VideoCapture("assets/cutscenes/starting_cutscene.mp4")

pygame.mixer.music.load("assets/sounds/musics/music.mp3")
pygame.mixer.music.set_volume(0.1)
pygame.mixer.music.play(-1)


# Image d'Elon

elon_img = pygame.image.load("assets/imgs/backgrounds/elon_crying.png")
elon_img = pygame.transform.scale(elon_img, (WIDTH, HEIGHT))

Scène_de_N = pygame.image.load("assets/imgs/other/Bg2.png")
Scène_de_N = pygame.transform.scale(Scène_de_N, (WIDTH, HEIGHT))

# Polices

FONT_TITLE = pygame.font.Font("assets/fonts/Minecraft.ttf", 72)
FONT_BUTTON = pygame.font.Font("assets/fonts/Minecraft.ttf", 36)

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
    
    Button("Nouvelle partie", 320, "new"),
    Button("Charger Partie", 400, "load"),
    Button("Tuer Elon Musk ?", 480, "options"),
    Button("Quitter", 560, "quit")
   
]

running = True
clock = pygame.time.Clock()

current_scene = "menu"
while running:
    clock.tick(60)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False


    # SCÈNE 1 : LE MENU 
  
    if current_scene == "menu":
        screen.blit(background, (0, 0))

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        title = FONT_TITLE.render("POKEMON CHESS", True, WHITE)
        shadow = FONT_TITLE.render("POKEMON CHESS", True, SHADOW)
        
        screen.blit(shadow, (WIDTH // 2 - title.get_width() // 2 + 4, 104))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        for btn in buttons:
            btn.draw(screen, mouse_pos)
            
            if btn.is_clicked(mouse_pos, mouse_pressed):
                pygame.time.delay(200)
                if btn.action == "new":
                    current_scene = "introduction"
                elif btn.action == "load":
                    print("Charger Partie")
                elif btn.action == "options":
                    current_scene = "image_elon"
                    pygame.mixer.music.load("assets/sounds/musics/caca.mp3")
                    pygame.mixer.music.set_volume(0.1)
                    pygame.mixer.music.play(-1)
                elif btn.action == "quit":
                    running = False 

   
    # SCÈNE 2 : IMAGE D'ELON QUI PLEURE

    elif current_scene == "image_elon":
        screen.blit(elon_img, (0, 0))

        ligne1 = "Il est ridicule, retourne au menu !"
        n_text1 = FONT_BUTTON.render(ligne1, True, WHITE)
        n_shadow1 = FONT_BUTTON.render(ligne1, True, SHADOW)
        text_x1 = WIDTH // 2 - n_text1.get_width() // 2
        text_y1 = HEIGHT - 140
        screen.blit(n_shadow1, (text_x1 + 2, text_y1 + 2))
        screen.blit(n_text1, (text_x1, text_y1))
        
        
        
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]: 
            pygame.time.delay(200) 
            current_scene = "menu"
            pygame.mixer.music.load("assets/sounds/musics/music.mp3")
            pygame.mixer.music.set_volume(0.1)
            pygame.mixer.music.play(-1)
    
    elif current_scene == "introduction":
        screen.blit(Scène_de_N, (0, 0))
    
        ligne1 = "Bienvenue jeune dresseur !"
        n_text1 = FONT_BUTTON.render(ligne1, True, WHITE)
        n_shadow1 = FONT_BUTTON.render(ligne1, True, SHADOW)
        text_x1 = WIDTH // 2 - n_text1.get_width() // 2
        text_y1 = HEIGHT - 140
        screen.blit(n_shadow1, (text_x1 + 2, text_y1 + 2))
        screen.blit(n_text1, (text_x1, text_y1))


        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:
            pygame.time.delay(200) 
            current_scene = "cinématique"
            cinématique.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    # SCÈNE 3 : CINÉMATIQUE
    elif current_scene == "cinématique":
        # protect against VideoCapture failures
        if not cinématique.isOpened():
            print("Ciné non ouverte, retour au menu")
            current_scene = "menu"
        else:
            try:
                ret, frame = cinématique.read()
            except Exception as e:
                print("Erreur lecture cinématique:", e)
                current_scene = "menu"
                ret = False
                frame = None
            if ret and frame is not None:
                try:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(frame, (WIDTH, HEIGHT))
                    frame_surf = pygame.image.fromstring(frame.tobytes(), frame.shape[1::-1], "RGB")
                    screen.blit(frame_surf, (0, 0))
                except Exception as e:
                    print("Erreur affichage frame:", e)
                    current_scene = "menu"
            else:
                current_scene = "menu"
        
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:
            pygame.time.delay(200)
            current_scene = "menu"
    
    pygame.display.flip()



pygame.quit()
sys.exit()
