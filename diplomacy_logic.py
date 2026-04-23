import tours


RELATION_NEUTRAL = "neutral"
RELATION_ALLIED = "allied"
RELATION_WAR = "war"

RELATION_LABELS = {
    RELATION_NEUTRAL: "Neutre",
    RELATION_ALLIED: "Alliance",
    RELATION_WAR: "Guerre",
}


TRADE_PLANS = {
    # Niveau 1 : Poste. Niveau 2 : Messagers et diligence.
    1: {
        "label": "Convoi marchand",
        "sender_give": {"wood": 2, "food": 2},
        "receiver_give": {"gold": 1},
        "sender_bonus": {"money": 2},
    },
    2: {
        "label": "Convoi de diligence",
        "sender_give": {"wood": 3, "food": 3},
        "receiver_give": {"gold": 2},
        "sender_bonus": {"money": 4},
    },
}


def relation_label(relation: str) -> str:
    return RELATION_LABELS.get(relation, relation.title())


def get_trade_plan(sender):
    # Le niveau de route vient des batiments possedes par le joueur.
    route_level = sender.trade_route_level() if sender is not None else 0
    if route_level >= 2:
        return TRADE_PLANS[2]
    if route_level >= 1:
        return TRADE_PLANS[1]
    return None


def get_trade_preview(sender, receiver, relation: str):
    if sender is None or receiver is None or sender is receiver:
        return {"available": False, "reason": "", "label": "", "short": ""}
    if sender.trade_used:
        return {"available": False, "reason": "Echange deja utilise ce tour.", "label": "", "short": ""}
    if relation == RELATION_WAR:
        return {"available": False, "reason": "Pas d'echange en temps de guerre.", "label": "", "short": ""}

    plan = get_trade_plan(sender)
    if plan is None:
        return {"available": False, "reason": "Construisez un Poste pour commercer.", "label": "", "short": ""}

    sender_missing = tours.get_missing_resources(sender.resources, plan["sender_give"])
    receiver_missing = tours.get_missing_resources(receiver.resources, plan["receiver_give"])
    if sender_missing or receiver_missing:
        return {
            "available": False,
            "reason": "Commerce indisponible pour le moment.",
            "label": plan["label"],
            "short": build_trade_summary(plan),
        }

    return {
        "available": True,
        "reason": "",
        "label": plan["label"],
        "short": build_trade_summary(plan),
    }


def build_trade_summary(plan) -> str:
    sender_part = tours.format_resource_bundle_short(plan["sender_give"])
    receiver_part = tours.format_resource_bundle_short(plan["receiver_give"])
    bonus_part = tours.format_resource_bundle_short(plan["sender_bonus"])
    return f"{sender_part} <-> {receiver_part} + {bonus_part}"


def execute_trade(sender, receiver, relation: str):
    # On refait la preview ici pour garder une seule porte d'entree sure.
    preview = get_trade_preview(sender, receiver, relation)
    if not preview["available"]:
        return False, preview["reason"]

    plan = get_trade_plan(sender)
    sender.pay_cost(plan["sender_give"])
    receiver.pay_cost(plan["receiver_give"])

    for resource, amount in plan["receiver_give"].items():
        sender.add_resource(resource, amount)
    for resource, amount in plan["sender_give"].items():
        receiver.add_resource(resource, amount)

    bonus = dict(plan["sender_bonus"])
    if relation == RELATION_ALLIED:
        bonus["money"] = bonus.get("money", 0) + 1
    for resource, amount in bonus.items():
        sender.add_resource(resource, amount)

    sender.successful_trades += 1
    sender.trade_used = True
    return True, f"{plan['label']} etabli avec {receiver.name}."
