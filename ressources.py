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
            "gold": self.gold,
            "money": self.money,
            "food": self.food,
            "wood": self.wood,
        }

    def __str__(self):
        return f"Gold: {self.gold}, Money: {self.money}, Food: {self.food}, Wood: {self.wood}"


def get_resource_snapshot(player_resources):
    if player_resources is None:
        return {"gold": 0, "money": 0, "food": 0, "wood": 0}
    if hasattr(player_resources, "get_resources"):
        return player_resources.get_resources()
    return {
        "gold": player_resources.get("gold", 0),
        "money": player_resources.get("money", 0),
        "food": player_resources.get("food", 0),
        "wood": player_resources.get("wood", 0),
    }


def draw_resources_overlay(screen, player_resources, area=None, title="Ressources"):
    resources = get_resource_snapshot(player_resources)
    lines = [
        f"Or: {resources.get('gold', 0)}",
        f"Nourriture: {resources.get('food', 0)}",
        f"Bois: {resources.get('wood', 0)}",
        f"Argent: {resources.get('money', 0)}",
    ]

    title_font = pygame.font.SysFont("arial", 26, bold=True)
    line_font = pygame.font.SysFont("arial", 22)

    if area is None:
        win_w, _ = screen.get_size()
        area = pygame.Rect(win_w - 230, 10, 210, 150)

    panel = pygame.Surface((area.width, area.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (12, 18, 34, 210), panel.get_rect(), border_radius=18)
    pygame.draw.rect(panel, (100, 145, 235, 220), panel.get_rect(), width=2, border_radius=18)

    title_surf = title_font.render(title, True, (255, 255, 255))
    panel.blit(title_surf, (14, 10))

    for idx, line in enumerate(lines):
        y = 46 + idx * 24
        shadow = line_font.render(line, True, (0, 0, 0))
        text = line_font.render(line, True, (235, 240, 255))
        panel.blit(shadow, (16, y + 2))
        panel.blit(text, (14, y))

    screen.blit(panel, area.topleft)
