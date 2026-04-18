import sys
import subprocess
import os
import warnings
import random
from io import StringIO

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def asset_path(name):
    return os.path.join(BASE_DIR, name)


# Rediriger stdout et stderr pour supprimer les messages de pygame
old_stdout = sys.stdout
old_stderr = sys.stderr
sys.stdout = StringIO()
sys.stderr = StringIO()

import pygame
from pygame.locals import *
import ressources
import tours
import player_select

sys.stdout = old_stdout
sys.stderr = old_stderr

# Fichier principal: Gere menu, carte hex, ressources, et integration multiplayer/tours
# Etat jeu: "menu" / "game" / "multi_game"


pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    pass

# creation d'une fenetre
display_info = pygame.display.Info()
start_w = min(1920, max(1024, display_info.current_w))
start_h = min(1080, max(720, display_info.current_h))
fenetre = pygame.display.set_mode((start_w, start_h), pygame.RESIZABLE)

# Variables globales jeu
# game_state controle affichage/logique (menu / game / multi_game)
game_state = "menu"
carte = None
turn_manager = None
current_player_resources = None

# chargement des images
liste_actuelle = []

# images de fond (menus et maps)
menu = pygame.image.load(asset_path("background.png")).convert_alpha()
menu = pygame.transform.scale(menu, (1920, 1080))

# tuiles de terrain
try:
    Eau_1 = pygame.transform.scale(pygame.image.load(asset_path("Eau_1.png")), (32, 42))
    Eau_2 = pygame.transform.scale(pygame.image.load(asset_path("Eau_2.png")), (32, 42))
    Eau_3 = pygame.transform.scale(pygame.image.load(asset_path("Eau_3.png")), (32, 42))
    Herbe_1 = pygame.transform.scale(pygame.image.load(asset_path("Herbe_1.png")), (32, 42))
    Herbe_2 = pygame.transform.scale(pygame.image.load(asset_path("Herbe_2.png")), (32, 42))
    Herbe_3 = pygame.transform.scale(pygame.image.load(asset_path("Herbe_3.png")), (32, 42))
    Pierre_1 = pygame.transform.scale(pygame.image.load(asset_path("Pierre_1.png")), (32, 42))
    IMAGES_LOADED = True
except Exception:
    Eau_1 = pygame.Surface((32, 42))
    Eau_1.fill((0, 0, 255))
    Eau_2 = Eau_1
    Eau_3 = Eau_1
    Herbe_1 = pygame.Surface((32, 42))
    Herbe_1.fill((0, 255, 0))
    Herbe_2 = Herbe_1
    Herbe_3 = Herbe_1
    Pierre_1 = pygame.Surface((32, 42))
    Pierre_1.fill((128, 128, 128))
    IMAGES_LOADED = False

# Dictionnaire des tuiles
tuiles = {
    "eau": Eau_1,
    "herbe": Herbe_1,
    "foret": Herbe_2,
    "montagne": Pierre_1,
}

terrain_variantes = {
    "eau": [Eau_1, Eau_2, Eau_3],
    "herbe": [Herbe_1],
    "foret": [Herbe_2, Herbe_3],
    "montagne": [Pierre_1],
}

# musique
menu_music = asset_path("menu-musique.mp3")

# couleurs
BLANC = (255, 255, 255)
NOIR = (0, 0, 0)
VERT = (0, 255, 0)
ROUGE = (255, 0, 0)
BLEU = (0, 0, 255)
JAUNE = (255, 255, 0)
TRANSLUCENT_BLUE = (0, 80, 255, 100)
HOVER_BLUE = (0, 140, 255, 220)
SHADOW = (0, 0, 0)
PANEL_BG = (6, 12, 22, 190)
PANEL_BORDER = (210, 210, 210, 125)

PLAYER_COLORS = [
    (244, 210, 92),
    (116, 180, 255),
    (118, 224, 146),
    (241, 130, 120),
]

# polices
FONT_TITLE = pygame.font.SysFont(None, 72)
FONT_BUTTON = pygame.font.SysFont(None, 36)
FONT_HUD = pygame.font.SysFont(None, 30)
FONT_SMALL = pygame.font.SysFont(None, 24)
FONT_TINY = pygame.font.SysFont(None, 21)
FONT_TILE = pygame.font.SysFont(None, 16, bold=True)
STARTING_TERRITORY_RADIUS = 1
STARTING_POSITION_SEPARATION = 12
HUD_PADDING = 18
HEADER_HEIGHT = 88
FOOTER_HEIGHT = 88
MAP_INSET = 12
MAP_PAN_SPEED = 14
SIDEBAR_GAP = 18
SELECTED_PANEL_DROP = 56
END_TURN_BUTTON_HEIGHT = 56
END_TURN_BOTTOM_MARGIN = 16
END_TURN_PANEL_GAP = 18
TURN_DURATION_MS = 2 * 60 * 1000

camera_pan_x = 0
camera_pan_y = 0
map_drag_active = False
turn_timer_started_at = None


def load_trimmed_image(path, min_alpha=25):
    """Charge une image et retourne uniquement la partie visible."""
    full_path = asset_path(path)
    if not os.path.exists(full_path):
        return None
    image = pygame.image.load(full_path).convert_alpha()
    bounds = image.get_bounding_rect(min_alpha=min_alpha)
    if bounds.width > 0 and bounds.height > 0:
        return image.subsurface(bounds).copy()
    return image


def load_menu_button_images(path):
    """Detecte les regions de boutons dans le spritesheet et retourne un dict par action."""
    full_path = asset_path(path)
    if not os.path.exists(full_path):
        return {}
    sheet = pygame.image.load(full_path).convert_alpha()
    mask = pygame.mask.from_surface(sheet, threshold=25)
    components = mask.connected_components()
    if not components:
        return {}
    rects = sorted(
        [
            c.get_bounding_rects()[0]
            for c in components
            if (c.get_bounding_rects()[0].width * c.get_bounding_rects()[0].height) >= 500
        ],
        key=lambda r: (r.y, r.x),
    )
    actions = ["new_game", "multiplayer", "quit", "options"]
    images = {}
    for i, action in enumerate(actions):
        if i < len(rects):
            normal = sheet.subsurface(rects[i]).copy()
            hover = normal.copy()
            bright = pygame.Surface(hover.get_size(), pygame.SRCALPHA)
            bright.fill((255, 255, 255, 40))
            hover.blit(bright, (0, 0))
            images[action] = {"normal": normal, "hover": hover}
    return images


def load_option_button_images(path):
    """Charge les images des boutons d'options depuis le spritesheet."""
    full_path = asset_path(path)
    if not os.path.exists(full_path):
        return {}
    sheet = pygame.image.load(full_path).convert_alpha()
    mask = pygame.mask.from_surface(sheet, threshold=25)
    components = mask.connected_components()
    if not components:
        return {}
    rects = sorted(
        [
            c.get_bounding_rects()[0]
            for c in components
            if (c.get_bounding_rects()[0].width * c.get_bounding_rects()[0].height) >= 500
        ],
        key=lambda r: (r.y, r.x),
    )
    key_map = {4: "1920x1080", 5: "1280x720", 6: "2560x1440", 7: "back"}
    images = {}
    for idx, key in key_map.items():
        if idx < len(rects):
            images[key] = sheet.subsurface(rects[idx]).copy()

    path_1600 = asset_path("1600 x 900.png")
    if os.path.exists(path_1600):
        img_1600 = pygame.image.load(path_1600).convert_alpha()
        mask_1600 = pygame.mask.from_surface(img_1600, threshold=25)
        comps_1600 = mask_1600.connected_components()
        if comps_1600:
            rects_1600 = sorted(
                [
                    c.get_bounding_rects()[0]
                    for c in comps_1600
                    if (c.get_bounding_rects()[0].width * c.get_bounding_rects()[0].height) >= 500
                ],
                key=lambda r: r.y,
            )
            if rects_1600:
                images["1600x900"] = img_1600.subsurface(rects_1600[0]).copy()
    return images


def scale_surface_to_fit(surface, max_width, max_height):
    w, h = surface.get_size()
    scale = min(max_width / w, max_height / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return pygame.transform.smoothscale(surface, (new_w, new_h))


def get_button_display_image(action, is_hover, win_size):
    if not button_images or action not in button_images:
        return None
    win_w, win_h = win_size
    max_width = min(420, win_w * 0.24)
    max_height = min(100, win_h * 0.1)
    key = "hover" if is_hover else "normal"
    img = button_images[action].get(key, button_images[action]["normal"])
    return scale_surface_to_fit(img, max_width, max_height)


def get_option_button_background(key, max_width, max_height):
    if option_button_images and key in option_button_images:
        bg = option_button_images[key]
        return pygame.transform.smoothscale(bg, (int(max_width), int(max_height)))
    if button_images and "new_game" in button_images:
        bg = button_images["new_game"]["normal"]
        return pygame.transform.smoothscale(bg, (int(max_width), int(max_height)))
    return None


def draw_option_image_button(surface, rect, image, label=None):
    if image:
        img_rect = image.get_rect(center=rect.center)
        surface.blit(image, img_rect)


def draw_panel_background(surface, rect, fill=PANEL_BG, border=PANEL_BORDER, radius=16):
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=radius)
    pygame.draw.rect(panel, border, panel.get_rect(), width=1, border_radius=radius)
    surface.blit(panel, rect)
    return rect


def draw_info_panel(surface, texts, anchor, align="topleft", font=FONT_HUD):
    if isinstance(texts, str):
        texts = [texts]

    rendered = [font.render(text, True, BLANC) for text in texts]
    shadows = [font.render(text, True, SHADOW) for text in texts]

    pad_x = 14
    pad_y = 10
    line_gap = 6
    panel_width = max(surf.get_width() for surf in rendered) + pad_x * 2
    panel_height = sum(surf.get_height() for surf in rendered) + pad_y * 2 + line_gap * (len(rendered) - 1)

    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (6, 12, 22, 175), panel.get_rect(), border_radius=14)
    pygame.draw.rect(panel, (210, 210, 210, 120), panel.get_rect(), width=1, border_radius=14)

    rect = panel.get_rect(**{align: anchor})
    surface.blit(panel, rect)

    current_y = rect.y + pad_y
    for shadow, text in zip(shadows, rendered):
        text_rect = text.get_rect(x=rect.x + pad_x, y=current_y)
        surface.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text, text_rect)
        current_y += text.get_height() + line_gap

    return rect


def draw_timer_panel(surface, remaining_ms, midtop=None):
    mins = remaining_ms // 60000
    secs = (remaining_ms % 60000) // 1000
    timer_text = f"{mins:02d}:{secs:02d}"
    timer_surf = FONT_TIMER.render(timer_text, False, BLANC)
    pad_x, pad_y = 14, 8
    box_w = timer_surf.get_width() + pad_x * 2
    box_h = timer_surf.get_height() + pad_y * 2
    box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    pygame.draw.rect(box_surf, (6, 12, 22, 190), (0, 0, box_w, box_h), border_radius=14)
    pygame.draw.rect(box_surf, (210, 210, 210, 130), (0, 0, box_w, box_h), width=1, border_radius=14)

    if midtop is None:
        midtop = (surface.get_width() // 2, HUD_PADDING)
    box_rect = box_surf.get_rect(midtop=midtop)
    surface.blit(box_surf, box_rect)
    timer_rect = timer_surf.get_rect(center=box_rect.center)
    surface.blit(timer_surf, timer_rect)


def update_menu_layout(win):
    win_w, win_h = win.get_size()
    title_w = min(1305, win_w * 0.72)
    title_h = min(252, win_h * 0.234)
    title_y = max(8, win_h * 0.01)
    if title_banner is not None:
        title_surf = scale_surface_to_fit(title_banner, title_w, title_h)
    else:
        title_surf = FONT_TITLE.render("Timeless Empire", True, BLANC)
    title_rect = title_surf.get_rect(centerx=win_w // 2, top=int(title_y))

    sample_img = get_button_display_image("new_game", False, (win_w, win_h))
    btn_h_actual = sample_img.get_height() if sample_img else 70
    gap = max(18, win_h * 0.02)
    btn_start_y = title_rect.bottom + gap * 2
    for i, btn in enumerate(boutons_menu):
        img = get_button_display_image(btn.action, False, (win_w, win_h))
        if img:
            btn.widtht = img.get_width()
            btn.height = img.get_height()
        btn.center_y = int(btn_start_y + i * (btn_h_actual + gap) + btn_h_actual // 2)
        btn.rect = pygame.Rect(0, 0, btn.widtht, btn.height)
        btn.rect.center = (win_w // 2, btn.center_y)
    return title_surf, title_rect


title_banner = load_trimmed_image("Banière_titre.png", min_alpha=25)
button_images = load_menu_button_images("Boutons_menu.png")
option_button_images = load_option_button_images("Boutons_menu.png")


class Hexagone:
    def __init__(self, q, r, type_terrain, tuile_surface=None):
        self.q = q
        self.r = r
        self.type_terrain = type_terrain
        self.tuile = tuile_surface if tuile_surface is not None else tuiles[type_terrain]
        self.selection_lift = 0.0
        self.target_lift = 0.0

    def get_pixel_pos(self, size=32, vertical_spacing=42):
        x = self.q * size * 1.0
        if self.r % 2 == 1:
            x += size * 0.5
        y = self.r * vertical_spacing * 0.5
        return int(x), int(y)


class Carte:
    def __init__(self, largeur, hauteur):
        self.largeur = largeur
        self.hauteur = hauteur
        self.hexagones = []
        self.hex_lookup = {}
        self.selected_hex = None
        self._mask_cache = {}
        self.generer_carte()

    def update_selection_animation(self):
        for hex_obj in self.hexagones:
            delta = hex_obj.target_lift - hex_obj.selection_lift
            if abs(delta) < 0.01:
                hex_obj.selection_lift = hex_obj.target_lift
            else:
                hex_obj.selection_lift += delta * 0.22

    def select_hex(self, hex_obj):
        if self.selected_hex is not None and self.selected_hex is not hex_obj:
            self.selected_hex.target_lift = 0.0

        if hex_obj is None:
            self.selected_hex = None
            return

        self.selected_hex = hex_obj
        self.selected_hex.target_lift = 1.0

    def generer_carte(self):
        self.hexagones.clear()
        self.hex_lookup.clear()

        terrain_pool = ["herbe"] * 45 + ["foret"] * 28 + ["montagne"] * 18 + ["eau"] * 9
        n_seeds = max(28, (self.largeur * self.hauteur) // 10)
        seeds = [
            (
                random.randint(0, self.largeur - 1),
                random.randint(0, self.hauteur - 1),
                random.choice(terrain_pool),
            )
            for _ in range(n_seeds)
        ]

        noise_scale = (self.largeur + self.hauteur) / 28.0
        terrain_grid = {}
        for r in range(self.hauteur):
            for q in range(self.largeur):
                best_type = "herbe"
                min_dist = float("inf")
                for sq, sr, st in seeds:
                    d = ((q - sq) ** 2 + (r - sr) ** 2) ** 0.5
                    d += random.gauss(0, noise_scale)
                    if d < min_dist:
                        min_dist = d
                        best_type = st
                terrain_grid[(q, r)] = best_type

        for _ in range(2):
            new_grid = {}
            for r in range(self.hauteur):
                for q in range(self.largeur):
                    neighbors = self._get_existing_neighbors(q, r, terrain_grid)
                    if len(neighbors) < 2:
                        new_grid[(q, r)] = terrain_grid[(q, r)]
                        continue
                    counts = {}
                    for t in neighbors:
                        counts[t] = counts.get(t, 0) + 1
                    majority = max(counts, key=counts.get)
                    if counts[majority] >= 5:
                        new_grid[(q, r)] = majority
                    else:
                        new_grid[(q, r)] = terrain_grid[(q, r)]
            terrain_grid = new_grid

        for r in range(self.hauteur):
            for q in range(self.largeur):
                type_terrain = terrain_grid[(q, r)]
                tuile_surface = self._choose_tile_surface(type_terrain)
                hex_obj = Hexagone(q, r, type_terrain, tuile_surface=tuile_surface)
                self.hexagones.append(hex_obj)
                self.hex_lookup[(q, r)] = hex_obj

    def _choose_tile_surface(self, type_terrain):
        variantes = terrain_variantes.get(type_terrain, [tuiles[type_terrain]])
        return random.choice(variantes)

    def _get_existing_neighbors(self, q, r, terrain_grid):
        if r % 2 == 0:
            offsets = [(-1, 0), (1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1)]
        else:
            offsets = [(-1, 0), (1, 0), (1, -1), (0, -1), (1, 1), (0, 1)]

        found = []
        for dq, dr in offsets:
            nq, nr = q + dq, r + dr
            if (nq, nr) in terrain_grid:
                found.append(terrain_grid[(nq, nr)])
        return found

    def get_hex(self, q, r):
        return self.hex_lookup.get((q, r))

    def get_neighbors(self, hex_obj):
        if hex_obj.r % 2 == 0:
            offsets = [(-1, 0), (1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1)]
        else:
            offsets = [(-1, 0), (1, 0), (1, -1), (0, -1), (1, 1), (0, 1)]

        neighbors = []
        for dq, dr in offsets:
            neighbor = self.get_hex(hex_obj.q + dq, hex_obj.r + dr)
            if neighbor is not None:
                neighbors.append(neighbor)
        return neighbors

    def get_hexes_in_radius(self, center_hex, radius):
        visited = {(center_hex.q, center_hex.r)}
        frontier = [center_hex]
        results = [center_hex]

        for _ in range(radius):
            next_frontier = []
            for hex_obj in frontier:
                for neighbor in self.get_neighbors(hex_obj):
                    key = (neighbor.q, neighbor.r)
                    if key not in visited:
                        visited.add(key)
                        next_frontier.append(neighbor)
                        results.append(neighbor)
            frontier = next_frontier

        return results

    def get_world_bounds(self):
        if not self.hexagones:
            return pygame.Rect(0, 0, 0, 0)

        left = min(hex_obj.get_pixel_pos()[0] for hex_obj in self.hexagones)
        top = min(hex_obj.get_pixel_pos()[1] for hex_obj in self.hexagones)
        right = max(hex_obj.get_pixel_pos()[0] + hex_obj.tuile.get_width() for hex_obj in self.hexagones)
        bottom = max(hex_obj.get_pixel_pos()[1] + hex_obj.tuile.get_height() for hex_obj in self.hexagones)
        return pygame.Rect(left, top, right - left, bottom - top)

    def dessiner(self, surface, territory_lookup=None, placed_buildings=None, offset_x=0, offset_y=0):
        self.update_selection_animation()
        hexagones_tries = sorted(self.hexagones, key=lambda h: (h.get_pixel_pos()[1], h.get_pixel_pos()[0]))

        for hex_obj in hexagones_tries:
            x, y = hex_obj.get_pixel_pos()
            x += offset_x
            y += offset_y
            y -= int(hex_obj.selection_lift * 10)
            if -50 < x < surface.get_width() + 50 and -50 < y < surface.get_height() + 50:
                try:
                    surface.blit(hex_obj.tuile, (x, y))
                    if territory_lookup is not None:
                        owner_player = territory_lookup.get((hex_obj.q, hex_obj.r))
                        if owner_player is not None:
                            self.draw_territory_overlay(surface, hex_obj, x, y, owner_player.color)
                    if placed_buildings is not None:
                        building_info = placed_buildings.get((hex_obj.q, hex_obj.r))
                        if building_info is not None:
                            self.draw_building_marker(surface, hex_obj, x, y, building_info)
                except Exception:
                    pass

    def draw_territory_overlay(self, surface, hex_obj, x, y, color):
        if color is None:
            return

        tile = hex_obj.tuile
        mask = self._get_mask_for_tile(tile)
        overlay_key = (id(tile), "territory", color)

        if overlay_key not in self._mask_cache:
            overlay = pygame.Surface(tile.get_size(), pygame.SRCALPHA)
            w, h = tile.get_size()
            for px in range(w):
                for py in range(h):
                    if mask.get_at((px, py)):
                        overlay.set_at((px, py), (*color, 58))
            self._mask_cache[overlay_key] = overlay

        overlay = self._mask_cache[overlay_key]
        surface.blit(overlay, (x, y))

    def draw_building_marker(self, surface, hex_obj, x, y, building_info):
        owner_player, placed_building = building_info
        badge_text = tours.get_building_short(placed_building.building)
        badge_color = owner_player.color if owner_player and owner_player.color is not None else (110, 110, 110)
        text_surf = FONT_TILE.render(badge_text, True, NOIR)
        badge_w = max(22, text_surf.get_width() + 10)
        badge_h = text_surf.get_height() + 6
        badge_rect = pygame.Rect(0, 0, badge_w, badge_h)
        badge_rect.center = (x + hex_obj.tuile.get_width() // 2, y + int(hex_obj.tuile.get_height() * 0.7))

        badge = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
        pygame.draw.rect(badge, (*badge_color, 220), badge.get_rect(), border_radius=8)
        pygame.draw.rect(badge, (0, 0, 0, 150), badge.get_rect(), width=1, border_radius=8)
        surface.blit(badge, badge_rect)
        text_rect = text_surf.get_rect(center=badge_rect.center)
        surface.blit(text_surf, text_rect)

    def draw_buildable_overlay(self, surface, hex_obj, x, y):
        tile = hex_obj.tuile
        mask = self._get_mask_for_tile(tile)
        w, h = tile.get_size()
        cut_y = int(h * 0.62)

        tile_key = id(tile)
        overlay_key = (tile_key, "buildable_overlay62")
        if overlay_key not in self._mask_cache:
            top_overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            for cx in range(w):
                for yy in range(cut_y):
                    if mask.get_at((cx, yy)):
                        top_overlay.set_at((cx, yy), (255, 255, 0, 80))
            self._mask_cache[overlay_key] = top_overlay

        top_overlay = self._mask_cache[overlay_key]
        surface.blit(top_overlay, (x, y))

        outline_key = (tile_key, "buildable_outline62")
        if outline_key not in self._mask_cache:
            top_mask = pygame.mask.from_surface(top_overlay, threshold=1)
            self._mask_cache[outline_key] = top_mask.outline()

        outline = self._mask_cache[outline_key]
        if len(outline) > 1:
            max_oy = max(oy for _, oy in outline)
            pts = [(x + ox, y + oy) for ox, oy in outline if oy < max_oy - 1]
            if len(pts) > 1:
                pygame.draw.lines(surface, (255, 255, 0), False, pts, 2)

    def _get_mask_for_tile(self, tile_surface):
        key = id(tile_surface)
        if key not in self._mask_cache:
            self._mask_cache[key] = pygame.mask.from_surface(tile_surface, threshold=10)
        return self._mask_cache[key]

    def get_hex_at_pixel(self, px, py, offset_x=0, offset_y=0):
        hexagones_tries = sorted(self.hexagones, key=lambda h: (h.get_pixel_pos()[1], h.get_pixel_pos()[0]))
        for hex_obj in reversed(hexagones_tries):
            x, y = hex_obj.get_pixel_pos()
            x += offset_x
            y += offset_y
            y -= int(hex_obj.selection_lift * 10)
            tile = hex_obj.tuile
            rect = pygame.Rect(x, y, tile.get_width(), tile.get_height())
            if not rect.collidepoint(px, py):
                continue
            lx = px - x
            ly = py - y
            mask = self._get_mask_for_tile(tile)
            if 0 <= lx < tile.get_width() and 0 <= ly < tile.get_height() and mask.get_at((int(lx), int(ly))):
                return hex_obj
        return None

    def draw_hex_highlight(self, surface, hex_obj, offset_x=0, offset_y=0):
        if hex_obj is None:
            return
        x, y = hex_obj.get_pixel_pos()
        x += offset_x
        y += offset_y
        y -= int(hex_obj.selection_lift * 10)
        tile = hex_obj.tuile
        mask = self._get_mask_for_tile(tile)

        w, h = tile.get_size()
        cut_y = int(h * 0.62)

        tile_key = id(tile)
        overlay_key = (tile_key, "overlay62")
        if overlay_key not in self._mask_cache:
            top_overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            for cx in range(w):
                for yy in range(cut_y):
                    if mask.get_at((cx, yy)):
                        top_overlay.set_at((cx, yy), (255, 255, 0, 80))
            self._mask_cache[overlay_key] = top_overlay

        top_overlay = self._mask_cache[overlay_key]
        surface.blit(top_overlay, (x, y))

        top_mask = pygame.mask.from_surface(top_overlay, threshold=1)
        outline = top_mask.outline()
        if len(outline) > 1:
            max_oy = max(oy for _, oy in outline)
            pts = [(x + ox, y + oy) for ox, oy in outline if oy < max_oy - 1]
            if len(pts) > 1:
                pygame.draw.lines(surface, (255, 255, 0), False, pts, 2)


class Button:
    def __init__(self, text, center_y, action):
        self.text = text
        self.center_y = center_y
        self.action = action
        self.widtht, self.height = 320, 70
        self.rect = pygame.Rect((0, 0, self.widtht, self.height))
        self.rect.center = (0, self.center_y)

    def draw(self, win, mouse_pos):
        self.rect.center = (win.get_width() // 2, self.center_y)
        is_hover = self.rect.collidepoint(mouse_pos)
        img = get_button_display_image(self.action, is_hover, win.get_size())
        if img:
            img_rect = img.get_rect(center=self.rect.center)
            win.blit(img, img_rect)
            return
        color = HOVER_BLUE if is_hover else TRANSLUCENT_BLUE
        button_surface = pygame.Surface((self.widtht, self.height), pygame.SRCALPHA)
        pygame.draw.rect(button_surface, color, (0, 0, self.widtht, self.height), border_radius=16)
        win.blit(button_surface, self.rect)
        text_surf = FONT_BUTTON.render(self.text, True, BLANC)
        text_rect = text_surf.get_rect(center=self.rect.center)
        shadow = FONT_BUTTON.render(self.text, True, SHADOW)
        win.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
        win.blit(text_surf, text_rect)

    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]


boutons_menu = [
    Button("New Game", 400, "new_game"),
    Button("Multiplayer", 480, "multiplayer"),
    Button("Options", 560, "options"),
    Button("Quit", 640, "quit"),
]


def show_options(screen, menu_surface, clock):
    """Affiche un menu modal pour choisir la resolution. Retourne (screen, menu_surface)."""
    options_running = True
    resolutions = [(1280, 720), (1600, 900), (1920, 1080), (2560, 1440)]
    btn_w, btn_h = 320, 70
    padding = 20

    while options_running:
        win_w, win_h = screen.get_size()
        total_height = len(resolutions) * btn_h + (len(resolutions) - 1) * padding
        start_y = max(90, (win_h - total_height) // 2)

        option_buttons = []
        for i, (rw, rh) in enumerate(resolutions):
            rect = pygame.Rect(0, 0, btn_w, btn_h)
            rect.center = (win_w // 2, start_y + i * (btn_h + padding) + btn_h // 2)
            option_buttons.append((rect, (rw, rh)))

        back_rect = pygame.Rect(0, 0, btn_w, btn_h)
        back_rect.center = (win_w // 2, start_y + total_height + btn_h // 2 + padding * 2)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                options_running = False
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                if back_rect.collidepoint((mx, my)):
                    options_running = False
                else:
                    for rect, (rw, rh) in option_buttons:
                        if rect.collidepoint((mx, my)):
                            screen = pygame.display.set_mode((rw, rh), pygame.RESIZABLE)
                            try:
                                menu_image = pygame.image.load(asset_path("background.png")).convert_alpha()
                                menu_surface = pygame.transform.scale(menu_image, (rw, rh))
                            except Exception:
                                menu_surface = pygame.transform.scale(menu_surface, (rw, rh))
                            options_running = False
                            break

        scaled_menu = pygame.transform.smoothscale(menu_surface, (win_w, win_h))
        screen.blit(scaled_menu, (0, 0))
        overlay = pygame.Surface((win_w, win_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        mx, my = pygame.mouse.get_pos()

        for rect, (rw, rh) in option_buttons:
            label = f"{rw} x {rh}"
            key = f"{rw}x{rh}"
            bg = get_option_button_background(key, rect.width, rect.height)
            if bg:
                draw_option_image_button(screen, rect, bg)
            else:
                is_hover = rect.collidepoint((mx, my))
                color = HOVER_BLUE if is_hover else TRANSLUCENT_BLUE
                surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
                pygame.draw.rect(surf, color, (0, 0, btn_w, btn_h), border_radius=16)
                screen.blit(surf, rect)
                text_surf = FONT_BUTTON.render(label, True, BLANC)
                text_rect = text_surf.get_rect(center=rect.center)
                shadow = FONT_BUTTON.render(label, True, SHADOW)
                screen.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
                screen.blit(text_surf, text_rect)

        bg = get_option_button_background("back", back_rect.width, back_rect.height)
        if bg:
            draw_option_image_button(screen, back_rect, bg)
        else:
            is_hover = back_rect.collidepoint((mx, my))
            color = HOVER_BLUE if is_hover else TRANSLUCENT_BLUE
            surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
            pygame.draw.rect(surf, color, (0, 0, btn_w, btn_h), border_radius=16)
            screen.blit(surf, back_rect)
            back_text = FONT_BUTTON.render("Back", True, BLANC)
            back_text_rect = back_text.get_rect(center=back_rect.center)
            back_shadow = FONT_BUTTON.render("Back", True, SHADOW)
            screen.blit(back_shadow, (back_text_rect.x + 2, back_text_rect.y + 2))
            screen.blit(back_text, back_text_rect)

        pygame.display.flip()
        clock.tick(60)

    return screen, menu_surface


def music_menu(music_file):
    try:
        if not pygame.mixer.get_init():
            return
        if not os.path.exists(music_file):
            return
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(-1)
    except pygame.error:
        pass


status_message = ""
status_message_until = 0
build_action_rects = []
end_turn_rect = None


def assign_player_colors(players):
    for index, player in enumerate(players):
        player.color = PLAYER_COLORS[index % len(PLAYER_COLORS)]


def get_building_entry_at_coords(q, r):
    if not turn_manager:
        return None, None

    for player in turn_manager.players:
        for placed_building in player.buildings:
            if placed_building.q == q and placed_building.r == r:
                return player, placed_building

    return None, None


def get_building_entry_at_hex(hex_obj):
    if hex_obj is None:
        return None, None
    return get_building_entry_at_coords(hex_obj.q, hex_obj.r)


def get_territory_owner_at_coords(q, r):
    if not turn_manager:
        return None

    for player in turn_manager.players:
        if player.owns_tile(q, r):
            return player

    return None


def get_territory_owner_at_hex(hex_obj):
    if hex_obj is None:
        return None
    return get_territory_owner_at_coords(hex_obj.q, hex_obj.r)


def get_territory_lookup():
    territory_lookup = {}
    if not turn_manager:
        return territory_lookup

    for player in turn_manager.players:
        for q, r in player.owned_tiles:
            territory_lookup[(q, r)] = player

    return territory_lookup


def get_placed_buildings_lookup():
    placed_buildings = {}
    if not turn_manager:
        return placed_buildings

    for player in turn_manager.players:
        for placed_building in player.buildings:
            if placed_building.q is None or placed_building.r is None:
                continue
            placed_buildings[(placed_building.q, placed_building.r)] = (player, placed_building)

    return placed_buildings


def get_buildable_hexes_for_player(player):
    if not carte or not turn_manager or player is None:
        return []

    buildable_hexes = []
    for q, r in player.owned_tiles:
        hex_obj = carte.get_hex(q, r)
        if hex_obj is None or hex_obj.type_terrain == "eau":
            continue

        owner_player, placed_building = get_building_entry_at_coords(q, r)
        if owner_player is not None and owner_player is not player:
            continue

        current_building = placed_building.building if placed_building else None
        options = turn_manager.get_available_buildings(hex_obj.type_terrain, current_building)
        if options:
            buildable_hexes.append(hex_obj)

    return buildable_hexes


def get_game_layout(surface):
    win_w, win_h = surface.get_size()
    sidebar_w = min(390, max(320, int(win_w * 0.28)))
    sidebar_rect = pygame.Rect(
        win_w - sidebar_w - HUD_PADDING,
        HUD_PADDING,
        sidebar_w,
        win_h - HUD_PADDING * 2,
    )

    map_rect = pygame.Rect(
        HUD_PADDING,
        HEADER_HEIGHT + HUD_PADDING,
        sidebar_rect.x - HUD_PADDING * 2,
        win_h - HEADER_HEIGHT - FOOTER_HEIGHT - HUD_PADDING * 2,
    )

    resources_rect = pygame.Rect(sidebar_rect.x, sidebar_rect.y, sidebar_rect.width, 146)
    selected_top = resources_rect.bottom + SIDEBAR_GAP + SELECTED_PANEL_DROP
    end_turn_top = sidebar_rect.bottom - END_TURN_BOTTOM_MARGIN - END_TURN_BUTTON_HEIGHT
    selected_height = max(120, end_turn_top - END_TURN_PANEL_GAP - selected_top)
    selected_rect = pygame.Rect(sidebar_rect.x, selected_top, sidebar_rect.width, selected_height)
    footer_rect = pygame.Rect(HUD_PADDING, map_rect.bottom + 12, map_rect.width, FOOTER_HEIGHT - 12)
    map_offset = (map_rect.x + MAP_INSET, map_rect.y + MAP_INSET)

    return {
        "sidebar_rect": sidebar_rect,
        "resources_rect": resources_rect,
        "selected_rect": selected_rect,
        "map_rect": map_rect,
        "map_base_offset": map_offset,
        "footer_rect": footer_rect,
    }


def clamp_map_camera(layout):
    global camera_pan_x, camera_pan_y

    if not carte:
        camera_pan_x = 0
        camera_pan_y = 0
        return

    bounds = carte.get_world_bounds()
    viewport_w = max(1, layout["map_rect"].width - MAP_INSET * 2)
    viewport_h = max(1, layout["map_rect"].height - MAP_INSET * 2)

    if bounds.width <= viewport_w:
        camera_pan_x = int((viewport_w - bounds.width) / 2 - bounds.left)
    else:
        min_pan_x = viewport_w - bounds.right
        max_pan_x = -bounds.left
        camera_pan_x = max(min_pan_x, min(max_pan_x, camera_pan_x))

    if bounds.height <= viewport_h:
        camera_pan_y = int((viewport_h - bounds.height) / 2 - bounds.top)
    else:
        min_pan_y = viewport_h - bounds.bottom
        max_pan_y = -bounds.top
        camera_pan_y = max(min_pan_y, min(max_pan_y, camera_pan_y))


def center_map_camera(layout):
    global camera_pan_x, camera_pan_y

    if not carte:
        camera_pan_x = 0
        camera_pan_y = 0
        return

    bounds = carte.get_world_bounds()
    viewport_w = max(1, layout["map_rect"].width - MAP_INSET * 2)
    viewport_h = max(1, layout["map_rect"].height - MAP_INSET * 2)
    camera_pan_x = int((viewport_w - bounds.width) / 2 - bounds.left)
    camera_pan_y = int((viewport_h - bounds.height) / 2 - bounds.top)
    clamp_map_camera(layout)


def get_map_draw_offset(layout):
    base_x, base_y = layout["map_base_offset"]
    return base_x + camera_pan_x, base_y + camera_pan_y


def pan_map(dx, dy, layout):
    global camera_pan_x, camera_pan_y
    camera_pan_x += dx
    camera_pan_y += dy
    clamp_map_camera(layout)


def get_start_targets(player_count, largeur, hauteur):
    if player_count <= 1:
        return [(largeur // 2, hauteur // 2)]
    if player_count == 2:
        return [(largeur // 4, hauteur // 2), (largeur * 3 // 4, hauteur // 2)]
    if player_count == 3:
        return [(largeur // 4, hauteur // 3), (largeur * 3 // 4, hauteur // 3), (largeur // 2, hauteur * 2 // 3)]
    return [
        (largeur // 4, hauteur // 4),
        (largeur * 3 // 4, hauteur // 4),
        (largeur // 4, hauteur * 3 // 4),
        (largeur * 3 // 4, hauteur * 3 // 4),
    ]


def choose_starting_hexes(players):
    if not carte or not players:
        return []

    land_hexes = [hex_obj for hex_obj in carte.hexagones if hex_obj.type_terrain != "eau"]
    targets = get_start_targets(len(players), carte.largeur, carte.hauteur)
    chosen_hexes = []

    for target_q, target_r in targets:
        best_hex = None
        best_score = None

        for hex_obj in land_hexes:
            too_close = any(
                ((hex_obj.q - other.q) ** 2 + (hex_obj.r - other.r) ** 2) < STARTING_POSITION_SEPARATION ** 2
                for other in chosen_hexes
            )
            if too_close:
                continue

            nearby_hexes = carte.get_hexes_in_radius(hex_obj, 2)
            land_count = sum(1 for nearby in nearby_hexes if nearby.type_terrain != "eau")
            terrain_types = {nearby.type_terrain for nearby in nearby_hexes if nearby.type_terrain != "eau"}
            dist_score = (hex_obj.q - target_q) ** 2 + (hex_obj.r - target_r) ** 2
            grass_bonus = 35 if hex_obj.type_terrain == "herbe" else 0
            score = land_count * 100 + len(terrain_types) * 20 + grass_bonus - dist_score

            if best_score is None or score > best_score:
                best_score = score
                best_hex = hex_obj

        if best_hex is None:
            remaining = [hex_obj for hex_obj in land_hexes if hex_obj not in chosen_hexes]
            if remaining:
                best_hex = remaining[0]
        if best_hex is not None:
            chosen_hexes.append(best_hex)

    return chosen_hexes


def assign_starting_territories(players):
    if not carte:
        return

    for player in players:
        player.owned_tiles.clear()

    starting_hexes = choose_starting_hexes(players)
    for player, start_hex in zip(players, starting_hexes):
        starting_zone = [
            hex_obj
            for hex_obj in carte.get_hexes_in_radius(start_hex, STARTING_TERRITORY_RADIUS)
            if hex_obj.type_terrain != "eau"
        ]
        player.claim_tiles((hex_obj.q, hex_obj.r) for hex_obj in starting_zone)

    if starting_hexes:
        carte.select_hex(starting_hexes[0])
        center_map_camera(get_game_layout(fenetre))


def expand_player_territory(player, source_hex, building_id):
    if not carte or source_hex is None:
        return 0

    territory_radius = tours.get_building_territory_radius(building_id)
    claimed = 0

    for hex_obj in carte.get_hexes_in_radius(source_hex, territory_radius):
        if hex_obj.type_terrain == "eau":
            continue

        current_owner = get_territory_owner_at_coords(hex_obj.q, hex_obj.r)
        if current_owner is None:
            player.claim_tile(hex_obj.q, hex_obj.r)
            claimed += 1
        elif current_owner is player:
            player.claim_tile(hex_obj.q, hex_obj.r)

    return claimed


def set_status_message(text, duration_ms=2600):
    global status_message, status_message_until
    status_message = text
    status_message_until = pygame.time.get_ticks() + duration_ms


def draw_action_button(
    surface,
    rect,
    text,
    mouse_pos,
    enabled=True,
    base_color=(74, 98, 184),
    font=FONT_SMALL,
    right_text=None,
    right_font=None,
):
    if enabled:
        is_hover = rect.collidepoint(mouse_pos)
        color = HOVER_BLUE if is_hover else base_color
        border = (235, 235, 235, 120)
    else:
        color = (70, 74, 90)
        border = (150, 150, 150, 80)

    button_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
    fill_color = color if len(color) == 4 else (*color, 220)
    pygame.draw.rect(button_surface, fill_color, button_surface.get_rect(), border_radius=12)
    pygame.draw.rect(button_surface, border, button_surface.get_rect(), width=1, border_radius=12)
    surface.blit(button_surface, rect)

    text_color = BLANC if enabled else (210, 210, 210)
    text_surf = font.render(text, True, text_color)
    shadow = font.render(text, True, SHADOW)

    if right_text:
        right_font = right_font or font
        text_rect = text_surf.get_rect(midleft=(rect.x + 12, rect.centery))
        surface.blit(shadow, (text_rect.x + 1, text_rect.y + 1))
        surface.blit(text_surf, text_rect)

        right_surf = right_font.render(right_text, True, text_color)
        right_shadow = right_font.render(right_text, True, SHADOW)
        right_rect = right_surf.get_rect(midright=(rect.right - 10, rect.centery))
        surface.blit(right_shadow, (right_rect.x + 1, right_rect.y + 1))
        surface.blit(right_surf, right_rect)
    else:
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(shadow, (text_rect.x + 1, text_rect.y + 1))
        surface.blit(text_surf, text_rect)


def get_active_player():
    if not turn_manager:
        return None
    try:
        return turn_manager.current_player()
    except RuntimeError:
        return None


def add_debug_resources(resource_store):
    if resource_store is None:
        return
    if hasattr(resource_store, "add_resource"):
        resource_store.add_resource("wood", 10)
        resource_store.add_resource("food", 10)
        resource_store.add_resource("gold", 5)
        resource_store.add_resource("money", 5)
    elif isinstance(resource_store, dict):
        resource_store["wood"] = resource_store.get("wood", 0) + 10
        resource_store["food"] = resource_store.get("food", 0) + 10
        resource_store["gold"] = resource_store.get("gold", 0) + 5
        resource_store["money"] = resource_store.get("money", 0) + 5


def handle_end_turn(timed_out=False):
    global current_player_resources

    player = get_active_player()
    if not turn_manager or player is None:
        return

    old_turn_number = turn_manager.turn_number
    old_period = turn_manager.period
    turn_manager.player_finished(player)
    next_player = get_active_player()

    if next_player is not None:
        current_player_resources = next_player.resources
        reset_turn_timer()

    if turn_manager.period != old_period:
        prefix = "Temps ecoule. " if timed_out else ""
        set_status_message(f"{prefix}Periode {turn_manager.period} - {tours.get_period_name(turn_manager.period)}")
    elif turn_manager.turn_number != old_turn_number:
        prefix = "Temps ecoule. " if timed_out else ""
        set_status_message(f"{prefix}Nouveau tour pour {next_player.name}")
    elif next_player is not None:
        prefix = "Temps ecoule. " if timed_out else ""
        set_status_message(f"{prefix}Tour de {next_player.name}")


def handle_build_action(building_id):
    global current_player_resources

    player = get_active_player()
    if not player or not carte or not carte.selected_hex:
        set_status_message("Selectionnez une case avant de construire.")
        return

    hex_obj = carte.selected_hex
    if hex_obj.type_terrain == "eau":
        set_status_message("Impossible de construire sur l'eau.")
        return

    territory_owner = get_territory_owner_at_hex(hex_obj)
    if territory_owner is not player:
        if territory_owner is None:
            set_status_message("Cette case est hors de votre territoire.")
        else:
            set_status_message(f"Cette zone appartient a {territory_owner.name}.")
        return

    owner_player, placed_building = get_building_entry_at_hex(hex_obj)

    if owner_player and owner_player.name != player.name:
        set_status_message(f"Cette case appartient a {owner_player.name}.")
        return

    current_building = placed_building.building if placed_building else None
    options = turn_manager.get_available_buildings(hex_obj.type_terrain, current_building)
    if building_id not in options:
        set_status_message("Ce batiment n'est pas disponible ici.")
        return

    building_data = tours.get_building_definition(building_id)
    has_free_build_token = not placed_building and player.free_build_tokens.get(building_id, 0) > 0
    missing = tours.get_missing_resources(player.resources, building_data["cost"])
    if missing and not has_free_build_token:
        set_status_message("Il manque : " + tours.format_resource_bundle(missing))
        return

    success = False
    if placed_building:
        previous_label = tours.get_building_label(current_building)
        success = player.upgrade_building(placed_building, building_id)
        if success:
            gained_tiles = expand_player_territory(player, hex_obj, building_id)
            if gained_tiles:
                set_status_message(
                    f"{previous_label} devient {tours.get_building_label(building_id)}. Territoire +{gained_tiles}."
                )
            else:
                set_status_message(f"{previous_label} devient {tours.get_building_label(building_id)}.")
    else:
        success = player.build(building_id, hex_obj.q, hex_obj.r)
        if success:
            gained_tiles = expand_player_territory(player, hex_obj, building_id)
            if gained_tiles:
                set_status_message(f"{tours.get_building_label(building_id)} construit. Territoire +{gained_tiles}.")
            else:
                set_status_message(f"{tours.get_building_label(building_id)} construit.")

    if success:
        current_player_resources = player.resources


def draw_selected_hex_panel(surface, mouse_pos, panel_rect):
    action_rects = []
    player = get_active_player()
    selected_hex = carte.selected_hex if carte else None

    available_actions = []
    info_line_count = 0
    owner_player = None
    placed_building = None
    current_building = None
    territory_owner = None
    if turn_manager and selected_hex:
        territory_owner = get_territory_owner_at_hex(selected_hex)
        owner_player, placed_building = get_building_entry_at_hex(selected_hex)
        current_building = placed_building.building if placed_building else None
        if territory_owner is player:
            available_actions = turn_manager.get_available_buildings(selected_hex.type_terrain, current_building)
        info_line_count = 5 if current_building else 4

    base_height = 92 if not selected_hex else 86 + info_line_count * 28
    panel_h = min(panel_rect.height, base_height + len(available_actions) * 44)
    panel_rect = pygame.Rect(panel_rect.x, panel_rect.y, panel_rect.width, panel_h)

    draw_panel_background(surface, panel_rect)

    title = FONT_SMALL.render("Case selectionnee", True, (245, 220, 120))
    title_rect = title.get_rect(x=panel_rect.x + 16, y=panel_rect.y + 14)
    surface.blit(title, title_rect)

    if not selected_hex:
        helper = FONT_TINY.render("Cliquez sur une case pour voir ses options.", True, BLANC)
        helper_rect = helper.get_rect(x=panel_rect.x + 16, y=title_rect.bottom + 18)
        surface.blit(helper, helper_rect)
        return action_rects

    terrain_labels = {
        "herbe": "Plaine",
        "foret": "Foret",
        "montagne": "Montagne",
        "eau": "Eau",
    }

    owner_name = owner_player.name if owner_player else "Aucun"
    zone_label = "Votre territoire" if territory_owner is player else "Neutre"
    if territory_owner and territory_owner is not player:
        zone_label = f"Zone de {territory_owner.name}"
    building_label = tours.get_building_label(current_building)
    info_lines = [
        f"Terrain : {terrain_labels.get(selected_hex.type_terrain, selected_hex.type_terrain)}",
        f"Zone : {zone_label}",
        f"Batiment : {building_label}",
        f"Occupant : {owner_name}",
    ]

    if current_building:
        info_lines.append("Bonus : " + tours.get_building_income_text(current_building))

    line_y = title_rect.bottom + 14
    for line in info_lines:
        line_surf = FONT_TINY.render(line, True, BLANC)
        surface.blit(line_surf, (panel_rect.x + 16, line_y))
        line_y += line_surf.get_height() + 6

    if selected_hex.type_terrain == "eau":
        water_note = FONT_TINY.render("Aucune construction possible sur l'eau.", True, (220, 220, 220))
        surface.blit(water_note, (panel_rect.x + 16, line_y + 8))
        return action_rects

    if territory_owner is None:
        blocked = FONT_TINY.render("Construisez d'abord dans votre territoire.", True, (220, 220, 220))
        surface.blit(blocked, (panel_rect.x + 16, line_y + 8))
        return action_rects

    if territory_owner and player and territory_owner.name != player.name:
        blocked = FONT_TINY.render("Zone deja controlee par un autre joueur.", True, (220, 220, 220))
        surface.blit(blocked, (panel_rect.x + 16, line_y + 8))
        return action_rects

    if not available_actions:
        no_action = FONT_TINY.render("Pas d'amelioration disponible ici.", True, (220, 220, 220))
        surface.blit(no_action, (panel_rect.x + 16, line_y + 8))
        return action_rects

    for action_index, building_id in enumerate(available_actions):
        button_rect = pygame.Rect(panel_rect.x + 16, line_y + 8 + action_index * 44, panel_rect.width - 32, 36)
        cost_text = tours.format_resource_bundle_short(tours.get_building_definition(building_id)["cost"])
        draw_action_button(
            surface,
            button_rect,
            tours.get_building_label(building_id),
            mouse_pos,
            enabled=True,
            font=FONT_TINY,
            right_text=cost_text,
            right_font=FONT_TILE,
        )
        action_rects.append((button_rect, building_id))

    return action_rects


def draw_end_turn_button(surface, mouse_pos, sidebar_rect):
    btn_w = min(240, max(180, int(surface.get_width() * 0.18)))
    btn_h = END_TURN_BUTTON_HEIGHT
    rect = pygame.Rect(0, 0, btn_w, btn_h)
    rect.midbottom = (sidebar_rect.centerx, sidebar_rect.bottom - END_TURN_BOTTOM_MARGIN)
    draw_action_button(surface, rect, "Fin du tour", mouse_pos, enabled=True, base_color=(0, 156, 88))
    return rect


def draw_status_banner(surface, anchor):
    if status_message and pygame.time.get_ticks() < status_message_until:
        draw_info_panel(
            surface,
            status_message,
            anchor,
            align="midbottom",
            font=FONT_SMALL,
        )


def reset_turn_timer():
    global turn_timer_started_at
    turn_timer_started_at = pygame.time.get_ticks()


def get_turn_time_remaining():
    if turn_timer_started_at is None:
        return TURN_DURATION_MS
    elapsed = pygame.time.get_ticks() - turn_timer_started_at
    return max(0, TURN_DURATION_MS - elapsed)


running = True
clock = pygame.time.Clock()
FONT_TIMER = pygame.font.SysFont("consolas", 34, bold=True)
music_menu(menu_music)

while running:
    clock.tick(120)

    win_w, win_h = fenetre.get_size()
    game_layout = get_game_layout(fenetre)
    clamp_map_camera(game_layout)
    for btn in boutons_menu:
        btn.rect.center = (win_w // 2, btn.center_y)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game_state = "menu"
                build_action_rects = []
                end_turn_rect = None
            elif event.key == pygame.K_t and game_state in ("game", "multi_game"):
                add_debug_resources(current_player_resources)
                set_status_message("Ressources de debug ajoutees.")
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 3
            and game_state in ("game", "multi_game")
        ):
            if game_layout["map_rect"].collidepoint(event.pos):
                map_drag_active = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if game_state == "menu":
                for btn in boutons_menu:
                    if btn.is_clicked(mouse_pos, (1, 0, 0)):
                        if btn.action == "quit":
                            running = False
                        elif btn.action == "new_game":
                            solo_player = tours.Player("Joueur 1")
                            assign_player_colors([solo_player])
                            turn_manager = tours.TurnManager([solo_player])
                            carte = Carte(60, 52)
                            assign_starting_territories(turn_manager.players)
                            game_state = "game"
                            reset_turn_timer()
                            current_player_resources = turn_manager.current_player().resources
                            set_status_message("Votre territoire de depart est pret.")
                        elif btn.action == "multiplayer":
                            selection_result = player_select.select_players(fenetre, clock)
                            if selection_result:
                                turn_manager, players = selection_result
                                assign_player_colors(players)
                                carte = Carte(60, 52)
                                assign_starting_territories(turn_manager.players)
                                game_state = "multi_game"
                                reset_turn_timer()
                                current_player_resources = turn_manager.current_player().resources
                                set_status_message("Les territoires de depart sont assignes.")
                        elif btn.action == "options":
                            fenetre, menu = show_options(fenetre, menu, clock)
            elif game_state in ("game", "multi_game"):
                handled = False
                for rect, building_id in build_action_rects:
                    if rect.collidepoint(mouse_pos):
                        handle_build_action(building_id)
                        handled = True
                        break

                if not handled and end_turn_rect and end_turn_rect.collidepoint(mouse_pos):
                    handle_end_turn()
                    handled = True

                if not handled and carte and game_layout["map_rect"].collidepoint(mouse_pos):
                    map_offset_x, map_offset_y = get_map_draw_offset(game_layout)
                    clicked_hex = carte.get_hex_at_pixel(mouse_pos[0], mouse_pos[1], offset_x=map_offset_x, offset_y=map_offset_y)
                    carte.select_hex(clicked_hex)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
            map_drag_active = False
        elif event.type == pygame.MOUSEMOTION and map_drag_active and game_state in ("game", "multi_game"):
            pan_map(event.rel[0], event.rel[1], game_layout)

    mouse_pos = pygame.mouse.get_pos()
    keys = pygame.key.get_pressed()
    if game_state in ("game", "multi_game") and carte:
        move_x = 0
        move_y = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_q]:
            move_x += MAP_PAN_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x -= MAP_PAN_SPEED
        if keys[pygame.K_UP] or keys[pygame.K_z]:
            move_y += MAP_PAN_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_y -= MAP_PAN_SPEED
        if move_x or move_y:
            pan_map(move_x, move_y, game_layout)
    if game_state == "menu":
        build_action_rects = []
        end_turn_rect = None
        win_w, win_h = fenetre.get_size()
        fenetre.blit(menu, (0, 0))
        title_surf, title_rect = update_menu_layout(fenetre)
        fenetre.blit(title_surf, title_rect)
        for btn in boutons_menu:
            btn.draw(fenetre, mouse_pos)

    elif game_state == "game":
        if turn_manager and get_turn_time_remaining() <= 0:
            handle_end_turn(timed_out=True)
        fenetre.fill(NOIR)
        draw_panel_background(fenetre, game_layout["map_rect"], fill=(8, 12, 20, 255), border=(115, 132, 162, 110), radius=18)
        draw_panel_background(fenetre, game_layout["footer_rect"], fill=(6, 12, 22, 160), border=(210, 210, 210, 90), radius=16)
        territory_lookup = get_territory_lookup()
        placed_buildings = get_placed_buildings_lookup()
        buildable_hexes = get_buildable_hexes_for_player(get_active_player())
        if carte:
            map_offset_x, map_offset_y = get_map_draw_offset(game_layout)
            previous_clip = fenetre.get_clip()
            fenetre.set_clip(game_layout["map_rect"])
            carte.dessiner(fenetre, territory_lookup, placed_buildings, offset_x=map_offset_x, offset_y=map_offset_y)
            hovered_hex = None
            if game_layout["map_rect"].collidepoint(mouse_pos):
                hovered_hex = carte.get_hex_at_pixel(mouse_pos[0], mouse_pos[1], offset_x=map_offset_x, offset_y=map_offset_y)
            for hex_obj in buildable_hexes:
                if hovered_hex and (hex_obj.q, hex_obj.r) == (hovered_hex.q, hovered_hex.r):
                    continue
                x, y = hex_obj.get_pixel_pos()
                carte.draw_buildable_overlay(fenetre, hex_obj, x + map_offset_x, y + map_offset_y - int(hex_obj.selection_lift * 10))
            if hovered_hex:
                carte.draw_hex_highlight(fenetre, hovered_hex, offset_x=map_offset_x, offset_y=map_offset_y)
            fenetre.set_clip(previous_clip)
        if turn_manager:
            solo_player = turn_manager.current_player()
            header_info_rect = draw_info_panel(
                fenetre,
                [
                    f"{solo_player.name}",
                    f"Tour {turn_manager.turn_number + 1}   |   Periode {turn_manager.period} ({tours.get_period_name(turn_manager.period)})",
                ],
                (HUD_PADDING, HUD_PADDING),
            )
        else:
            header_info_rect = None
        draw_info_panel(
            fenetre,
            "Echap : Menu   |   T : +Ressources   |   ZQSD/Fleches ou clic droit-glisser : deplacer la carte",
            (game_layout["footer_rect"].x + 14, game_layout["footer_rect"].bottom - 12),
            align="bottomleft",
            font=FONT_SMALL,
        )

        remaining = get_turn_time_remaining()
        timer_x = game_layout["map_rect"].right - 72
        if header_info_rect is not None:
            timer_x = max(timer_x, header_info_rect.right + 90)
        timer_x = min(timer_x, game_layout["map_rect"].right - 36)
        draw_timer_panel(fenetre, remaining, midtop=(timer_x, HUD_PADDING))

        build_action_rects = draw_selected_hex_panel(fenetre, mouse_pos, game_layout["selected_rect"])
        end_turn_rect = draw_end_turn_button(fenetre, mouse_pos, game_layout["sidebar_rect"])
        ressources.draw_resources_overlay(fenetre, current_player_resources, panel_rect=game_layout["resources_rect"])
        draw_status_banner(fenetre, (game_layout["map_rect"].centerx, game_layout["map_rect"].y - 10))

    elif game_state == "multi_game":
        if turn_manager and get_turn_time_remaining() <= 0:
            handle_end_turn(timed_out=True)
        fenetre.fill(NOIR)
        draw_panel_background(fenetre, game_layout["map_rect"], fill=(8, 12, 20, 255), border=(115, 132, 162, 110), radius=18)
        draw_panel_background(fenetre, game_layout["footer_rect"], fill=(6, 12, 22, 160), border=(210, 210, 210, 90), radius=16)
        territory_lookup = get_territory_lookup()
        placed_buildings = get_placed_buildings_lookup()
        buildable_hexes = get_buildable_hexes_for_player(get_active_player())
        if carte:
            map_offset_x, map_offset_y = get_map_draw_offset(game_layout)
            previous_clip = fenetre.get_clip()
            fenetre.set_clip(game_layout["map_rect"])
            carte.dessiner(fenetre, territory_lookup, placed_buildings, offset_x=map_offset_x, offset_y=map_offset_y)
            hovered_hex = None
            if game_layout["map_rect"].collidepoint(mouse_pos):
                hovered_hex = carte.get_hex_at_pixel(mouse_pos[0], mouse_pos[1], offset_x=map_offset_x, offset_y=map_offset_y)
            for hex_obj in buildable_hexes:
                if hovered_hex and (hex_obj.q, hex_obj.r) == (hovered_hex.q, hovered_hex.r):
                    continue
                x, y = hex_obj.get_pixel_pos()
                carte.draw_buildable_overlay(fenetre, hex_obj, x + map_offset_x, y + map_offset_y - int(hex_obj.selection_lift * 10))
            if hovered_hex:
                carte.draw_hex_highlight(fenetre, hovered_hex, offset_x=map_offset_x, offset_y=map_offset_y)
            fenetre.set_clip(previous_clip)
        if turn_manager:
            header_info_rect = draw_info_panel(
                fenetre,
                [
                    f"Tour de {turn_manager.current_player().name}",
                    f"Manche {turn_manager.turn_number + 1}   |   Periode {turn_manager.period} ({tours.get_period_name(turn_manager.period)})",
                ],
                (HUD_PADDING, HUD_PADDING),
            )
        else:
            header_info_rect = None
        draw_info_panel(
            fenetre,
            "Echap : Menu   |   ZQSD/Fleches ou clic droit-glisser : deplacer la carte",
            (game_layout["footer_rect"].x + 14, game_layout["footer_rect"].bottom - 12),
            align="bottomleft",
            font=FONT_SMALL,
        )
        remaining = get_turn_time_remaining()
        timer_x = game_layout["map_rect"].right - 72
        if header_info_rect is not None:
            timer_x = max(timer_x, header_info_rect.right + 90)
        timer_x = min(timer_x, game_layout["map_rect"].right - 36)
        draw_timer_panel(fenetre, remaining, midtop=(timer_x, HUD_PADDING))
        build_action_rects = draw_selected_hex_panel(fenetre, mouse_pos, game_layout["selected_rect"])
        end_turn_rect = draw_end_turn_button(fenetre, mouse_pos, game_layout["sidebar_rect"])
        ressources.draw_resources_overlay(fenetre, current_player_resources, panel_rect=game_layout["resources_rect"])
        draw_status_banner(fenetre, (game_layout["map_rect"].centerx, game_layout["map_rect"].y - 10))

    pygame.display.flip()

pygame.quit()
sys.exit()
