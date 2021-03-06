from itertools import chain

from src.python.chess.chess_movement import get_moves, targeted_by, dir_left_right,\
    in_board
from src.python.chess.chess_consts import kings, pawns, white, material, color_o,\
    affinity, black, lowest_score, highest_score
from src.python.primitive import interleave
from src.python.search import GameSearch


def score_end(chess_state):
    if chess_state.is_done:
        # the player affinity is used here to make losing 1 better than the default value in search
        return chess_state.player_affinity() + (lowest_score if chess_state.active_color is white else highest_score)
    else:
        # Presumption that this function is called with a !is_done state only when there are no available moves
        return 0


# Avoid trading pieces when losing unless the difference is big enough
losing_side_tradeoff_penalty = (material["R"] - (material["N"] - 1))


# At the leaf nodes need to assess if the position landed on is a good trade outcome if it"s under attack,
# this is my attempt to handle "The Horizon Effect"
def horizon_outcome(chess_state, p_color, subject, pos):
    # This function depends on the lists being generated from least to greatest abs(material)
    (enemies, friends) = targeted_by(chess_state, p_color, pos)

    # Slows things down too much
    # trade_off_bonus = -affinity[p_color] * losing_side_tradeoff_penalty if chess_state.is_losing(p_color) else 0
    trade_off_bonus = 0

    if enemies:
        ordering = interleave(enemies, friends)
        avengers = list(chain(ordering, [enemies[len(friends)]]) if len(enemies) > len(friends) else ordering)
        victim = subject

        for i, (_, p) in enumerate(avengers):
            m1 = material[victim]
            m2 = material[p]
            if abs(m1) >= abs(m2) or i == len(avengers) - 1:
                trade_off_bonus -= m1
                victim = p
            else:
                break

    return trade_off_bonus


rank_bonus = [None, 120, 60, 13, 14, 10, 0]


def pawn_bonus(chess_state, p_color):
    us_pawn = "P" if p_color == white else "p"
    bonus = 0
    promotion_rank = 0 if p_color == white else 7
    fwd = -1 if p_color == white else 1

    for (y, x) in chess_state.positions[us_pawn]:
        bonus += rank_bonus[abs(promotion_rank - y)]

        for left_right in dir_left_right:
            to = (-fwd + y, left_right + x)

            if in_board(to):
                piece = chess_state.pos(to)

                if piece is not None and piece == us_pawn:
                    bonus += 5

    return bonus


def knight_on_edge(chess_state, p_color):
    knight = "N" if p_color == white else "n"
    bonus = 0

    for (y, x) in chess_state.positions[knight]:
        if y == 0 or y == 7 or x == 0 or x == 7:
            bonus -= 25
    return bonus


# "Evaluation" -- assess the balance of a position
def score_state(chess_state, last_move):
    if chess_state.is_done:
        return score_end(chess_state)
    else:
        piece_moved = chess_state.pos(last_move.to_)
        material_score = chess_state.material_balance
        # The trade off bonus needs to be assessed from the perspective of the player that last moved
        # which is not the player to play
        p_color = color_o[chess_state.active_color]

        # If moving a non-king (because king safety was already checked), need to assess a penalty if this
        # move results in a bad trade
        if piece_moved not in kings:
            material_score += horizon_outcome(chess_state, p_color, piece_moved, last_move.to_)

        bonus = 0

        # TODO
        # Stacked Pinners
        # Open rays
        # Keep pieces together endgame

        for c in (white, black):
            c_bonus = pawn_bonus(chess_state, c)
            c_bonus += knight_on_edge(chess_state, c)
            bonus += c_bonus * affinity[c]

        return material_score + bonus


# This is used to guess at what a good move looks like, the better the guess the more likely to produce
# an alphaBeta prune
def ranking_score(move, move_lookup, piece):
    base_score = 100 if piece in kings or piece in pawns else 200

    if move in move_lookup["critical_path"]:
        base_score *= 100

    if move in move_lookup["pruners"]:
        base_score *= 50

    bonus_co = 11

    if move.castle is not None:
        base_score *= bonus_co

    if move.victim is not None or move.ept_cap is not None:
        p_material = abs(material[piece])
        v_material = abs(material[move.victim or move.ept_cap[1]])
        base_score *= ((v_material - p_material + 100) / 500 + bonus_co)

    return -base_score


def next_actions(chess_state, move_lookup):
    moves = get_moves(chess_state)
    return sorted(moves, key=lambda m: ranking_score(m, move_lookup, chess_state.pos(m.from_)))


def apply_action(chess_state, move):
    undo = chess_state.apply(move)
    return (chess_state, undo)


def undo_action(chess_state, back):
    redo = chess_state.undo(back)
    return (chess_state, redo)


chess_search = GameSearch(score_state, next_actions, apply_action, undo_action, score_end)
