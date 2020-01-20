from collections import namedtuple

from src.python.chess.chess_consts import b_range, white, black, castling_rooks, material, pieces,\
    initial_fen, kings, pawns

from src.python.chess.chess_interop import coords_to_chess, chess_to_coords

empty_set = set()

Undo = namedtuple("Undo", [
    "undo_balance",
    "undo_ca",
    "undo_ept",
    "undo_board",
    "redo_move"
])


class ChessState():
    # all 2d coords are in (y, x) form where positive y is down (from white's perspective),
    # this is to ease working with 2d array board representation
    # e.g. (0, 0) -> a8; (0, 7) -> h8; (7, 0) -> a1; (7,7) -> h1
    def __init__(
            self,
            is_done,  # If the game is in a complete state or not
            active_color,  # Which color (player) whose turn should be played next
            castling_available,  # A str containing all available castling moves, fen style
            en_passant_target,  # If the opponent played a pawn "leap", the coords of that target
            halfmoves,  # TODO The halfmove counter for 50-move stalemate rule
            move,  # The turn counter, incremented after each player has played a turn
            board,
            positions,
            material_balance):

        self.is_done = is_done
        self.active_color = active_color
        self.castling_available = castling_available
        self.en_passant_target = en_passant_target
        self.halfmoves = halfmoves  # TODO implement later
        self.move = move
        self.board = board
        self.positions = positions
        self.material_balance = material_balance

    def to_fen(self):
        # A FEN "record" defines a particular game position, all in one text line and using only the ASCII character
        # set.
        files = []

        for i in b_range:
            empty_c = 0
            file_str = ""

            for j in b_range:
                piece = self.board[i][j]

                if (piece is None):
                    empty_c += 1
                else:
                    file_str += piece if empty_c == 0 else str(empty_c) + piece
                    empty_c = 0

            if empty_c != 0:
                file_str += str(empty_c)

            files.append(file_str)

        return " ".join([
            "/".join(files),
            self.active_color,
            self.castling_available if self.castling_available is not None else "-",
            coords_to_chess(self.en_passant_target) if self.en_passant_target is not None else "-",
            str(self.halfmoves),
            str(self.move)
        ])

    def player_affinity(self):
        return 1 if self.active_color == white else -1

    def board_apply(self, move):
        (f_y, f_x) = move.from_
        (t_y, t_x) = move.to_
        piece = self.board[f_y][f_x]
        promotion = piece is not None and piece in pawns and (t_y == 0 or t_y == 7)
        queen = "Q" if self.active_color == white else "q"
        to_piece = queen if promotion else piece

        undos = [
            (move.from_, move.to_, piece)
        ]

        if move.victim is not None:
            undos.append((move.to_, None, move.victim))

        if piece is not None:
            self.positions[piece].discard(move.from_)
            self.positions[to_piece].add(move.to_)

        if move.victim is not None:
            self.positions[move.victim].discard(move.to_)

        self.board[t_y][t_x] = to_piece
        self.board[f_y][f_x] = None

        if move.ept_cap is not None:
            (ept, epp) = move.ept_cap
            (y, x) = ept
            self.positions[epp].discard(ept)
            self.board[y][x] = None
            undos.append((ept, None, epp))

        if move.castle is not None:
            # Have to move the rook too
            c_from = castling_rooks[move.castle]
            c_to = None

            if move.castle == "K":
                c_to = (7, 5)
            elif move.castle == "Q":
                c_to = (7, 3)
            elif move.castle == "k":
                c_to = (0, 5)
            else:
                c_to = (0, 3)

            c_piece = self.board[c_from[0]][c_from[1]]
            undos.append((c_from, c_to, c_piece))
            self.positions[c_piece].discard(c_from)
            self.positions[c_piece].add(c_to)
            self.board[c_to[0]][c_to[1]] = c_piece
            self.board[c_from[0]][c_from[1]] = None

        return undos

    def board_undo(self, undos):
        for undo in undos:
            (from_, to, piece) = undo
            (f_y, f_x) = from_
            self.board[f_y][f_x] = piece
            if to is not None:
                (t_y, t_x) = to
                self.board[t_y][t_x] = None  # If a victim needs to be replaced there will be a following undo for that

            if piece is not None:
                self.positions[piece].add(from_)
                self.positions[piece].discard(to)

        return self

    def apply(self, move):
        undo_balance = self.material_balance

        if move.victim is not None:
            self.material_balance -= material[move.victim]

        if move.victim in kings:
            self.is_done = True

        if move.ept_cap is not None:
            (pos, piece) = move.ept_cap
            self.material_balance -= material[piece]

        undo_ca = self.castling_available

        if move.new_castling_available is not None:
            self.castling_available = None if move.new_castling_available == "-" else move.new_castling_available

        undo_ept = self.en_passant_target
        self.en_passant_target = move.new_en_passant_target
        self.move += 1 if self.active_color == black else 0
        self.halfmoves = self.halfmoves + 1

        undo_board = self.board_apply(move)
        self.active_color = black if self.active_color == white else white

        return Undo(
            undo_balance,
            undo_ca,
            undo_ept,
            undo_board,
            move
        )

    def undo(self, undo):
        (
            undo_balance,
            undo_ca,
            undo_ept,
            undo_board,
            move
        ) = undo

        if undo_balance is not None:
            self.material_balance = undo_balance
        if undo_ca is not None:
            self.castling_available = undo_ca
        if undo_ept is not None:
            self.en_passant_target = undo_ept

        self.board_undo(undo_board)
        self.move -= 1 if self.active_color == white else 0
        self.halfmoves = self.halfmoves - 1
        self.active_color = black if self.active_color == white else white
        self.is_done = False
        return move

    def pos(self, pos):
        (y, x) = pos
        return self.board[y][x]


def fen_to_state(fen_str):
    [files, color, ca, ept, half_moves, moves] = fen_str.split(" ")
    board = []
    positions = {}
    i = 0
    balance = 0

    for p in pieces:
        positions[p] = set()

    for file_str in files.split("/"):
        file_arr = []

        for c in file_str:
            if c in pieces:
                file_arr.append(c)
                balance += material[c]
                positions.get(c).add((i, len(file_arr) - 1))
            else:
                for n in range(0, int(c)):
                    file_arr.append(None)
        board.append(file_arr)
        i += 1

    en_passant_target = chess_to_coords(ept) if ept != "-" else None
    castling_available = ca if ca != "-" else None

    state = ChessState(
        is_done=False,
        active_color=color,
        castling_available=castling_available,
        en_passant_target=en_passant_target,
        halfmoves=int(half_moves),
        move=int(moves),
        board=board,
        positions=positions,
        material_balance=balance
    )
    return state


initial_state = fen_to_state(initial_fen)