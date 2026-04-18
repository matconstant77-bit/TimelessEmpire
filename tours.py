from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Dict, List, Optional, Set

# ==============================
# PARAMETRES DU JEU
# ==============================

TURNS_PER_PERIOD = 5

STARTING_RESOURCES = {
    "wood": 24,
    "food": 18,
    "gold": 6,
    "money": 2,
}

BASE_RESOURCE_INCOME = {
    "wood": 1,
    "food": 1,
    "gold": 0,
    "money": 0,
}

PERIOD_NAMES = {
    1: "Prehistoire",
    2: "Moyen Age",
    3: "Temps Modernes",
    4: "Epoque Contemporaine",
    5: "Futur",
}

BUILDINGS = {
    "rock_field": {
        "label": "Champ de roche",
        "short": "CR",
        "period": 1,
        "terrain": {"montagne"},
        "cost": {"wood": 7, "food": 0, "gold": 0, "money": 0},
        "income": {"gold": 2},
        "territory_radius": 1,
        "description": "Premier site d'extraction sur montagne.",
    },
    "gathering_site": {
        "label": "Cueillette",
        "short": "CU",
        "period": 1,
        "terrain": {"herbe"},
        "cost": {"wood": 6, "food": 0, "gold": 0, "money": 0},
        "income": {"food": 2},
        "territory_radius": 1,
        "description": "Production simple de nourriture.",
    },
    "lumber_camp": {
        "label": "Camp de bucherons",
        "short": "CB",
        "period": 1,
        "terrain": {"foret"},
        "cost": {"wood": 6, "food": 0, "gold": 0, "money": 0},
        "income": {"wood": 2},
        "territory_radius": 1,
        "description": "Exploite une foret voisine.",
    },
    "mine": {
        "label": "Mine",
        "short": "MI",
        "period": 2,
        "terrain": {"montagne"},
        "cost": {"wood": 10, "food": 1, "gold": 2, "money": 0},
        "income": {"gold": 4},
        "territory_radius": 1,
        "description": "Amelioration du champ de roche.",
        "upgrades_from": "rock_field",
    },
    "fields": {
        "label": "Champs",
        "short": "CH",
        "period": 2,
        "terrain": {"herbe"},
        "cost": {"wood": 8, "food": 2, "gold": 1, "money": 0},
        "income": {"food": 5},
        "territory_radius": 1,
        "description": "Version developpee de la cueillette.",
        "upgrades_from": "gathering_site",
    },
    "sawmill": {
        "label": "Scierie",
        "short": "SC",
        "period": 2,
        "terrain": {"foret"},
        "cost": {"wood": 9, "food": 1, "gold": 1, "money": 0},
        "income": {"wood": 5},
        "territory_radius": 1,
        "description": "Traitement plus efficace du bois.",
        "upgrades_from": "lumber_camp",
    },
    "barracks": {
        "label": "Caserne",
        "short": "CA",
        "period": 2,
        "terrain": {"herbe", "foret"},
        "cost": {"wood": 12, "food": 6, "gold": 4, "money": 0},
        "income": {"gold": 1},
        "territory_radius": 1,
        "description": "Base militaire pour soldats et cavalerie.",
    },
    "livestock": {
        "label": "Elevage",
        "short": "EL",
        "period": 2,
        "terrain": {"herbe"},
        "cost": {"wood": 9, "food": 4, "gold": 1, "money": 0},
        "income": {"food": 4},
        "territory_radius": 1,
        "description": "Production alimentaire reguliere.",
    },
    "post": {
        "label": "Poste",
        "short": "PO",
        "period": 2,
        "terrain": {"herbe", "foret"},
        "cost": {"wood": 8, "food": 2, "gold": 3, "money": 0},
        "income": {"money": 2},
        "territory_radius": 1,
        "description": "Base de communication entre joueurs.",
    },
    "messenger_post": {
        "label": "Messagers et diligence",
        "short": "MD",
        "period": 3,
        "terrain": {"herbe", "foret"},
        "cost": {"wood": 10, "food": 2, "gold": 5, "money": 1},
        "income": {"money": 4},
        "territory_radius": 2,
        "description": "Evolution du poste pour messages et echanges.",
        "upgrades_from": "post",
    },
    "siege_workshop": {
        "label": "Batiments de siege",
        "short": "BS",
        "period": 3,
        "terrain": {"herbe", "foret"},
        "cost": {"wood": 14, "food": 7, "gold": 7, "money": 0},
        "income": {"gold": 2},
        "territory_radius": 2,
        "description": "Renforce la caserne avec armes de siege.",
        "upgrades_from": "barracks",
    },
    "printing_press": {
        "label": "Imprimerie",
        "short": "IM",
        "period": 3,
        "terrain": {"herbe"},
        "cost": {"wood": 12, "food": 2, "gold": 6, "money": 0},
        "income": {"money": 2},
        "gold_to_money": 1,
        "gold_to_money_ratio": 3,
        "territory_radius": 1,
        "description": "Transforme un peu d'or en argent a chaque tour.",
    },
    "modern_base": {
        "label": "Aviation et vehicules",
        "short": "AV",
        "period": 4,
        "terrain": {"herbe", "foret"},
        "cost": {"wood": 18, "food": 8, "gold": 10, "money": 4},
        "income": {"gold": 3, "money": 2},
        "territory_radius": 2,
        "description": "Evolution moderne de la caserne.",
        "upgrades_from": "siege_workshop",
    },
    "city": {
        "label": "Ville fortifiee",
        "short": "VI",
        "period": 4,
        "terrain": {"herbe"},
        "cost": {"wood": 16, "food": 8, "gold": 8, "money": 4},
        "income": {"food": 3, "money": 4},
        "territory_radius": 2,
        "description": "Gestion de la population et des fortifications.",
    },
}

BUILDING_ORDER = [
    "rock_field",
    "gathering_site",
    "lumber_camp",
    "mine",
    "fields",
    "sawmill",
    "barracks",
    "livestock",
    "post",
    "messenger_post",
    "siege_workshop",
    "printing_press",
    "modern_base",
    "city",
]

RESOURCE_CARDS = [
    {"name": "Reserve de bois", "effect": {"wood": 10}},
    {"name": "Chasse abondante", "effect": {"food": 10}},
    {"name": "Mine d'or decouverte", "effect": {"gold": 6}},
    {"name": "Caravane marchande", "effect": {"wood": 5, "food": 5, "money": 3}},
]

BUILDING_CARDS = [
    {"name": "Construction rapide", "building": "gathering_site"},
    {"name": "Caserne offerte", "building": "barracks"},
]

MALUS_CARDS = [
    {"name": "Incendie", "type": "fire"},
    {"name": "Tempete", "type": "storm"},
    {"name": "Sabotage", "type": "destroy_building"},
    {"name": "Voleurs", "type": "steal_gold"},
    {"name": "Batiment piege", "type": "trap_building"},
]


def ensure_resource_keys(resources: Dict[str, int]) -> Dict[str, int]:
    for key in ("wood", "food", "gold", "money"):
        resources.setdefault(key, 0)
    return resources


def get_period_name(period: int) -> str:
    return PERIOD_NAMES.get(period, f"Periode {period}")


def get_building_definition(building: str) -> Dict[str, object]:
    return BUILDINGS[building]


def get_building_label(building: Optional[str]) -> str:
    if not building:
        return "Aucun"
    return BUILDINGS.get(building, {}).get("label", building)


def get_building_short(building: Optional[str]) -> str:
    if not building:
        return "--"
    return BUILDINGS.get(building, {}).get("short", building[:2].upper())


def format_resource_bundle(bundle: Dict[str, int]) -> str:
    parts = []
    for key in ("wood", "food", "gold", "money"):
        amount = bundle.get(key, 0)
        if amount:
            parts.append(f"{amount} {key}")
    return ", ".join(parts) if parts else "aucun cout"


def format_resource_bundle_short(bundle: Dict[str, int]) -> str:
    labels = {
        "wood": "w",
        "food": "f",
        "gold": "g",
        "money": "$",
    }
    parts = []
    for key in ("wood", "food", "gold", "money"):
        amount = bundle.get(key, 0)
        if amount:
            parts.append(f"{amount}{labels[key]}")
    return " ".join(parts) if parts else "gratuit"


def get_missing_resources(resources: Dict[str, int], cost: Dict[str, int]) -> Dict[str, int]:
    ensure_resource_keys(resources)
    missing = {}
    for res, amount in cost.items():
        deficit = amount - resources.get(res, 0)
        if deficit > 0:
            missing[res] = deficit
    return missing


def get_build_options(period: int, terrain: str, current_building: Optional[str] = None) -> List[str]:
    options = []
    for building in BUILDING_ORDER:
        data = BUILDINGS[building]
        if period < data["period"]:
            continue
        if terrain not in data["terrain"]:
            continue
        upgrades_from = data.get("upgrades_from")
        if current_building:
            if upgrades_from == current_building:
                options.append(building)
        elif upgrades_from is None:
            options.append(building)
    return options


def get_building_income_text(building: str) -> str:
    data = BUILDINGS[building]
    effects = []
    income = data.get("income", {})
    if income:
        effects.append("+" + format_resource_bundle(income))
    if data.get("gold_to_money"):
        ratio = data.get("gold_to_money_ratio", 3)
        effects.append(f"convertit {data['gold_to_money']} gold en {ratio} money")
    return " | ".join(effects) if effects else "aucun bonus"


def get_building_territory_radius(building: str) -> int:
    return int(BUILDINGS.get(building, {}).get("territory_radius", 1))


@dataclass
class PlacedBuilding:
    building: str
    q: Optional[int] = None
    r: Optional[int] = None
    trapped: bool = False


class Player:
    def __init__(self, name: str, color=None):
        self.name = name
        self.color = color
        self.resources = STARTING_RESOURCES.copy()
        self.buildings: List[PlacedBuilding] = []
        self.free_build_tokens: Dict[str, int] = {}
        self.owned_tiles: Set[tuple[int, int]] = set()

    def add_resource(self, resource: str, amount: int):
        ensure_resource_keys(self.resources)
        self.resources[resource] = self.resources.get(resource, 0) + amount

    def receive_resources(self, extra: Optional[Dict[str, int]] = None):
        ensure_resource_keys(self.resources)
        for res, amount in BASE_RESOURCE_INCOME.items():
            self.resources[res] += amount
        if extra:
            for res, amount in extra.items():
                self.resources[res] = max(0, self.resources.get(res, 0) + amount)

    def can_afford(self, cost: Dict[str, int]) -> bool:
        return not get_missing_resources(self.resources, cost)

    def pay_cost(self, cost: Dict[str, int]):
        ensure_resource_keys(self.resources)
        for res, amount in cost.items():
            self.resources[res] -= amount

    def grant_free_build(self, building: str):
        self.free_build_tokens[building] = self.free_build_tokens.get(building, 0) + 1

    def claim_tile(self, q: int, r: int):
        self.owned_tiles.add((q, r))

    def claim_tiles(self, coords):
        for q, r in coords:
            self.claim_tile(q, r)

    def owns_tile(self, q: int, r: int) -> bool:
        return (q, r) in self.owned_tiles

    def find_building_at(self, q: int, r: int) -> Optional[PlacedBuilding]:
        for placed_building in self.buildings:
            if placed_building.q == q and placed_building.r == r:
                return placed_building
        return None

    def build(self, building: str, q: Optional[int] = None, r: Optional[int] = None) -> bool:
        if q is not None and r is not None and self.find_building_at(q, r):
            print("Un batiment existe deja sur cette case !")
            return False

        cost = BUILDINGS[building]["cost"]
        use_free_token = self.free_build_tokens.get(building, 0) > 0

        if not use_free_token and not self.can_afford(cost):
            print("Pas assez de ressources !")
            return False

        if use_free_token:
            self.free_build_tokens[building] -= 1
            if self.free_build_tokens[building] <= 0:
                del self.free_build_tokens[building]
        else:
            self.pay_cost(cost)

        self.buildings.append(PlacedBuilding(building=building, q=q, r=r))
        print(f"{self.name} construit {get_building_label(building)}")
        return True

    def upgrade_building(self, placed_building: PlacedBuilding, upgraded_building: str) -> bool:
        if placed_building not in self.buildings:
            return False
        data = BUILDINGS[upgraded_building]
        if data.get("upgrades_from") != placed_building.building:
            return False
        cost = data["cost"]
        if not self.can_afford(cost):
            print("Pas assez de ressources pour l'amelioration !")
            return False
        self.pay_cost(cost)
        previous_building = placed_building.building
        placed_building.building = upgraded_building
        placed_building.trapped = False
        print(f"{self.name} ameliore {get_building_label(previous_building)} en {get_building_label(upgraded_building)}")
        return True

    def destroy_random_building(self) -> Optional[PlacedBuilding]:
        if not self.buildings:
            print("Mais aucun batiment n'existe.")
            return None
        index = random.randrange(len(self.buildings))
        destroyed = self.buildings.pop(index)
        print(f"Le batiment {get_building_label(destroyed.building)} a ete detruit !")
        return destroyed

    def trap_random_building(self) -> bool:
        if not self.buildings:
            print("Mais aucun batiment a pieger.")
            return False
        random.choice(self.buildings).trapped = True
        print("Un batiment a ete piege !")
        return True

    def income_from_buildings(self) -> Dict[str, int]:
        ensure_resource_keys(self.resources)
        income = {"wood": 0, "food": 0, "gold": 0, "money": 0}
        available_gold = self.resources.get("gold", 0)

        for placed_building in self.buildings:
            if placed_building.trapped:
                print("Un batiment piege explose !")
                placed_building.trapped = False
                continue

            data = BUILDINGS.get(placed_building.building)
            if not data:
                continue

            for res, amount in data.get("income", {}).items():
                income[res] = income.get(res, 0) + amount

            gold_to_money = data.get("gold_to_money", 0)
            if gold_to_money:
                converted = min(gold_to_money, available_gold)
                if converted:
                    income["gold"] -= converted
                    income["money"] += converted * data.get("gold_to_money_ratio", 3)
                    available_gold -= converted

        return income

    def __repr__(self):
        building_names = [placed_building.building for placed_building in self.buildings]
        return f"<{self.name} {self.resources} {building_names}>"


def generate_cards():
    cards = []
    cards.append(("resource", random.choice(RESOURCE_CARDS)))
    cards.append(("building", random.choice(BUILDING_CARDS)))
    cards.append(("malus", random.choice(MALUS_CARDS)))
    random.shuffle(cards)
    return cards


def show_cards(cards):
    print("\n========================")
    print("Choisissez une carte :")
    print("========================\n")

    for i, (ctype, card) in enumerate(cards, start=1):
        if ctype == "resource":
            effects = ", ".join([f"+{v} {k}" for k, v in card["effect"].items()])
            print(f"{i} - {card['name']} ({effects})")
        elif ctype == "building":
            print(f"{i} - {card['name']} (construit {get_building_label(card['building'])})")
        elif ctype == "malus":
            name = card["name"]
            description = {
                "Incendie": "brule une partie de la nourriture",
                "Tempete": "detruit du bois",
                "Sabotage": "detruit un batiment",
                "Voleurs": "volent de l'or",
                "Batiment piege": "un batiment explose au prochain tour",
            }
            print(f"{i} - {name} ({description[name]})")

    print()


def apply_card(player: Player, card_type, card):
    print("\nEffet de la carte :")
    ensure_resource_keys(player.resources)

    if card_type == "resource":
        for res, value in card["effect"].items():
            player.resources[res] = player.resources.get(res, 0) + value
            print(f"+{value} {res}")

    elif card_type == "building":
        building = card["building"]
        player.grant_free_build(building)
        print(f"Construction gratuite accordee pour {get_building_label(building)}")

    elif card_type == "malus":
        t = card["type"]

        if t == "fire":
            loss = random.randint(3, 8)
            player.resources["food"] = max(0, player.resources["food"] - loss)
            print(f"Incendie ! -{loss} food")

        elif t == "storm":
            loss = random.randint(3, 8)
            player.resources["wood"] = max(0, player.resources["wood"] - loss)
            print(f"Tempete ! -{loss} wood")

        elif t == "destroy_building":
            player.destroy_random_building()

        elif t == "steal_gold":
            loss = random.randint(2, 6)
            player.resources["gold"] = max(0, player.resources["gold"] - loss)
            print(f"Voleurs ! -{loss} gold")

        elif t == "trap_building":
            player.trap_random_building()


class TurnManager:
    def __init__(self, players: List[Player]):
        self.players = players
        self._played_this_round: Set[Player] = set()
        self.turn_number = 0
        self.period = 1

    def current_player(self) -> Player:
        for player in self.players:
            if player not in self._played_this_round:
                return player
        raise RuntimeError("Tous les joueurs ont joue")

    def get_available_buildings(self, terrain: str, current_building: Optional[str] = None) -> List[str]:
        return get_build_options(self.period, terrain, current_building)

    def player_finished(self, player: Player):
        self._played_this_round.add(player)
        if self._played_this_round == set(self.players):
            self.end_round()

    def end_round(self):
        print("\n====== FIN DU TOUR ======")
        self.turn_number += 1

        for player in self.players:
            print(f"\nRessources pour {player.name}")
            bonus = {
                "wood": random.randint(0, 2),
                "food": random.randint(0, 2),
            }
            total_income = bonus.copy()
            for resource, amount in player.income_from_buildings().items():
                total_income[resource] = total_income.get(resource, 0) + amount
            player.receive_resources(extra=total_income)
            print(player.resources)

        next_period = min(5, self.turn_number // TURNS_PER_PERIOD + 1)
        if next_period > self.period:
            self.period = next_period
            print(f"\nNOUVELLE PERIODE : {self.period} ({get_period_name(self.period)})")

        self._played_this_round.clear()


if __name__ == "__main__":
    p1 = Player("Alice")
    p2 = Player("Bob")
    tm = TurnManager([p1, p2])

    print("\n===== JEU DE STRATEGIE TEST =====\n")

    while tm.turn_number < 10:
        player = tm.current_player()
        print("\n---------------------------------")
        print(f"Tour de {player.name}")
        print("---------------------------------")
        print("Periode :", get_period_name(tm.period))
        print("Ressources :", player.resources)
        print("Batiments :", [get_building_label(placed_building.building) for placed_building in player.buildings])

        cards = generate_cards()
        show_cards(cards)

        choice = int(input("Votre choix : ")) - 1
        card_type, card = cards[choice]
        apply_card(player, card_type, card)

        print("\nEtat du joueur :")
        print(player)

        tm.player_finished(player)
