from .entity import Entity


class NPC(Entity):
    """PNJ avec patrouille en carré. Attributs boss injectés par game.py."""

    def __init__(self, name: str, image_path: str, x: int, y: int, dialogue: str):
        super().__init__(image_path, 4, 4)
        self.name     = name
        self.dialogue = dialogue

        # Positionner immédiatement hitbox ET rect
        self.hitbox.midbottom = (x, y)
        super().update()   # sync rect dès la création

        self.speed          = 0.8
        self._patrol_size   = 60.0
        self._patrol_dist   = 0.0
        self._patrol_step   = 0

        # Attributs boss (définis par game.py)
        self.is_boss: bool = False
        self.arena: str    = ""

    def update(self):
        # Toujours syncer le rect, même si speed==0
        if self.speed == 0:
            super().update()
            return

        old_x, old_y = self.hitbox.x, self.hitbox.y

        if self._patrol_step == 0:
            self.hitbox.x += self.speed
            self._animate("right")
        elif self._patrol_step == 1:
            self.hitbox.y += self.speed
            self._animate("down")
        elif self._patrol_step == 2:
            self.hitbox.x -= self.speed
            self._animate("left")
        else:
            self.hitbox.y -= self.speed
            self._animate("up")

        if self._check_collisions():
            self.hitbox.x, self.hitbox.y = old_x, old_y
        else:
            self._patrol_dist += self.speed

        if self._patrol_dist >= self._patrol_size:
            self._patrol_dist = 0.0
            self._patrol_step = (self._patrol_step + 1) % 4

        super().update()
