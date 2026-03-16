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
  

def draw_resources_overlay(screen, player_resources):
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
    # Top-right positioning
    win_w, win_h = screen.get_size()
    x = win_w - 200  # 200px margin from right
    y = 10
    for i, line in enumerate(lines):
        shadow = font.render(line, True, (0, 0, 0))
        text = font.render(line, True, (255, 255, 255))
        screen.blit(shadow, (x + 4, y + i * 28 + 4))
        screen.blit(text, (x, y + i * 28))
