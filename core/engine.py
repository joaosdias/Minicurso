"""Motor principal do jogo (GameEngine) com estatísticas e novos comandos.

Gerencia o estado da partida, executa ações (Atacar, Especial, Defender, Poção)
e notifica os observadores inscritos via Observer Pattern.
"""

from typing import List, Protocol, Dict, Any
from core.entities import Player, Enemy
from core.items import Weapon
import config.settings as settings


class GameObserver(Protocol):
    """Protocolo de observador do jogo."""

    def on_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Notificação de eventos do motor."""
        ...


class GameEngine:
    """Gerenciador do combate e das regras de negócio."""

    def __init__(self) -> None:
        """Inicializa um novo motor de jogo e reseta os participantes."""
        self._observers: List[GameObserver] = []
        self.reset_game()

    def reset_game(self) -> None:
        """Reseta ou inicia um novo estado de jogo."""
        self.player: Player = Player(
            name="Guerreiro",
            max_health=settings.PLAYER_MAX_HEALTH,
            base_damage=settings.PLAYER_BASE_DAMAGE,
            potions=settings.PLAYER_INITIAL_POTIONS,
        )
        self.player.equip_weapon(Weapon("Espada Longa", settings.WEAPON_BONUS_DAMAGE))

        self.enemy: Enemy = Enemy(
            name="Goblin Voraz",
            max_health=settings.ENEMY_MAX_HEALTH,
            base_damage=settings.ENEMY_BASE_DAMAGE,
            xp_reward=50  # Definido como 50 como exemplo (pode puxar de um settings se preferir)
        )

        self.current_turn: str = "player"
        self.is_game_over: bool = False
        self.winner: str = ""

        self.total_turns: int = 0
        self.total_damage_dealt: int = 0
        self.potions_used: int = 0

    def subscribe(self, observer: GameObserver) -> None:
        """Inscreve um observador."""
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: GameObserver) -> None:
        """Remove um observador."""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emite evento aos observadores."""
        for observer in self._observers:
            observer.on_event(event_type, data)

    def start_game(self) -> None:
        """Inicia a partida e dispara evento inicial."""
        self.notify("GAME_STARTED", {
            "player_name": self.player.name,
            "player_health": self.player.health,
            "player_max_health": self.player.max_health,
            "player_level": self.player.level,
            "player_xp": self.player.xp,
            "player_xp_to_next_level": self.player.xp_to_next_level,
            "enemy_name": self.enemy.name,
            "enemy_health": self.enemy.health,
            "enemy_max_health": self.enemy.max_health,
            "potions": self.player.potions_count,
            "current_turn": self.current_turn,
        })

    def player_attack(self) -> bool:
        """Executa ataque normal do jogador."""
        if self.is_game_over or self.current_turn != "player":
            return False

        damage, is_critical = self.player.get_attack_power()
        actual_damage = self.enemy.take_damage(damage)
        self.total_damage_dealt += actual_damage

        self.notify("PLAYER_ATTACKED", {
            "attacker": self.player.name,
            "target": self.enemy.name,
            "damage": actual_damage,
            "is_critical": is_critical,
            "target_health": self.enemy.health,
            "target_max_health": self.enemy.max_health,
        })

        if not self.enemy.is_alive():
            self._handle_enemy_defeat()
            return True

        self._switch_turn()
        return True

    def player_special_attack(self) -> bool:
        """Executa a habilidade especial (Golpe Devastador)."""
        if self.is_game_over or self.current_turn != "player":
            return False

        if not self.player.can_use_special():
            cd = self.player.special_attack_cooldown
            msg = f"Golpe Devastador em cooldown ({cd} turnos)!"
            self.notify("ACTION_FAILED", {"reason": msg})
            return False

        damage = self.player.use_special_attack()
        actual_damage = self.enemy.take_damage(damage)
        self.total_damage_dealt += actual_damage

        self.notify("PLAYER_SPECIAL_ATTACKED", {
            "attacker": self.player.name,
            "target": self.enemy.name,
            "damage": actual_damage,
            "target_health": self.enemy.health,
            "target_max_health": self.enemy.max_health,
        })

        if not self.enemy.is_alive():
            self._handle_enemy_defeat()
            return True

        self._switch_turn()
        return True

    def player_defend(self) -> bool:
        """Ativa postura de defesa no próximo ataque."""
        if self.is_game_over or self.current_turn != "player":
            return False

        self.player.set_defense_stance()
        self.notify("PLAYER_DEFENDED", {
            "player_name": self.player.name,
        })

        self._switch_turn()
        return True

    def player_heal(self) -> bool:
        """Utiliza poção de cura."""
        if self.is_game_over or self.current_turn != "player":
            return False

        if self.player.potions_count <= 0:
            self.notify("ACTION_FAILED", {
                "reason": "Você não possui mais poções!"
            })
            return False

        healed = self.player.use_potion(settings.POTION_HEAL_AMOUNT)
        self.potions_used += 1

        self.notify("PLAYER_HEALED", {
            "player_name": self.player.name,
            "healed_amount": healed,
            "current_health": self.player.health,
            "max_health": self.player.max_health,
            "potions_remaining": self.player.potions_count,
        })

        self._switch_turn()
        return True

    def _enemy_turn(self) -> None:
        """IA simples do turno do inimigo."""
        if self.is_game_over or self.current_turn != "enemy":
            return

        damage, is_critical = self.enemy.get_attack_power()
        actual_damage = self.player.take_damage(damage)

        self.notify("ENEMY_ATTACKED", {
            "attacker": self.enemy.name,
            "target": self.player.name,
            "damage": actual_damage,
            "is_critical": is_critical,
            "is_defending": self.player.is_defending,
            "target_health": self.player.health,
            "target_max_health": self.player.max_health,
        })

        if not self.player.is_alive():
            self._finish_game(winner=self.enemy.name)
            return

        self._switch_turn()

    def _switch_turn(self) -> None:
        """Alterna turnos e atualiza tempo de recarga de habilidades."""
        if self.is_game_over:
            return

        self.total_turns += 1

        if self.current_turn == "player":
            self.player.update_cooldowns()
            self.current_turn = "enemy"
            self.notify("TURN_CHANGED", {"current_turn": self.current_turn})
            self._enemy_turn()
        else:
            self.current_turn = "player"
            self.notify("TURN_CHANGED", {"current_turn": self.current_turn})

    def _handle_enemy_defeat(self) -> None:
        """Processa a derrota do inimigo, incluindo ganho de XP e finalização."""
        xp_earned = self.enemy.xp_reward
        leveled_up = self.player.gain_xp(xp_earned)

        self.notify("XP_GAINED", {
            "amount": xp_earned,
            "current_xp": self.player.xp,
            "xp_to_next_level": self.player.xp_to_next_level
        })

        if leveled_up:
            self.notify("LEVEL_UP", {
                "new_level": self.player.level,
                "health": self.player.health,
                "max_health": self.player.max_health,
                "base_damage": self.player.base_damage
            })

        self._finish_game(winner=self.player.name)

    def _finish_game(self, winner: str) -> None:
        """Encerra a partida e compila as estatísticas."""
        self.is_game_over = True
        self.winner = winner
        self.notify("GAME_OVER", {
            "winner": winner,
            "is_player_winner": (winner == self.player.name),
            "total_turns": self.total_turns,
            "total_damage_dealt": self.total_damage_dealt,
            "potions_used": self.potions_used,
            })