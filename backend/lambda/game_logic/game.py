"""Game state machine — orchestrates the full game lifecycle."""

from __future__ import annotations

import uuid
import random
import string
from datetime import datetime, timezone
from typing import Optional

from .models import GameState, GamePhase, Player, Card, Suit
from .deck import deal
from .bidding import start_bidding, validate_bid, place_bid, get_scoring_points
from .trump import (
    validate_trump_selection, select_trump,
    validate_card_exchange, exchange_cards, skip_exchange,
    reveal_trump,
)
from .tricks import (
    validate_play, play_card, auto_play,
    calculate_team_points, check_spoilt_trump, get_valid_cards,
)


def generate_game_code() -> str:
    """Generate a 6-character alphanumeric game code."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=6))


def create_game(mode: int, creator_name: str) -> tuple[GameState, Player]:
    """Create a new game and add the creator as the first player.

    Returns (game_state, creator_player).
    """
    if mode not in (2, 3, 4):
        raise ValueError("Mode must be 2, 3, or 4")

    game_code = generate_game_code()
    state = GameState(
        game_code=game_code,
        mode=mode,
        phase=GamePhase.WAITING,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    # Initialize scores for all seats
    for i in range(mode):
        state.scores[i] = 0

    player = Player(
        player_id=str(uuid.uuid4()),
        name=creator_name,
        seat=0,
    )
    state.players.append(player)

    return state, player


def join_game(state: GameState, player_name: str) -> tuple[bool, str | Player]:
    """Add a player to the game.

    Returns (success, error_message | player).
    """
    if state.phase != GamePhase.WAITING:
        return False, "Game has already started"

    if len(state.players) >= state.mode:
        return False, "Game is full"

    # Assign next available seat
    taken_seats = {p.seat for p in state.players}
    seat = next(i for i in range(state.mode) if i not in taken_seats)

    player = Player(
        player_id=str(uuid.uuid4()),
        name=player_name,
        seat=seat,
    )
    state.players.append(player)

    return True, player


def start_game(state: GameState) -> tuple[bool, str]:
    """Start the game once all players have joined."""
    if state.phase != GamePhase.WAITING:
        return False, "Game already started"
    if len(state.players) != state.mode:
        return False, f"Need {state.mode} players, have {len(state.players)}"

    # Pick random dealer for first game
    state.dealer_seat = random.choice([p.seat for p in state.players])

    # Deal cards
    state.phase = GamePhase.DEALING
    deal(state)

    # Start bidding
    start_bidding(state)

    return True, ""


def handle_bid(state: GameState, seat: int, amount: Optional[int]) -> tuple[bool, dict]:
    """Handle a bid or pass action.

    Returns (success, result_dict).
    """
    valid, err = validate_bid(state, seat, amount)
    if not valid:
        return False, {"error": err}

    result = place_bid(state, seat, amount)
    return True, result


def handle_trump_selection(state: GameState, seat: int,
                            suit_str: str, card_id: str) -> tuple[bool, dict]:
    """Handle trump suit selection."""
    try:
        suit = Suit(suit_str)
        card = Card.from_id(card_id)
    except (ValueError, KeyError):
        return False, {"error": "Invalid suit or card"}

    valid, err = validate_trump_selection(state, seat, suit, card)
    if not valid:
        return False, {"error": err}

    result = select_trump(state, seat, suit, card)
    return True, result


def handle_card_exchange(state: GameState, seat: int,
                          card_ids: list[str]) -> tuple[bool, dict]:
    """Handle 3-player card exchange."""
    try:
        cards = [Card.from_id(cid) for cid in card_ids]
    except (ValueError, KeyError):
        return False, {"error": "Invalid card"}

    valid, err = validate_card_exchange(state, seat, cards)
    if not valid:
        return False, {"error": err}

    result = exchange_cards(state, seat, cards)
    return True, result


def handle_skip_exchange(state: GameState, seat: int) -> tuple[bool, dict]:
    """Handle skipping card exchange in 3-player mode."""
    success, result = skip_exchange(state, seat)
    if not success:
        return False, result
    return True, result


def handle_play_card(state: GameState, seat: int, card_id: str) -> tuple[bool, dict]:
    """Handle playing a card."""
    try:
        card = Card.from_id(card_id)
    except (ValueError, KeyError):
        return False, {"error": "Invalid card"}

    # Determine if this is a cut attempt
    from .tricks import get_calling_suit
    calling_suit = get_calling_suit(state)
    wants_to_cut = (
        calling_suit is not None
        and card.suit != calling_suit
        and card.suit == state.trump_suit
        and state.trump_revealed
    )

    valid, err = validate_play(state, seat, card, wants_to_cut=wants_to_cut)
    if not valid:
        return False, {"error": err}

    result = play_card(state, seat, card)

    # Check if game is over
    if result.get("game_over"):
        scoring = _score_game(state)
        result.update(scoring)

    return True, result


def handle_ask_trump(state: GameState, seat: int) -> tuple[bool, dict]:
    """Handle a non-trumper asking for trump reveal."""
    if state.trump_revealed:
        return False, {"error": "Trump is already revealed"}
    if seat == state.trumper_seat:
        return False, {"error": "You are the trumper — use reveal_trump instead"}
    if state.phase != GamePhase.PLAYING:
        return False, {"error": "Not in playing phase"}

    # Verify this player actually needs to cut (has no calling suit cards)
    calling_suit = get_calling_suit(state)
    if calling_suit is None:
        return False, {"error": "No trick in progress to cut"}

    player = state.get_player_by_seat(seat)
    has_calling_suit = any(c.suit == calling_suit for c in player.hand)
    if has_calling_suit:
        return False, {"error": "You have cards in the calling suit — cannot ask for trump"}

    success, err = reveal_trump(state, seat)
    if not success:
        return False, {"error": err}

    return True, {
        "trump_revealed": True,
        "suit": state.trump_suit.value,
        "trump_card": state.trump_card.id if state.trump_card else None,
    }


def handle_reveal_trump(state: GameState, seat: int) -> tuple[bool, dict]:
    """Handle trumper voluntarily revealing trump."""
    if seat != state.trumper_seat:
        return False, {"error": "Only the trumper can reveal trump"}
    if state.phase != GamePhase.PLAYING:
        return False, {"error": "Not in playing phase"}

    success, err = reveal_trump(state, seat)
    if not success:
        return False, {"error": err}

    return True, {
        "trump_revealed": True,
        "suit": state.trump_suit.value,
        "trump_card": state.trump_card.id if state.trump_card else None,
    }


def handle_timeout(state: GameState, seat: int) -> tuple[bool, dict]:
    """Handle turn timeout — auto-play a random valid card."""
    if state.turn_seat != seat:
        return False, {"error": "Not this player's turn"}

    result = auto_play(state, seat)

    if result.get("game_over"):
        scoring = _score_game(state)
        result.update(scoring)

    result["timeout"] = True
    return True, result


def _score_game(state: GameState) -> dict:
    """Score the completed game and update cumulative score points."""
    state.phase = GamePhase.SCORING

    # Check spoilt trump first
    if check_spoilt_trump(state):
        return {
            "spoilt": True,
            "trumper_points": 0,
            "opposing_points": 0,
            "scores": dict(state.scores),
        }

    points = calculate_team_points(state)
    bid_amount = state.current_bid.amount
    trumper_points = points["trumper_points"]
    win_points, lose_points = get_scoring_points(bid_amount)

    trumper_won = trumper_points >= bid_amount

    trumper_team = state.get_trumper_team_seats()
    opposing_team = state.get_opposing_team_seats()

    if trumper_won:
        for seat in trumper_team:
            state.scores[seat] = state.scores.get(seat, 0) + win_points
    else:
        for seat in opposing_team:
            state.scores[seat] = state.scores.get(seat, 0) + lose_points

    state.games_played += 1

    return {
        "trumper_won": trumper_won,
        "trumper_points": trumper_points,
        "opposing_points": points["opposing_points"],
        "bid": bid_amount,
        "points_awarded": win_points if trumper_won else lose_points,
        "scores": dict(state.scores),
    }


def next_game(state: GameState) -> tuple[bool, str]:
    """Reset for the next game, rotating dealer."""
    if state.phase != GamePhase.SCORING:
        return False, "Current game not finished"

    # Rotate dealer clockwise
    state.dealer_seat = state.next_seat(state.dealer_seat)

    # Reset game state
    state.bids = []
    state.current_bid = None
    state.bid_turn_seat = None
    state.trumper_seat = None
    state.trump_suit = None
    state.trump_card = None
    state.trump_revealed = False
    state.exchange_done = False
    state.current_trick = []
    state.tricks_won = {}
    state.turn_seat = None
    state.turn_deadline = None
    state.trick_number = 0
    state.lead_seat = None
    state.center_pile = []

    # Deal and start bidding
    state.phase = GamePhase.DEALING
    deal(state)
    start_bidding(state)

    return True, ""


def get_player_view(state: GameState, seat: int) -> dict:
    """Return the game state visible to a specific player.

    Hides opponent hands and the trump suit (if unrevealed).
    """
    player = state.get_player_by_seat(seat)

    view = {
        "game_code": state.game_code,
        "mode": state.mode,
        "phase": state.phase.value,
        "players": [p.to_public_dict() for p in state.players],
        "dealer_seat": state.dealer_seat,
        "your_seat": seat,
        "your_hand": [c.id for c in player.hand] if player else [],
        "bids": [b.to_dict() for b in state.bids],
        "current_bid": state.current_bid.to_dict() if state.current_bid else None,
        "trumper_seat": state.trumper_seat,
        "trump_revealed": state.trump_revealed,
        "current_trick": [tc.to_dict() for tc in state.current_trick],
        "turn_seat": state.turn_seat,
        "trick_number": state.trick_number,
        "scores": state.scores,
        "games_played": state.games_played,
    }

    # Only show trump info if revealed or player is trumper
    if state.trump_revealed:
        view["trump_suit"] = state.trump_suit.value if state.trump_suit else None
        view["trump_card"] = state.trump_card.id if state.trump_card else None
    elif seat == state.trumper_seat:
        view["trump_suit"] = state.trump_suit.value if state.trump_suit else None
        view["trump_card"] = state.trump_card.id if state.trump_card else None

    # Show valid cards if it's player's turn
    if state.turn_seat == seat and state.phase == GamePhase.PLAYING:
        view["valid_cards"] = [c.id for c in get_valid_cards(state, seat)]

    # Bidding turn indicator
    if state.phase == GamePhase.BIDDING:
        view["bid_turn_seat"] = state.bid_turn_seat

    # Points won by each team (visible to all)
    trumper_team = set(state.get_trumper_team_seats())
    view["team_tricks_points"] = {}
    for s, cards in state.tricks_won.items():
        team_key = "trumper" if s in trumper_team else "opposing"
        current = view["team_tricks_points"].get(team_key, 0)
        view["team_tricks_points"][team_key] = current + sum(c.points for c in cards)

    # Center pile count (not contents) for 2/3 player
    if state.mode in (2, 3):
        view["center_pile_count"] = len(state.center_pile)

    return view
