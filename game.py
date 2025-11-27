# Contient le code du jeu

import pygame #importation de pygame
from pygame.locals import *

pygame.init() #démarrage de pygame
pygame.mixer.init()

"""
Ajout des variables à mettre ici

"""

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




#création d'une fenêtre
fenetre=pygame.display.set_mode((1920,1080))#fenêtre de taille 1920*1080



#chargement des images
liste_actuelle=[]

#images de fond (menus et maps)
menu = pygame.image.load("menu.png").convert_alpha()
menu = pygame.transform.scale(menu,(1920,1080))
>>>>>>> c01f64c5de0585a6d7a250cd2887c04e006b1cf9




