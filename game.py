import pygame 
import pytmx
import pyscroll
from sys import exit
from player import Player

class Game:
    def __init__(self, player_sprite):
        self.screen = pygame.display.set_mode((1200, 800))
        pygame.display.set_caption("Mon Jeu Pygame")
        self.clock = pygame.time.Clock()
        self.framerate = 60
        self.running = True
        
        # Initialisation du joueur avec le sprite choisi dans le menu
        self.player = Player(player_sprite, 4, 4, [])

        # Chargement de la carte
        self.tmx_data = pytmx.util_pygame.load_pygame("assets/map_02.tmx")
        self.collisions = []
        for obj in self.tmx_data.objects:
            if obj.name == "collisions":
                self.collisions.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
            elif obj.name == "player_spawn":
                self.player.spawn = [obj.x, obj.y]
        self.player.collisions = self.collisions 
        self.map_data = pyscroll.data.TiledMapData(self.tmx_data)
        self.map_layer = pyscroll.orthographic.BufferedRenderer(self.map_data, self.screen.get_size())
        self.map_layer.zoom = 3.5

        # Groupe de rendu
        self.group = pyscroll.PyscrollGroup(map_layer=self.map_layer, default_layer=5)
        self.group.add(self.player)
        
        # On positionne la hitbox (car c'est elle qui dirige le perso maintenant)
        self.player.hitbox.x = 792.25 
        self.player.hitbox.y = 664.5
        self.player.update()

    def run(self):
        while self.running:
            # 1. Calcul du Delta Time (temps entre 2 frames)
            self.player.dt = self.clock.tick(self.framerate) / 1000 

            # 2. Entrées clavier
            self.get_input()
            
            # 3. Mise à jour de la logique (Appelle le update du Player)
            self.group.update()
            
            # 4. Rendu graphique
            self.group.center(self.player.rect.center)
            self.group.draw(self.screen)
            pygame.display.update()

        pygame.quit()
        exit()

    def get_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False