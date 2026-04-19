from __future__ import annotations

import random

import pygame

import tours


def clamp_color(color):
    return tuple(max(0, min(255, int(channel))) for channel in color[:3])


def brighten_color(color, amount):
    base = clamp_color(color)
    return tuple(min(255, channel + amount) for channel in base)


class Hexagone:
    def __init__(self, q, r, type_terrain, tuile_surface=None):
        self.q = q
        self.r = r
        self.type_terrain = type_terrain
        self.tuile = tuile_surface
        self.selection_lift = 0.0
        self.target_lift = 0.0

    def get_pixel_pos(self, size=32, vertical_spacing=42):
        x = self.q * size * 1.0
        if self.r % 2 == 1:
            x += size * 0.5
        y = self.r * vertical_spacing * 0.5
        return int(x), int(y)


class Carte:
    def __init__(self, largeur, hauteur, terrain_tiles, terrain_variants, tile_font):
        self.largeur = largeur
        self.hauteur = hauteur
        self.tuiles = terrain_tiles
        self.terrain_variantes = terrain_variants
        self.tile_font = tile_font
        self.hexagones = []
        self.hex_lookup = {}
        self.selected_hex = None
        self._mask_cache = {}
        self.generer_carte()

    def update_selection_animation(self):
        for hex_obj in self.hexagones:
            delta = hex_obj.target_lift - hex_obj.selection_lift
            if abs(delta) < 0.01:
                hex_obj.selection_lift = hex_obj.target_lift
            else:
                hex_obj.selection_lift += delta * 0.22

    def select_hex(self, hex_obj):
        if self.selected_hex is not None and self.selected_hex is not hex_obj:
            self.selected_hex.target_lift = 0.0

        if hex_obj is None:
            self.selected_hex = None
            return

        self.selected_hex = hex_obj
        self.selected_hex.target_lift = 1.0

    def generer_carte(self):
        self.hexagones.clear()
        self.hex_lookup.clear()

        terrain_pool = ["herbe"] * 45 + ["foret"] * 28 + ["montagne"] * 18 + ["eau"] * 9
        n_seeds = max(28, (self.largeur * self.hauteur) // 10)
        seeds = [
            (
                random.randint(0, self.largeur - 1),
                random.randint(0, self.hauteur - 1),
                random.choice(terrain_pool),
            )
            for _ in range(n_seeds)
        ]

        noise_scale = (self.largeur + self.hauteur) / 28.0
        terrain_grid = {}
        for r in range(self.hauteur):
            for q in range(self.largeur):
                best_type = "herbe"
                min_dist = float("inf")
                for sq, sr, st in seeds:
                    d = ((q - sq) ** 2 + (r - sr) ** 2) ** 0.5
                    d += random.gauss(0, noise_scale)
                    if d < min_dist:
                        min_dist = d
                        best_type = st
                terrain_grid[(q, r)] = best_type

        for _ in range(2):
            new_grid = {}
            for r in range(self.hauteur):
                for q in range(self.largeur):
                    neighbors = self._get_existing_neighbors(q, r, terrain_grid)
                    if len(neighbors) < 2:
                        new_grid[(q, r)] = terrain_grid[(q, r)]
                        continue
                    counts = {}
                    for terrain_type in neighbors:
                        counts[terrain_type] = counts.get(terrain_type, 0) + 1
                    majority = max(counts, key=counts.get)
                    if counts[majority] >= 5:
                        new_grid[(q, r)] = majority
                    else:
                        new_grid[(q, r)] = terrain_grid[(q, r)]
            terrain_grid = new_grid

        for r in range(self.hauteur):
            for q in range(self.largeur):
                type_terrain = terrain_grid[(q, r)]
                tuile_surface = self._choose_tile_surface(type_terrain)
                hex_obj = Hexagone(q, r, type_terrain, tuile_surface=tuile_surface)
                self.hexagones.append(hex_obj)
                self.hex_lookup[(q, r)] = hex_obj

    def _choose_tile_surface(self, type_terrain):
        variantes = self.terrain_variantes.get(type_terrain, [self.tuiles[type_terrain]])
        return random.choice(variantes)

    def _get_existing_neighbors(self, q, r, terrain_grid):
        if r % 2 == 0:
            offsets = [(-1, 0), (1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1)]
        else:
            offsets = [(-1, 0), (1, 0), (1, -1), (0, -1), (1, 1), (0, 1)]

        found = []
        for dq, dr in offsets:
            nq, nr = q + dq, r + dr
            if (nq, nr) in terrain_grid:
                found.append(terrain_grid[(nq, nr)])
        return found

    def get_hex(self, q, r):
        return self.hex_lookup.get((q, r))

    def get_neighbors(self, hex_obj):
        if hex_obj.r % 2 == 0:
            offsets = [(-1, 0), (1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1)]
        else:
            offsets = [(-1, 0), (1, 0), (1, -1), (0, -1), (1, 1), (0, 1)]

        neighbors = []
        for dq, dr in offsets:
            neighbor = self.get_hex(hex_obj.q + dq, hex_obj.r + dr)
            if neighbor is not None:
                neighbors.append(neighbor)
        return neighbors

    def get_hexes_in_radius(self, center_hex, radius):
        visited = {(center_hex.q, center_hex.r)}
        frontier = [center_hex]
        results = [center_hex]

        for _ in range(radius):
            next_frontier = []
            for hex_obj in frontier:
                for neighbor in self.get_neighbors(hex_obj):
                    key = (neighbor.q, neighbor.r)
                    if key not in visited:
                        visited.add(key)
                        next_frontier.append(neighbor)
                        results.append(neighbor)
            frontier = next_frontier

        return results

    def get_world_bounds(self):
        if not self.hexagones:
            return pygame.Rect(0, 0, 0, 0)

        left = min(hex_obj.get_pixel_pos()[0] for hex_obj in self.hexagones)
        top = min(hex_obj.get_pixel_pos()[1] for hex_obj in self.hexagones)
        right = max(hex_obj.get_pixel_pos()[0] + hex_obj.tuile.get_width() for hex_obj in self.hexagones)
        bottom = max(hex_obj.get_pixel_pos()[1] + hex_obj.tuile.get_height() for hex_obj in self.hexagones)
        return pygame.Rect(left, top, right - left, bottom - top)

    def dessiner(self, surface, territory_lookup=None, placed_buildings=None, offset_x=0, offset_y=0, active_player=None):
        self.update_selection_animation()
        hexagones_tries = sorted(self.hexagones, key=lambda h: (h.get_pixel_pos()[1], h.get_pixel_pos()[0]))

        for hex_obj in hexagones_tries:
            x, y = hex_obj.get_pixel_pos()
            x += offset_x
            y += offset_y
            y -= int(hex_obj.selection_lift * 10)
            if -50 < x < surface.get_width() + 50 and -50 < y < surface.get_height() + 50:
                try:
                    surface.blit(hex_obj.tuile, (x, y))
                    if territory_lookup is not None:
                        owner_player = territory_lookup.get((hex_obj.q, hex_obj.r))
                        if owner_player is not None:
                            self.draw_territory_overlay(
                                surface,
                                hex_obj,
                                x,
                                y,
                                owner_player.color,
                                is_active_owner=(active_player is owner_player),
                            )
                    if placed_buildings is not None:
                        building_info = placed_buildings.get((hex_obj.q, hex_obj.r))
                        if building_info is not None:
                            self.draw_building_marker(surface, hex_obj, x, y, building_info)
                except Exception:
                    pass

    def draw_territory_overlay(self, surface, hex_obj, x, y, color, is_active_owner=False):
        if color is None:
            return

        tile = hex_obj.tuile
        mask = self._get_mask_for_tile(tile)
        w, h = tile.get_size()
        cut_y = int(h * 0.62)
        base_color = clamp_color(color)
        overlay_alpha = 46 if is_active_owner else 92
        overlay_key = (id(tile), "territory", base_color, is_active_owner)

        if overlay_key not in self._mask_cache:
            overlay = pygame.Surface(tile.get_size(), pygame.SRCALPHA)
            for px in range(w):
                for py in range(cut_y):
                    if mask.get_at((px, py)):
                        overlay.set_at((px, py), (*base_color, overlay_alpha))
            self._mask_cache[overlay_key] = overlay

        overlay = self._mask_cache[overlay_key]
        surface.blit(overlay, (x, y))

        if not is_active_owner:
            outline_key = (id(tile), "territory_outline", base_color)
            if outline_key not in self._mask_cache:
                top_mask = pygame.mask.from_surface(overlay, threshold=1)
                self._mask_cache[outline_key] = top_mask.outline()

            outline = self._mask_cache[outline_key]
            if len(outline) > 1:
                max_oy = max(oy for _, oy in outline)
                points = [(x + ox, y + oy) for ox, oy in outline if oy < max_oy - 1]
                if len(points) > 1:
                    pygame.draw.lines(surface, brighten_color(base_color, 24), False, points, 2)

    def draw_building_marker(self, surface, hex_obj, x, y, building_info):
        owner_player, placed_building = building_info
        badge_text = tours.get_building_short(placed_building.building)
        badge_color = owner_player.color if owner_player and owner_player.color is not None else (110, 110, 110)
        text_surf = self.tile_font.render(badge_text, True, (0, 0, 0))
        badge_w = max(22, text_surf.get_width() + 10)
        badge_h = text_surf.get_height() + 6
        badge_rect = pygame.Rect(0, 0, badge_w, badge_h)
        badge_rect.center = (x + hex_obj.tuile.get_width() // 2, y + int(hex_obj.tuile.get_height() * 0.7))

        badge = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
        pygame.draw.rect(badge, (*badge_color, 220), badge.get_rect(), border_radius=8)
        pygame.draw.rect(badge, (0, 0, 0, 150), badge.get_rect(), width=1, border_radius=8)
        surface.blit(badge, badge_rect)
        text_rect = text_surf.get_rect(center=badge_rect.center)
        surface.blit(text_surf, text_rect)

    def draw_buildable_overlay(self, surface, hex_obj, x, y, color=(255, 255, 0)):
        tile = hex_obj.tuile
        mask = self._get_mask_for_tile(tile)
        w, h = tile.get_size()
        cut_y = int(h * 0.62)
        color = clamp_color(color)
        fill_color = (*brighten_color(color, 20), 80)
        outline_color = brighten_color(color, 28)

        tile_key = id(tile)
        overlay_key = (tile_key, "buildable_overlay62", color)
        if overlay_key not in self._mask_cache:
            top_overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            for cx in range(w):
                for yy in range(cut_y):
                    if mask.get_at((cx, yy)):
                        top_overlay.set_at((cx, yy), fill_color)
            self._mask_cache[overlay_key] = top_overlay

        top_overlay = self._mask_cache[overlay_key]
        surface.blit(top_overlay, (x, y))

        outline_key = (tile_key, "buildable_outline62", color)
        if outline_key not in self._mask_cache:
            top_mask = pygame.mask.from_surface(top_overlay, threshold=1)
            self._mask_cache[outline_key] = top_mask.outline()

        outline = self._mask_cache[outline_key]
        if len(outline) > 1:
            max_oy = max(oy for _, oy in outline)
            points = [(x + ox, y + oy) for ox, oy in outline if oy < max_oy - 1]
            if len(points) > 1:
                pygame.draw.lines(surface, outline_color, False, points, 2)

    def _get_mask_for_tile(self, tile_surface):
        key = id(tile_surface)
        if key not in self._mask_cache:
            self._mask_cache[key] = pygame.mask.from_surface(tile_surface, threshold=10)
        return self._mask_cache[key]

    def get_hex_at_pixel(self, px, py, offset_x=0, offset_y=0):
        hexagones_tries = sorted(self.hexagones, key=lambda h: (h.get_pixel_pos()[1], h.get_pixel_pos()[0]))
        for hex_obj in reversed(hexagones_tries):
            x, y = hex_obj.get_pixel_pos()
            x += offset_x
            y += offset_y
            y -= int(hex_obj.selection_lift * 10)
            tile = hex_obj.tuile
            rect = pygame.Rect(x, y, tile.get_width(), tile.get_height())
            if not rect.collidepoint(px, py):
                continue
            lx = px - x
            ly = py - y
            mask = self._get_mask_for_tile(tile)
            if 0 <= lx < tile.get_width() and 0 <= ly < tile.get_height() and mask.get_at((int(lx), int(ly))):
                return hex_obj
        return None

    def draw_hex_highlight(self, surface, hex_obj, offset_x=0, offset_y=0, color=(255, 255, 0)):
        if hex_obj is None:
            return
        x, y = hex_obj.get_pixel_pos()
        x += offset_x
        y += offset_y
        y -= int(hex_obj.selection_lift * 10)
        tile = hex_obj.tuile
        mask = self._get_mask_for_tile(tile)

        w, h = tile.get_size()
        cut_y = int(h * 0.62)
        color = clamp_color(color)
        fill_color = (*brighten_color(color, 20), 80)
        outline_color = brighten_color(color, 28)

        tile_key = id(tile)
        overlay_key = (tile_key, "overlay62", color)
        if overlay_key not in self._mask_cache:
            top_overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            for cx in range(w):
                for yy in range(cut_y):
                    if mask.get_at((cx, yy)):
                        top_overlay.set_at((cx, yy), fill_color)
            self._mask_cache[overlay_key] = top_overlay

        top_overlay = self._mask_cache[overlay_key]
        surface.blit(top_overlay, (x, y))

        outline_key = (tile_key, "overlay62_outline", color)
        if outline_key not in self._mask_cache:
            top_mask = pygame.mask.from_surface(top_overlay, threshold=1)
            self._mask_cache[outline_key] = top_mask.outline()
        outline = self._mask_cache[outline_key]
        if len(outline) > 1:
            max_oy = max(oy for _, oy in outline)
            points = [(x + ox, y + oy) for ox, oy in outline if oy < max_oy - 1]
            if len(points) > 1:
                pygame.draw.lines(surface, outline_color, False, points, 2)
