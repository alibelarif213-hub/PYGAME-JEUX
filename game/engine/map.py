import pygame
import pyscroll
import pytmx

from .entity import Shadow

_MAPS_DIR = "game/assets/maps"

# Correspondances anciens noms Tiled → nouveaux noms internes
_LEGACY_NAMES = {
    "Arène_1": "arena_eau",
    "Arène_2": "arena_plante",
    "Arène_3": "arena_feu",
    "Arène_4": "arena_finale",
    "map_02":  "world",
}


class InteractableObject:
    def __init__(self, rect: pygame.Rect, message: str, label: str = ""):
        self.rect    = rect
        self.message = message
        self.label   = label or "???"


class MapManager:
    def __init__(self, screen: pygame.Surface, player):
        self.screen = screen
        self.player = player
        self.maps: dict        = {}
        self.current_map       = "world"
        self.previous_position = (0, 0)

        # Callbacks boss
        self._exit_blocked_cb   = None
        self._entry_blocked_cb  = None
        self._on_exit_blocked   = None
        self._on_entry_blocked  = None

        self._fade_surf    = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        self._just_entered = False

        self.register_map("world",        zoom=2.2)
        self.register_map("arena_eau",    zoom=3.5)
        self.register_map("arena_plante", zoom=3.5)
        self.register_map("arena_feu",    zoom=3.5)
        self.register_map("arena_finale", zoom=1.2)

        self.teleport_to_spawn("world")

    # ------------------------------------------------------------------
    def register_map(self, map_name: str, zoom: float):
        tmx      = pytmx.util_pygame.load_pygame(f"{_MAPS_DIR}/{map_name}.tmx")
        map_data = pyscroll.data.TiledMapData(tmx)
        renderer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        renderer.zoom = zoom

        collisions:     list[pygame.Rect]        = []
        portals:        list                     = []
        interactables:  list[InteractableObject] = []
        npcs:           list                     = []
        spawn_point = None
        boss_spawn  = None

        for obj in tmx.objects:
            name_l = (obj.name or "").lower().strip()
            props  = getattr(obj, "properties", {}) or {}

            if name_l == "collisions":
                collisions.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
            elif name_l == "player spawn":
                spawn_point = (obj.x, obj.y)
            elif name_l == "spawn boss":
                boss_spawn = (obj.x, obj.y)
            elif "sortie" in name_l or name_l.startswith("tp "):
                portals.append(obj)
            elif props.get("message"):
                interactables.append(InteractableObject(
                    pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                    props["message"],
                    props.get("label", obj.name or "Objet"),
                ))

        # Murs de bordure invisibles : empêche de sortir de la carte par les côtés et le haut
        mw = tmx.width  * tmx.tilewidth
        mh = tmx.height * tmx.tileheight
        T  = 40  # épaisseur des murs fantômes
        collisions += [
            pygame.Rect(-T,  0,  T,  mh),   # gauche
            pygame.Rect(mw,  0,  T,  mh),   # droite
            pygame.Rect(0,  -T,  mw, T),    # haut
        ]

        group = pyscroll.PyscrollGroup(map_layer=renderer, default_layer=5)
        group.add(self.player)

        self.maps[map_name] = {
            "tmx":          tmx,
            "group":        group,
            "collisions":   collisions,
            "portals":      portals,
            "interactables": interactables,
            "npcs":         npcs,
            "spawn_point":  spawn_point,
            "boss_spawn":   boss_spawn,
        }

    # ------------------------------------------------------------------
    def set_boss_callbacks(self, exit_blocked_cb=None, entry_blocked_cb=None,
                           on_exit_blocked_cb=None, on_entry_blocked_cb=None):
        self._exit_blocked_cb  = exit_blocked_cb
        self._entry_blocked_cb = entry_blocked_cb
        self._on_exit_blocked  = on_exit_blocked_cb
        self._on_entry_blocked = on_entry_blocked_cb

    # ------------------------------------------------------------------
    def add_npc(self, map_name: str, npc):
        """Ajoute un PNJ et son ombre au groupe de la carte."""
        shadow = Shadow(npc)
        self.maps[map_name]["group"].add(shadow, layer=3)
        self.maps[map_name]["group"].add(npc, layer=5)
        self.maps[map_name]["npcs"].append(npc)

    def add_player_shadow(self, map_name: str):
        """Ajoute l'ombre du joueur à une carte donnée."""
        shadow = Shadow(self.player)
        self.maps[map_name]["group"].add(shadow, layer=3)

    # ------------------------------------------------------------------
    def check_teleport(self) -> bool:
        for portal in self.get_current_map()["portals"]:
            prect = pygame.Rect(portal.x, portal.y, portal.width, portal.height)
            if not self.player.hitbox.colliderect(prect):
                continue

            if "sortie" in (portal.name or "").lower():
                if self._exit_blocked_cb and self._exit_blocked_cb():
                    if self._on_exit_blocked:
                        self._on_exit_blocked()
                    return False
                self._transition(lambda: self._do_exit())
                return True
            else:
                target = (portal.name or "").replace("tp ", "").replace("TP ", "").strip()
                target = _LEGACY_NAMES.get(target, target)
                if target not in self.maps:
                    continue
                if self._entry_blocked_cb and self._entry_blocked_cb(target):
                    if self._on_entry_blocked:
                        self._on_entry_blocked(target)
                    return False
                self.previous_position = (self.player.hitbox.x, self.player.hitbox.y)
                self._transition(lambda t=target: self._enter_map(t))
                return True
        return False

    def check_bottom_exit(self) -> bool:
        """Déclenche la sortie si le joueur atteint le bas d'une arène boss."""
        if self._just_entered:
            self._just_entered = False
            return False
        if not self.is_boss_arena():
            return False
        tmx          = self.get_current_map()["tmx"]
        map_pixel_h  = tmx.height * tmx.tileheight
        if self.player.hitbox.bottom >= map_pixel_h - 24:
            if self._exit_blocked_cb and self._exit_blocked_cb():
                if self._on_exit_blocked:
                    self._on_exit_blocked()
                # Repousser le joueur pour ne pas boucler
                self.player.hitbox.bottom = map_pixel_h - 26
                self.player.update()
                return False
            self._transition(lambda: self._do_exit())
            return True
        return False

    def _do_exit(self):
        tx = self.previous_position[0]
        ty = self.previous_position[1] + 48
        self._switch_map("world", tx, ty)

    def _enter_map(self, map_name: str):
        self.current_map   = map_name
        self._just_entered = True
        self.teleport_to_spawn(map_name)

    def _switch_map(self, map_name: str, tx: int, ty: int):
        self.current_map = map_name
        self.player.hitbox.x = tx
        self.player.hitbox.y = ty
        self.player.update()

    # ------------------------------------------------------------------
    def _transition(self, switch_fn, duration_ms: int = 380):
        clock = pygame.time.Clock()
        steps = max(1, duration_ms // 16)

        for i in range(steps + 1):
            alpha = int(255 * i / steps)
            self._fade_surf.fill((0, 0, 0, alpha))
            g = self.get_group()
            g.center(self.player.rect.center)
            g.draw(self.screen)
            self.screen.blit(self._fade_surf, (0, 0))
            pygame.display.flip()
            clock.tick(60)

        switch_fn()

        for i in range(steps + 1):
            alpha = int(255 * (1 - i / steps))
            self._fade_surf.fill((0, 0, 0, alpha))
            g = self.get_group()
            g.center(self.player.rect.center)
            g.draw(self.screen)
            self.screen.blit(self._fade_surf, (0, 0))
            pygame.display.flip()
            clock.tick(60)

    # ------------------------------------------------------------------
    def get_nearby_interactable(self, radius: int = 44) -> "InteractableObject | None":
        zone = self.player.hitbox.inflate(radius * 2, radius * 2)
        for obj in self.get_current_map()["interactables"]:
            if zone.colliderect(obj.rect):
                return obj
        return None

    def add_interactable(self, map_name: str, x: int, y: int,
                         w: int, h: int, message: str, label: str = ""):
        """Ajoute un objet interactif en code (sans TMX)."""
        self.maps[map_name]["interactables"].append(
            InteractableObject(pygame.Rect(x, y, w, h), message, label)
        )

    # ------------------------------------------------------------------
    def teleport_to_spawn(self, map_name: str):
        spawn = self.maps[map_name].get("spawn_point")
        if spawn:
            self.player.hitbox.x = spawn[0]
            self.player.hitbox.y = spawn[1]
            if map_name == "world":
                self.previous_position = (spawn[0], spawn[1])
        else:
            print(f"[MapManager] Pas de 'player spawn' sur {map_name}.")
            self.player.hitbox.x = 400
            self.player.hitbox.y = 400
        self.player.update()

    # ------------------------------------------------------------------
    def get_current_map(self) -> dict:
        return self.maps[self.current_map]

    def get_group(self) -> pyscroll.PyscrollGroup:
        return self.get_current_map()["group"]

    def get_collisions(self) -> list[pygame.Rect]:
        return self.get_current_map()["collisions"]

    def get_npcs(self) -> list:
        return self.get_current_map()["npcs"]

    def get_boss_spawn(self, map_name: str):
        return self.maps[map_name].get("boss_spawn")

    def is_boss_arena(self) -> bool:
        return self.current_map.startswith("arena_")

    def get_nearby_portal_target(self, radius: int = 45) -> "str | None":
        """Retourne la carte cible si le joueur est proche d'un portail (monde uniquement)."""
        if self.current_map != "world":
            return None
        zone = self.player.hitbox.inflate(radius * 2, radius * 2)
        for portal in self.get_current_map().get("portals", []):
            prect = pygame.Rect(portal.x, portal.y, portal.width, portal.height)
            if zone.colliderect(prect):
                name   = (portal.name or "").replace("tp ", "").replace("TP ", "").strip()
                target = _LEGACY_NAMES.get(name, name)
                if target in self.maps and target != "world":
                    return target
        return None
