"""Tests for bidding rules engine."""

import pytest
from game_logic.bidding import (
    start_bidding, validate_bid, place_bid, get_scoring_points,
)
from game_logic.models import GameState, GamePhase, Player, Bid


def _make_game(mode: int = 4) -> GameState:
    state = GameState(game_code="TEST01", mode=mode, phase=GamePhase.DEALING)
    for i in range(mode):
        state.players.append(Player(
            player_id=f"p{i}", name=f"Player {i}", seat=i,
        ))
    state.dealer_seat = 0
    return state


def test_start_bidding():
    state = _make_game()
    start_bidding(state)
    assert state.phase == GamePhase.BIDDING
    # First bidder should be seat 1 (left of dealer at seat 0)
    assert state.bid_turn_seat == 1


def test_minimum_bid():
    state = _make_game()
    start_bidding(state)
    # Bid below minimum
    valid, err = validate_bid(state, 1, 140)
    assert not valid
    assert "150" in err


def test_bid_must_be_multiple_of_10():
    state = _make_game()
    start_bidding(state)
    valid, err = validate_bid(state, 1, 155)
    assert not valid
    assert "multiple" in err


def test_valid_bid():
    state = _make_game()
    start_bidding(state)
    valid, err = validate_bid(state, 1, 150)
    assert valid


def test_bid_must_exceed_current():
    state = _make_game()
    start_bidding(state)
    place_bid(state, 1, 160)
    # Next bidder (seat 2) tries to bid 150 — too low
    valid, err = validate_bid(state, 2, 150)
    assert not valid


def test_pass_is_valid():
    state = _make_game()
    start_bidding(state)
    valid, _ = validate_bid(state, 1, None)
    assert valid


def test_cannot_bid_twice_normal():
    state = _make_game()
    start_bidding(state)
    place_bid(state, 1, 160)
    state.bid_turn_seat = 1  # Force turn back to seat 1
    valid, err = validate_bid(state, 1, 170)
    assert not valid


def test_wrong_turn():
    state = _make_game()
    start_bidding(state)
    valid, err = validate_bid(state, 2, 150)
    assert not valid
    assert "Not your turn" in err


def test_forced_dealer_bid():
    """If everyone passes, dealer is forced to bid minimum."""
    state = _make_game()
    start_bidding(state)
    # All 4 players pass
    for seat in [1, 2, 3, 0]:
        state.bid_turn_seat = seat
        place_bid(state, seat, None)
    # After all pass, bidding should conclude with dealer forced bid
    assert state.phase == GamePhase.TRUMP_SELECTION
    assert state.trumper_seat == 0  # dealer
    assert state.current_bid.amount == 150


def test_cannot_overbid_partner_normally():
    """In 4-player, cannot overbid partner without opponent overbidding first."""
    state = _make_game(4)
    start_bidding(state)
    # Seat 1 bids 160
    place_bid(state, 1, 160)
    # Seat 2 passes
    state.bid_turn_seat = 2
    place_bid(state, 2, None)
    # Seat 3 (partner of seat 1) tries to overbid
    state.bid_turn_seat = 3
    valid, err = validate_bid(state, 3, 170)
    assert not valid
    assert "partner" in err.lower()


def test_scoring_tokens_low_bid():
    win, lose = get_scoring_points(150)
    assert win == 5
    assert lose == 3


def test_scoring_tokens_high_bid():
    win, lose = get_scoring_points(200)
    assert win == 6
    assert lose == 5


def test_scoring_tokens_304():
    win, lose = get_scoring_points(304)
    assert win == 10
    assert lose == 7


def test_max_bid_validation():
    state = _make_game()
    start_bidding(state)
    valid, _ = validate_bid(state, 1, 304)
    assert valid
    valid, err = validate_bid(state, 1, 310)
    assert not valid
