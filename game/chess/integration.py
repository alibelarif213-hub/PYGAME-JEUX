"""
integration.py — Combat PokéChess depuis le RPG.
  lancer_combat()       — combat simple
  lancer_combat_boss()  — combat RPG : sélection → intro → combat Undertale
"""
import threading
import textwrap
import requests
import pygame

from .jeu import Jeu
from .ia  import meilleur_coup_avec_statuts, _coup_aleatoire


# ---------------------------------------------------------------------------
# Saisie texte pendant le combat
# ---------------------------------------------------------------------------
class _TextInput:
    MAX_LEN = 100

    def __init__(self):
        self._font  = pygame.font.SysFont("Arial", 19)
        self.text   = ""
        self.active = False

    def open(self):
        self.text   = ""
        self.active = True

    def handle_event(self, event) -> str | None:
        if not self.active or event.type != pygame.KEYDOWN:
            return None
        if event.key == pygame.K_RETURN:
            result    = self.text.strip()
            self.text = ""
            self.active = False
            return result if result else None
        if event.key == pygame.K_ESCAPE:
            self.text   = ""
            self.active = False
            return None
        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif len(self.text) < self.MAX_LEN and event.unicode.isprintable():
            self.text += event.unicode
        return None

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return
        W, H = surface.get_size()
        rect = pygame.Rect(60, H - 46, W - 120, 36)
        bg   = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        bg.fill((10, 10, 30, 235))
        surface.blit(bg, (rect.x, rect.y))
        pygame.draw.rect(surface, (100, 180, 255), rect, 2, border_radius=6)
        label = self._font.render("Parler : " + self.text + "|", True, (200, 230, 255))
        surface.blit(label, (rect.x + 10, rect.centery - label.get_height() // 2))


# ---------------------------------------------------------------------------
# Dialogue boss + système Undertale
# ---------------------------------------------------------------------------
class _BattleDialogue:
    TRIGGER_INTERVAL = 5
    MORALE_MAX       = 2

    def __init__(self, personality: str, boss_name: str):
        self.personality  = personality
        self.boss_name    = boss_name
        self.active       = False
        self.speaker      = boss_name
        self.lines: list  = []
        self.is_fetching  = False
        self._moves       = 0
        self.morale       = self.MORALE_MAX
        self.weak_moves   = 0
        self.surrendered  = False   # True quand morale=0 → victoire par dialogue
        self._font        = pygame.font.SysFont("Arial", 19, bold=True)
        self._font_small  = pygame.font.SysFont("Arial", 15)

    # ── Message automatique ──────────────────────────────────────────────
    def on_move(self, jeu: Jeu):
        self._moves += 1
        if self._moves >= self.TRIGGER_INTERVAL and not self.is_fetching:
            self._moves = 0
            self._fetch_comment(jeu)

    def _fetch_comment(self, jeu: Jeu):
        self.is_fetching = True
        ia = sum(1 for y in range(8) for x in range(8)
                 if jeu.p.get(x, y) and jeu.p.get(x, y).couleur == "IA")
        jo = sum(1 for y in range(8) for x in range(8)
                 if jeu.p.get(x, y) and jeu.p.get(x, y).couleur == "JOUEUR")

        def _fetch():
            try:
                prompt = (f"{self.personality} Il reste {ia} de tes pieces et {jo} pieces adverses. "
                          "Dis une phrase courte (max 15 mots) sur le combat.")
                r = requests.post("http://localhost:11434/api/generate",
                                  json={"model": "mistral", "prompt": prompt, "stream": False},
                                  timeout=20)
                if r.status_code == 200:
                    self.lines   = textwrap.wrap(r.json().get("response", "...").strip()[:150], 55)
                    self.speaker = self.boss_name
                    self.active  = True
            except Exception:
                pass
            self.is_fetching = False

        threading.Thread(target=_fetch, daemon=True).start()

    # ── Provocation simple (A) ────────────────────────────────────────────
    def player_taunt(self):
        if self.is_fetching:
            return
        self.is_fetching = True
        self.speaker = "Vous"
        self.lines   = ["Vous : T'es vraiment trop nul !"]
        self.active  = True

        def _fetch():
            resp = "Tu me fais rire... Ce n'est pas fini !"
            try:
                prompt = (f"{self.personality} Le joueur se moque de toi. "
                          "Reponds par une phrase courte (max 15 mots).")
                r = requests.post("http://localhost:11434/api/generate",
                                  json={"model": "mistral", "prompt": prompt, "stream": False},
                                  timeout=20)
                if r.status_code == 200:
                    resp = r.json().get("response", resp).strip()[:150]
            except Exception:
                pass
            self.lines   = textwrap.wrap(resp, 55)
            self.speaker = self.boss_name
            self.is_fetching = False

        threading.Thread(target=_fetch, daemon=True).start()

    # ── Dialogue libre Undertale (T) ─────────────────────────────────────
    def discuss(self, player_text: str):
        if not player_text:
            return
        self.is_fetching = True
        self.speaker = "..."
        self.lines   = ["En attente de reponse..."]
        self.active  = True

        def _fetch():
            resp = "Tu ne me feras pas changer d'avis."
            try:
                prompt = (
                    f"{self.personality}\n"
                    f"Le joueur te dit : \"{player_text}\"\n"
                    f"REGLE : si son argument te touche, te derange, ou te fait hesiter, "
                    f"commence ta reponse par exactement 'DOUTE:' puis reponds. "
                    f"Sinon reponds normalement. Max 12 mots en francais."
                )
                r = requests.post("http://localhost:11434/api/generate",
                                  json={"model": "mistral", "prompt": prompt, "stream": False},
                                  timeout=30)
                if r.status_code == 200:
                    resp = r.json().get("response", resp).strip()
            except Exception:
                pass

            if resp.upper().startswith("DOUTE:") and self.morale > 0:
                self.morale     -= 1
                self.weak_moves += 3
                resp = resp[6:].strip()
                if self.morale <= 0:
                    self.surrendered = True
                    self.lines = textwrap.wrap(f"[{self.boss_name} s'effondre...] {resp}", 55)
                else:
                    self.lines = textwrap.wrap(f"[Moral -{1} / reste {self.morale}] {resp}", 55)
            else:
                self.lines = textwrap.wrap(resp[:200], 55)
            self.speaker = self.boss_name
            self.is_fetching = False

        threading.Thread(target=_fetch, daemon=True).start()

    def dismiss(self):
        self.active = False

    def should_play_weak(self) -> bool:
        if self.weak_moves > 0:
            self.weak_moves -= 1
            return True
        return False

    # ── Rendu ────────────────────────────────────────────────────────────
    def draw(self, surface: pygame.Surface, text_input_active: bool = False, talked_this_turn: bool = False):
        W, H = surface.get_size()
        self._draw_morale(surface, W, H)

        if not self.active and not text_input_active:
            parts = ["A : Provoquer"]
            if not talked_this_turn:
                parts.append("T : Parler (1/tour)")
            else:
                parts.append("T : deja parle ce tour")
            h = self._font_small.render("   ".join(parts), True, (80, 80, 80))
            surface.blit(h, (W - h.get_width() - 8, H - 18))
            return

        if not self.active:
            return

        box_h = 130
        box   = pygame.Rect(60, H - box_h - 52, W - 120, box_h)
        surf  = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
        surf.fill((8, 8, 28, 235))
        surface.blit(surf, (box.x, box.y))
        border_col = (255, 180, 50) if self.is_fetching else (100, 200, 255)
        pygame.draw.rect(surface, border_col, box, 2, border_radius=8)

        speaker_col = (255, 180, 50) if self.is_fetching else (100, 200, 255)
        surface.blit(
            self._font.render(f"[{self.speaker}]", True, speaker_col),
            (box.x + 10, box.y + 8)
        )
        for i, line in enumerate(self.lines[:4]):
            surface.blit(self._font.render(line, True, (240, 240, 240)),
                         (box.x + 10, box.y + 32 + i * 24))

        if self.is_fetching:
            hint_txt = "En attente de reponse..."
            hint_col = (255, 180, 50)
        else:
            hint_txt = "ENTREE ou clic : fermer"
            hint_col = (100, 100, 100)
        close_h = self._font_small.render(hint_txt, True, hint_col)
        surface.blit(close_h, (box.right - close_h.get_width() - 8, box.bottom - close_h.get_height() - 4))

    def _draw_morale(self, surface, W, H):
        r = 14
        gap = 8
        total_w = self.MORALE_MAX * (r * 2) + (self.MORALE_MAX - 1) * gap
        bx = W - total_w - 14
        by = 100

        label = self._font_small.render("Moral adversaire", True, (180, 180, 180))
        surface.blit(label, (bx, by - 20))

        for i in range(self.MORALE_MAX):
            cx = bx + i * (r * 2 + gap) + r
            cy = by + r
            filled = i < self.morale
            if filled:
                col = (220, 60, 60) if self.morale == 1 else (220, 160, 40)
                pygame.draw.circle(surface, col, (cx, cy), r)
                pygame.draw.circle(surface, (255, 255, 255), (cx, cy), r, 2)
            else:
                pygame.draw.circle(surface, (30, 30, 30), (cx, cy), r)
                pygame.draw.circle(surface, (100, 100, 100), (cx, cy), r, 2)
                # croix au centre = perdu
                pygame.draw.line(surface, (100, 100, 100), (cx - 6, cy - 6), (cx + 6, cy + 6), 2)
                pygame.draw.line(surface, (100, 100, 100), (cx + 6, cy - 6), (cx - 6, cy + 6), 2)


# ---------------------------------------------------------------------------
# Écrans de fin
# ---------------------------------------------------------------------------
def _draw_surrender_screen(surface: pygame.Surface, boss_name: str):
    W, H = surface.get_size()
    ov   = pygame.Surface((W, H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 190))
    surface.blit(ov, (0, 0))
    f_big = pygame.font.SysFont("Arial", 50, bold=True)
    f_med = pygame.font.SysFont("Arial", 28)
    f_sm  = pygame.font.SysFont("Arial", 20)
    t1 = f_big.render("Victoire par le dialogue !", True, (255, 220, 50))
    t2 = f_med.render(f"{boss_name} a abandonne face a vos arguments.", True, (200, 200, 200))
    t3 = f_med.render("Les mots peuvent tout changer...", True, (140, 200, 140))
    t4 = f_sm.render("Cliquez ou appuyez sur une touche pour continuer", True, (160, 160, 160))
    surface.blit(t1, (W // 2 - t1.get_width() // 2, H // 2 - 80))
    surface.blit(t2, (W // 2 - t2.get_width() // 2, H // 2))
    surface.blit(t3, (W // 2 - t3.get_width() // 2, H // 2 + 44))
    surface.blit(t4, (W // 2 - t4.get_width() // 2, H // 2 + 100))


def _draw_defeat_overlay(surface: pygame.Surface):
    W, H = surface.get_size()
    ov   = pygame.Surface((W, H), pygame.SRCALPHA)
    ov.fill((80, 0, 0, 120))
    surface.blit(ov, (0, 0))
    f = pygame.font.SysFont("Arial", 44, bold=True)
    t = f.render("Defaite...", True, (255, 100, 100))
    surface.blit(t, (W // 2 - t.get_width() // 2, H // 2 - t.get_height() // 2))
    hint = pygame.font.SysFont("Arial", 20).render("Appuyez sur une touche pour continuer", True, (180, 180, 180))
    surface.blit(hint, (W // 2 - hint.get_width() // 2, H // 2 + 50))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _setup(screen):
    from . import assets as _assets
    from . import draw   as _draw
    orig           = _assets.screen
    _assets.screen = screen
    _draw.screen   = screen
    return _assets, _draw, orig


def _restore(assets, draw_mod, orig):
    assets.screen   = orig
    draw_mod.screen = orig


def _run_ia(jeu: Jeu, dialogue: "_BattleDialogue | None" = None):
    if dialogue and dialogue.should_play_weak():
        coup = _coup_aleatoire(jeu)
    else:
        coup = meilleur_coup_avec_statuts(jeu)
    if coup:
        jeu.appliquer_coup(*coup)
        if dialogue:
            dialogue.on_move(jeu)
    else:
        for yy in range(8):
            for xx in range(8):
                p = jeu.p.get(xx, yy)
                if p and p.couleur == "IA":
                    p.statut = None
        jeu.tour       = "JOUEUR"
        jeu.ia_en_cours = False


# ---------------------------------------------------------------------------
# Combat simple
# ---------------------------------------------------------------------------
def lancer_combat(screen, difficulte="Moyen", types_joueur=None, type_ia="eau",
                  clock=None, callback=None) -> str:
    if clock is None:
        clock = pygame.time.Clock()
    if types_joueur is None:
        types_joueur = {k: "normal" for k in ["p","r_g","r_d","n_g","n_d","b_g","b_d","q","k"]}
    jeu = Jeu()
    jeu.niveau_ia = difficulte
    jeu.appliquer_types(types_joueur, type_ia)
    assets, draw_mod, orig = _setup(screen)
    from .draw import draw as draw_chess
    ia_turn_start = 0
    prev_tour     = jeu.tour
    IA_DELAY_MS   = 900
    try:
        while True:
            clock.tick(60)
            now = pygame.time.get_ticks()
            if jeu.tour == "IA" and prev_tour == "JOUEUR":
                ia_turn_start = now
            prev_tour = jeu.tour
            offset, _, _ = draw_chess(jeu)
            pygame.display.flip()
            if (jeu.tour == "IA" and not jeu.ia_en_cours and not jeu.partie_terminee
                    and ia_turn_start > 0 and now - ia_turn_start >= IA_DELAY_MS):
                jeu.ia_en_cours = True
                threading.Thread(target=_run_ia, args=(jeu,), daemon=True).start()
            if jeu.partie_terminee and jeu.gagnant:
                resultat = "VICTOIRE" if jeu.gagnant == "JOUEUR" else "DEFAITE"
                if callback:
                    callback(resultat)
                return resultat
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    if callback: callback("DEFAITE")
                    return "DEFAITE"
                if e.type == pygame.MOUSEBUTTONDOWN:
                    jeu.click(e.pos, offset)
    finally:
        _restore(assets, draw_mod, orig)


# ---------------------------------------------------------------------------
# Combat boss complet
# ---------------------------------------------------------------------------
def lancer_combat_boss(screen, boss_name, boss_personality, difficulte, type_ia,
                       types_joueur, types_disponibles=None, clock=None) -> str:
    if clock is None:
        clock = pygame.time.Clock()
    if types_disponibles is None:
        types_disponibles = ["normal", "feu", "eau", "plante"]

    assets, draw_mod, orig = _setup(screen)

    try:
        # ── Phase 1 : Sélection de types ────────────────────────────────
        from .draw import draw_choix_type

        class _Holder:
            def __init__(self, tj):
                self.types_joueur = dict(tj)

        holder = _Holder(types_joueur)
        for k in holder.types_joueur:
            if holder.types_joueur[k] not in types_disponibles:
                holder.types_joueur[k] = "normal"

        prochain = {"type_ia": type_ia, "arene": boss_name,
                    "label": f"Combat vs {boss_name}", "difficulte": difficulte}
        done = False
        while not done:
            clock.tick(60)
            rects = draw_choix_type(holder, prochain_combat=prochain,
                                    types_disponibles=types_disponibles)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return "DEFAITE"
                if e.type == pygame.MOUSEBUTTONDOWN:
                    for key, rect in rects.items():
                        if rect.collidepoint(e.pos):
                            if key == "tout_normal":
                                for k in holder.types_joueur:
                                    holder.types_joueur[k] = "normal"
                            elif key == "confirmer":
                                done = True
                            elif isinstance(key, tuple):
                                cle, t = key
                                if t in types_disponibles:
                                    holder.types_joueur[cle] = t
                            break

        selected = holder.types_joueur

        # ── Phase 2 : Intro boss ─────────────────────────────────────────
        from .draw import draw_intro_boss
        msg_box = ["..."]

        def _fetch_intro():
            try:
                prompt = (f"{boss_personality} Un dresseur vient te defier. "
                          "Dis une phrase provocatrice courte (max 20 mots).")
                r = requests.post("http://localhost:11434/api/generate",
                                  json={"model": "mistral", "prompt": prompt, "stream": False},
                                  timeout=20)
                msg_box[0] = r.json().get("response", "Prepare-toi !").strip()[:160] \
                    if r.status_code == 200 else "Prepare-toi a perdre !"
            except Exception:
                msg_box[0] = "Prepare-toi a perdre !"

        threading.Thread(target=_fetch_intro, daemon=True).start()

        intro_done = False
        while not intro_done:
            clock.tick(60)
            rects_i = draw_intro_boss(boss_name, type_ia, difficulte, msg_box[0])
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return "DEFAITE"
                if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                    if msg_box[0] != "...":
                        intro_done = True
                if e.type == pygame.MOUSEBUTTONDOWN:
                    btn = rects_i.get("commencer")
                    if btn and btn.collidepoint(e.pos):
                        intro_done = True

        # ── Phase 3 : Combat avec dialogue Undertale ─────────────────────
        from .draw import draw as draw_chess

        dialogue   = _BattleDialogue(boss_personality, boss_name)
        text_input = _TextInput()

        jeu = Jeu()
        jeu.niveau_ia = difficulte
        jeu.appliquer_types(selected, type_ia)

        def _run_ia_diag(j):
            _run_ia(j, dialogue)

        def _can_play():
            return not dialogue.is_fetching and not text_input.active and not dialogue.active

        talked_this_turn = False
        prev_tour        = jeu.tour
        ia_turn_start    = 0
        IA_DELAY_MS      = 900

        while True:
            clock.tick(60)
            now = pygame.time.get_ticks()

            # Réinitialiser la parole au début de chaque tour joueur
            if jeu.tour == "JOUEUR" and prev_tour == "IA":
                talked_this_turn = False
            # Horodater le début du tour IA pour le délai
            if jeu.tour == "IA" and prev_tour == "JOUEUR":
                ia_turn_start = now
            prev_tour = jeu.tour

            offset, _, _ = draw_chess(jeu, en_campagne=True, boss_name=boss_name)
            dialogue.draw(screen, text_input.active, talked_this_turn)
            text_input.draw(screen)
            pygame.display.flip()

            # ── Victoire par dialogue ────────────────────────────────────
            if dialogue.surrendered and not dialogue.is_fetching:
                _draw_surrender_screen(screen, boss_name)
                pygame.display.flip()
                _wait_for_click(clock)
                return "VICTOIRE"

            # ── IA joue après délai (laisse voir les effets de statut) ───
            if (jeu.tour == "IA" and not jeu.ia_en_cours and not jeu.partie_terminee
                    and not dialogue.is_fetching
                    and ia_turn_start > 0
                    and now - ia_turn_start >= IA_DELAY_MS):
                jeu.ia_en_cours = True
                threading.Thread(target=_run_ia_diag, args=(jeu,), daemon=True).start()

            # ── Fin de partie aux échecs ─────────────────────────────────
            if jeu.partie_terminee and jeu.gagnant:
                if jeu.gagnant == "IA":
                    _show_final_state(screen, clock, jeu, dialogue, boss_name, draw_chess, defeat=True)
                    return "DEFAITE"
                else:
                    _show_final_state(screen, clock, jeu, dialogue, boss_name, draw_chess, defeat=False)
                    return "VICTOIRE"

            # ── Événements ───────────────────────────────────────────────
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return "DEFAITE"

                if text_input.active:
                    result = text_input.handle_event(e)
                    if result is not None:
                        dialogue.discuss(result)
                    continue

                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_a and _can_play():
                        dialogue.player_taunt()
                    elif e.key == pygame.K_t and _can_play() and not talked_this_turn and jeu.tour == "JOUEUR":
                        text_input.open()
                        talked_this_turn = True
                    elif e.key == pygame.K_RETURN and not dialogue.is_fetching:
                        dialogue.dismiss()

                if e.type == pygame.MOUSEBUTTONDOWN:
                    if dialogue.active and not dialogue.is_fetching:
                        dialogue.dismiss()
                    elif _can_play():
                        prev = jeu.tour
                        jeu.click(e.pos, offset)
                        if jeu.tour != prev:
                            dialogue.on_move(jeu)

    finally:
        _restore(assets, draw_mod, orig)


def _wait_with_events(clock, duration_ms: int):
    """Attend `duration_ms` ms en traitant les événements (skip sur touche)."""
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < duration_ms:
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return


def _wait_for_click(clock):
    """Attend un clic ou une touche sans timeout."""
    while True:
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return


def _show_final_state(screen, clock, jeu, dialogue, boss_name, draw_chess_fn, defeat: bool):
    """Affiche l'état final du plateau avec overlay, attend un clic pour continuer."""
    while True:
        clock.tick(60)
        draw_chess_fn(jeu, en_campagne=True, boss_name=boss_name)
        if defeat:
            _draw_defeat_overlay(screen)
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return
