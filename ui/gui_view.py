"""Interface Gráfica de Usuário (GUI) com Fluxo de Telas, Animações e Sprites.

Suporta:
- Tela de Início (Start Screen / Menu Principal)
- Tela de Combate (Arena com sprites, números flutuantes, barra de XP e nível)
- Tela de Fim de Jogo (Victory / Defeat Screen com estatísticas)
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional
from core.engine import GameEngine
import config.settings as settings


class GUIView:
    """Interface Tkinter conectada ao GameEngine via Observer Pattern."""

    def __init__(self, engine: GameEngine) -> None:
        """Inicializa a interface gráfica e o fluxo de telas."""
        self.engine: GameEngine = engine

        self.root: tk.Tk = tk.Tk()
        self.root.title(settings.WINDOW_TITLE)
        self.root.configure(bg=settings.BG_COLOR)

        self.is_fullscreen: bool = True
        self.root.attributes("-fullscreen", True)

        self.root.bind("<Escape>", self._toggle_fullscreen)
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.root.bind("<a>", lambda e: self._on_attack_clicked())
        self.root.bind("<s>", lambda e: self._on_special_clicked())
        self.root.bind("<d>", lambda e: self._on_defend_clicked())
        self.root.bind("<p>", lambda e: self._on_heal_clicked())

        self.hero_img: Optional[tk.PhotoImage] = None
        self.enemy_img: Optional[tk.PhotoImage] = None

        self._load_sprites()

        self.container = tk.Frame(self.root, bg=settings.BG_COLOR)
        self.container.pack(fill=tk.BOTH, expand=True)

        self.engine.subscribe(self)

        self.show_start_screen()

    def _toggle_fullscreen(self, event: Optional[tk.Event] = None) -> None:
        """Alterna entre modo Tela Cheia e Janela Redimensionável."""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        if not self.is_fullscreen:
            self.root.geometry("1024x720")

    def _load_sprites(self) -> None:
        """Carrega os sprites visuais em formato PPM/GIF."""
        try:
            if os.path.exists(settings.HERO_SPRITE_PATH):
                self.hero_img = tk.PhotoImage(file=settings.HERO_SPRITE_PATH)
            if os.path.exists(settings.ENEMY_SPRITE_PATH):
                self.enemy_img = tk.PhotoImage(file=settings.ENEMY_SPRITE_PATH)
        except Exception as err:
            print(f"Aviso ao carregar sprites: {err}")

    def _clear_container(self) -> None:
        """Limpa todos os widgets do container principal para trocar de tela."""
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_start_screen(self) -> None:
        """Exibe o menu inicial do jogo."""
        self._clear_container()

        menu_frame = tk.Frame(self.container, bg=settings.BG_COLOR)
        menu_frame.place(relx=0.5, rely=0.5, anchor="center")

        title_lbl = tk.Label(
            menu_frame,
            text=" RPG ARENA IN TURNOS ",
            font=("Helvetica", 28, "bold"),
            bg=settings.BG_COLOR,
            fg=settings.ACCENT_COLOR,
            pady=10,
        )
        title_lbl.pack()

        subtitle_lbl = tk.Label(
            menu_frame,
            text="Projeto Base - Minicurso de Git & Engenharia de Software",
            font=("Helvetica", 14, "italic"),
            bg=settings.BG_COLOR,
            fg=settings.TEXT_COLOR,
            pady=15,
        )
        subtitle_lbl.pack()

        btn_start = tk.Button(
            menu_frame,
            text=" INICIAR BATALHA",
            font=("Helvetica", 14, "bold"),
            bg=settings.BUTTON_BG,
            fg=settings.BUTTON_FG,
            activebackground=settings.ACCENT_COLOR,
            padx=40,
            pady=12,
            cursor="hand2",
            command=self.start_battle,
        )
        btn_start.pack(pady=10, fill=tk.X)

        btn_story = tk.Button(
            menu_frame,
            text=" MODO HISTÓRIA (TASK-06)",
            font=("Helvetica", 14, "bold"),
            bg=settings.BUTTON_BG,
            fg=settings.ACCENT_COLOR,
            activebackground=settings.PANEL_BG,
            padx=40,
            pady=12,
            cursor="hand2",
            command=self._show_story_preview,
        )
        btn_story.pack(pady=10, fill=tk.X)

        btn_instructions = tk.Button(
            menu_frame,
            text="ℹ INSTRUÇÕES DO MINICURSO",
            font=("Helvetica", 12),
            bg=settings.PANEL_BG,
            fg=settings.TEXT_COLOR,
            padx=30,
            pady=8,
            cursor="hand2",
            command=self._show_instructions,
        )
        btn_instructions.pack(pady=5, fill=tk.X)

        btn_exit = tk.Button(
            menu_frame,
            text=" SAIR DO JOGO",
            font=("Helvetica", 12),
            bg=settings.PANEL_BG,
            fg=settings.ENEMY_HEALTH_BAR_COLOR,
            padx=30,
            pady=8,
            cursor="hand2",
            command=self.root.quit,
        )
        btn_exit.pack(pady=5, fill=tk.X)

    def _show_story_preview(self) -> None:
        """Exibe popup explicativo sobre a Task do Modo História."""
        messagebox.showinfo(
            "Modo História / Campanha (Task-06)",
            "MODO HISTÓRIA (Task em desenvolvimento para os alunos):\n\n"
            "Capítulo 1: O Resgate do Vilarejo\n"
            "Capítulo 2: As Ruínas do Dragão de Pedra\n\n"
            "Esta funcionalidade será desenvolvida durante a atividade prática de Git!"
        )

    def _show_instructions(self) -> None:
        """Exibe modal com instruções de atalhos e objetivos."""
        messagebox.showinfo(
            "Instruções do Jogo",
            "COMANDOS DE BATALHA:\n"
            " - [ A ]: Atacar (Dano normal com chance de Crítico)\n"
            " - [ S ]: Golpe Devastador (Ataque especial com 3 turnos de cooldown)\n"
            " - [ D ]: Defender (Reduz o próximo dano recebido em 50%)\n"
            " - [ P ]: Usar Poção (Recupera +30 HP)\n"
            " - [ Esc ]: Alternar Tela Cheia / Janela"
        )

    def start_battle(self) -> None:
        """Inicia a batalha na arena."""
        self._clear_container()
        self.engine.reset_game()
        self._setup_arena_ui()
        self.engine.start_game()

    def _setup_arena_ui(self) -> None:
        """Constrói o layout da tela de combate."""
        main_layout = tk.Frame(self.container, bg=settings.BG_COLOR, padx=20, pady=15)
        main_layout.pack(fill=tk.BOTH, expand=True)

        header_frame = tk.Frame(main_layout, bg=settings.BG_COLOR)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_lbl = tk.Label(
            header_frame,
            text="RPG ARENA - MODO DE COMBATE",
            font=("Helvetica", 18, "bold"),
            bg=settings.BG_COLOR,
            fg=settings.ACCENT_COLOR,
        )
        title_lbl.pack(side=tk.LEFT)

        btn_menu = tk.Button(
            header_frame,
            text=" Menu Principal",
            font=("Helvetica", 10),
            bg=settings.PANEL_BG,
            fg=settings.TEXT_COLOR,
            command=self.show_start_screen,
        )
        btn_menu.pack(side=tk.RIGHT)

        status_frame = tk.Frame(main_layout, bg=settings.BG_COLOR)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        # Box do Jogador (Hero)
        player_box = tk.LabelFrame(
            status_frame,
            text=f" HERÓI: {self.engine.player.name} ",
            font=("Helvetica", 11, "bold"),
            bg=settings.PANEL_BG,
            fg=settings.TEXT_COLOR,
            padx=15,
            pady=8,
        )
        player_box.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0, 5))

        # Nível do Jogador
        self.player_level_lbl = tk.Label(
            player_box,
            text="",
            font=("Helvetica", 10, "bold"),
            bg=settings.PANEL_BG,
            fg=settings.ACCENT_COLOR,
        )
        self.player_level_lbl.pack(anchor="w")

        # Vida (HP) do Jogador
        self.player_hp_lbl = tk.Label(
            player_box,
            text="",
            font=("Helvetica", 10, "bold"),
            bg=settings.PANEL_BG,
            fg=settings.HEALTH_BAR_COLOR,
        )
        self.player_hp_lbl.pack(anchor="w")

        self.player_progress = ttk.Progressbar(
            player_box, orient="horizontal", mode="determinate"
        )
        self.player_progress.pack(fill=tk.X, pady=(2, 5))

        # Experiência (XP) do Jogador
        self.player_xp_lbl = tk.Label(
            player_box,
            text="",
            font=("Helvetica", 9, "bold"),
            bg=settings.PANEL_BG,
            fg="#89b4fa",
        )
        self.player_xp_lbl.pack(anchor="w")

        self.player_xp_progress = ttk.Progressbar(
            player_box, orient="horizontal", mode="determinate"
        )
        self.player_xp_progress.pack(fill=tk.X, pady=(2, 5))

        # Poções
        self.potions_lbl = tk.Label(
            player_box,
            text="",
            font=("Helvetica", 9),
            bg=settings.PANEL_BG,
            fg=settings.ACCENT_COLOR,
        )
        self.potions_lbl.pack(anchor="w")

        # Box do Inimigo
        enemy_box = tk.LabelFrame(
            status_frame,
            text=f" OPONENTE: {self.engine.enemy.name} ",
            font=("Helvetica", 11, "bold"),
            bg=settings.PANEL_BG,
            fg=settings.TEXT_COLOR,
            padx=15,
            pady=8,
        )
        enemy_box.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=(5, 0))

        self.enemy_hp_lbl = tk.Label(
            enemy_box,
            text="",
            font=("Helvetica", 10, "bold"),
            bg=settings.PANEL_BG,
            fg=settings.ENEMY_HEALTH_BAR_COLOR,
        )
        self.enemy_hp_lbl.pack(anchor="w")

        self.enemy_progress = ttk.Progressbar(
            enemy_box, orient="horizontal", mode="determinate"
        )
        self.enemy_progress.pack(fill=tk.X, pady=5)

        self.turn_indicator_lbl = tk.Label(
            enemy_box,
            text="Turno Atual: Jogador",
            font=("Helvetica", 9, "italic"),
            bg=settings.PANEL_BG,
            fg=settings.TEXT_COLOR,
        )
        self.turn_indicator_lbl.pack(anchor="w")

        self.arena_canvas = tk.Canvas(
            main_layout,
            bg=settings.ARENA_BG,
            highlightthickness=1,
            highlightbackground=settings.PANEL_BG,
        )
        self.arena_canvas.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.arena_canvas.bind("<Configure>", self._draw_arena)

        bottom_frame = tk.Frame(main_layout, bg=settings.BG_COLOR)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        log_box = tk.LabelFrame(
            bottom_frame,
            text=" Histórico de Combate ",
            font=("Helvetica", 10, "bold"),
            bg=settings.PANEL_BG,
            fg=settings.TEXT_COLOR,
            padx=10,
            pady=8,
        )
        log_box.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0, 5))

        self.log_text = tk.Text(
            log_box,
            height=5,
            bg=settings.ARENA_BG,
            fg=settings.TEXT_COLOR,
            font=("Consolas", 10),
            state=tk.DISABLED,
            relief=tk.FLAT,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        controls_box = tk.LabelFrame(
            bottom_frame,
            text=" Comandos ",
            font=("Helvetica", 10, "bold"),
            bg=settings.PANEL_BG,
            fg=settings.TEXT_COLOR,
            padx=10,
            pady=8,
        )
        controls_box.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))

        btn_grid = tk.Frame(controls_box, bg=settings.PANEL_BG)
        btn_grid.pack()

        self.btn_attack = tk.Button(
            btn_grid,
            text="[ A ] ATACAR",
            font=("Helvetica", 10, "bold"),
            bg=settings.BUTTON_BG,
            fg=settings.BUTTON_FG,
            padx=15,
            pady=8,
            cursor="hand2",
            command=self._on_attack_clicked,
        )
        self.btn_attack.grid(row=0, column=0, padx=4, pady=4)

        self.btn_special = tk.Button(
            btn_grid,
            text="[ S ] ESPECIAL",
            font=("Helvetica", 10, "bold"),
            bg=settings.BUTTON_BG,
            fg=settings.ACCENT_COLOR,
            padx=15,
            pady=8,
            cursor="hand2",
            command=self._on_special_clicked,
        )
        self.btn_special.grid(row=0, column=1, padx=4, pady=4)

        self.btn_defend = tk.Button(
            btn_grid,
            text="[ D ] DEFENDER",
            font=("Helvetica", 10, "bold"),
            bg=settings.BUTTON_BG,
            fg=settings.BUTTON_FG,
            padx=15,
            pady=8,
            cursor="hand2",
            command=self._on_defend_clicked,
        )
        self.btn_defend.grid(row=1, column=0, padx=4, pady=4)

        self.btn_heal = tk.Button(
            btn_grid,
            text="[ P ] POÇÃO",
            font=("Helvetica", 10, "bold"),
            bg=settings.BUTTON_BG,
            fg=settings.HEALTH_BAR_COLOR,
            padx=15,
            pady=8,
            cursor="hand2",
            command=self._on_heal_clicked,
        )
        self.btn_heal.grid(row=1, column=1, padx=4, pady=4)

    def _draw_arena(self, event: Optional[tk.Event] = None) -> None:
        """Desenha a arena e posiciona os sprites (Goblin agora espelhado de frente)."""
        self.arena_canvas.delete("all")

        w = self.arena_canvas.winfo_width()
        h = self.arena_canvas.winfo_height()

        if w < 50 or h < 50:
            return

        ground_y = int(h * 0.82)
        self.arena_canvas.create_rectangle(
            0, ground_y, w, h, fill="#1e1e2e", outline="#313244"
        )
        self.arena_canvas.create_line(
            0, ground_y, w, ground_y, fill=settings.ACCENT_COLOR, width=2
        )

        self.hero_x = int(w * 0.25)
        self.hero_y = ground_y - 125

        self.enemy_x = int(w * 0.75)
        self.enemy_y = ground_y - 125

        if self.hero_img:
            self.hero_sprite_id = self.arena_canvas.create_image(
                self.hero_x, self.hero_y, image=self.hero_img, anchor="center"
            )

        if self.enemy_img:
            self.enemy_sprite_id = self.arena_canvas.create_image(
                self.enemy_x, self.enemy_y, image=self.enemy_img, anchor="center"
            )

    def _animate_floating_text(self, x: int, y: int, text: str, color: str) -> None:
        """Anima números flutuantes de dano/cura subindo no Canvas."""
        text_id = self.arena_canvas.create_text(
            x, y, text=text, fill=color, font=("Helvetica", 16, "bold")
        )

        def step(count: int = 0) -> None:
            if count < 10:
                self.arena_canvas.move(text_id, 0, -2)
                self.root.after(40, lambda: step(count + 1))
            else:
                self.arena_canvas.delete(text_id)

        step()

    def _animate_attack(self, attacker: str) -> None:
        """Animação de arremesso do lutador."""
        if not hasattr(self, "hero_sprite_id") or not hasattr(self, "enemy_sprite_id"):
            return

        target_id = self.hero_sprite_id if attacker == "player" else self.enemy_sprite_id
        dx = 35 if attacker == "player" else -35

        self.arena_canvas.move(target_id, dx, 0)
        self.root.update()
        self.root.after(80)

        self.arena_canvas.move(target_id, -dx, 0)
        self.root.update()

    def _append_log(self, text: str) -> None:
        """Adiciona texto no histórico de ações."""
        if hasattr(self, "log_text"):
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, text + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)

    def _update_ui_state(self) -> None:
        """Sincroniza elementos visuais com o estado do motor."""
        if not hasattr(self, "player_hp_lbl"):
            return

        p = self.engine.player
        e = self.engine.enemy

        # Atualiza Nível, HP e Barra de Vida do Jogador
        self.player_level_lbl.config(text=f"Nível: {p.level}")
        self.player_hp_lbl.config(text=f"Vida: {p.health} / {p.max_health} HP")
        self.player_progress["value"] = (p.health / p.max_health) * 100 if p.max_health > 0 else 0

        # Atualiza XP e Barra de Experiência
        self.player_xp_lbl.config(text=f"XP: {p.xp} / {p.xp_to_next_level}")
        self.player_xp_progress["value"] = (p.xp / p.xp_to_next_level) * 100 if p.xp_to_next_level > 0 else 0

        # Atualiza HP e Barra de Vida do Inimigo
        self.enemy_hp_lbl.config(text=f"Vida: {e.health} / {e.max_health} HP")
        self.enemy_progress["value"] = (e.health / e.max_health) * 100 if e.max_health > 0 else 0

        # Atualiza Poções
        potions_text = f"Poções: {p.potions_count} | Especial CD: {p.special_attack_cooldown}"
        self.potions_lbl.config(text=potions_text)

        is_p_turn = self.engine.current_turn == "player"
        turn_str = "Sua Vez de Jogar!" if is_p_turn else "Turno do Inimigo..."
        self.turn_indicator_lbl.config(text=f"Turno: {turn_str}")

        if p.special_attack_cooldown > 0:
            sp_text = f"ESPECIAL ({p.special_attack_cooldown})"
            self.btn_special.config(state=tk.DISABLED, text=sp_text)
        else:
            self.btn_special.config(state=tk.NORMAL, text="[ S ] ESPECIAL")

    def _on_attack_clicked(self) -> None:
        self.engine.player_attack()

    def _on_special_clicked(self) -> None:
        self.engine.player_special_attack()

    def _on_defend_clicked(self) -> None:
        self.engine.player_defend()

    def _on_heal_clicked(self) -> None:
        self.engine.player_heal()

    def show_end_screen(self, winner: str, is_player_winner: bool, data: Dict[str, Any]) -> None:
        """Exibe a tela de resultado final com relatório da partida."""
        self._clear_container()

        end_frame = tk.Frame(self.container, bg=settings.BG_COLOR)
        end_frame.place(relx=0.5, rely=0.5, anchor="center")

        result_title = "🏆 VITÓRIA GLORIOSA!" if is_player_winner else "💀 DERROTA NA ARENA..."
        title_color = settings.HEALTH_BAR_COLOR if is_player_winner else (
            settings.ENEMY_HEALTH_BAR_COLOR
        )

        lbl_title = tk.Label(
            end_frame,
            text=result_title,
            font=("Helvetica", 28, "bold"),
            bg=settings.BG_COLOR,
            fg=title_color,
            pady=10,
        )
        lbl_title.pack()

        stats_box = tk.LabelFrame(
            end_frame,
            text=" Relatório da Partida ",
            font=("Helvetica", 12, "bold"),
            bg=settings.PANEL_BG,
            fg=settings.TEXT_COLOR,
            padx=30,
            pady=20,
        )
        stats_box.pack(fill=tk.X, pady=15)

        tk.Label(
            stats_box,
            text=f"Vencedor da Arena: {winner}",
            font=("Helvetica", 12, "bold"),
            bg=settings.PANEL_BG,
            fg=settings.ACCENT_COLOR,
        ).pack(anchor="w", pady=4)

        tk.Label(
            stats_box,
            text=f"Nível Final: {self.engine.player.level} (XP: {self.engine.player.xp}/{self.engine.player.xp_to_next_level})",
            font=("Helvetica", 11, "bold"),
            bg=settings.PANEL_BG,
            fg="#89b4fa",
        ).pack(anchor="w", pady=2)

        tk.Label(
            stats_box,
            text=f"Total de Turnos Jogados: {data.get('total_turns', 0)}",
            font=("Helvetica", 11),
            bg=settings.PANEL_BG,
            fg=settings.TEXT_COLOR,
        ).pack(anchor="w", pady=2)

        tk.Label(
            stats_box,
            text=f"Dano Total Causado: {data.get('total_damage_dealt', 0)} DP",
            font=("Helvetica", 11),
            bg=settings.PANEL_BG,
            fg=settings.TEXT_COLOR,
        ).pack(anchor="w", pady=2)

        tk.Label(
            stats_box,
            text=f"Poções Consumidas: {data.get('potions_used', 0)}",
            font=("Helvetica", 11),
            bg=settings.PANEL_BG,
            fg=settings.TEXT_COLOR,
        ).pack(anchor="w", pady=2)

        btn_restart = tk.Button(
            end_frame,
            text=" JOGAR NOVAMENTE",
            font=("Helvetica", 13, "bold"),
            bg=settings.BUTTON_BG,
            fg=settings.BUTTON_FG,
            activebackground=settings.ACCENT_COLOR,
            padx=30,
            pady=10,
            cursor="hand2",
            command=self.start_battle,
        )
        btn_restart.pack(pady=8, fill=tk.X)

        btn_main_menu = tk.Button(
            end_frame,
            text=" VOLTAR AO MENU PRINCIPAL",
            font=("Helvetica", 12),
            bg=settings.PANEL_BG,
            fg=settings.TEXT_COLOR,
            padx=30,
            pady=8,
            cursor="hand2",
            command=self.show_start_screen,
        )
        btn_main_menu.pack(pady=5, fill=tk.X)

    def on_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Reage a eventos emitidos pelo GameEngine."""
        if event_type == "GAME_STARTED":
            self._update_ui_state()
            self._append_log(">> Combate iniciado! Escolha sua primeira ação.")

        elif event_type == "PLAYER_ATTACKED":
            self._animate_attack("player")
            crit_str = " (CRÍTICO!)" if data.get("is_critical") else ""
            self._animate_floating_text(
                getattr(self, "enemy_x", 400), getattr(self, "enemy_y", 200),
                f"-{data['damage']}{crit_str}", settings.ENEMY_HEALTH_BAR_COLOR
            )
            self._update_ui_state()
            msg = f">> Você atacou {data['target']} causando {data['damage']} de dano{crit_str}!"
            self._append_log(msg)

        elif event_type == "PLAYER_SPECIAL_ATTACKED":
            self._animate_attack("player")
            self._animate_floating_text(
                getattr(self, "enemy_x", 400), getattr(self, "enemy_y", 200),
                f"-{data['damage']} GOLPE DEVASTADOR!", "#f9e2af"
            )
            self._update_ui_state()
            msg = f">> GOLPE DEVASTADOR! Você causou {data['damage']} de dano em {data['target']}!"
            self._append_log(msg)

        elif event_type == "PLAYER_DEFENDED":
            self._animate_floating_text(
                getattr(self, "hero_x", 200), getattr(self, "hero_y", 200),
                "DEFESA ATIVA ", settings.ACCENT_COLOR
            )
            self._update_ui_state()
            msg = ">> Você assumiu uma postura de defesa (-50% dano no próximo ataque)!"
            self._append_log(msg)

        elif event_type == "ENEMY_ATTACKED":
            self._animate_attack("enemy")
            def_str = " (DEFENDIDO! )" if data.get("is_defending") else ""
            self._animate_floating_text(
                getattr(self, "hero_x", 200), getattr(self, "hero_y", 200),
                f"-{data['damage']}{def_str}", settings.ENEMY_HEALTH_BAR_COLOR
            )
            msg = f">> {data['attacker']} atacou causando {data['damage']} de dano{def_str}!"
            self._append_log(msg)
            self._update_ui_state()

        elif event_type == "PLAYER_HEALED":
            self._animate_floating_text(
                getattr(self, "hero_x", 200), getattr(self, "hero_y", 200),
                f"+{data['healed_amount']} HP ", settings.HEALTH_BAR_COLOR
            )
            self._update_ui_state()
            self._append_log(f">> CURA! Você recuperou +{data['healed_amount']} HP.")

        elif event_type == "XP_GAINED":
            self._update_ui_state()
            self._append_log(f">> Você ganhou +{data['amount']} XP por derrotar o inimigo!")

        elif event_type == "LEVEL_UP":
            self._animate_floating_text(
                getattr(self, "hero_x", 200), getattr(self, "hero_y", 200),
                "LEVEL UP! ✨", "#f9e2af"
            )
            self._update_ui_state()
            self._append_log(
                f"🎉 LEVEL UP! Nível {data['new_level']} alcançado! "
                f"Vida restaurada ({data['health']}/{data['max_health']} HP) e Dano Base aumentado!"
            )

        elif event_type == "ACTION_FAILED":
            self._append_log(f">> AVISO: {data['reason']}")

        elif event_type == "GAME_OVER":
            self._update_ui_state()
            self.root.after(1200, lambda: self.show_end_screen(
                data["winner"], data["is_player_winner"], data
            ))

    def start(self) -> None:
        """Inicia a aplicação gráfica Tkinter."""
        self.root.mainloop()