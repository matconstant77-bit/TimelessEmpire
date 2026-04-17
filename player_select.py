import pygame
import sys
from tours import Player, TurnManager

BLANC = (255, 255, 255)
SHADOW = (0, 0, 0)
HOVER_BLUE = (0, 140, 255)


def show_lobby(fenetre, clock, players):
    """Affiche un salon d'attente local avant de lancer la partie multi."""
    title_font = pygame.font.SysFont(None, 72)
    text_font = pygame.font.SysFont(None, 40)
    small_font = pygame.font.SysFont(None, 32)

    while True:
        fenetre.fill((18, 24, 44))
        w, h = fenetre.get_size()

        title = title_font.render("Salon d'attente", True, BLANC)
        title_rect = title.get_rect(center=(w // 2, 90))
        fenetre.blit(title, title_rect)

        panel_rect = pygame.Rect(w // 2 - 360, 150, 720, 340)
        pygame.draw.rect(fenetre, (12, 16, 30), panel_rect)
        pygame.draw.rect(fenetre, (120, 160, 255), panel_rect, width=2)

        subtitle = small_font.render("Joueurs en attente:", True, BLANC)
        fenetre.blit(subtitle, (panel_rect.x + 20, panel_rect.y + 16))

        for idx, player in enumerate(players):
            line_y = panel_rect.y + 60 + idx * 58
            line_rect = pygame.Rect(panel_rect.x + 20, line_y, panel_rect.width - 40, 46)
            pygame.draw.rect(fenetre, (26, 34, 60), line_rect)
            pygame.draw.rect(fenetre, (78, 112, 190), line_rect, width=1)

            name_text = text_font.render(player.name, True, BLANC)
            fenetre.blit(name_text, (line_rect.x + 14, line_rect.y + 8))

            status_text = small_font.render("Connecte", True, (130, 255, 130))
            status_rect = status_text.get_rect(midright=(line_rect.right - 12, line_rect.centery))
            fenetre.blit(status_text, status_rect)

        launch_rect = pygame.Rect(w // 2 - 180, h - 140, 360, 70)
        back_rect = pygame.Rect(24, h - 90, 180, 52)

        launch_hover = launch_rect.collidepoint(pygame.mouse.get_pos())
        back_hover = back_rect.collidepoint(pygame.mouse.get_pos())

        pygame.draw.rect(fenetre, HOVER_BLUE if launch_hover else (0, 170, 70), launch_rect)
        pygame.draw.rect(fenetre, HOVER_BLUE if back_hover else (100, 100, 130), back_rect)

        launch_text = text_font.render("Lancer la partie", True, BLANC)
        launch_text_rect = launch_text.get_rect(center=launch_rect.center)
        fenetre.blit(launch_text, launch_text_rect)

        back_text = small_font.render("Retour", True, BLANC)
        back_text_rect = back_text.get_rect(center=back_rect.center)
        fenetre.blit(back_text, back_text_rect)

        tip = small_font.render("Tous les joueurs sont en salle. Cliquez pour commencer.", True, (190, 210, 255))
        tip_rect = tip.get_rect(center=(w // 2, h - 30))
        fenetre.blit(tip, tip_rect)

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if launch_rect.collidepoint(event.pos):
                    return True
                if back_rect.collidepoint(event.pos):
                    return False

# Menu sélection nombre joueurs (1-4), crée TurnManager/Players
def select_players(fenetre, clock):
    running = True
    selected_players = 1
    players = []
    open_time = pygame.time.get_ticks()
    click_guard_ms = 180
    
    title_font = pygame.font.SysFont(None, 72)
    button_font = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 48)
    
    while running:
        # Fond sombre menu
        fenetre.fill((0, 0, 50))
        win_w, win_h = fenetre.get_size()
        
        # Titre centré
        title = title_font.render("Multiplayer - Nb Joueurs", True, BLANC)
        title_rect = title.get_rect(center=(win_w // 2, 110))
        shadow_title = title_font.render("Multiplayer - Nb Joueurs", True, SHADOW)
        fenetre.blit(shadow_title, (title_rect.x + 3, title_rect.y + 3))
        fenetre.blit(title, title_rect)

        subtitle = button_font.render("Choisissez le nombre de joueurs", True, (200, 220, 255))
        subtitle_rect = subtitle.get_rect(center=(win_w // 2, title_rect.bottom + 40))
        fenetre.blit(subtitle, subtitle_rect)

        panel_w = min(520, win_w - 120)
        panel_h = 240
        panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
        panel_rect.center = (win_w // 2, win_h // 2 - 55)
        pygame.draw.rect(fenetre, (16, 22, 40), panel_rect, border_radius=24)
        pygame.draw.rect(fenetre, (88, 126, 210), panel_rect, width=2, border_radius=24)
         
        # Boutons +/-
        btn_size = 84
        minus_rect = pygame.Rect(0, 0, btn_size, btn_size)
        plus_rect = pygame.Rect(0, 0, btn_size, btn_size)
        minus_rect.centery = panel_rect.centery
        plus_rect.centery = panel_rect.centery
        minus_rect.centerx = panel_rect.centerx - 140
        plus_rect.centerx = panel_rect.centerx + 140
        minus_hover = minus_rect.collidepoint(pygame.mouse.get_pos())
        plus_hover = plus_rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(fenetre, HOVER_BLUE if minus_hover else (70, 96, 180), minus_rect, border_radius=20)
        pygame.draw.rect(fenetre, HOVER_BLUE if plus_hover else (70, 96, 180), plus_rect, border_radius=20)
        minus_text = small_font.render('-', True, (255, 255, 255))
        plus_text = small_font.render('+', True, (255, 255, 255))
        fenetre.blit(minus_text, minus_text.get_rect(center=minus_rect.center))
        fenetre.blit(plus_text, plus_text.get_rect(center=plus_rect.center))
         
        # Nb actuel grand
        nb_text = title_font.render(str(selected_players), True, (255, 255, 0))
        nb_rect = nb_text.get_rect(center=(panel_rect.centerx, panel_rect.centery))
        shadow_nb = title_font.render(str(selected_players), True, SHADOW)
        fenetre.blit(shadow_nb, (nb_rect.x + 3, nb_rect.y + 3))
        fenetre.blit(nb_text, nb_rect)

        count_label = button_font.render("joueur(s)", True, (200, 220, 255))
        count_label_rect = count_label.get_rect(center=(panel_rect.centerx, panel_rect.centery + 58))
        fenetre.blit(count_label, count_label_rect)
         
        # Bouton START vert
        start_rect = pygame.Rect(0, 0, 260, 80)
        start_rect.center = (win_w // 2, panel_rect.bottom + 70)
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
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if pygame.time.get_ticks() - open_time < click_guard_ms:
                    continue
                mouse_pos = event.pos
                if minus_rect.collidepoint(mouse_pos) and selected_players > 1:
                    selected_players -= 1
                elif plus_rect.collidepoint(mouse_pos) and selected_players < 4:
                    selected_players += 1
                elif start_rect.collidepoint(mouse_pos):
                    # Crée les joueurs puis passe par le salon d'attente.
                    players = [Player(f"Joueur {i+1}") for i in range(selected_players)]
                    if show_lobby(fenetre, clock, players):
                        turn_manager = TurnManager(players)
                        running = False
    
    return turn_manager, players

# Exemple d'utilisation (à intégrer dans game.py)
# turn_manager, players = select_players(screen, clock)
# if turn_manager:
#     print(f"Tour {turn_manager.turn_number}, période {turn_manager.period}")

