from __future__ import annotations

import random
from typing import Dict, List, Optional, Set

# Nombre de tours nécessaires pour passer à la période suivante
TURNS_PER_PERIOD = 5

# Coût de chaque bâtiment en ressources
BUILDING_COSTS: Dict[str, Dict[str, int]] = {
    "farm": {"wood": 10, "food": 0, "gold": 0},
    "barracks": {"wood": 20, "food": 5, "gold": 0},
    "blacksmith": {"wood": 30, "food": 10, "gold": 5},
}

# Bâtiments débloqués au début de chaque période
BUILDINGS_BY_PERIOD: Dict[int, List[str]] = {
    1: ["farm"],
    2: ["barracks"],
    3: ["blacksmith"],
}

# Ressources reçues automatiquement à chaque fin de tour complet
BASE_RESOURCE_INCOME: Dict[str, int] = {"wood": 5, "food": 5, "gold": 2}


class Player:
    """Représente un joueur avec ses ressources et ses bâtiments."""

    def __init__(self, name: str) -> None:
        self.name = name                     # Nom du joueur
        self.resources = {"wood": 0, "food": 0, "gold": 0}  # Stock initial
        self.buildings: List[str] = []       # Liste des bâtiments construits

    def receive_resources(self, extra: Optional[Dict[str, int]] = None) -> None:
        """Ajoute les ressources de base + bonus éventuel."""
        # Ajoute les ressources fixes
        for res, amount in BASE_RESOURCE_INCOME.items():
            self.resources[res] += amount

        # Ajoute un bonus si fourni
        if extra:
            for res, amount in extra.items():
                self.resources[res] = self.resources.get(res, 0) + amount

    def can_build(self, building: str) -> bool:
        """Vérifie si le joueur possède assez de ressources."""
        cost = BUILDING_COSTS.get(building)
        if cost is None:
            raise ValueError(f"Bâtiment inconnu '{building}'")

        # Vérifie que chaque ressource est suffisante
        return all(self.resources.get(res, 0) >= amt for res, amt in cost.items())

    def build(self, building: str) -> bool:
        """Construit le bâtiment si possible."""
        if not self.can_build(building):
            return False  # Construction impossible

        # Retire le coût des ressources
        cost = BUILDING_COSTS[building]
        for res, amt in cost.items():
            self.resources[res] -= amt

        # Ajoute le bâtiment à la liste
        self.buildings.append(building)
        return True

    def income_from_buildings(self) -> Dict[str, int]:
        """Calcule les ressources générées par les bâtiments."""
        income: Dict[str, int] = {}

        for b in self.buildings:
            if b == "farm":
                income["food"] = income.get("food", 0) + 3
            elif b == "barracks":
                income["gold"] = income.get("gold", 0) + 1
            elif b == "blacksmith":
                income["wood"] = income.get("wood", 0) + 2

        return income

    def __repr__(self) -> str:
        return f"<Player {self.name} res={self.resources} builds={self.buildings}>"


class TurnManager:
    """Gère l'ordre des joueurs, les tours et les périodes."""

    def __init__(self, players: List[Player]) -> None:
        if not players:
            raise ValueError("Au moins un joueur requis")

        self.players = players                   # Liste des joueurs
        self._played_this_round: Set[Player] = set()  # Joueurs ayant déjà joué
        self.turn_number = 0                     # Nombre de tours complets effectués
        self.period = 1                          # Période actuelle
        self.available_buildings = BUILDINGS_BY_PERIOD.get(1, []).copy()

    def current_player(self) -> Player:
        """Retourne le prochain joueur qui n’a pas encore joué."""
        for p in self.players:
            if p not in self._played_this_round:
                return p

        # Tous ont joué
        raise RuntimeError("Tous les joueurs ont déjà joué")

    def player_finished(self, player: Player) -> None:
        """Appelé quand un joueur termine son tour."""
        if player not in self.players:
            raise ValueError("Joueur inconnu")

        # On marque le joueur comme ayant joué
        self._played_this_round.add(player)

        # Si tous les joueurs ont joué → fin du tour complet
        if self._played_this_round == set(self.players):
            self.end_round()

    def end_round(self) -> None:
        """Fin d’un tour complet : ressources + gestion du temps."""
        # Incrémente le nombre de tours
        self.turn_number += 1

        # Donne les ressources à chaque joueur
        for p in self.players:
            # Petit bonus aléatoire
            bonus = {
                "wood": random.randint(0, 2),
                "food": random.randint(0, 2),
            }

            # Ressources de base + bonus
            p.receive_resources(extra=bonus)

            # Revenus générés par les bâtiments
            p.receive_resources(extra=p.income_from_buildings())

        # Vérifie si on change de période
        if self.turn_number // TURNS_PER_PERIOD + 1 > self.period:
            self.period += 1
            self._unlock_buildings_for_period(self.period)

        # Réinitialise la liste des joueurs pour le prochain tour
        self._played_this_round.clear()

    def _unlock_buildings_for_period(self, period: int) -> None:
        """Ajoute les bâtiments débloqués pour la nouvelle période."""
        new = BUILDINGS_BY_PERIOD.get(period, [])
        self.available_buildings.extend(new)

    def __repr__(self) -> str:
        return (
            f"<TurnManager tour={self.turn_number} "
            f"periode={self.period}>"
        )