class GameSession:
    """Etat de partie partage entre la boucle Pygame et les modules d'UI."""

    def __init__(self):
        self.game_state = "menu"
        self.carte = None
        self.turn_manager = None
        self.current_player_resources = None
        self.camera_pan_x = 0
        self.camera_pan_y = 0
        self.map_drag_active = False
        self.turn_timer_started_at = None
        self.status_message = ""
        self.status_message_until = 0
        self.panel_action_rects = []
        self.end_turn_rect = None
        self.winner_name = None

    def clear_match_ui(self):
        self.panel_action_rects = []
        self.end_turn_rect = None

    def get_active_player(self):
        if not self.turn_manager:
            return None
        try:
            return self.turn_manager.current_player()
        except RuntimeError:
            return None

    def set_status_message(self, text: str, now_ticks: int, duration_ms: int = 2600):
        self.status_message = text
        self.status_message_until = now_ticks + duration_ms

    def reset_turn_timer(self, now_ticks: int):
        self.turn_timer_started_at = now_ticks

    def get_turn_time_remaining(self, now_ticks: int, turn_duration_ms: int) -> int:
        if self.turn_timer_started_at is None:
            return turn_duration_ms
        elapsed = now_ticks - self.turn_timer_started_at
        return max(0, turn_duration_ms - elapsed)

    def start_match(self, game_state: str, carte, turn_manager, current_player_resources, now_ticks: int):
        self.game_state = game_state
        self.carte = carte
        self.turn_manager = turn_manager
        self.current_player_resources = current_player_resources
        self.camera_pan_x = 0
        self.camera_pan_y = 0
        self.map_drag_active = False
        self.winner_name = None
        self.clear_match_ui()
        self.reset_turn_timer(now_ticks)

    @staticmethod
    def add_debug_resources(resource_store):
        if resource_store is None:
            return
        if hasattr(resource_store, "add_resource"):
            resource_store.add_resource("wood", 10)
            resource_store.add_resource("food", 10)
            resource_store.add_resource("gold", 5)
            resource_store.add_resource("money", 5)
        elif isinstance(resource_store, dict):
            resource_store["wood"] = resource_store.get("wood", 0) + 10
            resource_store["food"] = resource_store.get("food", 0) + 10
            resource_store["gold"] = resource_store.get("gold", 0) + 5
            resource_store["money"] = resource_store.get("money", 0) + 5
