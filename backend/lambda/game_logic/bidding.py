"""Bidding rules engine for the 304 card game."""

from __future__ import annotations

from typing import Optional
from .models import GameState, Bid, GamePhase

MIN_BID = 150
MAX_BID = 304
BID_STEP = 10
SPECIAL_BID_THRESHOLD = 200


def start_bidding(state: GameState) -> None:
    """Initialize bidding phase. First bidder is left of dealer."""
    state.phase = GamePhase.BIDDING
    state.bids = []
    state.current_bid = None
    state.bid_turn_seat = state.next_seat(state.dealer_seat)


def get_partner_seat(state: GameState, seat: int) -> Optional[int]:
    """Return partner's seat in 4-player mode, None otherwise."""
    if state.mode != 4:
        return None
    return (seat + 2) % 4


def _player_has_bid(state: GameState, seat: int) -> bool:
    """Check if a player has already placed a bid or pass."""
    return any(b.seat == seat for b in state.bids)


def _highest_bid_amount(state: GameState) -> int:
    """Return the current highest bid amount, or 0 if no bids."""
    amounts = [b.amount for b in state.bids if b.amount is not None]
    return max(amounts) if amounts else 0


def _any_200_plus_bid(state: GameState) -> bool:
    """Check if any bid of 200+ has been placed."""
    return any(b.amount is not None and b.amount >= SPECIAL_BID_THRESHOLD for b in state.bids)


def _partner_bid_amount(state: GameState, seat: int) -> Optional[int]:
    """Return the partner's bid amount, or None if partner hasn't bid or passed."""
    partner = get_partner_seat(state, seat)
    if partner is None:
        return None
    for b in state.bids:
        if b.seat == partner and b.amount is not None:
            return b.amount
    return None


def validate_bid(state: GameState, seat: int, amount: Optional[int]) -> tuple[bool, str]:
    """Validate a bid or pass.

    Args:
        state: Current game state
        seat: Seat making the bid
        amount: Bid amount, or None for pass

    Returns:
        (valid, error_message) tuple
    """
    if state.phase != GamePhase.BIDDING:
        return False, "Not in bidding phase"

    if state.bid_turn_seat != seat:
        return False, "Not your turn to bid"

    # Pass is always allowed
    if amount is None:
        return True, ""

    # Validate bid amount
    if amount < MIN_BID:
        return False, f"Minimum bid is {MIN_BID}"
    if amount > MAX_BID:
        return False, f"Maximum bid is {MAX_BID}"
    if amount != MAX_BID and amount % BID_STEP != 0:
        return False, f"Bid must be a multiple of {BID_STEP}"

    current_highest = _highest_bid_amount(state)
    if current_highest > 0 and amount <= current_highest:
        return False, f"Bid must exceed current highest bid of {current_highest}"

    has_bid = _player_has_bid(state, seat)
    any_200 = _any_200_plus_bid(state)
    is_200_plus = amount >= SPECIAL_BID_THRESHOLD

    # Check if player already bid
    if has_bid:
        # Can only bid again if making a 200+ bid and no one has bid 200+ yet
        if not (is_200_plus and not any_200):
            return False, "You have already bid or passed"

    # Cannot overbid yourself unless someone else overbid you first
    own_bids = [b.amount for b in state.bids if b.seat == seat and b.amount is not None]
    if own_bids:
        my_highest = max(own_bids)
        # Check if someone overbid us
        someone_overbid = any(
            b.amount is not None and b.amount > my_highest and b.seat != seat
            for b in state.bids
        )
        if not someone_overbid:
            return False, "Cannot overbid yourself unless someone has overbid you"

    # Partner overbidding rules (4-player only)
    partner_amount = _partner_bid_amount(state, seat)
    if partner_amount is not None and amount > partner_amount:
        # Cannot overbid partner unless an opponent has already overbid them,
        # OR this is a 200+ bid and no 200+ bids exist yet
        partner = get_partner_seat(state, seat)
        opponent_overbid_partner = any(
            b.amount is not None and b.amount > partner_amount
            and b.seat != seat and b.seat != partner
            for b in state.bids
        )
        if not opponent_overbid_partner:
            if not (is_200_plus and not any_200):
                return False, "Cannot overbid your partner unless an opponent has overbid them"

    return True, ""


def place_bid(state: GameState, seat: int, amount: Optional[int]) -> dict:
    """Place a bid or pass. Returns event dict for broadcasting.

    Assumes validate_bid was called first.
    """
    bid = Bid(seat=seat, amount=amount)
    state.bids.append(bid)

    if amount is not None:
        state.current_bid = bid

    # Determine next bidder or end bidding
    result = _advance_bidding(state)
    return result


def _advance_bidding(state: GameState) -> dict:
    """Advance to next bidder or conclude bidding.

    Returns event information.
    """
    num_players = len(state.players)
    seats = sorted(p.seat for p in state.players)
    current = state.bid_turn_seat

    # Find next eligible bidder
    for _ in range(num_players):
        current = state.next_seat(current)

        # Skip players who already bid (unless 200+ rules apply)
        if _player_has_bid(state, current):
            # Check if they can re-bid under 200+ rules
            any_200 = _any_200_plus_bid(state)
            if any_200:
                continue  # Already a 200+ bid exists, no re-bidding
            # If no 200+ yet, they might be able to re-bid with 200+
            # But we don't know their intent, so we skip for now
            continue

        # This player hasn't bid yet
        state.bid_turn_seat = current
        return {"next_bidder": current}

    # All players have bid — check if bidding is done
    return _conclude_bidding(state)


def _conclude_bidding(state: GameState) -> dict:
    """Conclude bidding phase and determine trumper."""
    if state.current_bid is None:
        # No one bid — dealer forced to bid minimum
        forced_bid = Bid(seat=state.dealer_seat, amount=MIN_BID)
        state.bids.append(forced_bid)
        state.current_bid = forced_bid

    state.trumper_seat = state.current_bid.seat
    state.phase = GamePhase.TRUMP_SELECTION

    return {
        "bidding_complete": True,
        "trumper_seat": state.trumper_seat,
        "bid": state.current_bid.amount,
    }


def get_scoring_points(bid_amount: int) -> tuple[int, int]:
    """Return (win_points, lose_points) based on bid range."""
    if bid_amount == 304:
        return 10, 7
    if bid_amount >= 200:
        return 6, 5
    return 5, 3
