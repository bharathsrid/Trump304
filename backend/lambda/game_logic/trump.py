"""Trump selection and reveal logic for the 304 card game."""

from __future__ import annotations

from typing import Optional
from .models import GameState, Card, Suit, GamePhase


def validate_trump_selection(state: GameState, seat: int, suit: Suit, card: Card) -> tuple[bool, str]:
    """Validate trump suit and card selection."""
    if state.phase != GamePhase.TRUMP_SELECTION:
        return False, "Not in trump selection phase"
    if state.trumper_seat != seat:
        return False, "Only the trumper can select trump"
    if card.suit != suit:
        return False, "Trump card must be of the selected trump suit"

    player = state.get_player_by_seat(seat)
    if card not in player.hand:
        return False, "You don't have that card"

    return True, ""


def select_trump(state: GameState, seat: int, suit: Suit, card: Card) -> dict:
    """Set the trump suit and place the trump card face-down.

    Removes the trump card from the player's hand.
    """
    player = state.get_player_by_seat(seat)
    player.hand.remove(card)

    state.trump_suit = suit
    state.trump_card = card
    state.trump_revealed = False

    # In 3-player mode, go to card exchange phase
    if state.mode == 3:
        state.phase = GamePhase.CARD_EXCHANGE
        return {"trump_selected": True, "next_phase": "CARD_EXCHANGE"}

    # Otherwise go straight to playing
    state.phase = GamePhase.PLAYING
    _set_first_player(state)
    return {"trump_selected": True, "next_phase": "PLAYING"}


def validate_card_exchange(state: GameState, seat: int, cards: list[Card]) -> tuple[bool, str]:
    """Validate 3-player card exchange."""
    if state.phase != GamePhase.CARD_EXCHANGE:
        return False, "Not in card exchange phase"
    if state.trumper_seat != seat:
        return False, "Only the trumper can exchange cards"
    if len(cards) != 2:
        return False, "Must exchange exactly 2 cards"

    player = state.get_player_by_seat(seat)
    for card in cards:
        if card not in player.hand:
            return False, f"You don't have {card}"

    return True, ""


def exchange_cards(state: GameState, seat: int, cards_to_give: list[Card]) -> dict:
    """Exchange 2 cards with the center pile in 3-player mode.

    The 2 cards given away count toward opposing team's points at end of game.
    """
    player = state.get_player_by_seat(seat)

    # Remove cards from hand
    for card in cards_to_give:
        player.hand.remove(card)

    # Pick up center pile cards
    picked_up = list(state.center_pile)
    player.hand.extend(picked_up)

    # The discarded cards go to opposing team's trick pile
    # Store them in a special way — we'll credit them during scoring
    state.center_pile = cards_to_give  # These count as opposing team's points
    state.exchange_done = True

    state.phase = GamePhase.PLAYING
    _set_first_player(state)

    return {"exchange_done": True, "next_phase": "PLAYING"}


def skip_exchange(state: GameState, seat: int) -> tuple[bool, dict]:
    """Skip card exchange in 3-player mode."""
    if state.phase != GamePhase.CARD_EXCHANGE:
        return False, {"error": "Not in card exchange phase"}
    if state.trumper_seat != seat:
        return False, {"error": "Only the trumper can skip exchange"}

    state.exchange_done = True
    state.phase = GamePhase.PLAYING
    _set_first_player(state)

    return True, {"exchange_skipped": True, "next_phase": "PLAYING"}


def reveal_trump(state: GameState, requesting_seat: int) -> tuple[bool, str]:
    """Reveal the trump suit.

    Can be triggered by:
    - A non-trumper asking for reveal (when they want to cut)
    - The trumper voluntarily revealing

    Returns the trump card to the trumper's hand.
    """
    if state.trump_revealed:
        return False, "Trump is already revealed"
    if state.trump_suit is None:
        return False, "Trump has not been selected yet"

    state.trump_revealed = True

    # Return trump card to trumper's hand
    if state.trump_card is not None:
        trumper = state.get_player_by_seat(state.trumper_seat)
        trumper.hand.append(state.trump_card)

    return True, ""


def _set_first_player(state: GameState) -> None:
    """Set the first player to lead the first trick."""
    # If bid is exactly 304, trumper leads
    if state.current_bid and state.current_bid.amount == 304:
        state.turn_seat = state.trumper_seat
    else:
        # Player to the left of the dealer leads
        state.turn_seat = state.next_seat(state.dealer_seat)
    state.lead_seat = state.turn_seat
    state.trick_number = 1
