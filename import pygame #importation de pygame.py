import pygame #importation de pygame
import sys
import subprocess
from pygame.locals import *

pygame.init() #démarrage de pygame
pygame.mixer.init()

"""
Ajout des variables à mettre ici

"""
#création d'une fenêtre
fenetre=pygame.display.set_mode((1920,1080))#fenêtre de taille 1920*1080



#chargement des images
liste_actuelle=[]

#images de fond (menus et maps)
menu = pygame.image.load("menu.png").convert_alpha()
menu = pygame.transform.scale(menu,(1920,1080))
"""
#tuiles de terrain
plaine_tuile = pygame.image.load("")

mountain_tuile = pygame.image.load("")

water_tuile = pygame.image.load("")

forest_tuile = pygame.image.load("")

snow_plaine_tuile = pygame.image.load("")

snow_forest_tuile = pygame.image.load("")

snow_mountain_tuile = pygame.image.load("")

ice_tuile = pygame.image.load("")

desert_tuile = pygame.image.load("")

desert_mountain_tuile = pygame.image.load("")
"""
#couleurs
BLANC = (255, 255, 255)
NOIR = (0, 0, 0)
VERT = (0, 255, 0)
ROUGE = (255, 0, 0)
BLEU = (0, 0, 255)
JAUNE = (255, 255, 0)
TRANSLUCENT_BLUE = (0, 80, 255, 100)
HOVER_BLUE = (0, 140, 255, 220)
SHADOW = (0, 0, 0,)

#polices
try:
    FONT_TITLE = pygame.font.Font("Pixeled.ttf", 72)
    FONT_BUTTON = pygame.font.Font("Pixeled.ttf", 36)

except:
    FONT_TITLE = pygame.font.SysFont(None, 72)
    FONT_BUTTON = pygame.font.SysFont(None, 36)

# Tuiles de terrain (à compléter avec les bons chemins d'accès aux images)
"""
tuiles = {
    'mountain_grass': pygame.image.load(""),
    'mountain_forest': pygame.image.load(""),
    'mountain_snow': pygame.image.load(""),
    'mountain_sand': pygame.image.load(""),
    'plain_grass': pygame.image.load(""),
    'plain_forest': pygame.image.load(""),
    'plain_snow': pygame.image.load(""),
    'desert': pygame.image.load(""),
    'forest': pygame.image.load(""),
    'snow_forest': pygame.image.load(""),
    'water': pygame.image.load(""),
}
"""
# création d'une classe Hexagone pour créer la map

class Hexagone:
    def __init__(self, q, r, type_terrain):
        self.q = q                           # Coordonnée q
        self.r = r                           # Coordonnée r
        self.type_terrain = type_terrain     # 'herbe', 'foret', 'eau', etc.
        self.tuile = tuiles[type_terrain]   # L'image PNG associée

# création d'une classe Button pour les boutons du menu

class Button:
    def __init__(self,text,center_y,action):
        self.text = text
        self.center_y = center_y
        self.action = action
        self.widtht, self.height = 320, 70
        self.rect = pygame.Rect((0,0,self.widtht,self.height))
        # la position centrale sera calculée dynamiquement selon la taille de la fenêtre
        self.rect.center = (0,self.center_y)
    
    def draw(self,win,mouse_pos):
        # s'assurer que le bouton est centré sur la largeur actuelle de la fenêtre
        self.rect.center = (win.get_width() // 2, self.center_y)
        is_hover = self.rect.collidepoint(mouse_pos)
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
    Button("Options", 500, "options"),
    Button("Quit", 600, "quit"),
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
            is_hover = rect.collidepoint((mx, my))
            color = HOVER_BLUE if is_hover else TRANSLUCENT_BLUE
            surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
            pygame.draw.rect(surf, color, (0, 0, btn_w, btn_h), border_radius=16)
            screen.blit(surf, rect)
            label = f"{rw} x {rh}"
            text_surf = FONT_BUTTON.render(label, True, BLANC)
            text_rect = text_surf.get_rect(center=rect.center)
            shadow = FONT_BUTTON.render(label, True, SHADOW)
            screen.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
            screen.blit(text_surf, text_rect)

        # Dessine le bouton Back
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


running = True
clock = pygame.time.Clock()

while running:
    clock.tick(60)  # Limite à 60 FPS

    # Met à jour la taille actuelle de la fenêtre et recentre les boutons
    win_w, win_h = fenetre.get_size()
    for btn in boutons_menu:
        btn.rect.center = (win_w // 2, btn.center_y)

    # Affiche le fond du menu
    fenetre.blit(menu, (0, 0))

    # Récupère la position de la souris
    mouse_pos = pygame.mouse.get_pos()

    # Gestion des événements
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Clic gauche : vérifier si un bouton est cliqué
            for btn in boutons_menu:
                if btn.rect.collidepoint(event.pos):
                    if btn.action == "quit":
                        running = False
                    elif btn.action == "new_game":
                        print("New game selected")
                    elif btn.action == "options":
                        # affiche le modal options (retourne éventuellement un nouvel écran/menu)
                        fenetre, menu = show_options(fenetre, menu, clock)

    # Titre
    title = FONT_TITLE.render("Timeless Empire", True, BLANC)
    shadow = FONT_TITLE.render("Timeless Empire", True, SHADOW)
    center_x = fenetre.get_width() // 2
    fenetre.blit(shadow, (center_x - title.get_width() // 2 + 3, 103))
    fenetre.blit(title, (center_x - title.get_width() // 2, 100))

    # Dessine les boutons
    for btn in boutons_menu:
        btn.draw(fenetre, mouse_pos)

    # Met à jour l'affichage
    pygame.display.flip()

# Nettoyage
pygame.quit()
sys.exit()


