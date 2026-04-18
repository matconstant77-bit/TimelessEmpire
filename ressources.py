import pygame


class PlayerResources:
    def __init__(self, gold=0, money=0, food=0, wood=0):
        self.gold = gold
        self.money = money
        self.food = food
        self.wood = wood

    def add_resource(self, resource, amount):
        if hasattr(self, resource):
            setattr(self, resource, getattr(self, resource) + amount)

    def remove_resource(self, resource, amount):
        if hasattr(self, resource):
            current = getattr(self, resource)
            setattr(self, resource, max(0, current - amount))

    def get_resources(self):
        return {
            'gold': self.gold,
            'money': self.money,
            'food': self.food,
            'wood': self.wood
        }

    def __str__(self):
        return f"Gold: {self.gold}, Money: {self.money}, Food: {self.food}, Wood: {self.wood}"


def draw_resources_overlay(screen, player_resources, panel_rect=None):
    """Handle PlayerResources obj or dict (tours.Player.resources)."""
    if hasattr(player_resources, 'get_resources'):
        resources = player_resources.get_resources()
    else:
        resources = player_resources  # dict from tours.Player.resources

    lines = [
        f"Gold: {resources.get('gold', 0)}",
        f"Money: {resources.get('money', 0)}",
        f"Food: {resources.get('food', 0)}",
        f"Wood: {resources.get('wood', 0)}"
    ]

    font = pygame.font.SysFont('Arial', 24)
    title_font = pygame.font.SysFont('Arial', 20, bold=True)
    line_gap = 6
    pad_x = 16
    pad_y = 14

    title = title_font.render("Ressources", True, (245, 220, 120))
    line_surfaces = [font.render(line, True, (255, 255, 255)) for line in lines]
    shadow_surfaces = [font.render(line, True, (0, 0, 0)) for line in lines]

    content_width = max([title.get_width()] + [surf.get_width() for surf in line_surfaces])
    line_height = font.get_height()
    panel_width = content_width + pad_x * 2
    panel_height = pad_y * 2 + title.get_height() + 10 + len(lines) * line_height + (len(lines) - 1) * line_gap

    win_w, win_h = screen.get_size()
    if panel_rect is None:
        x = win_w - panel_width - 18
        y = 18
        draw_w = panel_width
        draw_h = panel_height
    else:
        draw_w = max(panel_width, panel_rect.width)
        draw_h = max(panel_height, panel_rect.height)
        x = panel_rect.x
        y = panel_rect.y

    panel = pygame.Surface((draw_w, draw_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (6, 12, 22, 185), panel.get_rect(), border_radius=16)
    pygame.draw.rect(panel, (210, 210, 210, 120), panel.get_rect(), width=1, border_radius=16)
    screen.blit(panel, (x, y))

    title_rect = title.get_rect(midtop=(x + draw_w // 2, y + pad_y))
    screen.blit(title, title_rect)

    text_y = title_rect.bottom + 10
    for index, text in enumerate(line_surfaces):
        line_y = text_y + index * (line_height + line_gap)
        screen.blit(shadow_surfaces[index], (x + pad_x + 2, line_y + 2))
        screen.blit(text, (x + pad_x, line_y))

    return pygame.Rect(x, y, draw_w, draw_h)
