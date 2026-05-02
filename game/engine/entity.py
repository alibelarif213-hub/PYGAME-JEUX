import pygame


class Shadow(pygame.sprite.Sprite):
    """Ombre elliptique dessinée en dessous d'une entité (layer 3 dans pyscroll)."""

    def __init__(self, entity: "Entity"):
        super().__init__()
        self._entity = entity
        w = max(int(entity.frame_w * 0.58), 14)
        h = 9
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (0, 0, 0, 60), (0, 0, w, h))
        self.rect = self.image.get_rect()

    def update(self):
        e = self._entity
        self.rect.centerx = e.rect.centerx
        self.rect.top      = e.rect.bottom - 7


class Entity(pygame.sprite.Sprite):
    """Entité de base : sprite animé 4 directions avec hitbox."""

    def __init__(self, image_path: str, cols: int, rows: int):
        super().__init__()

        raw = pygame.image.load(image_path).convert_alpha()
        self.spritesheet = pygame.transform.scale_by(raw, 0.5)

        self.total_w, self.total_h = self.spritesheet.get_size()
        self.cols    = cols
        self.rows    = rows
        self.frame_w = self.total_w // cols
        self.frame_h = self.total_h // rows

        self.dt            = 0.0
        self.speed         = 2
        self.frame_index   = 0.0
        self.all_images    = self._parse_spritesheet()
        self.collisions: list[pygame.Rect] = []

        self.image = self.all_images["down"][0]
        self.rect  = self.image.get_rect()

        # Hitbox : 60 % largeur × 16 px hauteur au bas du sprite
        self.hitbox = pygame.Rect(0, 0, int(self.frame_w * 0.6), 16)

    def _parse_spritesheet(self) -> dict:
        frames: dict[str, list] = {"down": [], "left": [], "right": [], "up": []}
        for row, direction in enumerate(["down", "left", "right", "up"]):
            for col in range(self.cols):
                frames[direction].append(
                    self.spritesheet.subsurface(
                        (col * self.frame_w, row * self.frame_h, self.frame_w, self.frame_h)
                    )
                )
        return frames

    def update(self):
        self.rect.midbottom = self.hitbox.midbottom

    # ── Déplacement ──────────────────────────────────────────────────────────
    def move_right(self):
        self.hitbox.x += self.speed
        if self._check_collisions():
            self.hitbox.x -= self.speed
        self._animate("right")

    def move_left(self):
        self.hitbox.x -= self.speed
        if self._check_collisions():
            self.hitbox.x += self.speed
        self._animate("left")

    def move_up(self):
        self.hitbox.y -= self.speed
        if self._check_collisions():
            self.hitbox.y += self.speed
        self._animate("up")

    def move_down(self):
        self.hitbox.y += self.speed
        if self._check_collisions():
            self.hitbox.y -= self.speed
        self._animate("down")

    def _animate(self, direction: str):
        self.frame_index += 8 * self.dt
        frames = self.all_images[direction]
        self.image = frames[int(self.frame_index) % len(frames)]

    def _check_collisions(self) -> bool:
        return any(self.hitbox.colliderect(o) for o in self.collisions)
