import pygame
from game.engine.entity import Entity


class Player(Entity):
    def __init__(self, image_path: str, cols: int, rows: int):
        super().__init__(image_path, cols, rows)
        self.speed = 2
        self.spawn = (500, 500)

    def update(self):
        self._handle_input()
        super().update()

    def _handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.move_up()
        elif keys[pygame.K_DOWN]:
            self.move_down()
        elif keys[pygame.K_LEFT]:
            self.move_left()
        elif keys[pygame.K_RIGHT]:
            self.move_right()
        else:
            self.frame_index = 0
