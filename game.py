import sys
import os
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
import combat_logic
import diplomacy_logic
import ressources
import tours
import player_select
from game_state import GameSession
from gameplay_logic import (
    assign_starting_territories as assign_player_territories,
    expand_player_territory as expand_owned_territory,
    get_buildable_hexes_for_player as list_buildable_hexes,
    get_building_entry_at_coords as find_building_entry_at_coords,
    get_building_entry_at_hex as find_building_entry_at_hex,
    get_placed_buildings_lookup as build_placed_buildings_lookup,
    get_territory_lookup as build_territory_lookup,
    get_territory_owner_at_coords as find_territory_owner_at_coords,
    get_territory_owner_at_hex as find_territory_owner_at_hex,
)
from hex_map import Carte, brighten_color
from match_ui import (
    HudFonts,
    HudTheme,
    draw_end_turn_button as render_end_turn_button,
    draw_info_panel as render_info_panel,
    draw_panel_background as render_panel_background,
    draw_selected_hex_panel as render_selected_hex_panel,
    draw_status_banner as render_status_banner,
    draw_timer_panel as render_timer_panel,
    get_game_layout as build_game_layout,
)

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

# Etat mutable de la partie regroupe en un seul endroit.
session = GameSession()

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
FONT_TIMER = pygame.font.SysFont("consolas", 34, bold=True)
HUD_FONTS = HudFonts(hud=FONT_HUD, small=FONT_SMALL, tiny=FONT_TINY, tile=FONT_TILE, timer=FONT_TIMER)
HUD_THEME = HudTheme(
    white=BLANC,
    shadow=SHADOW,
    panel_bg=PANEL_BG,
    panel_border=PANEL_BORDER,
    hover_blue=HOVER_BLUE,
)
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


def assign_player_colors(players):
    for index, player in enumerate(players):
        player.color = PLAYER_COLORS[index % len(PLAYER_COLORS)]


def get_building_entry_at_coords(q, r):
    return find_building_entry_at_coords(session.turn_manager, q, r)


def get_building_entry_at_hex(hex_obj):
    return find_building_entry_at_hex(session.turn_manager, hex_obj)


def get_territory_owner_at_coords(q, r):
    return find_territory_owner_at_coords(session.turn_manager, q, r)


def get_territory_owner_at_hex(hex_obj):
    return find_territory_owner_at_hex(session.turn_manager, hex_obj)


def get_territory_lookup():
    return build_territory_lookup(session.turn_manager)


def get_placed_buildings_lookup():
    return build_placed_buildings_lookup(session.turn_manager)


def get_buildable_hexes_for_player(player):
    return list_buildable_hexes(session.carte, session.turn_manager, player)


def get_game_layout(surface):
    return build_game_layout(
        surface,
        HUD_PADDING,
        HEADER_HEIGHT,
        FOOTER_HEIGHT,
        MAP_INSET,
        SIDEBAR_GAP,
        SELECTED_PANEL_DROP,
        END_TURN_BOTTOM_MARGIN,
        END_TURN_PANEL_GAP,
        END_TURN_BUTTON_HEIGHT,
    )


def clamp_map_camera(layout):
    if not session.carte:
        session.camera_pan_x = 0
        session.camera_pan_y = 0
        return

    bounds = session.carte.get_world_bounds()
    viewport_w = max(1, layout["map_rect"].width - MAP_INSET * 2)
    viewport_h = max(1, layout["map_rect"].height - MAP_INSET * 2)

    if bounds.width <= viewport_w:
        session.camera_pan_x = int((viewport_w - bounds.width) / 2 - bounds.left)
    else:
        min_pan_x = viewport_w - bounds.right
        max_pan_x = -bounds.left
        session.camera_pan_x = max(min_pan_x, min(max_pan_x, session.camera_pan_x))

    if bounds.height <= viewport_h:
        session.camera_pan_y = int((viewport_h - bounds.height) / 2 - bounds.top)
    else:
        min_pan_y = viewport_h - bounds.bottom
        max_pan_y = -bounds.top
        session.camera_pan_y = max(min_pan_y, min(max_pan_y, session.camera_pan_y))


def center_map_camera(layout):
    if not session.carte:
        session.camera_pan_x = 0
        session.camera_pan_y = 0
        return

    bounds = session.carte.get_world_bounds()
    viewport_w = max(1, layout["map_rect"].width - MAP_INSET * 2)
    viewport_h = max(1, layout["map_rect"].height - MAP_INSET * 2)
    session.camera_pan_x = int((viewport_w - bounds.width) / 2 - bounds.left)
    session.camera_pan_y = int((viewport_h - bounds.height) / 2 - bounds.top)
    clamp_map_camera(layout)


def get_map_draw_offset(layout):
    base_x, base_y = layout["map_base_offset"]
    return base_x + session.camera_pan_x, base_y + session.camera_pan_y


def pan_map(dx, dy, layout):
    session.camera_pan_x += dx
    session.camera_pan_y += dy
    clamp_map_camera(layout)


def assign_starting_territories(players):
    starting_hexes = assign_player_territories(
        session.carte,
        players,
        STARTING_TERRITORY_RADIUS,
        STARTING_POSITION_SEPARATION,
    )
    if starting_hexes:
        center_map_camera(get_game_layout(fenetre))
    return starting_hexes


def expand_player_territory(player, source_hex, building_id):
    return expand_owned_territory(
        session.carte,
        session.turn_manager,
        player,
        source_hex,
        building_id,
        tours.get_building_territory_radius,
    )


def set_status_message(text, duration_ms=2600):
    session.set_status_message(text, pygame.time.get_ticks(), duration_ms)


def set_winner(player):
    if player is None:
        return
    session.winner_name = player.name
    set_status_message(f"{player.name} remporte la partie !", duration_ms=6000)


def evaluate_victory_state():
    if not session.turn_manager:
        return None
    winner = session.turn_manager.get_winner()
    if winner is not None and session.winner_name is None:
        set_winner(winner)
    return winner


def place_starting_capitals(players, starting_hexes):
    for player in players:
        player.defeated = False
        player.reset_turn_state()
        player.buildings = [
            placed_building
            for placed_building in player.buildings
            if not tours.get_building_definition(placed_building.building).get("is_capital")
        ]
    for player, start_hex in zip(players, starting_hexes):
        if start_hex is None:
            continue
        player.build("capital", start_hex.q, start_hex.r)
        expand_player_territory(player, start_hex, "capital")


def conquer_defeated_player(attacker, defender, destroyed_capital=None):
    capital_coords = None
    if destroyed_capital is not None:
        capital_coords = (destroyed_capital.q, destroyed_capital.r)
    for placed_building in list(defender.buildings):
        defender.remove_building(placed_building)
        if tours.get_building_definition(placed_building.building).get("is_capital"):
            continue
        if capital_coords == (placed_building.q, placed_building.r):
            continue
        placed_building.trapped = False
        if attacker.find_building_at(placed_building.q, placed_building.r) is None:
            attacker.buildings.append(placed_building)
    for q, r in list(defender.owned_tiles):
        attacker.claim_tile(q, r)
    defender.owned_tiles.clear()
    session.turn_manager.eliminate_player(defender)


def handle_relation_action(target_name, relation):
    player = get_active_player()
    if not player or not session.turn_manager:
        return
    target_player = session.turn_manager.get_player_by_name(target_name)
    if target_player is None or target_player is player or target_player.defeated:
        set_status_message("Cette relation n'est plus disponible.")
        return
    current_relation = session.turn_manager.get_relation(player, target_player)
    if current_relation == relation:
        if relation == diplomacy_logic.RELATION_ALLIED:
            set_status_message(f"Alliance deja active avec {target_player.name}.")
        elif relation == diplomacy_logic.RELATION_WAR:
            set_status_message(f"Vous etes deja en guerre avec {target_player.name}.")
        else:
            set_status_message(f"Relation deja definie avec {target_player.name}.")
        return
    session.turn_manager.set_relation(player, target_player, relation)
    if relation == diplomacy_logic.RELATION_ALLIED:
        set_status_message(f"Alliance conclue avec {target_player.name} : bonus d'economie et de commerce.")
    elif relation == diplomacy_logic.RELATION_WAR:
        set_status_message(f"Guerre declaree contre {target_player.name} : sa capitale devient votre cible.")
    else:
        set_status_message(f"Relation avec {target_player.name} mise a jour.")
    evaluate_victory_state()


def handle_trade_action(target_name):
    player = get_active_player()
    if not player or not session.turn_manager:
        return
    target_player = session.turn_manager.get_player_by_name(target_name)
    if target_player is None or target_player is player or target_player.defeated:
        set_status_message("Commerce indisponible.")
        return
    relation = session.turn_manager.get_relation(player, target_player)
    success, message = diplomacy_logic.execute_trade(player, target_player, relation)
    if success:
        session.current_player_resources = player.resources
    set_status_message(message)
    evaluate_victory_state()


def handle_attack_action():
    player = get_active_player()
    if not player or not session.turn_manager or not session.carte or not session.carte.selected_hex:
        set_status_message("Selectionnez une zone ennemie a attaquer.")
        return

    target_hex = session.carte.selected_hex
    defender = get_territory_owner_at_hex(target_hex)
    if defender is None or defender is player:
        set_status_message("Aucune cible ennemie sur cette case.")
        return

    owner_player, placed_building = get_building_entry_at_hex(target_hex)
    preview = combat_logic.get_attack_preview(
        session.carte,
        session.turn_manager,
        player,
        defender,
        target_hex,
        placed_building,
    )
    if not preview["available"]:
        set_status_message(preview["reason"])
        return

    player.pay_cost(combat_logic.ATTACK_COST)
    player.attack_used = True
    result = combat_logic.resolve_attack(player, defender, placed_building)

    if result["success"]:
        defender.release_tile(target_hex.q, target_hex.r)
        player.claim_tile(target_hex.q, target_hex.r)
        if owner_player is defender and placed_building is not None:
            defender.remove_building(placed_building)
            if tours.get_building_definition(placed_building.building).get("is_capital"):
                player.capitals_captured += 1
                conquer_defeated_player(player, defender, destroyed_capital=placed_building)
                set_status_message(
                    f"{player.name} prend la capitale de {defender.name} ! ({result['attack_roll']} vs {result['defense_roll']})",
                    duration_ms=4200,
                )
                evaluate_victory_state()
                session.current_player_resources = player.resources
                return
            placed_building.trapped = False
            if player.find_building_at(placed_building.q, placed_building.r) is None:
                player.buildings.append(placed_building)
        set_status_message(f"Attaque reussie ! ({result['attack_roll']} vs {result['defense_roll']})")
    else:
        set_status_message(f"Attaque repoussee. ({result['attack_roll']} vs {result['defense_roll']})")

    session.current_player_resources = player.resources
    evaluate_victory_state()


def get_selected_panel_extras():
    player = get_active_player()
    selected_hex = session.carte.selected_hex if session.carte else None
    if not player or not session.turn_manager or selected_hex is None:
        return [], []

    territory_owner = get_territory_owner_at_hex(selected_hex)
    if territory_owner is None or territory_owner is player or territory_owner.defeated:
        return [], []

    owner_player, placed_building = get_building_entry_at_hex(selected_hex)
    relation = session.turn_manager.get_relation(player, territory_owner)
    extra_lines = [f"Relation : {diplomacy_logic.relation_label(relation)}"]
    extra_actions = []

    if owner_player is territory_owner and placed_building is not None:
        if tours.get_building_definition(placed_building.building).get("is_capital"):
            extra_lines.append("Objectif : capitale ennemie")

    attack_preview = combat_logic.get_attack_preview(
        session.carte,
        session.turn_manager,
        player,
        territory_owner,
        selected_hex,
        placed_building,
    )
    if relation == diplomacy_logic.RELATION_WAR:
        extra_lines.append("But : prendre sa capitale ou ses zones.")
        if attack_preview["available"]:
            extra_lines.append(combat_logic.format_preview(attack_preview))
            extra_actions.append(
                {
                    "label": "Attaquer",
                    "payload": ("attack", None),
                    "right_text": tours.format_resource_bundle_short(combat_logic.ATTACK_COST),
                    "base_color": (176, 82, 54),
                }
            )
        elif attack_preview["reason"]:
            extra_lines.append(attack_preview["reason"])
    else:
        extra_lines.append("Guerre : debloque l'attaque et la conquete.")
        extra_actions.append(
            {
                "label": "Declarer guerre",
                "payload": ("declare_war", territory_owner.name),
                "base_color": (165, 62, 62),
            }
        )

    if relation == diplomacy_logic.RELATION_NEUTRAL:
        extra_lines.append("Alliance : bonus d'argent a chaque manche et meilleur commerce.")
        extra_actions.append(
            {
                "label": "Former alliance",
                "payload": ("alliance", territory_owner.name),
                "base_color": (78, 128, 201),
            }
        )
    elif relation == diplomacy_logic.RELATION_ALLIED:
        extra_lines.append("Alliance active : bonus d'argent et echanges facilites.")

    trade_preview = diplomacy_logic.get_trade_preview(player, territory_owner, relation)
    if trade_preview["available"]:
        extra_actions.append(
            {
                "label": trade_preview["label"],
                "payload": ("trade", territory_owner.name),
                "right_text": trade_preview["short"],
                "base_color": (104, 152, 84),
            }
        )
    elif trade_preview["reason"] and relation != diplomacy_logic.RELATION_WAR:
        extra_lines.append("Commerce : " + trade_preview["reason"])

    return extra_lines, extra_actions


def get_objective_lines():
    if not session.turn_manager:
        return []
    snapshot = session.turn_manager.get_objective_snapshot(get_active_player())
    lines = ["Objectif : detruire les capitales adverses"]
    if get_active_player() is not None:
        lines.append(
            f"Capitales prises {snapshot['player_capitals']} | Territoire {snapshot['player_territory']} cases | Batiments {snapshot['player_buildings']}"
        )
    if snapshot["leader_name"]:
        lines.append(
            f"Leader : {snapshot['leader_name']} ({snapshot['leader_capitals']} capitales, {snapshot['leader_territory']} cases) | Empires restants {snapshot['remaining_empires']}"
        )
    return lines


def handle_panel_action(payload):
    action_type, value = payload
    if action_type == "build":
        handle_build_action(value)
    elif action_type == "attack":
        handle_attack_action()
    elif action_type == "declare_war":
        handle_relation_action(value, diplomacy_logic.RELATION_WAR)
    elif action_type == "alliance":
        handle_relation_action(value, diplomacy_logic.RELATION_ALLIED)
    elif action_type == "trade":
        handle_trade_action(value)


def draw_panel_background(surface, rect, fill=PANEL_BG, border=PANEL_BORDER, radius=16):
    return render_panel_background(surface, rect, HUD_THEME, fill=fill, border=border, radius=radius)


def draw_info_panel(surface, texts, anchor, align="topleft", font=FONT_HUD):
    return render_info_panel(surface, texts, anchor, HUD_THEME, HUD_FONTS, align=align, font=font)


def draw_timer_panel(surface, remaining_ms, midtop=None):
    return render_timer_panel(surface, remaining_ms, HUD_THEME, HUD_FONTS, HUD_PADDING, midtop=midtop)


def get_active_player():
    return session.get_active_player()


def add_debug_resources(resource_store):
    GameSession.add_debug_resources(resource_store)


def handle_end_turn(timed_out=False):
    if session.winner_name:
        return
    player = get_active_player()
    if not session.turn_manager or player is None:
        return

    old_turn_number = session.turn_manager.turn_number
    old_period = session.turn_manager.period
    session.turn_manager.player_finished(player)
    if evaluate_victory_state() is not None:
        return
    next_player = get_active_player()

    if next_player is not None:
        session.current_player_resources = next_player.resources
        reset_turn_timer()

    if session.turn_manager.period != old_period:
        prefix = "Temps ecoule. " if timed_out else ""
        set_status_message(f"{prefix}Periode {session.turn_manager.period} - {tours.get_period_name(session.turn_manager.period)}")
    elif session.turn_manager.turn_number != old_turn_number:
        prefix = "Temps ecoule. " if timed_out else ""
        set_status_message(f"{prefix}Nouveau tour pour {next_player.name}")
    elif next_player is not None:
        prefix = "Temps ecoule. " if timed_out else ""
        set_status_message(f"{prefix}Tour de {next_player.name}")


def handle_build_action(building_id):
    player = get_active_player()
    if not player or not session.carte or not session.carte.selected_hex:
        set_status_message("Selectionnez une case avant de construire.")
        return

    hex_obj = session.carte.selected_hex
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
    options = session.turn_manager.get_available_buildings(hex_obj.type_terrain, current_building)
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
        session.current_player_resources = player.resources


def draw_selected_hex_panel(surface, mouse_pos, panel_rect):
    extra_lines, extra_actions = get_selected_panel_extras()
    return render_selected_hex_panel(
        surface,
        mouse_pos,
        panel_rect,
        session.carte.selected_hex if session.carte else None,
        get_active_player(),
        session.turn_manager,
        get_territory_owner_at_hex,
        get_building_entry_at_hex,
        HUD_THEME,
        HUD_FONTS,
        extra_lines=extra_lines,
        extra_actions=extra_actions,
    )


def draw_end_turn_button(surface, mouse_pos, sidebar_rect):
    return render_end_turn_button(
        surface,
        mouse_pos,
        sidebar_rect,
        HUD_THEME,
        HUD_FONTS,
        END_TURN_BUTTON_HEIGHT,
        END_TURN_BOTTOM_MARGIN,
    )


def draw_status_banner(surface, anchor):
    render_status_banner(
        surface,
        anchor,
        session.status_message,
        session.status_message_until,
        pygame.time.get_ticks(),
        HUD_THEME,
        HUD_FONTS,
    )


def reset_turn_timer():
    session.reset_turn_timer(pygame.time.get_ticks())


def get_turn_time_remaining():
    return session.get_turn_time_remaining(pygame.time.get_ticks(), TURN_DURATION_MS)


def begin_match(game_state_name, turn_manager, players):
    new_map = Carte(60, 52, tuiles, terrain_variantes, FONT_TILE)
    session.carte = new_map
    session.turn_manager = turn_manager
    starting_hexes = assign_starting_territories(players)
    place_starting_capitals(players, starting_hexes)
    active_resources = turn_manager.current_player().resources if turn_manager else None
    session.start_match(
        game_state_name,
        new_map,
        turn_manager,
        active_resources,
        pygame.time.get_ticks(),
    )


def render_match_scene(mode, mouse_pos, game_layout):
    if session.turn_manager and session.winner_name is None and get_turn_time_remaining() <= 0:
        handle_end_turn(timed_out=True)

    fenetre.fill(NOIR)
    draw_panel_background(fenetre, game_layout["map_rect"], fill=(8, 12, 20, 255), border=(115, 132, 162, 110), radius=18)
    draw_panel_background(fenetre, game_layout["footer_rect"], fill=(6, 12, 22, 160), border=(210, 210, 210, 90), radius=16)

    active_player = get_active_player()
    active_color = active_player.color if active_player and active_player.color is not None else JAUNE
    hover_color = brighten_color(active_color, 18)
    territory_lookup = get_territory_lookup()
    placed_buildings = get_placed_buildings_lookup()
    buildable_hexes = get_buildable_hexes_for_player(active_player)

    if session.carte:
        map_offset_x, map_offset_y = get_map_draw_offset(game_layout)
        previous_clip = fenetre.get_clip()
        fenetre.set_clip(game_layout["map_rect"])
        session.carte.dessiner(
            fenetre,
            territory_lookup,
            placed_buildings,
            offset_x=map_offset_x,
            offset_y=map_offset_y,
            active_player=active_player,
        )
        hovered_hex = None
        if game_layout["map_rect"].collidepoint(mouse_pos):
            hovered_hex = session.carte.get_hex_at_pixel(mouse_pos[0], mouse_pos[1], offset_x=map_offset_x, offset_y=map_offset_y)
        for hex_obj in buildable_hexes:
            if hovered_hex and (hex_obj.q, hex_obj.r) == (hovered_hex.q, hovered_hex.r):
                continue
            x, y = hex_obj.get_pixel_pos()
            session.carte.draw_buildable_overlay(
                fenetre,
                hex_obj,
                x + map_offset_x,
                y + map_offset_y - int(hex_obj.selection_lift * 10),
                color=active_color,
            )
        if hovered_hex:
            session.carte.draw_hex_highlight(
                fenetre,
                hovered_hex,
                offset_x=map_offset_x,
                offset_y=map_offset_y,
                color=hover_color,
            )
        fenetre.set_clip(previous_clip)

    if mode == "game" and session.turn_manager:
        header_lines = [
            f"{session.turn_manager.current_player().name}",
            f"Tour {session.turn_manager.turn_number + 1}   |   Periode {session.turn_manager.period} ({tours.get_period_name(session.turn_manager.period)})",
        ] + get_objective_lines()
        footer_text = "Echap : Menu   |   T : +Ressources   |   ZQSD/Fleches ou clic droit-glisser : deplacer la carte   |   But : capitales, alliances, commerce et conquete"
    elif session.turn_manager:
        header_lines = [
            f"Tour de {session.turn_manager.current_player().name}",
            f"Manche {session.turn_manager.turn_number + 1}   |   Periode {session.turn_manager.period} ({tours.get_period_name(session.turn_manager.period)})",
        ] + get_objective_lines()
        footer_text = "Echap : Menu   |   ZQSD/Fleches ou clic droit-glisser : deplacer la carte   |   But : capitales, alliances, commerce et conquete"
    else:
        header_lines = []
        footer_text = "Echap : Menu"

    header_info_rect = None
    if header_lines:
        header_info_rect = draw_info_panel(
            fenetre,
            header_lines,
            (HUD_PADDING, HUD_PADDING),
            font=FONT_SMALL,
        )

    draw_info_panel(
        fenetre,
        footer_text,
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

    session.panel_action_rects = draw_selected_hex_panel(fenetre, mouse_pos, game_layout["selected_rect"])
    session.end_turn_rect = draw_end_turn_button(fenetre, mouse_pos, game_layout["sidebar_rect"])
    ressources.draw_resources_overlay(fenetre, session.current_player_resources, panel_rect=game_layout["resources_rect"])
    draw_status_banner(fenetre, (game_layout["map_rect"].centerx, game_layout["map_rect"].y - 10))

    if session.winner_name:
        draw_info_panel(
            fenetre,
            [f"Victoire de {session.winner_name}", "Echap pour revenir au menu"],
            (game_layout["map_rect"].centerx, game_layout["map_rect"].centery),
            align="center",
            font=FONT_HUD,
        )


running = True
clock = pygame.time.Clock()
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
                session.game_state = "menu"
                session.clear_match_ui()
            elif event.key == pygame.K_t and session.game_state in ("game", "multi_game"):
                add_debug_resources(session.current_player_resources)
                set_status_message("Ressources de debug ajoutees.")
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 3
            and session.game_state in ("game", "multi_game")
        ):
            if game_layout["map_rect"].collidepoint(event.pos):
                session.map_drag_active = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if session.game_state == "menu":
                for btn in boutons_menu:
                    if btn.is_clicked(mouse_pos, (1, 0, 0)):
                        if btn.action == "quit":
                            running = False
                        elif btn.action == "new_game":
                            solo_player = tours.Player("Joueur 1")
                            assign_player_colors([solo_player])
                            solo_turn_manager = tours.TurnManager([solo_player])
                            begin_match("game", solo_turn_manager, solo_turn_manager.players)
                            set_status_message("Votre territoire de depart est pret.")
                        elif btn.action == "multiplayer":
                            selection_result = player_select.select_players(fenetre, clock)
                            if selection_result:
                                multi_turn_manager, players = selection_result
                                assign_player_colors(players)
                                begin_match("multi_game", multi_turn_manager, players)
                                set_status_message("Les territoires de depart sont assignes.")
                        elif btn.action == "options":
                            fenetre, menu = show_options(fenetre, menu, clock)
            elif session.game_state in ("game", "multi_game"):
                if session.winner_name:
                    continue
                handled = False
                for rect, payload in session.panel_action_rects:
                    if rect.collidepoint(mouse_pos):
                        handle_panel_action(payload)
                        handled = True
                        break

                if not handled and session.end_turn_rect and session.end_turn_rect.collidepoint(mouse_pos):
                    handle_end_turn()
                    handled = True

                if not handled and session.carte and game_layout["map_rect"].collidepoint(mouse_pos):
                    map_offset_x, map_offset_y = get_map_draw_offset(game_layout)
                    clicked_hex = session.carte.get_hex_at_pixel(mouse_pos[0], mouse_pos[1], offset_x=map_offset_x, offset_y=map_offset_y)
                    session.carte.select_hex(clicked_hex)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
            session.map_drag_active = False
        elif event.type == pygame.MOUSEMOTION and session.map_drag_active and session.game_state in ("game", "multi_game"):
            pan_map(event.rel[0], event.rel[1], game_layout)

    mouse_pos = pygame.mouse.get_pos()
    keys = pygame.key.get_pressed()
    if session.game_state in ("game", "multi_game") and session.carte:
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
    if session.game_state == "menu":
        session.clear_match_ui()
        win_w, win_h = fenetre.get_size()
        fenetre.blit(menu, (0, 0))
        title_surf, title_rect = update_menu_layout(fenetre)
        fenetre.blit(title_surf, title_rect)
        for btn in boutons_menu:
            btn.draw(fenetre, mouse_pos)

    elif session.game_state == "game":
        render_match_scene("game", mouse_pos, game_layout)

    elif session.game_state == "multi_game":
        render_match_scene("multi_game", mouse_pos, game_layout)

    pygame.display.flip()

pygame.quit()
sys.exit()
