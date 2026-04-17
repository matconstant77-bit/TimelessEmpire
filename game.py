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
players = []
turn_started_at = None
current_turn_cards = None
status_message = "Bienvenue dans Timeless Empire."
status_message_until = 0

#chargement des images
liste_actuelle=[]

#images de fond (menus et maps)
menu = pygame.image.load(asset_path("background.png")).convert_alpha()
menu = pygame.transform.scale(menu,(1920,1080))

#tuiles de terrain

try:
    Eau_1 = pygame.transform.scale(pygame.image.load(asset_path("Eau_1.png")),(32,42))
    Eau_2 = pygame.transform.scale(pygame.image.load(asset_path("Eau_2.png")),(32,42))
    Eau_3 = pygame.transform.scale(pygame.image.load(asset_path("Eau_3.png")),(32,42))
    Herbe_1 = pygame.transform.scale(pygame.image.load(asset_path("Herbe_1.png")),(32,42))
    Herbe_2 = pygame.transform.scale(pygame.image.load(asset_path("Herbe_2.png")),(32,42))
    Herbe_3 = pygame.transform.scale(pygame.image.load(asset_path("Herbe_3.png")),(32,42))
    Pierre_1 = pygame.transform.scale(pygame.image.load(asset_path("Pierre_1.png")),(32,42))
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

terrain_variantes = {
    'eau': [Eau_1, Eau_2, Eau_3],
    'herbe': [Herbe_1],
    'foret': [Herbe_2, Herbe_3],
    'montagne': [Pierre_1],
}


#musique
menu_music = asset_path("menu-musique.mp3")

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
FONT_PANEL_TITLE = pygame.font.SysFont(None, 34)
FONT_PANEL_TEXT = pygame.font.SysFont(None, 26)
FONT_SMALL = pygame.font.SysFont(None, 22)

PANEL_WIDTH = 340
TURN_DURATION_MS = tours.TURN_DURATION_MS
EXPAND_COST = {"wood": 8, "food": 4, "gold": 2}
BUILDING_TERRAINS = {
    "farm": {"herbe", "foret"},
    "barracks": {"herbe", "foret", "montagne"},
    "blacksmith": {"herbe", "montagne"},
}
BUILDING_LABELS = {
    "farm": "Ferme",
    "barracks": "Caserne",
    "blacksmith": "Forge",
}
TERRAIN_LABELS = {
    "herbe": "Plaine",
    "foret": "Foret",
    "montagne": "Montagne",
    "eau": "Eau",
}
PLAYER_COLORS = [
    (255, 214, 92),
    (96, 190, 255),
    (255, 120, 120),
    (130, 235, 150),
    (220, 150, 255),
]

# --- Fonctions utilitaires pour les images UI ---

def load_trimmed_image(path, min_alpha=25):
    """Charge une image et retourne uniquement la partie visible (alpha > min_alpha)."""
    path = asset_path(path)
    if not os.path.exists(path):
        return None
    image = pygame.image.load(path).convert_alpha()
    bounds = image.get_bounding_rect(min_alpha=min_alpha)
    if bounds.width > 0 and bounds.height > 0:
        return image.subsurface(bounds).copy()
    return image

def load_menu_button_images(path):
    """Détecte les régions de boutons dans le spritesheet et retourne un dict par action."""
    path = asset_path(path)
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
    path = asset_path(path)
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
    """Dessine un bouton image dans le rect."""
    if image:
        img_rect = image.get_rect(center=rect.center)
        surface.blit(image, img_rect)
    if label:
        text_surf = FONT_BUTTON.render(label, True, BLANC)
        shadow_surf = FONT_BUTTON.render(label, True, SHADOW)
        text_rect = text_surf.get_rect(center=rect.center)
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
    def __init__(self, q, r, type_terrain, tuile_surface=None):
        self.q = q                           # Coord q (cube coords)
        self.r = r                           # Coord r
        self.type_terrain = type_terrain     # Type ('herbe', 'eau'...)
        self.tuile = tuile_surface if tuile_surface is not None else tuiles[type_terrain]   # Image associée
        self.selection_lift = 0.0           # Animation visuelle de sélection
        self.target_lift = 0.0              # Cible d'animation (0.0 ou 1.0)
        self.owner = None
        self.building = None
    
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
        self.hex_by_coord = {}
        self.selected_hex = None
        self._mask_cache = {}
        self.generer_carte()

    def update_selection_animation(self):
        """Anime en douceur le relèvement des hexagones sélectionnés."""
        for hex_obj in self.hexagones:
            delta = hex_obj.target_lift - hex_obj.selection_lift
            if abs(delta) < 0.01:
                hex_obj.selection_lift = hex_obj.target_lift
            else:
                hex_obj.selection_lift += delta * 0.22

    def select_hex(self, hex_obj):
        """Sélectionne un hexagone et déclenche son animation de relèvement."""
        if self.selected_hex is not None and self.selected_hex is not hex_obj:
            self.selected_hex.target_lift = 0.0

        if hex_obj is None:
            self.selected_hex = None
            return

        self.selected_hex = hex_obj
        self.selected_hex.target_lift = 1.0
    
    def generer_carte(self):
        """Génère une carte en grands amas organiques avec moins d'eau."""
        self.hexagones.clear()
        self.hex_by_coord.clear()

        # Poids de base (proportion de chaque terrain dans le pool de germes)
        terrain_pool = ['herbe'] * 45 + ['foret'] * 28 + ['montagne'] * 18 + ['eau'] * 9

        # --- Étape 1: Germes Voronoi répartis aléatoirement ---
        # ~1 germe pour 85 cases → amas de taille ~85 cases chacun
        n_seeds = max(28, (self.largeur * self.hauteur) // 10)
        seeds = [
            (random.randint(0, self.largeur - 1),
             random.randint(0, self.hauteur - 1),
             random.choice(terrain_pool))
            for _ in range(n_seeds)
        ]

        # --- Étape 2: Attribution Voronoi avec bruit gaussien sur la distance ---
        # Le bruit rend les frontières irrégulières et organiques (pas des droites)
        noise_scale = (self.largeur + self.hauteur) / 28.0
        terrain_grid = {}
        for r in range(self.hauteur):
            for q in range(self.largeur):
                best_type = 'herbe'
                min_dist = float('inf')
                for sq, sr, st in seeds:
                    d = ((q - sq) ** 2 + (r - sr) ** 2) ** 0.5
                    d += random.gauss(0, noise_scale)
                    if d < min_dist:
                        min_dist = d
                        best_type = st
                terrain_grid[(q, r)] = best_type

        # --- Étape 3: Lissage cellulaire (2 passes) ---
        # Élimine les cellules seules et adoucit les transitions trop abruptes.
        # Seulement si 5 voisins sur 6 sont d'un même type → conversion douce.
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

        # --- Étape 4: Création des hexagones avec variantes visuelles ---
        for r in range(self.hauteur):
            for q in range(self.largeur):
                type_terrain = terrain_grid[(q, r)]
                tuile_surface = self._choose_tile_surface(type_terrain)
                hex_obj = Hexagone(q, r, type_terrain, tuile_surface=tuile_surface)
                self.hexagones.append(hex_obj)
                self.hex_by_coord[(q, r)] = hex_obj

    def _choose_tile_surface(self, type_terrain):
        """Choisit une variante visuelle d'une famille de terrain."""
        variantes = terrain_variantes.get(type_terrain, [tuiles[type_terrain]])
        return random.choice(variantes)

    def _get_existing_neighbors(self, q, r, terrain_grid):
        """Retourne les types des voisins déjà générés (layout odd-r)."""
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
        return self.hex_by_coord.get((q, r))

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

    def get_bounds(self):
        if not self.hexagones:
            return pygame.Rect(0, 0, 0, 0)
        min_x = min(h.get_pixel_pos()[0] for h in self.hexagones)
        min_y = min(h.get_pixel_pos()[1] for h in self.hexagones)
        max_x = max(h.get_pixel_pos()[0] + h.tuile.get_width() for h in self.hexagones)
        max_y = max(h.get_pixel_pos()[1] + h.tuile.get_height() for h in self.hexagones)
        return pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
    
    def dessiner(self, surface, offset_x=0, offset_y=0):
        """Dessine tous les hexagones sur la surface en ordre de profondeur correct."""
        self.update_selection_animation()

        # Trier les hexagones: d'abord par y (position verticale), puis par x (position horizontale)
        # Cela affiche de bas en haut, et pour une même hauteur, de gauche à droite
        hexagones_tries = sorted(self.hexagones, key=lambda h: (h.get_pixel_pos()[1], h.get_pixel_pos()[0]))
        
        for hex_obj in hexagones_tries:
            x, y = hex_obj.get_pixel_pos()
            x += offset_x
            y += offset_y
            y -= int(hex_obj.selection_lift * 10)
            
            # Vérifier que l'hexagone est dans les limites de la surface
            if -50 < x < surface.get_width() + 50 and -50 < y < surface.get_height() + 50:
                try:
                    surface.blit(hex_obj.tuile, (x, y))
                    if hex_obj.owner is not None:
                        owner_color = getattr(hex_obj.owner, "color", JAUNE)
                        indicator = (x + hex_obj.tuile.get_width() // 2, y + max(10, int(hex_obj.tuile.get_height() * 0.24)))
                        pygame.draw.circle(surface, (0, 0, 0), indicator, 10)
                        pygame.draw.circle(surface, owner_color, indicator, 7)
                    if hex_obj.building:
                        badge_rect = pygame.Rect(0, 0, 64, 20)
                        badge_rect.midbottom = (x + hex_obj.tuile.get_width() // 2, y + int(hex_obj.tuile.get_height() * 0.62))
                        pygame.draw.rect(surface, (10, 16, 28), badge_rect, border_radius=10)
                        pygame.draw.rect(surface, (215, 225, 255), badge_rect, width=1, border_radius=10)
                        badge_text = FONT_SMALL.render(BUILDING_LABELS.get(hex_obj.building, hex_obj.building), True, BLANC)
                        badge_text = scale_surface_to_fit(badge_text, badge_rect.width - 8, badge_rect.height - 4)
                        badge_text_rect = badge_text.get_rect(center=badge_rect.center)
                        surface.blit(badge_text, badge_text_rect)
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
        """Dessine une surbrillance sur la face supérieure de l'hexagone ciblé."""
        if hex_obj is None:
            return
        x, y = hex_obj.get_pixel_pos()
        x += offset_x
        y += offset_y
        y -= int(hex_obj.selection_lift * 10)
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


def set_status(message, duration_ms=3200):
    global status_message, status_message_until
    status_message = message
    status_message_until = pygame.time.get_ticks() + duration_ms


def get_current_player():
    if not turn_manager:
        return None
    try:
        return turn_manager.current_player()
    except RuntimeError:
        return None


def get_map_offsets(win, current_map):
    if not current_map:
        return 0, 0
    bounds = current_map.get_bounds()
    available_w = max(260, win.get_width() - PANEL_WIDTH - 24)
    available_h = max(240, win.get_height() - 24)
    offset_x = 12 + (available_w - bounds.width) // 2 - bounds.x
    offset_y = 12 + (available_h - bounds.height) // 2 - bounds.y
    return offset_x, offset_y


def claim_hex(hex_obj, player):
    if hex_obj is None:
        return
    hex_obj.owner = player


def assign_starting_territories(current_map, current_players):
    if not current_map or not current_players:
        return

    land_hexes = [hex_obj for hex_obj in current_map.hexagones if hex_obj.type_terrain != "eau"]
    chosen_spawns = []

    def score_spawn(hex_obj, target_q, target_r):
        distance = abs(hex_obj.q - target_q) + abs(hex_obj.r - target_r)
        if not chosen_spawns:
            return distance
        min_spacing = min(abs(hex_obj.q - other.q) + abs(hex_obj.r - other.r) for other in chosen_spawns)
        spacing_penalty = max(0, 14 - min_spacing) * 12
        return distance + spacing_penalty

    for idx, player in enumerate(current_players):
        target_q = int((idx + 1) * current_map.largeur / (len(current_players) + 1))
        target_r = current_map.hauteur // 2 + (-7 if idx % 2 == 0 else 7)
        available_hexes = [hex_obj for hex_obj in land_hexes if hex_obj not in chosen_spawns]
        spawn_hex = min(available_hexes, key=lambda hex_obj: score_spawn(hex_obj, target_q, target_r))
        chosen_spawns.append(spawn_hex)
        player.home_hex = spawn_hex
        claim_hex(spawn_hex, player)

        claimed_neighbors = 0
        for neighbor in current_map.get_neighbors(spawn_hex):
            if neighbor.type_terrain == "eau" or neighbor.owner is not None:
                continue
            claim_hex(neighbor, player)
            claimed_neighbors += 1
            if claimed_neighbors >= 3:
                break

        spawn_hex.building = "farm"
        if "farm" not in player.buildings:
            player.build("farm", free=True)


def setup_players(current_players):
    for idx, player in enumerate(current_players):
        player.color = PLAYER_COLORS[idx % len(PLAYER_COLORS)]
        player.buildings = []
        player.trapped_buildings.clear()
        player.home_hex = None
        player.grant_starting_resources()


def start_session(current_players, next_game_state):
    global players, turn_manager, carte, game_state, current_player_resources
    players = current_players
    setup_players(players)
    turn_manager = tours.TurnManager(players)
    carte = Carte(22, 18)
    assign_starting_territories(carte, players)
    game_state = next_game_state
    current_player_resources = turn_manager.current_player().resources
    begin_turn(f"Tour de {turn_manager.current_player().name}. Choisissez une carte.")


def begin_turn(message=None):
    global current_player_resources, turn_started_at, current_turn_cards
    player = get_current_player()
    if player is None:
        return
    current_player_resources = player.resources
    turn_started_at = pygame.time.get_ticks()
    current_turn_cards = tours.generate_cards()
    if message is None:
        message = f"Tour de {player.name}. Choisissez une carte."
    set_status(message)


def choose_card(card_index):
    global current_turn_cards, current_player_resources
    player = get_current_player()
    if player is None or not current_turn_cards or not (0 <= card_index < len(current_turn_cards)):
        return
    card_type, card = current_turn_cards[card_index]
    tours.apply_card(player, card_type, card)
    current_turn_cards = None
    current_player_resources = player.resources
    set_status(f"{player.name} choisit : {card['name']}")


def finish_current_turn(auto=False):
    global current_player_resources
    player = get_current_player()
    if player is None or not turn_manager:
        return
    if current_turn_cards:
        if auto:
            choose_card(random.randrange(len(current_turn_cards)))
        else:
            set_status("Choisissez d'abord une carte.")
            return
    turn_manager.player_finished(player)
    current_player_resources = turn_manager.current_player().resources
    begin_turn(f"Nouveau tour : {turn_manager.current_player().name}")


def has_adjacent_owned_tile(current_map, player, target_hex):
    return any(neighbor.owner is player for neighbor in current_map.get_neighbors(target_hex))


def can_expand_to_hex(player, target_hex):
    if player is None or target_hex is None:
        return False, "Case invalide"
    if target_hex.type_terrain == "eau":
        return False, "Impossible sur l'eau"
    if target_hex.owner is player:
        return False, "Territoire deja a vous"
    if target_hex.owner is not None:
        return False, "Territoire deja occupe"
    if not has_adjacent_owned_tile(carte, player, target_hex):
        return False, "Besoin d'une case voisine"
    if not player.can_afford(EXPAND_COST):
        return False, "Ressources insuffisantes"
    return True, ""


def expand_selected_hex():
    player = get_current_player()
    selected_hex = carte.selected_hex if carte else None
    ok, reason = can_expand_to_hex(player, selected_hex)
    if not ok:
        set_status(reason)
        return
    player.spend_resources(EXPAND_COST)
    selected_hex.owner = player
    set_status(f"{player.name} etend son territoire.")


def can_build_on_hex(player, target_hex, building):
    if player is None or target_hex is None:
        return False, "Selectionnez une case"
    if target_hex.owner is not player:
        return False, "Case hors territoire"
    if target_hex.type_terrain == "eau":
        return False, "Impossible sur l'eau"
    if target_hex.building is not None:
        return False, "Batiment deja present"
    if building not in turn_manager.available_buildings:
        return False, "Batiment non debloque"
    if target_hex.type_terrain not in BUILDING_TERRAINS.get(building, set()):
        return False, "Terrain incompatible"
    if not player.can_afford(tours.BUILDING_COSTS[building]):
        return False, "Ressources insuffisantes"
    return True, ""


def build_on_selected_hex(building):
    player = get_current_player()
    selected_hex = carte.selected_hex if carte else None
    ok, reason = can_build_on_hex(player, selected_hex, building)
    if not ok:
        set_status(reason)
        return
    if player.build(building):
        selected_hex.building = building
        set_status(f"{BUILDING_LABELS.get(building, building)} construit.")


def get_turn_remaining_ms():
    if turn_started_at is None:
        return TURN_DURATION_MS
    return max(0, TURN_DURATION_MS - (pygame.time.get_ticks() - turn_started_at))


def draw_button(surface, rect, label, mouse_pos, enabled=True, accent=(75, 112, 210)):
    hovered = rect.collidepoint(mouse_pos)
    base_color = accent if enabled else (70, 70, 82)
    hover_color = tuple(min(255, c + 28) for c in base_color)
    pygame.draw.rect(surface, hover_color if hovered and enabled else base_color, rect, border_radius=16)
    pygame.draw.rect(surface, (18, 24, 44), rect, width=2, border_radius=16)
    text_color = BLANC if enabled else (185, 185, 195)
    text = FONT_BUTTON.render(label, True, text_color)
    text_rect = text.get_rect(center=rect.center)
    surface.blit(text, text_rect)


def build_game_ui_layout(win):
    win_w, win_h = win.get_size()
    panel_rect = pygame.Rect(win_w - PANEL_WIDTH, 0, PANEL_WIDTH, win_h)
    end_turn_rect = pygame.Rect(panel_rect.x + 20, panel_rect.bottom - 72, panel_rect.width - 40, 50)
    action_buttons = []

    selected_hex = carte.selected_hex if carte else None
    current_player = get_current_player()
    action_y = panel_rect.y + 360
    button_w = panel_rect.width - 40
    button_h = 42
    gap = 10

    if selected_hex is not None and current_turn_cards is None:
        can_expand, _ = can_expand_to_hex(current_player, selected_hex)
        action_buttons.append({
            "id": "expand",
            "label": "Revendiquer (8B/4N/2O)",
            "rect": pygame.Rect(panel_rect.x + 20, action_y, button_w, button_h),
            "enabled": can_expand,
        })
        action_y += button_h + gap

        for building in turn_manager.available_buildings:
            enabled, _ = can_build_on_hex(current_player, selected_hex, building)
            cost = tours.BUILDING_COSTS.get(building, {})
            cost_text = "/".join(
                f"{amount}{key[0].upper()}" for key, amount in cost.items() if amount > 0
            ) or "Gratuit"
            action_buttons.append({
                "id": f"build:{building}",
                "label": f"{BUILDING_LABELS.get(building, building)} ({cost_text})",
                "rect": pygame.Rect(panel_rect.x + 20, action_y, button_w, button_h),
                "enabled": enabled,
            })
            action_y += button_h + gap

    card_buttons = []
    card_panel = None
    if current_turn_cards:
        modal_w = min(860, max(560, win_w - PANEL_WIDTH - 60))
        modal_h = 250
        modal_x = max(20, (win_w - PANEL_WIDTH - modal_w) // 2)
        card_panel = pygame.Rect(modal_x, 36, modal_w, modal_h)
        card_w = (modal_w - 60) // 3
        for idx, _card in enumerate(current_turn_cards):
            rect = pygame.Rect(card_panel.x + 15 + idx * (card_w + 15), card_panel.y + 70, card_w, 150)
            card_buttons.append({"id": idx, "rect": rect})

    return {
        "panel_rect": panel_rect,
        "end_turn_rect": end_turn_rect,
        "action_buttons": action_buttons,
        "card_panel": card_panel,
        "card_buttons": card_buttons,
    }


def draw_game_ui(surface, layout, mouse_pos):
    panel_rect = layout["panel_rect"]
    pygame.draw.rect(surface, (10, 14, 24), panel_rect)
    pygame.draw.rect(surface, (88, 126, 210), panel_rect, width=2)

    player = get_current_player()
    player_name = player.name if player else "Aucun joueur"
    title = FONT_PANEL_TITLE.render(player_name, True, BLANC)
    surface.blit(title, (panel_rect.x + 18, 16))

    remaining_ms = get_turn_remaining_ms()
    mins = remaining_ms // 60000
    secs = (remaining_ms % 60000) // 1000
    timer = FONT_PANEL_TEXT.render(f"Temps restant : {mins:02d}:{secs:02d}", True, (255, 232, 160))
    surface.blit(timer, (panel_rect.x + 18, 48))

    if turn_manager:
        info_lines = [
            f"Tour : {turn_manager.turn_number + 1}",
            f"Periode : {turn_manager.period}",
            f"Batiments : {', '.join(BUILDING_LABELS.get(b, b) for b in turn_manager.available_buildings)}",
        ]
        for idx, line in enumerate(info_lines):
            text = FONT_SMALL.render(line, True, (205, 218, 255))
            surface.blit(text, (panel_rect.x + 18, 80 + idx * 22))

    ressources.draw_resources_overlay(
        surface,
        current_player_resources,
        area=pygame.Rect(panel_rect.x + 16, 150, panel_rect.width - 32, 150),
        title="Ressources",
    )

    selected_hex = carte.selected_hex if carte else None
    info_top = 318
    info_title = FONT_PANEL_TITLE.render("Case selectionnee", True, BLANC)
    surface.blit(info_title, (panel_rect.x + 18, info_top))

    if selected_hex is None:
        help_lines = [
            "Cliquez sur une case pour voir ses details.",
            "Choisissez une carte au debut du tour,",
            "puis etendez votre territoire ou construisez.",
        ]
        for idx, line in enumerate(help_lines):
            text = FONT_SMALL.render(line, True, (200, 208, 230))
            surface.blit(text, (panel_rect.x + 18, info_top + 36 + idx * 22))
    else:
        owner_name = selected_hex.owner.name if selected_hex.owner else "Neutre"
        building_name = BUILDING_LABELS.get(selected_hex.building, "Aucun")
        if selected_hex.building is None:
            building_name = "Aucun"
        details = [
            f"Coordonnees : ({selected_hex.q}, {selected_hex.r})",
            f"Terrain : {TERRAIN_LABELS.get(selected_hex.type_terrain, selected_hex.type_terrain)}",
            f"Proprietaire : {owner_name}",
            f"Batiment : {building_name}",
        ]
        for idx, line in enumerate(details):
            text = FONT_SMALL.render(line, True, (218, 225, 245))
            surface.blit(text, (panel_rect.x + 18, info_top + 36 + idx * 22))

    for button in layout["action_buttons"]:
        draw_button(surface, button["rect"], button["label"], mouse_pos, enabled=button["enabled"])

    draw_button(surface, layout["end_turn_rect"], "Fin du tour", mouse_pos, enabled=True, accent=(0, 150, 82))

    if current_turn_cards and layout["card_panel"] is not None:
        shade = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 110))
        surface.blit(shade, (0, 0))

        modal = layout["card_panel"]
        pygame.draw.rect(surface, (14, 20, 36), modal, border_radius=24)
        pygame.draw.rect(surface, (110, 150, 240), modal, width=2, border_radius=24)
        title = FONT_PANEL_TITLE.render("Choisissez une carte", True, BLANC)
        subtitle = FONT_SMALL.render("Chaque debut de tour commence par un choix de carte.", True, (205, 215, 240))
        surface.blit(title, (modal.x + 18, modal.y + 14))
        surface.blit(subtitle, (modal.x + 18, modal.y + 44))

        for idx, button in enumerate(layout["card_buttons"]):
            rect = button["rect"]
            hovered = rect.collidepoint(mouse_pos)
            pygame.draw.rect(surface, (42, 62, 118) if hovered else (24, 34, 60), rect, border_radius=18)
            pygame.draw.rect(surface, (130, 175, 255), rect, width=2, border_radius=18)

            card_type, card = current_turn_cards[idx]
            card_name = FONT_PANEL_TEXT.render(card["name"], True, BLANC)
            desc = tours.describe_card(card_type, card)
            card_desc = FONT_SMALL.render(desc, True, (215, 225, 245))
            card_desc = scale_surface_to_fit(card_desc, rect.width - 24, 32)
            surface.blit(card_name, (rect.x + 12, rect.y + 12))
            surface.blit(card_desc, (rect.x + 12, rect.y + 50))

            pick = FONT_SMALL.render("Cliquer pour choisir", True, (255, 229, 160))
            surface.blit(pick, (rect.x + 12, rect.bottom - 28))

    if pygame.time.get_ticks() < status_message_until:
        status_rect = pygame.Rect(18, surface.get_height() - 46, max(340, min(720, surface.get_width() - PANEL_WIDTH - 36)), 30)
        pygame.draw.rect(surface, (8, 12, 22), status_rect, border_radius=12)
        pygame.draw.rect(surface, (100, 145, 235), status_rect, width=1, border_radius=12)
        status_text = FONT_SMALL.render(status_message, True, (235, 240, 255))
        surface.blit(status_text, (status_rect.x + 12, status_rect.y + 6))


def handle_game_ui_click(mouse_pos, layout):
    if current_turn_cards:
        for button in layout["card_buttons"]:
            if button["rect"].collidepoint(mouse_pos):
                choose_card(button["id"])
                return True
        return True

    for button in layout["action_buttons"]:
        if button["rect"].collidepoint(mouse_pos):
            if not button["enabled"]:
                return True
            if button["id"] == "expand":
                expand_selected_hex()
                return True
            if button["id"].startswith("build:"):
                build_on_selected_hex(button["id"].split(":", 1)[1])
                return True

    if layout["end_turn_rect"].collidepoint(mouse_pos):
        finish_current_turn(auto=False)
        return True

    if layout["panel_rect"].collidepoint(mouse_pos):
        return True

    return False


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
                            screen = pygame.display.set_mode((rw, rh), pygame.RESIZABLE)
                            try:
                                menu_image = pygame.image.load(asset_path("background.png")).convert_alpha()
                                menu_surface = pygame.transform.scale(menu_image, (rw, rh))
                            except Exception:
                                # Si le rechargement échoue, conserver un fond cohérent à la nouvelle taille.
                                menu_surface = pygame.transform.scale(menu_surface, (rw, rh))
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
                draw_option_image_button(screen, rect, None, label=label)

        # Dessine le bouton Back
        bg = get_option_button_background("back", back_rect.width, back_rect.height)
        if bg:
            draw_option_image_button(screen, back_rect, bg, label="Retour")
        else:
            is_hover = back_rect.collidepoint((mx, my))
            color = HOVER_BLUE if is_hover else TRANSLUCENT_BLUE
            surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
            pygame.draw.rect(surf, color, (0, 0, btn_w, btn_h), border_radius=16)
            screen.blit(surf, back_rect)
            draw_option_image_button(screen, back_rect, None, label="Retour")

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
        pygame.mixer.music.play(-1)  # -1 pour une boucle infinie
    except pygame.error:
        pass


running = True
clock = pygame.time.Clock()
music_menu(menu_music)

while running:
    clock.tick(120)

    ui_layout = build_game_ui_layout(fenetre) if game_state in ("game", "multi_game") and turn_manager else None

    if game_state in ("game", "multi_game") and turn_manager and get_turn_remaining_ms() <= 0:
        finish_current_turn(auto=True)
        ui_layout = build_game_ui_layout(fenetre)

    win_w, win_h = fenetre.get_size()
    for btn in boutons_menu:
        btn.rect.center = (win_w // 2, btn.center_y)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game_state = "menu"
                set_status("Retour au menu.")
            elif event.key == pygame.K_t and game_state in ("game", "multi_game"):
                player = get_current_player()
                if player:
                    player.add_resource("wood", 10)
                    player.add_resource("food", 10)
                    player.add_resource("gold", 5)
                    current_player_resources = player.resources
                    set_status("Bonus de ressources ajoute.")
            elif event.key == pygame.K_SPACE and game_state in ("game", "multi_game"):
                finish_current_turn(auto=False)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if game_state == "menu":
                for btn in boutons_menu:
                    if btn.is_clicked(mouse_pos, (1, 0, 0)):
                        if btn.action == "quit":
                            running = False
                        elif btn.action == "new_game":
                            start_session([tours.Player("Empire")], "game")
                        elif btn.action == "multiplayer":
                            selection_result = player_select.select_players(fenetre, clock)
                            if selection_result:
                                _, selected_players = selection_result
                                start_session(selected_players, "multi_game")
                        elif btn.action == "options":
                            fenetre, menu = show_options(fenetre, menu, clock)
            elif game_state in ("game", "multi_game") and carte:
                if ui_layout and handle_game_ui_click(mouse_pos, ui_layout):
                    continue
                map_offset_x, map_offset_y = get_map_offsets(fenetre, carte)
                clicked_hex = carte.get_hex_at_pixel(mouse_pos[0], mouse_pos[1], map_offset_x, map_offset_y)
                carte.select_hex(clicked_hex)

    mouse_pos = pygame.mouse.get_pos()
    if game_state == "menu":
        win_w, win_h = fenetre.get_size()
        fenetre.blit(pygame.transform.smoothscale(menu, (win_w, win_h)), (0, 0))
        title_surf, title_rect = update_menu_layout(fenetre)
        fenetre.blit(title_surf, title_rect)
        for btn in boutons_menu:
            btn.draw(fenetre, mouse_pos)

    elif game_state in ("game", "multi_game"):
        fenetre.fill((6, 10, 18))
        map_offset_x, map_offset_y = get_map_offsets(fenetre, carte)
        if carte:
            carte.dessiner(fenetre, map_offset_x, map_offset_y)
            hovered_hex = None
            if not (ui_layout and ui_layout["panel_rect"].collidepoint(mouse_pos)) and not current_turn_cards:
                hovered_hex = carte.get_hex_at_pixel(mouse_pos[0], mouse_pos[1], map_offset_x, map_offset_y)
            carte.draw_hex_highlight(fenetre, hovered_hex, map_offset_x, map_offset_y)
        if ui_layout:
            draw_game_ui(fenetre, ui_layout, mouse_pos)

    pygame.display.flip()

# Nettoyage
pygame.quit()
sys.exit()


