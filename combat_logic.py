import random

import diplomacy_logic
import tours


ATTACK_COST = {"food": 3, "gold": 1}


def make_preview(available, reason="", attack_base=0, defense_base=0):
    # Petit dictionnaire utilise par l'UI pour afficher pourquoi une attaque est possible ou non.
    return {
        "available": available,
        "reason": reason,
        "attack_base": attack_base,
        "defense_base": defense_base,
    }


def has_adjacent_owned_tile(carte, player, target_hex) -> bool:
    if carte is None or player is None or target_hex is None:
        return False
    return any(player.owns_tile(neighbor.q, neighbor.r) for neighbor in carte.get_neighbors(target_hex))


def get_attack_base(attacker) -> int:
    if attacker is None:
        return 0
    return max(0, attacker.military_power("attack"))


def get_defense_base(defender, target_building=None) -> int:
    if defender is None:
        return 0
    local_bonus = 0
    if target_building is not None:
        local_bonus += int(tours.get_building_definition(target_building.building).get("defense", 0))
        if tours.get_building_definition(target_building.building).get("is_capital"):
            local_bonus += 2
    return max(0, defender.military_power("defense") + local_bonus)


def get_attack_preview(carte, turn_manager, attacker, defender, target_hex, target_building=None):
    # Les checks restent ici pour eviter de dupliquer les regles dans game.py et dans le HUD.
    if attacker is None or defender is None or attacker is defender or target_hex is None:
        return make_preview(False, "Aucune cible ennemie valide.")
    if attacker.defeated or defender.defeated:
        return make_preview(False, "Cette attaque n'est plus valable.")
    if attacker.attack_used:
        return make_preview(False, "Attaque deja utilisee ce tour.")
    if turn_manager.get_relation(attacker, defender) != diplomacy_logic.RELATION_WAR:
        return make_preview(False, "Il faut etre en guerre pour attaquer.")
    if not has_adjacent_owned_tile(carte, attacker, target_hex):
        return make_preview(False, "La cible doit toucher votre territoire.")

    attack_base = get_attack_base(attacker)
    defense_base = get_defense_base(defender, target_building)
    if attack_base <= 0:
        return make_preview(False, "Aucune force militaire disponible.")
    missing = tours.get_missing_resources(attacker.resources, ATTACK_COST)
    if missing:
        return make_preview(False, "Cout d'attaque : " + tours.format_resource_bundle(ATTACK_COST))
    return make_preview(True, attack_base=attack_base, defense_base=defense_base)


def format_preview(preview) -> str:
    if not preview["available"]:
        return preview["reason"]
    return f"ATK {preview['attack_base']} / DEF {preview['defense_base']}"


def resolve_attack(attacker, defender, target_building=None, rng=None):
    # Combat volontairement simple : puissance des batiments + un lancer de de.
    rng = rng or random
    attack_roll = get_attack_base(attacker) + rng.randint(1, 6)
    defense_roll = get_defense_base(defender, target_building) + rng.randint(1, 6)
    success = attack_roll > defense_roll
    return {
        "success": success,
        "attack_roll": attack_roll,
        "defense_roll": defense_roll,
    }
