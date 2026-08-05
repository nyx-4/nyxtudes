import curses
from enum import Enum
from collections.abc import Iterator


type Cell = tuple[int, int]
type Game = set[Cell]


class CycleState(Enum):
    CYCLE_NOT_DETECTED = 0
    CYCLE_AND_CALCULATING_PERIOD = 1
    CYCLE_AND_STABLE_PERIOD = 2


def cell_neighbors(cell: Cell) -> Iterator[Cell]:
    "get all 8 neighbors of cells, and the `cell` itself also"
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            yield (cell[0] + i, cell[1] + j)


def games_neighbors(game: Game) -> Iterator[Cell]:
    "get neighbors of all cells in a game"
    for cell in game:
        yield from cell_neighbors(cell)


def will_live(cell: Cell, game: Game) -> bool:
    "whether this cell will 'live' in next generation, or not"
    num_live_neighbors: int = sum((cell in game) for cell in cell_neighbors(cell))

    return num_live_neighbors == 3 or (cell in game and num_live_neighbors == 4)


def next_state(game: Game) -> Game:
    "return next state of game"
    updated_game: Game = {
        cell for cell in games_neighbors(game) if will_live(cell, game)
    }
    return updated_game


def check_cycles(tortoise_eq_hare: bool, cycle: CycleState, period: int):
    if cycle == CycleState.CYCLE_AND_CALCULATING_PERIOD:
        if tortoise_eq_hare:
            cycle = CycleState.CYCLE_AND_STABLE_PERIOD
        else:
            period += 1

    elif cycle == CycleState.CYCLE_NOT_DETECTED and tortoise_eq_hare:
        cycle = CycleState.CYCLE_AND_CALCULATING_PERIOD
        period = 1

    match cycle:
        case CycleState.CYCLE_AND_CALCULATING_PERIOD:
            pstr: str = "Cycle Detected"
        case CycleState.CYCLE_AND_STABLE_PERIOD:
            pstr: str = f"Cycle Detected ({period=})"
        case _:
            pstr: str = ""

    return cycle, period, pstr


def setup_color_pairs() -> int:
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_MAGENTA)
    curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_RED)
    curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    return 7


def get_game(stdscr: curses.window, trans_ax: tuple[int, int]) -> Game:
    presets: tuple[Game, ...] = (
        {        
            (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 6), (0, 7), (0, 8), 
            (0, 9), (0, 10), (0, 12), (0, 13), (0, 14), (0, 15), (0, 16),
        },
        {(1, 1), (2, 2), (3, 0), (3, 1), (3, 2)},
        {(0, 2), (0, 3), (1, 1), (1, 2), (2, 0), (2, 1), (3, 0), (3, 1)},
      )  # fmt: skip
    game: Game = presets[0].copy()
    pstr = "click to toggle cells; type 0-9 to use built-in preset; press q to continue"

    print_game(stdscr, game, trans_ax, pstr)

    event: int = 0
    while chr(event) not in "qQ":  # 'q' to continue with given state
        event = stdscr.getch()
        pstr = "click to toggle cells; type 0-9 to use built-in preset; press q to continue"

        if event == curses.KEY_MOUSE:
            _, x, y, _, _ = curses.getmouse()
            cell_yx: Cell = (y + trans_ax[1]), (x // 2 + trans_ax[0])

            # toggle cell between on and off state
            game.remove(cell_yx) if cell_yx in game else game.add(cell_yx)

        elif event == 48:  # preset 0 is empty set
            game = set()

        elif 49 <= event <= 57:  # 1-9 changes preset
            try:
                game = presets[event - 49].copy()
            except IndexError:  # not enough preset defined
                pstr = f"Preset {event - 48} is not defined"

        print_game(stdscr, game, trans_ax, pstr)

    return game


def print_game(
    stdscr: curses.window, game: Game, trans_ax: tuple[int, int], pstr: str
) -> None:
    # TODO: update trans_ax when things moves out of view point
    stdscr.clear()

    for cell in game:
        y, x = (cell[0] - trans_ax[0]), 2 * (cell[1] - trans_ax[1])
        color = curses.color_pair((x + y) % 7 + 1)

        if 0 <= y < curses.LINES and 0 <= x < curses.COLS:
            stdscr.addstr(y, x, "  ", color)

    stdscr.addstr(0, 0, pstr, curses.color_pair(0))


def main(stdscr: curses.window) -> None:
    # if period_is_stable is True:
    #     period is length of cycle if cycle is detected else -1 (when cycle is not yet detected)
    # if period_is_stable is False:
    #     then cycle is detected but period is not yet known, and is updated after every iteration
    period: int = -1
    cycle: CycleState = CycleState.CYCLE_NOT_DETECTED
    trans_ax = (-10, -10)

    # clear screen, hide cursor, setup mouse, and setup color pairs
    stdscr.clear()
    curses.curs_set(0)
    curses.mousemask(1)
    setup_color_pairs()

    game: Game = get_game(stdscr, trans_ax)
    tortoise, hare = game, next_state(game)

    while True:
        cycle, period, pstr = check_cycles(tortoise == hare, cycle, period)
        print_game(stdscr, tortoise, trans_ax, pstr)

        tortoise = next_state(tortoise)
        hare = next_state(next_state(hare))

        stdscr.getkey()


if __name__ == "__main__":
    curses.wrapper(main)


# test functions
def test_will_live() -> None:
    cell1, cell2, cell3 = (2, 0), (3, 0), (3, 1)
    game: Game = {(1, 1), (2, 2), (3, 0), (3, 1), (3, 2)}

    assert will_live(cell1, game) is True
    assert will_live(cell2, game) is False
    assert will_live(cell3, game) is True


def test_next_state() -> None:
    game: Game = {(1, 1), (2, 2), (3, 0), (3, 1), (3, 2)}
    next_game: Game = {(3, 1), (2, 0), (2, 2), (3, 2), (4, 1)}

    assert next_state(game) == next_game


def test_check_cycle() -> None:
    # fmt: off
    assert check_cycles(True, CycleState.CYCLE_AND_CALCULATING_PERIOD, period=4) == (CycleState.CYCLE_AND_STABLE_PERIOD, 4, "Cycle Detected (period=4)")
    assert check_cycles(True, CycleState.CYCLE_AND_STABLE_PERIOD, period=4) == (CycleState.CYCLE_AND_STABLE_PERIOD, 4, "Cycle Detected (period=4)")
    assert check_cycles(True, CycleState.CYCLE_NOT_DETECTED, period=-1) == (CycleState.CYCLE_AND_CALCULATING_PERIOD, 1, "Cycle Detected")

    assert check_cycles(False, CycleState.CYCLE_AND_CALCULATING_PERIOD, period=4) == (CycleState.CYCLE_AND_CALCULATING_PERIOD, 5, "Cycle Detected")
    assert check_cycles(False, CycleState.CYCLE_AND_STABLE_PERIOD, period=4) == (CycleState.CYCLE_AND_STABLE_PERIOD, 4, "Cycle Detected (period=4)")
    assert check_cycles(False, CycleState.CYCLE_NOT_DETECTED, period=-1) == (CycleState.CYCLE_NOT_DETECTED, -1, "")
    # fmt: on
