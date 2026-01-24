# Contient le code du jeu
 
import pygame

# Tuiles de terrain (à compléter avec les bons chemins d'accès aux images)

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

import pygame #importation de pygame
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
