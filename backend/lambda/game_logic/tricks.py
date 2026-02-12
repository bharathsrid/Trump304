"""Trick play, cutting, and trick scoring for the 304 card game."""

from __future__ import annotations

import random
from typing import Optional
from .models import GameState, Card, Suit, TrickCard, GamePhase, RANK_POINTS


def get_calling_suit(state: GameState) -> Optional[Suit]:
    """Return the suit of the first card played in the current trick."""
    if state.current_trick:
        return state.current_trick[0].card.suit
    return None


def get_valid_cards(state: GameState, seat: int) -> list[Card]:
    """Return list of cards the player can legally play."""
    player = state.get_player_by_seat(seat)
    hand = player.hand
    calling_suit = get_calling_suit(state)

    if not hand:
        return []

    # Leading the trick — can play anything
    if calling_suit is None:
        return list(hand)

    # Must follow suit if possible
    same_suit = [c for c in hand if c.suit == calling_suit]
    if same_suit:
        return same_suit

    # No cards in calling suit — can play anything
    # (Cutting logic is handled in play_card validation, not here.
    #  Player can choose to cut with trump or discard.)
    return list(hand)


def validate_play(state: GameState, seat: int, card: Card,
                   wants_to_cut: bool = False) -> tuple[bool, str]:
    """Validate that a card play is legal.

    Args:
        state: Current game state
        seat: Seat playing the card
        card: Card being played
        wants_to_cut: Whether the player intends this as a trump cut
    """
    if state.phase != GamePhase.PLAYING:
        return False, "Not in playing phase"
    if state.turn_seat != seat:
        return False, "Not your turn"

    player = state.get_player_by_seat(seat)
    if card not in player.hand:
        return False, "You don't have that card"

    valid = get_valid_cards(state, seat)
    if card not in valid:
        return False, "You must follow suit"

    calling_suit = get_calling_suit(state)

    # Cutting rules
    if calling_suit is not None and card.suit != calling_suit:
        if wants_to_cut and card.suit == state.trump_suit:
            # Player wants to cut with trump
            if seat == state.trumper_seat:
                # Trumper must reveal before cutting
                if not state.trump_revealed:
                    return False, "Trumper must reveal trump before cutting"
            else:
                # Non-trumper must ask for reveal first (handled at action layer)
                if not state.trump_revealed:
                    return False, "Trump must be revealed before cutting"

    return True, ""


def play_card(state: GameState, seat: int, card: Card) -> dict:
    """Play a card into the current trick.

    Returns event dict with what happened.
    """
    player = state.get_player_by_seat(seat)
    player.hand.remove(card)

    is_cut = False
    calling_suit = get_calling_suit(state)

    if calling_suit is not None and card.suit != calling_suit:
        # Check if this is a trump cut
        if state.trump_revealed and card.suit == state.trump_suit:
            is_cut = True
        # If trump not revealed and card happens to be trump suit,
        # it does NOT count as a cut (per rules section 2.5.1 Option B)

    trick_card = TrickCard(seat=seat, card=card)
    state.current_trick.append(trick_card)

    result = {"card_played": card.id, "seat": seat, "is_cut": is_cut}

    # Check if trick is complete
    if len(state.current_trick) == len(state.players):
        trick_result = _resolve_trick(state)
        result.update(trick_result)

    else:
        # Advance to next player
        state.turn_seat = state.next_seat(seat)
        result["next_turn"] = state.turn_seat

    return result


def _resolve_trick(state: GameState) -> dict:
    """Resolve a completed trick — determine winner, collect cards."""
    calling_suit = state.current_trick[0].card.suit
    winner_tc = state.current_trick[0]

    for tc in state.current_trick[1:]:
        if tc.card.beats(
            winner_tc.card,
            trump_suit=state.trump_suit,
            trump_revealed=state.trump_revealed,
            calling_suit=calling_suit,
        ):
            winner_tc = tc

    winner_seat = winner_tc.seat
    trick_points = sum(tc.card.points for tc in state.current_trick)
    trick_cards = [tc.card for tc in state.current_trick]

    # Add cards to winner's trick pile
    if winner_seat not in state.tricks_won:
        state.tricks_won[winner_seat] = []
    state.tricks_won[winner_seat].extend(trick_cards)

    state.current_trick = []
    state.trick_number += 1

    result = {
        "trick_won": True,
        "winner_seat": winner_seat,
        "trick_points": trick_points,
    }

    # 2-player: draw cards from center pile after trick
    if state.mode == 2 and state.center_pile:
        draw_result = _draw_cards_2p(state, winner_seat)
        result["draws"] = draw_result

    # Check if game is over
    total_tricks = 8  # Always 8 tricks in 304
    if state.mode == 2:
        total_tricks = 8  # Each player starts with 10 cards - 1 trump = 9, but draw pile extends
        # Actually in 2-player, they draw after each trick until pile is exhausted
        # Game ends when both players have no cards left
        p0 = state.get_player_by_seat(state.players[0].seat)
        p1 = state.get_player_by_seat(state.players[1].seat)
        if not p0.hand and not p1.hand:
            result["game_over"] = True
            return result

    if state.trick_number > total_tricks and state.mode != 2:
        # Force reveal trump on last trick if not revealed
        if not state.trump_revealed:
            from .trump import reveal_trump
            reveal_trump(state, state.trumper_seat)
            result["trump_revealed_final"] = True

        result["game_over"] = True
        return result

    # Check for 2/3 player: if all hands are empty
    all_empty = all(len(p.hand) == 0 for p in state.players)
    if all_empty:
        result["game_over"] = True
        return result

    # Next trick — winner leads
    state.turn_seat = winner_seat
    state.lead_seat = winner_seat
    result["next_turn"] = winner_seat

    return result


def _draw_cards_2p(state: GameState, trick_winner_seat: int) -> list[dict]:
    """In 2-player mode, both players draw from center pile. Winner draws first."""
    draws = []
    seats = [trick_winner_seat, state.next_seat(trick_winner_seat)]

    for seat in seats:
        if not state.center_pile:
            break
        card = state.center_pile.pop(0)
        player = state.get_player_by_seat(seat)
        player.hand.append(card)
        draws.append({"seat": seat, "card": card.id})

    return draws


def auto_play(state: GameState, seat: int) -> dict:
    """Auto-play a random valid card for timeout."""
    valid = get_valid_cards(state, seat)
    if not valid:
        return {"error": "No valid cards to play"}

    card = random.choice(valid)

    # If trump not revealed and this would be a cut, try to avoid it
    # by picking a non-trump card if available
    calling_suit = get_calling_suit(state)
    if calling_suit and card.suit != calling_suit and not state.trump_revealed:
        non_trump = [c for c in valid if c.suit != state.trump_suit]
        if non_trump:
            card = random.choice(non_trump)

    return play_card(state, seat, card)


def calculate_team_points(state: GameState) -> dict[str, int]:
    """Calculate total points for each team after all tricks played."""
    trumper_team = set(state.get_trumper_team_seats())
    opposing_team = set(state.get_opposing_team_seats())

    trumper_points = 0
    opposing_points = 0

    for seat, cards in state.tricks_won.items():
        points = sum(c.points for c in cards)
        if seat in trumper_team:
            trumper_points += points
        else:
            opposing_points += points

    # 3-player: center pile discarded cards count for opposing team
    if state.mode == 3 and state.exchange_done and state.center_pile:
        opposing_points += sum(c.points for c in state.center_pile)

    # Trump card points — if never played, add to trumper's total
    if state.trump_card and not state.trump_revealed:
        trumper_points += state.trump_card.points

    return {
        "trumper_points": trumper_points,
        "opposing_points": opposing_points,
    }


def check_spoilt_trump(state: GameState) -> bool:
    """Check if all 8 trump cards ended up with trumper's team (spoilt game)."""
    if state.trump_suit is None:
        return False

    trumper_team = set(state.get_trumper_team_seats())
    trump_cards_in_team = 0

    for seat, cards in state.tricks_won.items():
        if seat in trumper_team:
            trump_cards_in_team += sum(1 for c in cards if c.suit == state.trump_suit)

    # Count trump card itself if not played
    if state.trump_card and not state.trump_revealed:
        trump_cards_in_team += 1

    # Count any trump cards still in trumper's hand (shouldn't happen after game)
    for seat in trumper_team:
        player = state.get_player_by_seat(seat)
        if player:
            trump_cards_in_team += sum(1 for c in player.hand if c.suit == state.trump_suit)

    return trump_cards_in_team == 8
