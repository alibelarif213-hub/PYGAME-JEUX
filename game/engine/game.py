import sys
import os
import threading
import textwrap

import pygame
import requests

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from game.engine.player import Player
from game.engine.npc    import NPC
from game.engine.map    import MapManager
import save as save_module

_IMG_CHARS = "game/assets/images/chars"
_IMG_NPCS  = "game/assets/images/npcs"

# ---------------------------------------------------------------------------
BOSS_CONFIG = {
    "arena_eau": {
        "npc_name": "DJ Mary", "type_ia": "eau", "difficulte": "Facile",
        "type_debloque": "eau", "requires": [],
        "battle_prompt": "Tu es DJ Mary, une DJ rebelle dévouée à l'UNEF (L'Union nationale des étudiants de France (UNEF) est un syndicat étudiant français de gauche fondé en 1907. Elle se donne pour but de défendre les intérêts des étudiants sur la gestion des infrastructures universitaires, que ce soit la recherche scientifique, la restauration universitaire ou les logements étudiants.) et à la révolution. Chaque phrase fait référence à l'UNEF.",
    },
    "arena_plante": {
        "npc_name": "Mafieuse Banquière", "type_ia": "plante", "difficulte": "Moyen",
        "type_debloque": "plante", "requires": [],
        "battle_prompt": "Tu es une mafieuse banquière froide et arrogante, dévouée à la Cocarde (La Cocarde étudiante est une organisation étudiante et lycéenne française fondée en 2015. Elle est positionnée à l'extrême droite et impliquée dans plusieurs faits de violences.). Chaque phrase fait référence à la Cocarde.",
    },
    "arena_feu": {
        "npc_name": "Membre du FSE", "type_ia": "feu", "difficulte": "Difficile",
        "type_debloque": "feu", "requires": [],
        "battle_prompt": "Tu es un membre fanatique du FSE de Nanterre (La FSE est généralement classée comme proche de l'extrême gauche[2],[3],[4]. La FSE se positionne comme un syndicat opposé au capitalisme, laïc, « anti-impérialiste » et « anti-sexiste » et estime que « seule la lutte et la grève générale sont à même de venir à bout du système capitaliste), totalement dévoué à la révolution. Chaque phrase fait référence au FSE.",
    },
    "arena_finale": {
        "npc_name": "Bessière", "difficulte": "Difficile", "type_debloque": None,
        "requires": ["arena_eau", "arena_plante", "arena_feu"],
        "type_ia": {"p": "eau", "r_g": "feu", "r_d": "plante",
                    "n_g": "plante", "n_d": "feu", "b_g": "eau", "b_d": "feu",
                    "q": "plante", "k": "eau"},
        "battle_prompt": "Tu es Bessière (Bessiere forme, dans le secteur tertiaire, des futurs cadres et techniciens supérieurs. Sa spécificité tient au fait de ne proposer que des formations post-bac et de développer un enseignement technique du second degré dans les domaines de l'administration, de la gestion des entreprises, du commerce et du tourisme.), incarnation de l'élitisme universitaire. Tu méprises les MIASHS (MIASHS utilise l’approche méthodologique et les connaissances scientifiques de mathématiques et d’informatique pour étudier les sciences humaines et sociales : économie gestion, sociologie, géographie, sciences du langage.). Chaque phrase exprime ta supériorité.",
    },
}


class Game:
    def __init__(self, screen: pygame.Surface, player_sprite: str, save_data: dict):
        self.screen    = screen
        self.save_data = save_data
        self.running   = True
        self.framerate = 60
        self.clock     = pygame.time.Clock()

        self.font       = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 17)

        self.dialogue_active  = False
        self.is_ai_thinking   = False
        self.current_dialogue: list[str] = []
        self.dialogue_speaker = ""

        self._flash_msg      = ""
        self._flash_timer    = 0
        self._flash_duration = 3000

        self.player = Player(f"{_IMG_CHARS}/{player_sprite}", 4, 4)
        self.map_manager = MapManager(screen, self.player)

        # Ombre du joueur sur toutes les cartes
        for map_name in self.map_manager.maps:
            self.map_manager.add_player_shadow(map_name)

        self.map_manager.set_boss_callbacks(
            exit_blocked_cb    = self._exit_bloque,
            entry_blocked_cb   = self._entree_bloquee,
            on_exit_blocked_cb = self._notifier_sortie_bloquee,
            on_entry_blocked_cb= self._notifier_entree_bloquee,
        )

        self._setup_npcs()
        self._setup_interactables()

    # ------------------------------------------------------------------
    def _setup_npcs(self):
        def _add(map_name, name, img, x, y, dialogue, arena="", is_boss=False, speed=0.8):
            n = NPC(name, f"{_IMG_NPCS}/{img}", x, y, dialogue)
            n.is_boss = is_boss
            n.arena   = arena
            n.speed   = speed
            self.map_manager.add_npc(map_name, n)
            return n

        self.samurai = _add("world", "Samurai", "samurai.png", 850, 700,
            "Tu es un maitre samourai sarcastique et fier, expert en echecs. "
            "Reponds toujours avec une pointe d'humour ironique sur les syndicats etudiants. "
            "Max 25 mots.", speed=0.8)
        self.delbot  = _add("world", "M. Delbot", "delbot.png", 600, 500,
            "Tu es un professeur enthousiaste et maladroit qui adore les brocolis. "
            "Tu es sincèrement nul aux echecs mais tu le caches mal. "
            "Reponds avec humour et auto-derision. Max 25 mots.", speed=0)

        for arena, img, nm in [
            ("arena_eau",    "dj_mary.png",   "DJ Mary"),
            ("arena_plante", "banquiere.png",  "Mafieuse Banquière"),
            ("arena_feu",    "fse.png",        "Membre du FSE"),
            ("arena_finale", "bessiere.png",   "Bessière"),
        ]:
            pos = self.map_manager.get_boss_spawn(arena) or (400, 300)
            _add(arena, nm, img, *pos,
                 BOSS_CONFIG[arena]["battle_prompt"],
                 arena=arena, is_boss=True, speed=0)

    def _setup_interactables(self):
        mm = self.map_manager

        # Arenes : panneaux proches du spawn de chaque arene
        infos = {
            "arena_eau":    ("Arene Eau - DJ Mary",
                             "EAU bat FEU. Victoire = type EAU debloque (Tortank, Carabaffe)."),
            "arena_plante": ("Arene Plante - Banquiere",
                             "PLANTE bat EAU. Victoire = type PLANTE debloque (Florizarre)."),
            "arena_feu":    ("Arene Feu - FSE",
                             "FEU bat PLANTE. Victoire = type FEU debloque (Drakofeu)."),
            "arena_finale": ("Arene Finale - Bessiere",
                             "Mix de tous les types. Niveau Difficile. Utilise T pour parler !"),
        }
        for arena, (label, msg) in infos.items():
            sp2 = mm.maps[arena].get("spawn_point") or (200, 150)
            ax, ay = int(sp2[0]), int(sp2[1])
            mm.add_interactable(arena, ax + 40, ay + 30, 24, 20, msg, label)
            mm.add_interactable(arena, ax - 30, ay + 30, 24, 20,
                "Descends jusqu'en bas pour sortir. Impossible tant que le boss est debout.",
                "Sortie arene")

    # ------------------------------------------------------------------
    def _exit_bloque(self) -> bool:
        arena = self.map_manager.current_map
        return arena in BOSS_CONFIG and arena not in self.save_data["bosses_vaincus"]

    def _entree_bloquee(self, target: str) -> bool:
        cfg = BOSS_CONFIG.get(target)
        if not cfg:
            return False
        return any(r not in self.save_data["bosses_vaincus"] for r in cfg.get("requires", []))

    def _notifier_sortie_bloquee(self):
        self._flash("Impossible de fuir ! Bats le boss pour sortir.", duree=3500)

    def _notifier_entree_bloquee(self, target: str):
        noms = ", ".join(BOSS_CONFIG[r]["npc_name"]
                         for r in BOSS_CONFIG[target].get("requires", [])
                         if r not in self.save_data["bosses_vaincus"])
        self._flash(f"Arène verrouillée ! Bats d'abord : {noms}", duree=4000)

    def _flash(self, msg: str, duree: int = 3000):
        self._flash_msg      = msg
        self._flash_timer    = pygame.time.get_ticks()
        self._flash_duration = duree

    # ------------------------------------------------------------------
    def _draw_flash(self):
        if not self._flash_msg:
            return
        if pygame.time.get_ticks() - self._flash_timer > self._flash_duration:
            self._flash_msg = ""
            return
        W, H = self.screen.get_size()
        surf = self.font.render(self._flash_msg, True, (255, 80, 80))
        bg   = pygame.Surface((surf.get_width() + 22, surf.get_height() + 12), pygame.SRCALPHA)
        bg.fill((10, 10, 10, 215))
        self.screen.blit(bg,   (W // 2 - bg.get_width() // 2,   H - 78))
        self.screen.blit(surf, (W // 2 - surf.get_width() // 2, H - 72))

    def _draw_hud(self):
        ARENES   = ["arena_eau", "arena_plante", "arena_feu", "arena_finale"]
        LABELS   = ["Eau", "Plante", "Feu", "Bessiere"]
        COULEURS = [(50, 140, 220), (60, 180, 60), (220, 80, 30), (200, 50, 200)]
        x = 10
        for arena, label, col in zip(ARENES, LABELS, COULEURS):
            vaincu = arena in self.save_data["bosses_vaincus"]
            bg     = col if vaincu else (55, 55, 55)
            rect   = pygame.Rect(x, 8, 82, 22)
            pygame.draw.rect(self.screen, bg, rect, border_radius=4)
            pygame.draw.rect(self.screen, (200, 200, 200) if vaincu else (80, 80, 80),
                             rect, 1, border_radius=4)
            # Checkmark dessiné (pas de caractère Unicode)
            if vaincu:
                cx, cy = x + 10, rect.centery
                pygame.draw.line(self.screen, (255, 255, 255), (cx - 4, cy),     (cx - 1, cy + 3), 2)
                pygame.draw.line(self.screen, (255, 255, 255), (cx - 1, cy + 3), (cx + 4, cy - 3), 2)
            txt = self.font_small.render(label, True, (255, 255, 255))
            tx  = x + (20 if vaincu else 8)
            self.screen.blit(txt, (tx, rect.y + (rect.height - txt.get_height()) // 2))
            x += 90

    def _draw_arena_type_badge(self, arena: str):
        """Affiche un badge de type au centre de l'écran quand on approche d'une arène."""
        cfg     = BOSS_CONFIG.get(arena, {})
        type_ia = cfg.get("type_ia")
        if not isinstance(type_ia, str):
            type_ia = "mixte"
        TYPE_INFO = {
            "eau":    ("EAU",    (50, 140, 220)),
            "feu":    ("FEU",    (220, 80,  30)),
            "plante": ("PLANTE", (60, 180,  60)),
            "mixte":  ("MIXTE",  (200, 50, 200)),
        }
        type_label, col = TYPE_INFO.get(type_ia, (type_ia.upper(), (150, 150, 150)))
        npc_name        = cfg.get("npc_name", "Boss")
        W, H            = self.screen.get_size()
        f_name  = pygame.font.SysFont("Arial", 26, bold=True)
        f_type  = pygame.font.SysFont("Arial", 20)
        surf1   = f_name.render(npc_name,            True, (255, 255, 255))
        surf2   = f_type.render(f"Type : {type_label}", True, col)
        hint    = self.font_small.render("[A] Combattre", True, (180, 220, 160))
        box_w   = max(surf1.get_width(), surf2.get_width(), hint.get_width()) + 28
        box_h   = surf1.get_height() + surf2.get_height() + hint.get_height() + 22
        bx      = W // 2 - box_w // 2
        by      = H // 2 - box_h - 20
        bg      = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg.fill((10, 10, 20, 215))
        self.screen.blit(bg, (bx, by))
        pygame.draw.rect(self.screen, col, (bx, by, box_w, box_h), 2, border_radius=8)
        cy = by + 8
        for surf in (surf1, surf2, hint):
            self.screen.blit(surf, (bx + (box_w - surf.get_width()) // 2, cy))
            cy += surf.get_height() + 5

    def _draw_dialogue(self):
        if not self.dialogue_active:
            return
        W, H = self.screen.get_size()
        # Boîte plus haute et mieux positionnée
        rect = pygame.Rect(80, H - 175, W - 160, 155)
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((10, 10, 26, 240))
        self.screen.blit(overlay, (rect.x, rect.y))
        # Bordure colorée selon speaker (PNJ = doré, objet = bleu)
        border_col = (255, 220, 50) if self.dialogue_speaker else (100, 180, 255)
        pygame.draw.rect(self.screen, border_col, rect, 2, border_radius=10)

        if self.dialogue_speaker:
            # Nom en gras, fond coloré
            name_bg = pygame.Surface((len(self.dialogue_speaker) * 13 + 20, 28), pygame.SRCALPHA)
            name_bg.fill((50, 40, 0, 200))
            self.screen.blit(name_bg, (rect.x + 10, rect.y + 6))
            ns = self.font.render(self.dialogue_speaker, True, (255, 220, 50))
            self.screen.blit(ns, (rect.x + 20, rect.y + 8))

        if self.is_ai_thinking and not self.current_dialogue:
            dots_lbl = self.font.render("...", True, (200, 200, 0))
            self.screen.blit(dots_lbl, (rect.x + 20, rect.y + 44))
        else:
            for i, line in enumerate(self.current_dialogue[:4]):
                self.screen.blit(self.font.render(line, True, (240, 240, 240)),
                                 (rect.x + 20, rect.y + 44 + i * 28))

        hint = self.font_small.render("ENTREE : fermer", True, (80, 80, 80))
        self.screen.blit(hint, (rect.right - hint.get_width() - 10, rect.bottom - hint.get_height() - 4))

    def _draw_hint(self, label: str):
        W, H = self.screen.get_size()
        # Texte plus petit et discret, en bas à droite
        hint = self.font_small.render(f"[A] {label}", True, (200, 220, 160))
        bg   = pygame.Surface((hint.get_width() + 12, hint.get_height() + 6), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 160))
        bx = W - bg.get_width() - 12
        by = H - bg.get_height() - 10
        self.screen.blit(bg,   (bx, by))
        self.screen.blit(hint, (bx + 6, by + 3))

    # ------------------------------------------------------------------
    def _fetch_npc_response(self, name: str, personality: str):
        try:
            r = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "mistral",
                      "prompt": f"{personality} Un dresseur t'approche. Réponds une seule phrase courte en français (max 30 mots).",
                      "stream": False},
                timeout=10,
            )
            self.current_dialogue = textwrap.wrap(
                r.json().get("response", "...") if r.status_code == 200 else "Le PNJ semble fatigué…",
                width=65
            )
        except Exception:
            self.current_dialogue = ["…"]
        self.is_ai_thinking = False

    # ------------------------------------------------------------------
    def _boss_proche(self):
        for npc in self.map_manager.get_npcs():
            if npc.is_boss and self.player.hitbox.inflate(70, 70).colliderect(npc.hitbox):
                return npc, npc.arena, BOSS_CONFIG.get(npc.arena, {})
        return None, "", {}

    def _lancer_combat_boss(self, npc, arena: str, cfg: dict):
        from game.chess.integration import lancer_combat_boss

        if arena in self.save_data["bosses_vaincus"]:
            self.dialogue_speaker = npc.name
            self.current_dialogue = ["Tu m'as déjà vaincu… mais je reviendrai !"]
            self.dialogue_active  = True
            return

        for req in cfg.get("requires", []):
            if req not in self.save_data["bosses_vaincus"]:
                noms = ", ".join(BOSS_CONFIG[r]["npc_name"] for r in cfg["requires"])
                self._flash(f"Bats d'abord : {noms}", duree=3500)
                return

        resultat = lancer_combat_boss(
            screen=self.screen,
            boss_name=npc.name,
            boss_personality=cfg["battle_prompt"],
            difficulte=cfg["difficulte"],
            type_ia=cfg["type_ia"],
            types_joueur=dict(self.save_data["types_joueur"]),
            types_disponibles=list(self.save_data["types_debloque"]),
            clock=self.clock,
        )

        if resultat == "VICTOIRE":
            if arena not in self.save_data["bosses_vaincus"]:
                self.save_data["bosses_vaincus"].append(arena)
            t = cfg.get("type_debloque")
            if t and t not in self.save_data["types_debloque"]:
                self.save_data["types_debloque"].append(t)
            save_module.sauvegarder(self.save_data)
            nb = len(self.save_data["bosses_vaincus"])
            if nb >= 4:
                self._flash("🏆 CHAMPION ! Tu as vaincu les 4 boss !", duree=6000)
            else:
                type_msg = f" — Type {t.upper()} débloqué !" if t else ""
                self._flash(f"Victoire contre {npc.name} !{type_msg}", duree=4000)
        else:
            self._flash("Défaite… Tu peux recommencer !", duree=3000)

    # ------------------------------------------------------------------
    def _handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if not self.is_ai_thinking:
                        self.dialogue_active = False

                if event.key == pygame.K_a and not self.dialogue_active:
                    boss_npc, arena, cfg = self._boss_proche()
                    if boss_npc:
                        self._lancer_combat_boss(boss_npc, arena, cfg)
                        return

                    obj = self.map_manager.get_nearby_interactable()
                    if obj:
                        self.dialogue_speaker = obj.label
                        self.current_dialogue = textwrap.wrap(obj.message, 65)
                        self.dialogue_active  = True
                        self.is_ai_thinking   = False
                        return

                    if not self.is_ai_thinking:
                        for npc in self.map_manager.get_npcs():
                            if not npc.is_boss and self.player.hitbox.inflate(60, 60).colliderect(npc.hitbox):
                                self.is_ai_thinking   = True
                                self.dialogue_active  = True
                                self.dialogue_speaker = npc.name
                                self.current_dialogue = []
                                threading.Thread(
                                    target=self._fetch_npc_response,
                                    args=(npc.name, npc.dialogue),
                                    daemon=True,
                                ).start()
                                break

    # ------------------------------------------------------------------
    def run(self):
        while self.running:
            dt = self.clock.tick(self.framerate) / 1000
            self.player.dt = dt
            for npc in self.map_manager.get_npcs():
                npc.dt = dt

            self._handle_input()

            if not self.dialogue_active:
                self.player.update()
                for npc in self.map_manager.get_npcs():
                    npc.update()
                    if npc.speed == 0:
                        npc.image = npc.all_images["down"][0]
                self.map_manager.check_teleport()
                self.map_manager.check_bottom_exit()

            walls   = self.map_manager.get_collisions()
            npc_boxes = [n.hitbox for n in self.map_manager.get_npcs()]
            self.player.collisions = walls + npc_boxes
            for npc in self.map_manager.get_npcs():
                npc.collisions = walls + [self.player.hitbox]

            group = self.map_manager.get_group()
            group.center(self.player.rect.center)
            group.draw(self.screen)

            self._draw_hud()

            # Badge de type quand on approche d'une arène dans le monde
            if self.map_manager.current_map == "world" and not self.dialogue_active:
                portal_target = self.map_manager.get_nearby_portal_target()
                if portal_target:
                    self._draw_arena_type_badge(portal_target)

            boss_npc, arena, _ = self._boss_proche()
            if boss_npc and not self.dialogue_active:
                label = f"Combattre {boss_npc.name}" if arena not in self.save_data["bosses_vaincus"] else boss_npc.name
                self._draw_hint(label)
            else:
                obj = self.map_manager.get_nearby_interactable()
                if obj and not self.dialogue_active:
                    self._draw_hint(obj.label)

            self._draw_dialogue()
            self._draw_flash()
            pygame.display.update()

        pygame.quit()
