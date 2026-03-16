import sys
import subprocess
import os
import warnings
from io import StringIO

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# Rediriger stdout et stderr pour supprimer les messages de pygame
old_stdout = sys.stdout
old_stderr = sys.stderr
sys.stdout = StringIO()
sys.stderr = StringIO()

import pygame #importation de pygame
from pygame.locals import *
import ressources
import tours
import player_select

sys.stdout = old_stdout
sys.stderr = old_stderr

# Fichier principal: Gère menu, carte hex, ressources, et intégration multiplayer/tours
# État jeu: "menu" / "game" / "multi_game"


pygame.init() #démarrage de pygame
try:
    pygame.mixer.init()
except pygame.error:
    pass

#création d'une fenêtre
display_info = pygame.display.Info()
start_w = min(1920, max(1024, display_info.current_w))
start_h = min(1080, max(720, display_info.current_h))
fenetre = pygame.display.set_mode((start_w, start_h), pygame.RESIZABLE)

# Variables globales jeu
# game_state contrôle affichage/logique (menu / game / multi_game)
game_state = "menu"
carte = None  # Instance Carte hex
turn_manager = None
current_player_resources = None  # dict or PlayerResources

#chargement des images
liste_actuelle=[]

#images de fond (menus et maps)
menu = pygame.image.load("background.png").convert_alpha()
menu = pygame.transform.scale(menu,(1920,1080))

#tuiles de terrain

try:
    Eau_1 = pygame.transform.scale(pygame.image.load("Eau_1.png"),(32,42))
    Eau_2 = pygame.transform.scale(pygame.image.load("Eau_2.png"),(32,42))
    Eau_3 = pygame.transform.scale(pygame.image.load("Eau_3.png"),(32,42))
    Herbe_1 = pygame.transform.scale(pygame.image.load("Herbe_1.png"),(32,42))
    Herbe_2 = pygame.transform.scale(pygame.image.load("Herbe_2.png"),(32,42))
    Herbe_3 = pygame.transform.scale(pygame.image.load("Herbe_3.png"),(32,42))
    Pierre_1 = pygame.transform.scale(pygame.image.load("Pierre_1.png"),(32,42))
    IMAGES_LOADED = True
except Exception as e:
    # Créer des surfaces de couleur de remplacement
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
    'eau': Eau_1,
    'herbe': Herbe_1,
    'foret': Herbe_2,
    'montagne': Pierre_1,
}


#musique
menu_music = "menu-musique.mp3"

#couleurs
BLANC = (255, 255, 255)
NOIR = (0, 0, 0)
VERT = (0, 255, 0)
ROUGE = (255, 0, 0)
BLEU = (0, 0, 255)
JAUNE = (255, 255, 0)
TRANSLUCENT_BLUE = (0, 80, 255, 100)
HOVER_BLUE = (0, 140, 255, 220)
SHADOW = (0, 0, 0)

#polices
FONT_TITLE = pygame.font.SysFont(None, 72)
FONT_BUTTON = pygame.font.SysFont(None, 36)

# --- Fonctions utilitaires pour les images UI ---

def load_trimmed_image(path, min_alpha=25):
    """Charge une image et retourne uniquement la partie visible (alpha > min_alpha)."""
    if not os.path.exists(path):
        return None
    image = pygame.image.load(path).convert_alpha()
    bounds = image.get_bounding_rect(min_alpha=min_alpha)
    if bounds.width > 0 and bounds.height > 0:
        return image.subsurface(bounds).copy()
    return image

def load_menu_button_images(path):
    """Détecte les régions de boutons dans le spritesheet et retourne un dict par action."""
    if not os.path.exists(path):
        return {}
    sheet = pygame.image.load(path).convert_alpha()
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
        key=lambda r: (r.y, r.x)
    )
    # Le spritesheet courant a les deux dernières lignes inversées (Quit puis Options)
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
    """Charge les images des boutons d'options depuis le spritesheet (indices 4-7)."""
    if not os.path.exists(path):
        return {}
    sheet = pygame.image.load(path).convert_alpha()
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
        key=lambda r: (r.y, r.x)
    )
    # rects[4]=1920x1080, rects[5]=1280x720, rects[6]=2560x1440, rects[7]=Back
    key_map = {4: "1920x1080", 5: "1280x720", 6: "2560x1440", 7: "back"}
    images = {}
    for idx, key in key_map.items():
        if idx < len(rects):
            images[key] = sheet.subsurface(rects[idx]).copy()
    # Charge 1600x900 depuis son propre fichier
    path_1600 = "1600 x 900.png"
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
                key=lambda r: r.y
            )
            if rects_1600:
                images["1600x900"] = img_1600.subsurface(rects_1600[0]).copy()
    return images

def scale_surface_to_fit(surface, max_width, max_height):
    """Redimensionne une surface pour tenir dans max_width × max_height (haut et bas)."""
    w, h = surface.get_size()
    scale = min(max_width / w, max_height / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return pygame.transform.smoothscale(surface, (new_w, new_h))

def get_button_display_image(action, is_hover, win_size):
    """Retourne l'image du bouton mise à l'échelle pour la taille de la fenêtre."""
    if not button_images or action not in button_images:
        return None
    win_w, win_h = win_size
    max_width = min(420, win_w * 0.24)
    max_height = min(100, win_h * 0.1)
    key = "hover" if is_hover else "normal"
    img = button_images[action].get(key, button_images[action]["normal"])
    return scale_surface_to_fit(img, max_width, max_height)

def get_option_button_background(key, max_width, max_height):
    """Retourne l'image de fond du bouton d'option (style bouton menu)."""
    if option_button_images and key in option_button_images:
        bg = option_button_images[key]
        return pygame.transform.smoothscale(bg, (int(max_width), int(max_height)))
    if button_images and "new_game" in button_images:
        # fallback visuel si une image option manque
        bg = button_images["new_game"]["normal"]
        return pygame.transform.smoothscale(bg, (int(max_width), int(max_height)))
    return None

def draw_option_image_button(surface, rect, image, label=None):
    """Dessine un bouton image dans le rect avec un label optionnel par dessus."""
    if image:
        img_rect = image.get_rect(center=rect.center)
        surface.blit(image, img_rect)
    if label:
        text_surf = FONT_BUTTON.render(label, True, BLANC)
        text_rect = text_surf.get_rect(center=rect.center)
        shadow_surf = FONT_BUTTON.render(label, True, SHADOW)
        surface.blit(shadow_surf, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text_surf, text_rect)

def update_menu_layout(win):
    """Met à jour le layout adaptatif du menu. Retourne (title_surf, title_rect)."""
    win_w, win_h = win.get_size()
    # Titre bannière
    title_w = min(1305, win_w * 0.72)
    title_h = min(252, win_h * 0.234)
    title_y = max(8, win_h * 0.01)
    if title_banner is not None:
        title_surf = scale_surface_to_fit(title_banner, title_w, title_h)
    else:
        title_surf = FONT_TITLE.render("Timeless Empire", True, BLANC)
    title_rect = title_surf.get_rect(centerx=win_w // 2, top=int(title_y))
    # Boutons menu
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

# Chargement des images UI
title_banner = load_trimmed_image("Banière_titre.png", min_alpha=25)
button_images = load_menu_button_images("Boutons_menu.png")
option_button_images = load_option_button_images("Boutons_menu.png")

# création d'une classe Hexagone pour créer la map

# Hexagone : Tuile carte hex (layout "odd-r")
class Hexagone:
    def __init__(self, q, r, type_terrain):
        self.q = q                           # Coord q (cube coords)
        self.r = r                           # Coord r
        self.type_terrain = type_terrain     # Type ('herbe', 'eau'...)
        self.tuile = tuiles[type_terrain]   # Image associée
    
    def get_pixel_pos(self, size=32, vertical_spacing=42):
        """Retourne la position en pixels de l'hexagone."""
        # Layout hexagonal "odd-r" - lignes impaires décalées
        # Espacement horizontal: 100% de la largeur
        x = self.q * size * 1.0
        # Décalage pour lignes impaires
        if self.r % 2 == 1:
            x += size * 0.5
        # Espacement vertical: 1/2 de la hauteur
        y = self.r * vertical_spacing * 0.5
        return int(x), int(y)


class Carte:
    def __init__(self, largeur, hauteur):
        """Crée une carte hexagonale avec des tuiles aléatoires."""
        self.largeur = largeur
        self.hauteur = hauteur
        self.hexagones = []
        self._mask_cache = {}
        self.generer_carte()
    
    def generer_carte(self):
        """Génère la carte avec des hexagones aléatoires."""
        import random
        types_terrain = ['eau', 'herbe', 'foret', 'montagne']
        
        for r in range(self.hauteur):
            for q in range(self.largeur):
                type_terrain = random.choice(types_terrain)
                hex_obj = Hexagone(q, r, type_terrain)
                self.hexagones.append(hex_obj)
    
    def dessiner(self, surface, offset_x=0, offset_y=0):
        """Dessine tous les hexagones sur la surface en ordre de profondeur correct."""
        # Trier les hexagones: d'abord par y (position verticale), puis par x (position horizontale)
        # Cela affiche de bas en haut, et pour une même hauteur, de gauche à droite
        hexagones_tries = sorted(self.hexagones, key=lambda h: (h.get_pixel_pos()[1], h.get_pixel_pos()[0]))
        
        for hex_obj in hexagones_tries:
            x, y = hex_obj.get_pixel_pos()
            x += offset_x
            y += offset_y
            
            # Vérifier que l'hexagone est dans les limites de la surface
            if -50 < x < surface.get_width() + 50 and -50 < y < surface.get_height() + 50:
                try:
                    surface.blit(hex_obj.tuile, (x, y))
                except Exception as e:
                    pass

    def _get_mask_for_tile(self, tile_surface):
        """Retourne (et met en cache) le masque alpha d'une tuile."""
        key = id(tile_surface)
        if key not in self._mask_cache:
            self._mask_cache[key] = pygame.mask.from_surface(tile_surface, threshold=10)
        return self._mask_cache[key]

    def get_hex_at_pixel(self, px, py, offset_x=0, offset_y=0):
        """Trouve l'hexagone sous la souris en testant le masque alpha de la tuile."""
        # Même tri que le rendu, puis inversé pour récupérer l'élément visuellement au-dessus
        hexagones_tries = sorted(self.hexagones, key=lambda h: (h.get_pixel_pos()[1], h.get_pixel_pos()[0]))
        for hex_obj in reversed(hexagones_tries):
            x, y = hex_obj.get_pixel_pos()
            x += offset_x
            y += offset_y
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
        """Dessine une surbrillance sur la face supérieure de l'hexagone ciblé."""
        if hex_obj is None:
            return
        x, y = hex_obj.get_pixel_pos()
        x += offset_x
        y += offset_y
        tile = hex_obj.tuile
        mask = self._get_mask_for_tile(tile)

        # Surbrillance de la face supérieure :
        # - Remplissage colonne par colonne jusqu'à cut_y
        # - Outline dessiné SANS le bord inférieur (pour éviter le trait horizontal parasite)
        w, h = tile.get_size()
        cut_y = int(h * 0.62)

        tile_key = id(tile)
        overlay_key = (tile_key, 'overlay62')
        if overlay_key not in self._mask_cache:
            top_overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            for cx in range(w):
                for yy in range(cut_y):
                    if mask.get_at((cx, yy)):
                        top_overlay.set_at((cx, yy), (255, 255, 0, 80))
            self._mask_cache[overlay_key] = top_overlay

        top_overlay = self._mask_cache[overlay_key]
        surface.blit(top_overlay, (x, y))

        # Outline : on récupère les points du contour, puis on sépare les deux arcs
        # (gauche→sommet→droite) pour ne JAMAIS relier le bas horizontalement.
        top_mask = pygame.mask.from_surface(top_overlay, threshold=1)
        outline = top_mask.outline()
        if len(outline) > 1:
            max_oy = max(oy for _, oy in outline)
            # Garder uniquement les points qui ne sont PAS sur la ligne inférieure plate
            pts = [(x + ox, y + oy) for ox, oy in outline if oy < max_oy - 1]
            if len(pts) > 1:
                pygame.draw.lines(surface, (255, 255, 0), False, pts, 2)

# Classe Button : Boutons interactifs (hover, shadow, click)
class Button:
    def __init__(self,text,center_y,action):
        self.text = text
        self.center_y = center_y
        self.action = action  # Action déclenchée au clic ("new_game", "multiplayer"...)
        self.widtht, self.height = 320, 70
        self.rect = pygame.Rect((0,0,self.widtht,self.height))
        self.rect.center = (0,self.center_y)  # Center Y fixe, X dynamique
    
    def draw(self,win,mouse_pos):
        self.rect.center = (win.get_width() // 2, self.center_y)
        is_hover = self.rect.collidepoint(mouse_pos)
        # Utilise l'image si disponible
        img = get_button_display_image(self.action, is_hover, win.get_size())
        if img:
            img_rect = img.get_rect(center=self.rect.center)
            win.blit(img, img_rect)
            return
        # Fallback : rectangle coloré avec texte
        color = HOVER_BLUE if is_hover else TRANSLUCENT_BLUE
        button_surface = pygame.Surface((self.widtht, self.height), pygame.SRCALPHA)
        pygame.draw.rect(button_surface, color, (0, 0, self.widtht, self.height), border_radius=16)
        win.blit(button_surface, self.rect)
        text_surf = FONT_BUTTON.render(self.text, True, BLANC)
        text_rect = text_surf.get_rect(center=self.rect.center)
        shadow = FONT_BUTTON.render(self.text, True, SHADOW)
        win.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
        win.blit(text_surf, text_rect)

    def is_clicked(self,mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]
    
# création des boutons du menu principal

boutons_menu = [
    Button("New Game", 400, "new_game"),
    Button("Multiplayer", 480, "multiplayer"),
    Button("Options", 560, "options"),
    Button("Quit", 640, "quit"),
]


def show_options(screen, menu_surface, clock):
    """Affiche un menu modal pour choisir la résolution. Retourne (screen, menu_surface)."""
    options_running = True
    resolutions = [(1280, 720), (1600, 900), (1920, 1080), (2560, 1440)]
    win_w, win_h = screen.get_size()
    btn_w, btn_h = 320, 70
    padding = 20
    start_y = win_h // 2 - (len(resolutions) * (btn_h + padding)) // 2

    # Crée les rects des choix et du bouton "Back"
    option_buttons = []
    for i, (rw, rh) in enumerate(resolutions):
        rect = pygame.Rect(0, 0, btn_w, btn_h)
        rect.center = (win_w // 2, start_y + i * (btn_h + padding))
        option_buttons.append((rect, (rw, rh)))

    back_rect = pygame.Rect(0, 0, btn_w, btn_h)
    back_rect.center = (win_w // 2, start_y + len(resolutions) * (btn_h + padding) + 2 * padding)

    while options_running:
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
                            # change la résolution et remet à l'échelle l'image de fond du menu si possible
                            screen = pygame.display.set_mode((rw, rh))
                            try:
                                menu_image = pygame.image.load("menu.png").convert_alpha()
                                menu_surface = pygame.transform.scale(menu_image, (rw, rh))
                            except Exception:
                                # si le rechargement échoue, ignore et continue avec l'ancien menu
                                pass
                            options_running = False
                            break

        # Affichage du fond + overlay sombre
        win_w, win_h = screen.get_size()
        screen.blit(menu_surface, (0, 0))
        overlay = pygame.Surface((win_w, win_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        mx, my = pygame.mouse.get_pos()

        # Dessine les options
        for rect, (rw, rh) in option_buttons:
            label = f"{rw} x {rh}"
            key = f"{rw}x{rh}"
            bg = get_option_button_background(key, rect.width, rect.height)
            if bg:
                draw_option_image_button(screen, rect, bg, label=label)
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

        # Dessine le bouton Back
        bg = get_option_button_background("back", back_rect.width, back_rect.height)
        if bg:
            draw_option_image_button(screen, back_rect, bg, label="Back")
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
        pygame.mixer.music.set_volume(0)
        pygame.mixer.music.play(-1)  # -1 pour une boucle infinie
    except pygame.error:
        pass


running = True
clock = pygame.time.Clock()
# Lance la musique du menu
music_menu(menu_music)

# Met à jour la taille actuelle de la fenêtre et recentre les boutons
while running:
    clock.tick(120)  # Limite à 120 FPS

    # Mettre à jour les positions des boutons EN PREMIER

    win_w, win_h = fenetre.get_size()
    for btn in boutons_menu:
        btn.rect.center = (win_w // 2, btn.center_y)

# Boucle principale : Événements (clics, touches), update, render (120 FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game_state = "menu"  # Retour menu
            elif event.key == pygame.K_t and game_state == "game":
                if current_player_resources and hasattr(current_player_resources, 'add_resource'):
                    current_player_resources.add_resource('wood', 10)
                    current_player_resources.add_resource('food', 10)
                    current_player_resources.add_resource('gold', 5)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if game_state == "menu":
                for btn in boutons_menu:
                    if btn.is_clicked(mouse_pos, (1,0,0)):
                        if btn.action == "quit":
                            running = False
                        elif btn.action == "new_game":
                            carte = Carte(60, 52)
                            game_state = "game"
                            current_player_resources = ressources.PlayerResources(wood=50, food=50, gold=20, money=0)
                        elif btn.action == "multiplayer":
                            turn_manager, players = player_select.select_players(fenetre, clock)
                            if turn_manager:
                                game_state = "multi_game"
                                current_player_resources = turn_manager.current_player().resources
                        elif btn.action == "options":
                            fenetre, menu = show_options(fenetre, menu, clock)  # Resize fenêtre
            elif game_state == "multi_game" and 'end_turn_rect' in locals() and end_turn_rect.collidepoint(mouse_pos):
                if turn_manager:
                    turn_manager.player_finished(turn_manager.current_player())

    # Render selon game_state
    mouse_pos = pygame.mouse.get_pos()
    if game_state == "menu":
        win_w, win_h = fenetre.get_size()
        fenetre.blit(menu, (0, 0))  # Fond menu
        title_surf, title_rect = update_menu_layout(fenetre)
        fenetre.blit(title_surf, title_rect)  # Bannière titre image
        for btn in boutons_menu:
            btn.draw(fenetre, mouse_pos)

    elif game_state == "game":
        fenetre.fill(NOIR)
        if carte:
            carte.dessiner(fenetre)
            hovered_hex = carte.get_hex_at_pixel(mouse_pos[0], mouse_pos[1])
            carte.draw_hex_highlight(fenetre, hovered_hex)
        ressources.draw_resources_overlay(fenetre, current_player_resources)
        instruction = FONT_BUTTON.render("Échap: Menu | T: +Ressources", True, BLANC)
        fenetre.blit(instruction, (20, 20))
    elif game_state == "multi_game":
        fenetre.fill(NOIR)
        if carte:
            carte.dessiner(fenetre)
            hovered_hex = carte.get_hex_at_pixel(mouse_pos[0], mouse_pos[1])
            carte.draw_hex_highlight(fenetre, hovered_hex)
        ressources.draw_resources_overlay(fenetre, current_player_resources)
        # Turn indicator
        if turn_manager:
            turn_text = FONT_BUTTON.render(f"Tour de {turn_manager.current_player().name} (Tour {turn_manager.turn_number + 1}, Période {turn_manager.period})", True, BLANC)
            fenetre.blit(turn_text, (20, 60))
        instruction = FONT_BUTTON.render("Échap: Menu | Cliquez End Turn", True, BLANC)
        fenetre.blit(instruction, (20, 20))
        # End Turn button
        end_turn_btn = Button("End Turn", win_h - 100, "end_turn")
        end_turn_btn.draw(fenetre, mouse_pos)
        end_turn_rect = end_turn_btn.rect

    # Met à jour l'affichage
    pygame.display.flip()

# Nettoyage
pygame.quit()
sys.exit()


