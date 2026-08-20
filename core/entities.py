"""Entidades do domínio do RPG (Character, Player e Enemy).

Este módulo define os dados e regras de negócio para todos os participantes do combate.
Regra de arquitetura: Nenhuma função neste arquivo deve fazer chamadas de UI (print ou tkinter).
"""

from typing import Optional
import random
from core.items import Weapon
import config.settings as settings


class Character:
    """Classe base para todos os personagens do jogo."""

    def __init__(self, name: str, max_health: int, base_damage: int) -> None:
        """Inicializa um personagem."""
        self.name: str = name
        self.max_health: int = max_health
        self.health: int = max_health
        self.base_damage: int = base_damage
        self.weapon: Optional[Weapon] = None
        self.is_defending: bool = False

    def take_damage(self, amount: int) -> int:
        """Aplica dano ao personagem considerando postura de defesa."""
        actual_damage = amount
        if self.is_defending:
            actual_damage = int(amount * (1.0 - settings.DEFENSE_DAMAGE_REDUCTION))
            self.is_defending = False

        damage_taken = min(self.health, max(0, actual_damage))
        self.health -= damage_taken
        return damage_taken

    def heal(self, amount: int) -> int:
        """Restaura vida do personagem sem ultrapassar a vida máxima."""
        actual_heal = min(self.max_health - self.health, max(0, amount))
        self.health += actual_heal
        return actual_heal

    def is_alive(self) -> bool:
        """Verifica se o personagem ainda tem vida."""
        return self.health > 0

    def equip_weapon(self, weapon: Weapon) -> None:
        """Equipa uma arma no personagem."""
        self.weapon = weapon

    def get_attack_power(self) -> tuple[int, bool]:
        """Calcula o dano do ataque e verifica se foi um Acerto Crítico.

        Returns:
            tuple[int, bool]: (Valor do dano, True se for crítico).
        """
        bonus = self.weapon.bonus_damage if self.weapon else 0
        base_total = self.base_damage + bonus

        is_critical = random.random() < settings.CRITICAL_HIT_CHANCE
        if is_critical:
            final_damage = int(base_total * settings.CRITICAL_HIT_MULTIPLIER)
        else:
            final_damage = base_total

        return final_damage, is_critical

    def set_defense_stance(self) -> None:
        """Ativa a postura de defesa para o próximo turno."""
        self.is_defending = True


class Player(Character):
    """Representa o herói controlado pelo jogador."""

    def __init__(
        self,
        name: str = "Herói",
        max_health: int = 100,
        base_damage: int = 15,
        potions: int = 3
    ) -> None:
        """Inicializa o jogador com poções, habilidade especial, e atributos de nível."""
        super().__init__(name, max_health, base_damage)
        self.potions_count: int = potions
        self.special_attack_cooldown: int = 0
        
        # Novos atributos de progressão
        self.level: int = 1
        self.xp: int = 0
        self.xp_to_next_level: int = 100  # Quantidade de XP necessária para o nível 2

    def use_potion(self, heal_amount: int) -> int:
        """Utiliza uma poção do inventário."""
        if self.potions_count <= 0:
            return 0

        self.potions_count -= 1
        return self.heal(heal_amount)

    def can_use_special(self) -> bool:
        """Verifica se a habilidade especial está fora de recarga (cooldown == 0)."""
        return self.special_attack_cooldown == 0

    def use_special_attack(self) -> int:
        """Executa a habilidade Golpe Devastador e ativa o tempo de recarga."""
        if not self.can_use_special():
            return 0

        self.special_attack_cooldown = settings.SPECIAL_ATTACK_COOLDOWN + 1
        return settings.SPECIAL_ATTACK_DAMAGE

    def update_cooldowns(self) -> None:
        """Decrementa os turnos de recarga das habilidades."""
        if self.special_attack_cooldown > 0:
            self.special_attack_cooldown -= 1

    def gain_xp(self, amount: int) -> bool:
        """Adiciona XP ao jogador e verifica se subiu de nível.
        
        Returns:
            bool: True se o jogador subiu de nível neste ganho de XP.
        """
        self.xp += amount
        leveled_up = False
        
        # Usando while caso o jogador ganhe muito XP e suba múltiplos níveis de uma vez
        while self.xp >= self.xp_to_next_level:
            self.level_up()
            leveled_up = True
            
        return leveled_up

    def level_up(self) -> None:
        """Aumenta o nível, recupera a vida total e aumenta o dano base."""
        self.xp -= self.xp_to_next_level
        self.level += 1
        self.xp_to_next_level = int(self.xp_to_next_level * 1.5)  # Aumenta a dificuldade de subir de nível
        
        # Bônus de Subida de Nível
        self.base_damage += 5  # Incrementa o dano base
        self.max_health += 10  # Opcional: Aumentar a vida máxima
        self.health = self.max_health  # Restaura a vida completamente


class Enemy(Character):
    """Representa o oponente da arena."""

    def __init__(
        self,
        name: str = "Gargula de Pedra",
        max_health: int = 80,
        base_damage: int = 12,
        xp_reward: int = 50  # Nova adição: XP concedido ao ser derrotado
    ) -> None:
        """Inicializa o inimigo."""
        super().__init__(name, max_health, base_damage)
        self.xp_reward = xp_reward