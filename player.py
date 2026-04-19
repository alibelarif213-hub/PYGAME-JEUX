import pygame
from entity import Entity

class Player(Entity):
    def __init__(self, path, cols, rows, keys):
        super().__init__(path, cols, rows)
        self.speed =  2# Vitesse de déplacement
        
    def update(self):
        self.check_move()
        super().update() # Important pour synchroniser rect et hitbox
       
        self.spawn = [500, 500] # On définit le point d'apparition ici
    def check_move(self):
        keys_pressed = pygame.key.get_pressed()

        if keys_pressed[pygame.K_UP]:
            self.move_up()
        elif keys_pressed[pygame.K_DOWN]:
            self.move_down()
        elif keys_pressed[pygame.K_LEFT]:
            self.move_left()
        elif keys_pressed[pygame.K_RIGHT]:
            self.move_right()
        else:
            # Si on ne bouge pas, on remet l'index à 0 (facultatif)
            self.frame_index = 0
    