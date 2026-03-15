from __future__ import annotations
import random
from typing import Dict, List, Optional, Set

# ==============================
# PARAMÈTRES DU JEU
# ==============================

TURNS_PER_PERIOD = 5

BASE_RESOURCE_INCOME = {
    "wood": 5,
    "food": 5,
    "gold": 2
}

BUILDING_COSTS = {
    "farm": {"wood": 10, "food": 0, "gold": 0},
    "barracks": {"wood": 20, "food": 5, "gold": 0},
    "blacksmith": {"wood": 30, "food": 10, "gold": 5},
}

BUILDINGS_BY_PERIOD = {
    1: ["farm"],
    2: ["barracks"],
    3: ["blacksmith"]
}

# ==============================
# CARTES
# ==============================

RESOURCE_CARDS = [
    {"name": "Réserve de bois", "effect": {"wood": 10}},
    {"name": "Chasse abondante", "effect": {"food": 10}},
    {"name": "Mine d'or découverte", "effect": {"gold": 6}},
    {"name": "Caravane marchande", "effect": {"wood": 5, "food": 5}},
]

BUILDING_CARDS = [
    {"name": "Construction rapide", "building": "farm"},
    {"name": "Caserne offerte", "building": "barracks"},
]

MALUS_CARDS = [
    {"name": "Incendie", "type": "fire"},
    {"name": "Tempête", "type": "storm"},
    {"name": "Sabotage", "type": "destroy_building"},
    {"name": "Voleurs", "type": "steal_gold"},
    {"name": "Bâtiment piégé", "type": "trap_building"},
]

# ==============================
# JOUEUR
# ==============================


class Player:

    def __init__(self, name: str):

        self.name = name

        self.resources = {
            "wood": 0,
            "food": 0,
            "gold": 0
        }

        self.buildings: List[str] = []
        self.trapped_buildings: Set[int] = set()

    # --------------------------

    def receive_resources(self, extra: Optional[Dict[str, int]] = None):

        for res, amount in BASE_RESOURCE_INCOME.items():
            self.resources[res] += amount

        if extra:
            for res, amount in extra.items():
                self.resources[res] = self.resources.get(res, 0) + amount

    # --------------------------

    def build(self, building: str):

        cost = BUILDING_COSTS[building]

        for res, amount in cost.items():

            if self.resources[res] < amount:
                print("Pas assez de ressources !")
                return False

        for res, amount in cost.items():
            self.resources[res] -= amount

        self.buildings.append(building)

        print(f"{self.name} construit {building}")

        return True

    # --------------------------

    def destroy_random_building(self):

        if not self.buildings:
            print("Mais aucun bâtiment n'existe.")
            return

        index = random.randrange(len(self.buildings))
        destroyed = self.buildings.pop(index)

        print(f"🔥 Le bâtiment {destroyed} a été détruit !")

    # --------------------------

    def income_from_buildings(self):

        income = {}

        for i, b in enumerate(self.buildings):

            if i in self.trapped_buildings:
                print("💥 Un bâtiment piégé explose !")
                self.trapped_buildings.remove(i)
                continue

            if b == "farm":
                income["food"] = income.get("food", 0) + 3

            elif b == "barracks":
                income["gold"] = income.get("gold", 0) + 1

            elif b == "blacksmith":
                income["wood"] = income.get("wood", 0) + 2

        return income

    # --------------------------

    def __repr__(self):

        return f"<{self.name} {self.resources} {self.buildings}>"

# ==============================
# CARTES
# ==============================


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

            effects = ", ".join(
                [f"+{v} {k}" for k, v in card["effect"].items()])
            print(f"{i} - {card['name']} ({effects})")

        elif ctype == "building":

            print(f"{i} - {card['name']} (construit {card['building']})")

        elif ctype == "malus":

            name = card["name"]

            description = {
                "Incendie": "brûle une partie de la nourriture",
                "Tempête": "détruit du bois",
                "Sabotage": "détruit un bâtiment",
                "Voleurs": "volent de l'or",
                "Bâtiment piégé": "un bâtiment explose au prochain tour"
            }

            print(f"{i} - {name} ({description[name]})")

    print()


def apply_card(player: Player, card_type, card):

    print("\nEffet de la carte :")

    if card_type == "resource":

        for res, value in card["effect"].items():
            player.resources[res] += value
            print(f"+{value} {res}")

    elif card_type == "building":

        building = card["building"]
        player.buildings.append(building)

        print(f"Bâtiment {building} ajouté gratuitement")

    elif card_type == "malus":

        t = card["type"]

        if t == "fire":

            loss = random.randint(3, 8)
            player.resources["food"] = max(
                0, player.resources["food"] - loss)

            print(f"🔥 Incendie ! -{loss} food")

        elif t == "storm":

            loss = random.randint(3, 8)
            player.resources["wood"] = max(
                0, player.resources["wood"] - loss)

            print(f"🌪 Tempête ! -{loss} wood")

        elif t == "destroy_building":

            player.destroy_random_building()

        elif t == "steal_gold":

            loss = random.randint(2, 6)
            player.resources["gold"] = max(
                0, player.resources["gold"] - loss)

            print(f"💰 Voleurs ! -{loss} gold")

        elif t == "trap_building":

            if player.buildings:
                index = random.randrange(len(player.buildings))
                player.trapped_buildings.add(index)
                print("💣 Un bâtiment a été piégé !")
            else:
                print("Mais aucun bâtiment à piéger.")

# ==============================
# GESTION DES TOURS
# ==============================


class TurnManager:

    def __init__(self, players: List[Player]):

        self.players = players
        self._played_this_round: Set[Player] = set()

        self.turn_number = 0
        self.period = 1

        self.available_buildings = BUILDINGS_BY_PERIOD[1].copy()

    # --------------------------

    def current_player(self):

        for p in self.players:
            if p not in self._played_this_round:
                return p

        raise RuntimeError("Tous les joueurs ont joué")

    # --------------------------

    def player_finished(self, player):

        self._played_this_round.add(player)

        if self._played_this_round == set(self.players):
            self.end_round()

    # --------------------------

    def end_round(self):

        print("\n====== FIN DU TOUR ======")

        self.turn_number += 1

        for p in self.players:

            print(f"\nRessources pour {p.name}")

            bonus = {
                "wood": random.randint(0, 2),
                "food": random.randint(0, 2),
            }

            p.receive_resources(extra=bonus)
            p.receive_resources(extra=p.income_from_buildings())

            print(p.resources)

        if self.turn_number // TURNS_PER_PERIOD + 1 > self.period:

            self.period += 1
            print(f"\nNOUVELLE PÉRIODE : {self.period}")

        self._played_this_round.clear()

# ==============================
# TEST DU JEU
# ==============================


if __name__ == "__main__":

    p1 = Player("Alice")
    p2 = Player("Bob")

    tm = TurnManager([p1, p2])

    print("\n===== JEU DE STRATÉGIE TEST =====\n")

    while tm.turn_number < 10:

        player = tm.current_player()

        print("\n---------------------------------")
        print(f"Tour de {player.name}")
        print("---------------------------------")

        print("Ressources :", player.resources)
        print("Bâtiments :", player.buildings)

        cards = generate_cards()

        show_cards(cards)

        choice = int(input("Votre choix : ")) - 1

        card_type, card = cards[choice]

        apply_card(player, card_type, card)

        print("\nEtat du joueur :")
        print(player)

        tm.player_finished(player)
