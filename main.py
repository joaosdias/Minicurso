"""Ponto de entrada do jogo RPG de Arena em Turnos.

Este arquivo é responsável por inicializar o GameEngine e escolher a interface
de apresentação (GUI ou CLI) com base nos argumentos passados por linha de comando.

Exemplos de execução:
    python main.py          # Executa a interface gráfica Tkinter (padrão)
    python main.py --gui    # Executa a interface gráfica Tkinter
    python main.py --cli    # Executa a interface no terminal
"""

import argparse
from core.engine import GameEngine
from ui.cli_view import CLIView

def main() -> None:
    """Função principal que analisa argumentos da CLI e inicia o jogo."""
    parser = argparse.ArgumentParser(
        description="RPG de Arena em Turnos - Projeto Base para Minicurso de Git"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--gui",
        action="store_true",
        default=True,
        help="Inicia o jogo no modo de Interface Gráfica (Tkinter) [Padrão]",
    )
    group.add_argument(
        "--cli",
        action="store_true",
        help="Inicia o jogo no modo de Interface de Linha de Comando (Terminal)",
    )

    args = parser.parse_args()

    engine = GameEngine()

    if args.cli:
        cli_view = CLIView(engine)
        cli_view.run_loop()
    else:
        try:
            from ui.gui_view import GUIView
            gui_view = GUIView(engine)
            gui_view.start()
        except ImportError as err:
            print(f"Não foi possível carregar a interface gráfica Tkinter: {err}")
            cli_view = CLIView(engine)
            cli_view.run_loop()


if __name__ == "__main__":
    main()
