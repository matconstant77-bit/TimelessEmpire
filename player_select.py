import pygame
from tours import Player, TurnManager

def select_players(fenetre, clock):
    # Menu sélection joueurs (1-4)
    running = True
    selected_players = 1
    players = []
    
    font = pygame.font.SysFont(None, 48)
    small_font = pygame.font.SysFont(None, 32)
    
    while running:
        fenetre.fill((0, 0, 50))
        
        # Titre
        title = font.render("Nombre de joueurs", True, (255, 255, 255))
        fenetre.blit(title, (fenetre.get_width()//2 - title.get_width()//2, 100))
        
        # Boutons +/-
        minus_rect = pygame.Rect(800, 300, 100, 80)
        plus_rect = pygame.Rect(1100, 300, 100, 80)
        pygame.draw.rect(fenetre, (100, 100, 255), minus_rect)
        pygame.draw.rect(fenetre, (100, 100, 255), plus_rect)
        minus_text = small_font.render('-', True, (255, 255, 255))
        plus_text = small_font.render('+', True, (255, 255, 255))
        fenetre.blit(minus_text, (minus_rect.centerx - 10, minus_rect.centery - 10))
        fenetre.blit(plus_text, (plus_rect.centerx - 10, plus_rect.centery - 10))
        
        # Nb actuel
        nb_text = font.render(f"{selected_players}", True, (255, 255, 255))
        fenetre.blit(nb_text, (960, 280))
        
        # Bouton start
        start_rect = pygame.Rect(900, 500, 240, 80)
        pygame.draw.rect(fenetre, (0, 255, 0), start_rect)
        start_text = small_font.render("START", True, (0, 0, 0))
        fenetre.blit(start_text, (start_rect.centerx - 40, start_rect.centery - 15))
        
        pygame.display.flip()
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if minus_rect.collidepoint(event.pos) and selected_players > 1:
                    selected_players -= 1
                elif plus_rect.collidepoint(event.pos) and selected_players < 4:
                    selected_players += 1
                elif start_rect.collidepoint(event.pos):
                    # Créer joueurs
                    players = [Player(f"Joueur {i+1}") for i in range(selected_players)]
                    turn_manager = TurnManager(players)
                    running = False
        
    return turn_manager, players

# Exemple d'utilisation (à intégrer dans game.py)
# turn_manager, players = select_players(screen, clock)
# if turn_manager:
#     print(f"Tour {turn_manager.turn_number}, période {turn_manager.period}")

