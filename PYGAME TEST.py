import pygame
import sys
import subprocess

pygame.init()

#Fenetre
WIDTH, HEIGHT = 1080, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mon jeux")

#Ressources
background = pygame.image.load("assets/bg.png")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

elon_img = pygame.image.load("assets/elon_crying.png")
elon_img = pygame.transform.scale(elon_img, (WIDTH, HEIGHT))
pygame.mixer.music.load("assets/music.mp3")
pygame.mixer.music.play(-1)

#Couleurs
WHITE = (255, 255, 255)
TRANSLUCENT_BLUE = (0,80,200,180)
HOVER_BLUE = (0,140,255,220)
SHADOW = (0,0,0)
YELLOW = (255, 255, 0)      # Jaune classique, très visible
GOLD = (255, 215, 0)        # Or, un peu plus chaleureux
CYAN = (0, 255, 255)        # Bleu clair fluo
NEON_GREEN = (57, 255, 20)
#polices
try:
    FONT_TITLE = pygame.font.Font("assets/Minecraft.ttf", 72)
    FONT_BUTTON = pygame.font.Font("assets/Minecraft.ttf",36)

except : 
    FONT_TITLE = pygame.font.SysFont(None,72)
    FONT_BUTTON = pygame.font.SysFont(None,36)

class Button:
    def __init__(self, text, center_y, action):
        self.text = text 
        self.action = action 
        self.center_y = center_y
        self.width, self.height = 320,70
        self.rect = pygame.Rect((0,0,self.width,self.height))
        self.rect.center = (WIDTH//2,center_y)
    
    def draw(self, win, mouse_pos):
        is_hover = self.rect.collidepoint(mouse_pos)
        color = HOVER_BLUE if is_hover else TRANSLUCENT_BLUE
        button_surface = pygame.Surface((self.width,self.height),pygame.SRCALPHA)
        pygame.draw.rect(button_surface,color,(0,0,self.width,self.height), border_radius=16)
        win.blit(button_surface, self.rect)

        text_surf = FONT_BUTTON.render(self.text,True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)

        shadow = FONT_BUTTON.render(self.text, True, SHADOW)
        win.blit(shadow, (text_rect.x+2, text_rect.y+2))
        win.blit(text_surf, text_rect)

    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]
    
#listes des boutons 


buttons = [
    Button("Nouvelle partie", 320, "new"),
    Button("Charger Partie", 400, "load"),
    Button("Tuer Elon Musk ?", 480, "options"),
    Button("Quitter", 560, "quit")
]

running = True
clock = pygame.time.Clock()

while running:
    clock.tick(60)
    screen.blit(background,(0,0))

    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()

    title = FONT_TITLE.render("Pokémon Chess", True, GOLD)
    shadow = FONT_TITLE.render("Pokémon Chess", True, SHADOW)
    screen.blit(shadow, (WIDTH//2 - title.get_width()//2 + 40, 103))
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))

    for btn in buttons:
        btn.draw(screen, mouse_pos)
        if btn.is_clicked(mouse_pos, mouse_pressed):
            pygame.time.delay(200)
            if btn.action == "new":
                print("Nouvelle Partie")
                pygame.quit()
                subprocess.run(['python',"new_game.py"])
                sys.exit()
            elif btn.action == "load":
                print("charger Partie")
            elif btn.action == "options":
                current_scene == "image_elon"
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running == False
    pygame.display.flip()



pygame.quit()
print("Cioa mon ami !")

            


