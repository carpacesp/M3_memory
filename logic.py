"""Plantilla con las funciones que el alumnado debe completar para M3.

La capa gráfica llama a estas funciones para mover el estado del juego. No es
necesario crear clases; basta con manipular listas, diccionarios y tuplas.
"""
from __future__ import annotations

import random
from typing import Dict, List, Tuple

STATE_HIDDEN = "hidden"
STATE_VISIBLE = "visible"
STATE_FOUND = "found"

Card = Dict[str, str]
Board = List[List[Card]]
Position = Tuple[int, int]
GameState = Dict[str, object]


def build_symbol_pool(rows: int, cols: int) -> List[str]:
    """Crea la lista de símbolos necesaria para rellenar todo el tablero.

    Sugerencia: parte de un listado básico de caracteres y duplícalo tantas
    veces como parejas necesites. Después baraja el resultado.
    """

    total_cells = rows * cols
    total_pairs = total_cells // 2

    base_symbols: List[str] = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&?*+-=")

    # Si el tablero necesita más parejas que símbolos disponibles,
    # repetimos la lista (habrá símbolos repetidos y no pasa nada).
    available = base_symbols[:]
    while len(available) < total_pairs:
        available.extend(base_symbols)

    chosen = available[:total_pairs]

    pool: List[str] = []
    for symbol in chosen:
        pool.append(symbol)
        pool.append(symbol)

    random.shuffle(pool)
    return pool


def create_game(rows: int, cols: int) -> GameState:
    """Genera el diccionario con el estado inicial del juego.

    El estado debe incluir:
    - ``board``: lista de listas con cartas (cada carta es un dict con
      ``symbol`` y ``state``).
    - ``pending``: lista de posiciones descubiertas en el turno actual.
    - ``moves``: contador de movimientos realizados.
    - ``matches``: parejas acertadas.
    - ``total_pairs``: número total de parejas disponibles.
    - ``rows`` / ``cols``: dimensiones del tablero.
    """

    if rows * cols % 2 != 0:
        raise ValueError("El tablero debe tener un número par de casillas")

    symbols = build_symbol_pool(rows, cols)

    board: Board = []
    idx = 0
    for r in range(rows):
        row_cards: List[Card] = []
        for c in range(cols):
            row_cards.append({"symbol": symbols[idx], "state": STATE_HIDDEN})
            idx += 1
        board.append(row_cards)

    game: GameState = {
        "board": board,
        "pending": [],
        "moves": 0,
        "matches": 0,
        "total_pairs": (rows * cols) // 2,
        "rows": rows,
        "cols": cols,
    }
    return game


def reveal_card(game: GameState, row: int, col: int) -> bool:
    """Intenta descubrir la carta ubicada en ``row``, ``col``.

    Debe devolver ``True`` si el estado ha cambiado (es decir, la carta estaba
    oculta y ahora está visible) y ``False`` en cualquier otro caso. No permitas
    dar la vuelta a más de dos cartas simultáneamente.
    """

    board = game.get("board", [])
    if not isinstance(board, list) or not board:
        return False

    if row < 0 or col < 0:
        return False
    if row >= len(board):
        return False
    if col >= len(board[row]):
        return False

    pending = game.get("pending")
    if not isinstance(pending, list):
        pending = []
        game["pending"] = pending

    # No se pueden tener más de 2 cartas "pendientes".
    if len(pending) >= 2:
        return False

    card = board[row][col]
    if not isinstance(card, dict):
        return False

    if card.get("state") != STATE_HIDDEN:
        return False

    card["state"] = STATE_VISIBLE
    pending.append((row, col))
    return True


def resolve_pending(game: GameState) -> Tuple[bool, bool]:
    """Resuelve el turno si hay dos cartas pendientes.

    Devuelve una tupla ``(resuelto, pareja_encontrada)``. Este método debe
    ocultar las cartas si son diferentes o marcarlas como ``found`` cuando
    coincidan. Además, incrementa ``moves`` y ``matches`` según corresponda.
    """

    pending = game.get("pending")
    if not isinstance(pending, list) or len(pending) != 2:
        return (False, False)

    board = game.get("board", [])
    if not isinstance(board, list) or not board:
        return (False, False)

    (r1, c1) = pending[0]
    (r2, c2) = pending[1]

    # Si por lo que sea la posición está mal, limpiamos pendiente y listo.
    if (
        not isinstance(r1, int)
        or not isinstance(c1, int)
        or not isinstance(r2, int)
        or not isinstance(c2, int)
    ):
        game["pending"] = []
        return (True, False)

    if r1 < 0 or r2 < 0 or r1 >= len(board) or r2 >= len(board):
        game["pending"] = []
        return (True, False)
    if c1 < 0 or c2 < 0 or c1 >= len(board[r1]) or c2 >= len(board[r2]):
        game["pending"] = []
        return (True, False)

    card1 = board[r1][c1]
    card2 = board[r2][c2]

    # Un movimiento es "he intentado una pareja".
    game["moves"] = int(game.get("moves", 0)) + 1

    found_pair = False
    if card1.get("symbol") == card2.get("symbol"):
        card1["state"] = STATE_FOUND
        card2["state"] = STATE_FOUND
        game["matches"] = int(game.get("matches", 0)) + 1
        found_pair = True
    else:
        # Si no coinciden, se vuelven a ocultar.
        if card1.get("state") == STATE_VISIBLE:
            card1["state"] = STATE_HIDDEN
        if card2.get("state") == STATE_VISIBLE:
            card2["state"] = STATE_HIDDEN

    game["pending"] = []
    return (True, found_pair)


def has_won(game: GameState) -> bool:
    """Indica si se han encontrado todas las parejas."""

    matches = int(game.get("matches", 0))
    total_pairs = int(game.get("total_pairs", 0))
    return matches >= total_pairs
