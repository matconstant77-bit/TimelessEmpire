from __future__ import annotations


def get_building_entry_at_coords(turn_manager, q, r):
    if not turn_manager:
        return None, None

    for player in turn_manager.players:
        for placed_building in player.buildings:
            if placed_building.q == q and placed_building.r == r:
                return player, placed_building

    return None, None


def get_building_entry_at_hex(turn_manager, hex_obj):
    if hex_obj is None:
        return None, None
    return get_building_entry_at_coords(turn_manager, hex_obj.q, hex_obj.r)


def get_territory_owner_at_coords(turn_manager, q, r):
    if not turn_manager:
        return None

    for player in turn_manager.players:
        if player.owns_tile(q, r):
            return player

    return None


def get_territory_owner_at_hex(turn_manager, hex_obj):
    if hex_obj is None:
        return None
    return get_territory_owner_at_coords(turn_manager, hex_obj.q, hex_obj.r)


def get_territory_lookup(turn_manager):
    territory_lookup = {}
    if not turn_manager:
        return territory_lookup

    for player in turn_manager.players:
        for q, r in player.owned_tiles:
            territory_lookup[(q, r)] = player

    return territory_lookup


def get_placed_buildings_lookup(turn_manager):
    placed_buildings = {}
    if not turn_manager:
        return placed_buildings

    for player in turn_manager.players:
        for placed_building in player.buildings:
            if placed_building.q is None or placed_building.r is None:
                continue
            placed_buildings[(placed_building.q, placed_building.r)] = (player, placed_building)

    return placed_buildings


def get_buildable_hexes_for_player(carte, turn_manager, player):
    if not carte or not turn_manager or player is None:
        return []

    buildable_hexes = []
    for q, r in player.owned_tiles:
        hex_obj = carte.get_hex(q, r)
        if hex_obj is None or hex_obj.type_terrain == "eau":
            continue

        owner_player, placed_building = get_building_entry_at_coords(turn_manager, q, r)
        if owner_player is not None and owner_player is not player:
            continue

        current_building = placed_building.building if placed_building else None
        options = turn_manager.get_available_buildings(hex_obj.type_terrain, current_building)
        if options:
            buildable_hexes.append(hex_obj)

    return buildable_hexes


def get_start_targets(player_count, largeur, hauteur):
    if player_count <= 1:
        return [(largeur // 2, hauteur // 2)]
    if player_count == 2:
        return [(largeur // 4, hauteur // 2), (largeur * 3 // 4, hauteur // 2)]
    if player_count == 3:
        return [(largeur // 4, hauteur // 3), (largeur * 3 // 4, hauteur // 3), (largeur // 2, hauteur * 2 // 3)]
    return [
        (largeur // 4, hauteur // 4),
        (largeur * 3 // 4, hauteur // 4),
        (largeur // 4, hauteur * 3 // 4),
        (largeur * 3 // 4, hauteur * 3 // 4),
    ]


def choose_starting_hexes(carte, players, starting_position_separation):
    if not carte or not players:
        return []

    land_hexes = [hex_obj for hex_obj in carte.hexagones if hex_obj.type_terrain != "eau"]
    targets = get_start_targets(len(players), carte.largeur, carte.hauteur)
    chosen_hexes = []

    for target_q, target_r in targets:
        best_hex = None
        best_score = None

        for hex_obj in land_hexes:
            too_close = any(
                ((hex_obj.q - other.q) ** 2 + (hex_obj.r - other.r) ** 2) < starting_position_separation ** 2
                for other in chosen_hexes
            )
            if too_close:
                continue

            nearby_hexes = carte.get_hexes_in_radius(hex_obj, 2)
            land_count = sum(1 for nearby in nearby_hexes if nearby.type_terrain != "eau")
            terrain_types = {nearby.type_terrain for nearby in nearby_hexes if nearby.type_terrain != "eau"}
            dist_score = (hex_obj.q - target_q) ** 2 + (hex_obj.r - target_r) ** 2
            grass_bonus = 35 if hex_obj.type_terrain == "herbe" else 0
            score = land_count * 100 + len(terrain_types) * 20 + grass_bonus - dist_score

            if best_score is None or score > best_score:
                best_score = score
                best_hex = hex_obj

        if best_hex is None:
            remaining = [hex_obj for hex_obj in land_hexes if hex_obj not in chosen_hexes]
            if remaining:
                best_hex = remaining[0]
        if best_hex is not None:
            chosen_hexes.append(best_hex)

    return chosen_hexes


def assign_starting_territories(carte, players, starting_territory_radius, starting_position_separation):
    if not carte:
        return []

    for player in players:
        player.owned_tiles.clear()

    starting_hexes = choose_starting_hexes(carte, players, starting_position_separation)
    for player, start_hex in zip(players, starting_hexes):
        starting_zone = [
            hex_obj
            for hex_obj in carte.get_hexes_in_radius(start_hex, starting_territory_radius)
            if hex_obj.type_terrain != "eau"
        ]
        player.claim_tiles((hex_obj.q, hex_obj.r) for hex_obj in starting_zone)

    if starting_hexes:
        carte.select_hex(starting_hexes[0])

    return starting_hexes


def expand_player_territory(carte, turn_manager, player, source_hex, building_id, get_building_territory_radius):
    if not carte or source_hex is None:
        return 0

    territory_radius = get_building_territory_radius(building_id)
    if building_id != "capital":
        territory_radius += 1
    claimed = 0

    for hex_obj in carte.get_hexes_in_radius(source_hex, territory_radius):
        if hex_obj.type_terrain == "eau":
            continue

        current_owner = get_territory_owner_at_coords(turn_manager, hex_obj.q, hex_obj.r)
        if current_owner is None:
            player.claim_tile(hex_obj.q, hex_obj.r)
            claimed += 1
        elif current_owner is player:
            player.claim_tile(hex_obj.q, hex_obj.r)

    return claimed
