from src.chess.chess_agency import next_actions, score_move, ChessAgent
from src.chess.chess_state import fen_to_state
from src.chess.chess_movement import Move


def test_score_move():
    m1 = Move(
        from_=(2, 4), to_=(1, 3), victim=None, new_en_passant_target=None, ept_cap=((1, 3), 'p'),
        new_castling_available=None, castle=None
    )
    assert score_move(m1, "P") == -1120.0

    m2 = Move(
        from_=(6, 4), to_=(5, 3), victim='p', new_en_passant_target=None, ept_cap=None,
        new_castling_available=None, castle=None
    )
    assert score_move(m2, "P") == -1120.0

    m3 = Move(
        from_=(7, 4), to_=(7, 6), victim=None, new_en_passant_target=None, ept_cap=None,
        new_castling_available='-', castle='K'
    )
    assert score_move(m3, "K") == -990.0

    m4 = Move(
        from_=(6, 4), to_=(5, 3), victim='q', new_en_passant_target=None, ept_cap=None,
        new_castling_available=None, castle=None
    )
    assert score_move(m4, "P") == -1300.0

    m5 = Move(
        from_=(7, 4), to_=(7, 5), victim=None, new_en_passant_target=None, ept_cap=None,
        new_castling_available='-', castle=None
    )
    assert score_move(m5, "K") == -90.0

    m6 = Move(
        from_=(7, 5), to_=(7, 4), victim='q', new_en_passant_target=None, ept_cap=None,
        new_castling_available='-', castle=None
    )
    assert score_move(m6, "K") == -1008.0


def test_next_actions():
    s1 = fen_to_state("6k1/4p3/3pP3/6r1/1p3P2/3p4/PP2P3/R3K3 w Q d7 0 50")
    assert next_actions(s1) == [
        Move(
            from_=(4, 5), to_=(3, 6), victim='r', new_en_passant_target=None, ept_cap=None,
            new_castling_available=None, castle=None),
        Move(
            from_=(2, 4), to_=(1, 3), victim=None, new_en_passant_target=None, ept_cap=((1, 3), 'p'),
            new_castling_available=None, castle=None),
        Move(
            from_=(6, 4), to_=(5, 3), victim='p', new_en_passant_target=None, ept_cap=None,
            new_castling_available=None, castle=None),
        Move(
            from_=(7, 4), to_=(7, 2), victim=None, new_en_passant_target=None, ept_cap=None,
            new_castling_available='-', castle='Q'),
        Move(
            from_=(7, 0), to_=(7, 1), victim=None, new_en_passant_target=None, ept_cap=None,
            new_castling_available='-', castle=None),
        Move(
            from_=(7, 0), to_=(7, 2), victim=None, new_en_passant_target=None, ept_cap=None,
            new_castling_available='-', castle=None),
        Move(
            from_=(7, 0), to_=(7, 3), victim=None, new_en_passant_target=None, ept_cap=None,
            new_castling_available='-', castle=None),
        Move(
            from_=(4, 5), to_=(3, 5), victim=None, new_en_passant_target=None, ept_cap=None,
            new_castling_available=None, castle=None),
        Move(
            from_=(6, 0), to_=(5, 0), victim=None, new_en_passant_target=None, ept_cap=None,
            new_castling_available=None, castle=None),
        Move(
            from_=(6, 0), to_=(4, 0), victim=None, new_en_passant_target=(5, 0), ept_cap=None,
            new_castling_available=None, castle=None),
        Move(
            from_=(6, 1), to_=(5, 1), victim=None, new_en_passant_target=None, ept_cap=None,
            new_castling_available=None, castle=None),
        Move(
            from_=(6, 4), to_=(5, 4), victim=None, new_en_passant_target=None, ept_cap=None,
            new_castling_available=None, castle=None),
        Move(
            from_=(6, 4), to_=(4, 4), victim=None, new_en_passant_target=(5, 4), ept_cap=None,
            new_castling_available=None, castle=None),
        Move(
            from_=(7, 4), to_=(7, 5), victim=None, new_en_passant_target=None, ept_cap=None,
            new_castling_available='-', castle=None),
        Move(
            from_=(7, 4), to_=(6, 3), victim=None, new_en_passant_target=None, ept_cap=None,
            new_castling_available='-', castle=None),
        Move(
            from_=(7, 4), to_=(6, 5), victim=None, new_en_passant_target=None, ept_cap=None,
            new_castling_available='-', castle=None),
        Move(
            from_=(7, 4), to_=(7, 3), victim=None, new_en_passant_target=None, ept_cap=None,
            new_castling_available='-', castle=None
        )
    ]


def test_agent():
    s1 = fen_to_state("4k3/8/8/8/4q3/3P4/8/4K3 w - - 0 50")
    ca = ChessAgent(2)
    best = ca.start_game(s1)
    assert best == Move(
        from_=(5, 3), to_=(4, 4), victim='q', new_en_passant_target=None, ept_cap=None,
        new_castling_available=None, castle=None
    )