import pygame
from tours import Player, TurnManager
from game import FONT_BUTTON, FONT_TITLE, SHADOW  # Reuse fonts/colors from game.py

# Menu sélection nombre joueurs (1-4), crée TurnManager/Players
def select_players(fenetre, clock):
    running = True
    selected_players = 1
    players = []
    
    # Fonts réutilisées du game.py pour cohérence
    title_font = FONT_TITLE if 'FONT_TITLE' in globals() else pygame.font.SysFont(None, 72)
    button_font = FONT_BUTTON if 'FONT_BUTTON' in globals() else pygame.font.SysFont(None, 36)
    
    while running:
        # Fond sombre menu
        fenetre.fill((0, 0, 50))
        
        # Titre centré
        title = title_font.render("Multiplayer - Nb Joueurs", True, BLANC)
        title_rect = title.get_rect(center=(fenetre.get_width()//2, 150))
        shadow_title = title_font.render("Multiplayer - Nb Joueurs", True, SHADOW)
        fenetre.blit(shadow_title, (title_rect.x + 3, title_rect.y + 3))
        fenetre.blit(title, title_rect)
        
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
        
        # Nb actuel grand
        nb_text = title_font.render(str(selected_players), True, (255, 255, 0))
        nb_rect = nb_text.get_rect(center=(960, 350))
        shadow_nb = title_font.render(str(selected_players), True, SHADOW)
        fenetre.blit(shadow_nb, (nb_rect.x + 3, nb_rect.y + 3))
        fenetre.blit(nb_text, nb_rect)
        
        # Bouton START vert
        start_rect = pygame.Rect(fenetre.get_width()//2 - 120, 500, 240, 80)
        is_hover_start = start_rect.collidepoint(pygame.mouse.get_pos())
        color_start = HOVER_BLUE if is_hover_start else (0, 255, 0)
        pygame.draw.rect(fenetre, color_start, start_rect, border_radius=16)
        start_text = button_font.render("START", True, BLANC)
        start_rect_text = start_text.get_rect(center=start_rect.center)
        shadow_start = button_font.render("START", True, SHADOW)
        fenetre.blit(shadow_start, (start_rect_text.x + 2, start_rect_text.y + 2))
        fenetre.blit(start_text, start_rect_text)
        
        pygame.display.flip()
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if minus_rect.collidepoint(mouse_pos) and selected_players > 1:
                    selected_players -= 1
                elif plus_rect.collidepoint(mouse_pos) and selected_players < 4:
                    selected_players += 1
                elif start_rect.collidepoint(mouse_pos):
                    # Init tours.py : Crée players + TurnManager
                    players = [Player(f"Joueur {i+1}") for i in range(selected_players)]
                    turn_manager = TurnManager(players)
                    print(f"Tours init: {len(players)} joueurs, période 1")
                    running = False
    
    return turn_manager, players
        
    return turn_manager, players

# Exemple d'utilisation (à intégrer dans game.py)
# turn_manager, players = select_players(screen, clock)
# if turn_manager:
#     print(f"Tour {turn_manager.turn_number}, période {turn_manager.period}")

