import pygame
import sys

pygame.init()

# Paramètres de la fenêtre
WIDTH, HEIGHT = 1080, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Clicker - Frappe Elon Musk!")

# Couleurs
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GRAY = (50, 50, 50)
GOLD = (255, 215, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 150, 100)
DARK_ORANGE = (200, 100, 50)
DARK_RED = (200, 0, 0)

# Polices
FONT_TITLE = pygame.font.Font(None, 72)
FONT_BIG = pygame.font.Font(None, 48)
FONT_NORMAL = pygame.font.Font(None, 36)

# Créer un sprite de poing avec pygame (pas besoin de PIL)
def create_poing_surface(color_main, color_outline):
    """Créer une surface avec un poing dessiné"""
    size = 150
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Paume (ellipse)
    pygame.draw.ellipse(surface, color_main, (20, 30, 110, 90))
    pygame.draw.ellipse(surface, color_outline, (20, 30, 110, 90), 3)
    
    # Pouce
    pygame.draw.ellipse(surface, color_main, (10, 50, 40, 35))
    pygame.draw.ellipse(surface, color_outline, (10, 50, 40, 35), 3)
    
    # Doigts
    positions = [35, 65, 95, 125]
    for x in positions:
        pygame.draw.ellipse(surface, color_main, (x-15, 10, 30, 35))
        pygame.draw.ellipse(surface, color_outline, (x-15, 10, 30, 35), 3)
    
    return surface

# Créer les sprites de poing
poing_normal = create_poing_surface(ORANGE, DARK_ORANGE)
poing_red = create_poing_surface(RED, DARK_RED)

try:
    elon = pygame.image.load("assets/elon_crying.png")
    elon = pygame.transform.scale(elon, (400, 400))
except:
    elon = None
    print("Image d'Elon non trouvée, elle sera affichée en blanc")

# Variables du jeu
money = 0
poing_rect = poing_normal.get_rect(center=(300, 400))
click_animation = 0  # 0 = pas d'animation, > 0 = en cours
click_timer = 0
money_gain = 100  # Argent gagné par clic

# Boucle de jeu
running = True
clock = pygame.time.Clock()

while running:
    clock.tick(60)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if poing_rect.collidepoint(event.pos):
                money += money_gain
                click_animation = 30  # Durée de l'animation en frames
                click_timer = 0
                print(f"Argent: ${money}")
    
    # Remplir le fond
    screen.fill(DARK_GRAY)
    
    # Afficher Elon Musk à droite
    if elon:
        screen.blit(elon, (650, 150))
    else:
        elon_text = FONT_BIG.render("ELON MUSK", True, WHITE)
        screen.blit(elon_text, (700, 300))
    
    # Gestion de l'animation du poing
    if click_animation > 0:
        # Transition de couleur du normal au rouge et retour
        ratio = click_timer / 30
        if ratio < 0.5:
            # Normale -> Rouge
            current_poing = poing_red
        else:
            # Rouge -> Normal
            current_poing = poing_normal
        
        click_animation -= 1
        click_timer += 1
    else:
        current_poing = poing_normal
    
    # Afficher le poing
    screen.blit(current_poing, poing_rect)
    
    # Afficher "Clique!" au-dessus du poing
    click_text = FONT_NORMAL.render("CLIQUE!", True, GOLD)
    screen.blit(click_text, (poing_rect.centerx - click_text.get_width() // 2, poing_rect.top - 50))
    
    # Afficher l'argent total en haut
    money_text = FONT_TITLE.render(f"${money}", True, GREEN)
    screen.blit(money_text, (20, 20))
    
    # Afficher le gain par clic
    gain_text = FONT_NORMAL.render(f"+${money_gain} par clic", True, GOLD)
    screen.blit(gain_text, (20, 100))
    
    # Instructions
    instruction = FONT_NORMAL.render("Clique sur le poing pour gagner de l'argent!", True, WHITE)
    screen.blit(instruction, (20, HEIGHT - 50))
    
    # Quitter
    if not running:
        break
    
    pygame.display.flip()

pygame.quit()
sys.exit()
