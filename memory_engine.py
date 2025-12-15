"""Motor gráfico simple para el hito Memory-M3.

Este archivo no debe modificarse durante la entrega: contiene la capa de
interfaz que pinta el tablero utilizando `pygame` y delega toda la lógica en
las funciones del módulo `logic` (o el que se inyecte al instanciar
``MemoryUI``).
"""
from __future__ import annotations

from types import ModuleType
from typing import Any, Dict, List, Optional, Tuple

import pygame

GameState = Dict[str, Any]
Position = Tuple[int, int]


class MemoryUI:
    """Encapsula la parte visual del juego de memoria.

    El alumnado solo debe tocar el módulo `logic`. Este motor asume que dicho
    módulo expone las constantes ``STATE_HIDDEN``, ``STATE_VISIBLE`` y
    ``STATE_FOUND`` además de las funciones ``create_game``, ``reveal_card``,
    ``resolve_pending`` y ``has_won``.
    """

    BG_COLOR = (12, 17, 29)
    GRID_COLOR = (18, 98, 151)
    TEXT_COLOR = (235, 239, 243)
    HIDDEN_CARD = (55, 71, 79)
    VISIBLE_CARD = (197, 202, 233)
    FOUND_CARD = (67, 160, 71)

    CARD_MARGIN = 12
    CARD_SIZE = 110
    HEADER_HEIGHT = 90
    FPS = 60
    REVEAL_DELAY_MS = 900

    def __init__(self, logic_module: ModuleType) -> None:
        self.logic = logic_module
        self.state_hidden = getattr(self.logic, "STATE_HIDDEN", "hidden")
        self.state_visible = getattr(self.logic, "STATE_VISIBLE", "visible")
        self.state_found = getattr(self.logic, "STATE_FOUND", "found")

        self.rows: int = 0
        self.cols: int = 0
        self.game: GameState = {}
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.font: Optional[pygame.font.Font] = None
        self.card_font: Optional[pygame.font.Font] = None
        self.lock_until: Optional[int] = None

    # Público -----------------------------------------------------------------
    def run(self, rows: int = 4, cols: int = 4) -> None:
        """Inicializa pygame y ejecuta el bucle principal del juego."""

        if rows * cols % 2 != 0:
            raise ValueError("El tablero debe tener un número par de casillas")

        pygame.init()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 34)
        self.card_font = pygame.font.Font(None, 72)

        width, height = self._compute_window_size(rows, cols)
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Memory M3")

        self.rows, self.cols = rows, cols
        self.game = self.logic.create_game(rows, cols)
        self.lock_until = None

        running = True
        while running:
            if not self.clock:
                break
            self.clock.tick(self.FPS)
            running = self._handle_events()
            self._update_logic()
            self._draw_scene()

        pygame.quit()

    # Bucle principal ---------------------------------------------------------
    def _handle_events(self) -> bool:
        assert self.screen is not None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)
        return True

    def _handle_click(self, pos: Tuple[int, int]) -> None:
        if self.lock_until is not None:
            return

        board_pos = self._pixel_to_board(pos)
        if board_pos is None:
            return

        row, col = board_pos
        turned = self.logic.reveal_card(self.game, row, col)
        if not turned:
            return

        pending = self.game.get("pending", [])
        if isinstance(pending, list) and len(pending) == 2:
            self.lock_until = pygame.time.get_ticks() + self.REVEAL_DELAY_MS

    def _update_logic(self) -> None:
        if self.lock_until is None:
            return

        now = pygame.time.get_ticks()
        if now < self.lock_until:
            return

        resolved, _ = self.logic.resolve_pending(self.game)
        self.lock_until = None if resolved else self.lock_until

    # Dibujo ------------------------------------------------------------------
    def _draw_scene(self) -> None:
        if self.screen is None:
            return

        self.screen.fill(self.BG_COLOR)
        self._draw_header()
        self._draw_cards()
        pygame.display.flip()

    def _draw_header(self) -> None:
        assert self.screen and self.font
        moves = int(self.game.get("moves", 0))
        matches = int(self.game.get("matches", 0))
        total = int(self.game.get("total_pairs", 0) or (self.rows * self.cols) // 2)

        summary = f"Movimientos: {moves}    Parejas: {matches}/{total}"
        summary_surface = self.font.render(summary, True, self.TEXT_COLOR)
        self.screen.blit(summary_surface, (20, 20))

        if self.logic.has_won(self.game):
            msg = "¡Completado! Pulsa ESC para cerrar"
        else:
            msg = "Haz clic en dos cartas para encontrar parejas"

        msg_surface = self.font.render(msg, True, self.TEXT_COLOR)
        self.screen.blit(msg_surface, (20, 50))

    def _draw_cards(self) -> None:
        assert self.screen and self.card_font
        board: List[List[Dict[str, Any]]] = self.game.get("board", [])
        for row_idx, row in enumerate(board):
            for col_idx, card in enumerate(row):
                rect = self._cell_rect(row_idx, col_idx)
                pygame.draw.rect(self.screen, self.GRID_COLOR, rect, border_radius=10)

                inner = rect.inflate(-6, -6)
                state = card.get("state")
                if state == self.state_found:
                    color = self.FOUND_CARD
                elif state == self.state_visible:
                    color = self.VISIBLE_CARD
                else:
                    color = self.HIDDEN_CARD

                pygame.draw.rect(self.screen, color, inner, border_radius=10)

                if state in (self.state_visible, self.state_found):
                    symbol = str(card.get("symbol", ""))
                    text_surface = self.card_font.render(symbol, True, self.BG_COLOR)
                    text_rect = text_surface.get_rect(center=inner.center)
                    self.screen.blit(text_surface, text_rect)

    # Helpers -----------------------------------------------------------------
    def _compute_window_size(self, rows: int, cols: int) -> Tuple[int, int]:
        width = cols * self.CARD_SIZE + (cols + 1) * self.CARD_MARGIN
        height = (
            rows * self.CARD_SIZE
            + (rows + 1) * self.CARD_MARGIN
            + self.HEADER_HEIGHT
        )
        return width, height

    def _cell_rect(self, row: int, col: int) -> pygame.Rect:
        x = self.CARD_MARGIN + col * (self.CARD_SIZE + self.CARD_MARGIN)
        y = (
            self.HEADER_HEIGHT
            + self.CARD_MARGIN
            + row * (self.CARD_SIZE + self.CARD_MARGIN)
        )
        return pygame.Rect(x, y, self.CARD_SIZE, self.CARD_SIZE)

    def _pixel_to_board(self, pos: Tuple[int, int]) -> Optional[Position]:
        x, y = pos
        if y < self.HEADER_HEIGHT:
            return None
        board: List[List[Any]] = self.game.get("board", [])
        for row_idx, row in enumerate(board):
            for col_idx, _ in enumerate(row):
                if self._cell_rect(row_idx, col_idx).collidepoint(x, y):
                    return row_idx, col_idx
        return None
