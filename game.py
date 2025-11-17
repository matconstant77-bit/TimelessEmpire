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