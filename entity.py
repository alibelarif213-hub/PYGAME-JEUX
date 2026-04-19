import pygame

class Entity(pygame.sprite.Sprite):
    def __init__(self, path, cols, rows):
        super().__init__()
        # Chargement de l'image
        self.spritesheet = pygame.image.load(f"assets/{path}").convert_alpha()
        self.spritesheet = pygame.transform.scale_by(self.spritesheet, 0.5)
        
        self.width, self.height = self.spritesheet.get_size()
        self.cols = cols
        self.rows = rows
        self.frame_width = self.width // cols
        self.frame_height = self.height // rows
        
        self.dt = 0
        self.speed = 4 # Vitesse ajustable
        self.frame_index = 0
        self.all_images = self.get_all_images()
        
        self.image = self.all_images["down"][0]
        self.rect = self.image.get_rect()
        
        # Hitbox pour les collisions (plus petite que le perso pour le réalisme)
        self.hitbox = pygame.rect.Rect(0, 0, self.frame_width * 0.6, self.frame_height * 0.3)
        self.collisions = []

    def update(self):
        # On synchronise le dessin sur la hitbox physique
        self.rect.midbottom = self.hitbox.midbottom

    def move_right(self):
        self.hitbox.x += self.speed
        if self.check_collisions(): self.hitbox.x -= self.speed
        self.animation("right")

    def move_left(self):
        self.hitbox.x -= self.speed
        if self.check_collisions(): self.hitbox.x += self.speed
        self.animation("left")

    def move_up(self):
        self.hitbox.y -= self.speed
        if self.check_collisions(): self.hitbox.y += self.speed
        self.animation("up")

    def move_down(self):
        self.hitbox.y += self.speed
        if self.check_collisions(): self.hitbox.y -= self.speed
        self.animation("down")

    def animation(self, direction):
        self.frame_index += 10 * self.dt 
        frames = self.all_images[direction]
        self.image = frames[int(self.frame_index) % len(frames)]
    
    def check_collisions(self):
        # Correction : on boucle sur chaque rectangle de la liste
        for obstacle in self.collisions:
            if self.hitbox.colliderect(obstacle):
                return True
        return False

    def get_all_images(self):
        frames = {"down": [], "left": [], "right": [], "up": []}
        for row, direction in enumerate(frames.keys()):
            for col in range(self.cols):
                x = col * self.frame_width
                y = row * self.frame_height
                frames[direction].append(self.spritesheet.subsurface((x, y, self.frame_width, self.frame_height)))
        return frames