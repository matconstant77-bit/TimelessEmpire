# Contient le code du jeu

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
        self.rect.center = (1920//2,self.center_y)
    
    def draw(self,win,mouse_pos):
        is_hover = self.rect.collidepoint(mouse_pos)
        color = HOVER_BLUE if is_hover else TRANSLUCENT_BLUE
        button_surface = pygame.Surface((self.widtht, self.height), pygame.SRCALPHA)
        pygame.draw.rect(button_surface, color, (0, 0, self.widtht, self.height), border_radius=16)
        win.blit(button_surface, self.rect.)

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


        










