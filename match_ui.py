import pygame

import tours


class HudFonts:
    def __init__(self, hud, small, tiny, tile, timer):
        self.hud = hud
        self.small = small
        self.tiny = tiny
        self.tile = tile
        self.timer = timer


class HudTheme:
    def __init__(self, white, shadow, panel_bg, panel_border, hover_blue):
        self.white = white
        self.shadow = shadow
        self.panel_bg = panel_bg
        self.panel_border = panel_border
        self.hover_blue = hover_blue


class GameLayout:
    def __init__(self, sidebar_rect, resources_rect, selected_rect, map_rect, map_base_offset, footer_rect):
        self.sidebar_rect = sidebar_rect
        self.resources_rect = resources_rect
        self.selected_rect = selected_rect
        self.map_rect = map_rect
        self.map_base_offset = map_base_offset
        self.footer_rect = footer_rect

    def __getitem__(self, key):
        return getattr(self, key)


def get_game_layout(
    surface,
    hud_padding,
    header_height,
    footer_height,
    map_inset,
    sidebar_gap,
    selected_panel_drop,
    end_turn_bottom_margin,
    end_turn_panel_gap,
    end_turn_button_height,
):
    # La carte garde sa zone a gauche, les panneaux de jeu restent dans la colonne de droite.
    win_w, win_h = surface.get_size()
    sidebar_w = min(390, max(320, int(win_w * 0.28)))
    sidebar_rect = pygame.Rect(
        win_w - sidebar_w - hud_padding,
        hud_padding,
        sidebar_w,
        win_h - hud_padding * 2,
    )

    map_rect = pygame.Rect(
        hud_padding,
        header_height + hud_padding,
        sidebar_rect.x - hud_padding * 2,
        win_h - header_height - footer_height - hud_padding * 2,
    )

    resources_rect = pygame.Rect(sidebar_rect.x, sidebar_rect.y, sidebar_rect.width, 146)
    selected_top = resources_rect.bottom + sidebar_gap + selected_panel_drop
    end_turn_top = sidebar_rect.bottom - end_turn_bottom_margin - end_turn_button_height
    selected_height = max(120, end_turn_top - end_turn_panel_gap - selected_top)
    selected_rect = pygame.Rect(sidebar_rect.x, selected_top, sidebar_rect.width, selected_height)
    footer_rect = pygame.Rect(hud_padding, map_rect.bottom + 12, map_rect.width, footer_height - 12)
    map_offset = (map_rect.x + map_inset, map_rect.y + map_inset)

    return GameLayout(
        sidebar_rect=sidebar_rect,
        resources_rect=resources_rect,
        selected_rect=selected_rect,
        map_rect=map_rect,
        map_base_offset=map_offset,
        footer_rect=footer_rect,
    )


def draw_panel_background(surface, rect, theme, fill=None, border=None, radius=16):
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, fill or theme.panel_bg, panel.get_rect(), border_radius=radius)
    pygame.draw.rect(panel, border or theme.panel_border, panel.get_rect(), width=1, border_radius=radius)
    surface.blit(panel, rect)
    return rect


def draw_info_panel(surface, texts, anchor, theme, fonts, align="topleft", font=None):
    if isinstance(texts, str):
        texts = [texts]

    font = font or fonts.hud
    rendered = [font.render(text, True, theme.white) for text in texts]
    shadows = [font.render(text, True, theme.shadow) for text in texts]

    pad_x = 14
    pad_y = 10
    line_gap = 6
    panel_width = max(surf.get_width() for surf in rendered) + pad_x * 2
    panel_height = sum(surf.get_height() for surf in rendered) + pad_y * 2 + line_gap * (len(rendered) - 1)

    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (6, 12, 22, 175), panel.get_rect(), border_radius=14)
    pygame.draw.rect(panel, (210, 210, 210, 120), panel.get_rect(), width=1, border_radius=14)

    rect = panel.get_rect(**{align: anchor})
    surface.blit(panel, rect)

    current_y = rect.y + pad_y
    for shadow, text in zip(shadows, rendered):
        text_rect = text.get_rect(x=rect.x + pad_x, y=current_y)
        surface.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text, text_rect)
        current_y += text.get_height() + line_gap

    return rect


def draw_timer_panel(surface, remaining_ms, theme, fonts, hud_padding, midtop=None):
    mins = remaining_ms // 60000
    secs = (remaining_ms % 60000) // 1000
    timer_text = f"{mins:02d}:{secs:02d}"
    timer_surf = fonts.timer.render(timer_text, False, theme.white)
    pad_x, pad_y = 14, 8
    box_w = timer_surf.get_width() + pad_x * 2
    box_h = timer_surf.get_height() + pad_y * 2
    box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    pygame.draw.rect(box_surf, (6, 12, 22, 190), (0, 0, box_w, box_h), border_radius=14)
    pygame.draw.rect(box_surf, (210, 210, 210, 130), (0, 0, box_w, box_h), width=1, border_radius=14)

    if midtop is None:
        midtop = (surface.get_width() // 2, hud_padding)
    box_rect = box_surf.get_rect(midtop=midtop)
    surface.blit(box_surf, box_rect)
    timer_rect = timer_surf.get_rect(center=box_rect.center)
    surface.blit(timer_surf, timer_rect)


def draw_action_button(
    surface,
    rect,
    text,
    mouse_pos,
    theme,
    fonts,
    enabled=True,
    base_color=(74, 98, 184),
    font=None,
    right_text=None,
    right_font=None,
):
    font = font or fonts.small
    if enabled:
        is_hover = rect.collidepoint(mouse_pos)
        color = theme.hover_blue if is_hover else base_color
        border = (235, 235, 235, 120)
    else:
        color = (70, 74, 90)
        border = (150, 150, 150, 80)

    button_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
    fill_color = color if len(color) == 4 else (*color, 220)
    pygame.draw.rect(button_surface, fill_color, button_surface.get_rect(), border_radius=12)
    pygame.draw.rect(button_surface, border, button_surface.get_rect(), width=1, border_radius=12)
    surface.blit(button_surface, rect)

    text_color = theme.white if enabled else (210, 210, 210)
    text_surf = font.render(text, True, text_color)
    shadow = font.render(text, True, theme.shadow)

    if right_text:
        right_font = right_font or font
        text_rect = text_surf.get_rect(midleft=(rect.x + 12, rect.centery))
        surface.blit(shadow, (text_rect.x + 1, text_rect.y + 1))
        surface.blit(text_surf, text_rect)

        right_surf = right_font.render(right_text, True, text_color)
        right_shadow = right_font.render(right_text, True, theme.shadow)
        right_rect = right_surf.get_rect(midright=(rect.right - 10, rect.centery))
        surface.blit(right_shadow, (right_rect.x + 1, right_rect.y + 1))
        surface.blit(right_surf, right_rect)
    else:
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(shadow, (text_rect.x + 1, text_rect.y + 1))
        surface.blit(text_surf, text_rect)


def draw_selected_hex_panel(
    surface,
    mouse_pos,
    panel_rect,
    selected_hex,
    active_player,
    turn_manager,
    get_territory_owner_at_hex,
    get_building_entry_at_hex,
    theme,
    fonts,
    extra_lines=None,
    extra_actions=None,
):
    # Ce panneau affiche a la fois les constructions et les actions diplomatiques/attaque.
    extra_lines = extra_lines or []
    extra_actions = extra_actions or []
    action_rects = []
    available_actions = []
    info_line_count = 0
    owner_player = None
    placed_building = None
    current_building = None
    territory_owner = None

    if turn_manager and selected_hex:
        territory_owner = get_territory_owner_at_hex(selected_hex)
        owner_player, placed_building = get_building_entry_at_hex(selected_hex)
        current_building = placed_building.building if placed_building else None
        if territory_owner is active_player:
            available_actions = turn_manager.get_available_buildings(selected_hex.type_terrain, current_building)
        info_line_count = 5 if current_building else 4

    action_count = len(available_actions) + len(extra_actions)
    base_height = 92 if not selected_hex else 86 + (info_line_count + len(extra_lines)) * 28
    panel_h = min(panel_rect.height, base_height + action_count * 44)
    panel_rect = pygame.Rect(panel_rect.x, panel_rect.y, panel_rect.width, panel_h)

    draw_panel_background(surface, panel_rect, theme)

    title = fonts.small.render("Case selectionnee", True, (245, 220, 120))
    title_rect = title.get_rect(x=panel_rect.x + 16, y=panel_rect.y + 14)
    surface.blit(title, title_rect)

    if not selected_hex:
        helper = fonts.tiny.render("Cliquez sur une case pour voir ses options.", True, theme.white)
        helper_rect = helper.get_rect(x=panel_rect.x + 16, y=title_rect.bottom + 18)
        surface.blit(helper, helper_rect)
        return action_rects

    terrain_labels = {
        "herbe": "Plaine",
        "foret": "Foret",
        "montagne": "Montagne",
        "eau": "Eau",
    }

    owner_name = owner_player.name if owner_player else "Aucun"
    zone_label = "Votre territoire" if territory_owner is active_player else "Neutre"
    if territory_owner and territory_owner is not active_player:
        zone_label = f"Zone de {territory_owner.name}"
    building_label = tours.get_building_label(current_building)
    info_lines = [
        f"Terrain : {terrain_labels.get(selected_hex.type_terrain, selected_hex.type_terrain)}",
        f"Zone : {zone_label}",
        f"Batiment : {building_label}",
        f"Occupant : {owner_name}",
    ]

    if current_building:
        info_lines.append("Bonus : " + tours.get_building_income_text(current_building))
    info_lines.extend(extra_lines)

    line_y = title_rect.bottom + 14
    for line in info_lines:
        line_surf = fonts.tiny.render(line, True, theme.white)
        surface.blit(line_surf, (panel_rect.x + 16, line_y))
        line_y += line_surf.get_height() + 6

    blocked_message = ""
    if selected_hex.type_terrain == "eau":
        blocked_message = "Aucune construction possible sur l'eau."

    elif territory_owner is None:
        blocked_message = "Construisez d'abord dans votre territoire."

    elif territory_owner and active_player and territory_owner.name != active_player.name:
        blocked_message = "Construction impossible dans cette zone."

    elif not available_actions and not extra_actions:
        blocked_message = "Pas d'amelioration disponible ici."

    for action_index, building_id in enumerate(available_actions):
        button_rect = pygame.Rect(panel_rect.x + 16, line_y + 8 + action_index * 44, panel_rect.width - 32, 36)
        cost_text = tours.format_resource_bundle_short(tours.get_building_definition(building_id)["cost"])
        draw_action_button(
            surface,
            button_rect,
            tours.get_building_label(building_id),
            mouse_pos,
            theme,
            fonts,
            enabled=True,
            font=fonts.tiny,
            right_text=cost_text,
            right_font=fonts.tile,
        )
        action_rects.append((button_rect, ("build", building_id)))

    rendered_action_count = len(available_actions)
    for extra_index, action in enumerate(extra_actions):
        button_rect = pygame.Rect(
            panel_rect.x + 16,
            line_y + 8 + (rendered_action_count + extra_index) * 44,
            panel_rect.width - 32,
            36,
        )
        draw_action_button(
            surface,
            button_rect,
            action["label"],
            mouse_pos,
            theme,
            fonts,
            enabled=action.get("enabled", True),
            base_color=action.get("base_color", (74, 98, 184)),
            font=fonts.tiny,
            right_text=action.get("right_text"),
            right_font=fonts.tile,
        )
        action_rects.append((button_rect, action["payload"]))

    if blocked_message and not action_rects:
        blocked = fonts.tiny.render(blocked_message, True, (220, 220, 220))
        surface.blit(blocked, (panel_rect.x + 16, line_y + 8))

    return action_rects


def draw_end_turn_button(
    surface,
    mouse_pos,
    sidebar_rect,
    theme,
    fonts,
    end_turn_button_height,
    end_turn_bottom_margin,
):
    btn_w = min(240, max(180, int(surface.get_width() * 0.18)))
    rect = pygame.Rect(0, 0, btn_w, end_turn_button_height)
    rect.midbottom = (sidebar_rect.centerx, sidebar_rect.bottom - end_turn_bottom_margin)
    draw_action_button(surface, rect, "Fin du tour", mouse_pos, theme, fonts, enabled=True, base_color=(0, 156, 88))
    return rect


def draw_status_banner(surface, anchor, status_message, status_message_until, now_ticks, theme, fonts):
    if status_message and now_ticks < status_message_until:
        draw_info_panel(
            surface,
            status_message,
            anchor,
            theme,
            fonts,
            align="midbottom",
            font=fonts.small,
        )
