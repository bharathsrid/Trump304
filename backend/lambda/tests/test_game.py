"""Tests for game state machine — full lifecycle."""

import pytest
from game_logic.game import (
    create_game, join_game, start_game, handle_bid,
    handle_trump_selection, handle_play_card, handle_ask_trump,
    handle_reveal_trump, get_player_view, next_game,
)
from game_logic.models import (
    GameState, GamePhase, Card, Suit, Rank, Player,
)


def test_create_game():
    state, player = create_game(4, "Alice")
    assert state.mode == 4
    assert state.phase == GamePhase.WAITING
    assert len(state.players) == 1
    assert player.name == "Alice"
    assert player.seat == 0
    assert len(state.game_code) == 6


def test_join_game():
    state, _ = create_game(4, "Alice")
    success, player = join_game(state, "Bob")
    assert success
    assert player.name == "Bob"
    assert player.seat == 1
    assert len(state.players) == 2


def test_join_full_game():
    state, _ = create_game(2, "Alice")
    join_game(state, "Bob")
    success, err = join_game(state, "Charlie")
    assert not success
    assert "full" in err.lower()


def test_start_game():
    state, _ = create_game(4, "Alice")
    join_game(state, "Bob")
    join_game(state, "Charlie")
    join_game(state, "Dave")
    success, _ = start_game(state)
    assert success
    assert state.phase == GamePhase.BIDDING
    # All players should have 8 cards
    for p in state.players:
        assert len(p.hand) == 8


def test_cannot_start_incomplete():
    state, _ = create_game(4, "Alice")
    join_game(state, "Bob")
    success, err = start_game(state)
    assert not success


def test_full_bidding_flow():
    state, _ = create_game(4, "Alice")
    join_game(state, "Bob")
    join_game(state, "Charlie")
    join_game(state, "Dave")
    start_game(state)

    # Bidding: seat left of dealer bids first
    first_bidder = state.bid_turn_seat
    handle_bid(state, first_bidder, 160)

    # Others pass
    while state.phase == GamePhase.BIDDING:
        handle_bid(state, state.bid_turn_seat, None)

    assert state.phase == GamePhase.TRUMP_SELECTION
    assert state.trumper_seat == first_bidder


def test_player_view_hides_trump():
    state, _ = create_game(4, "Alice")
    join_game(state, "Bob")
    join_game(state, "Charlie")
    join_game(state, "Dave")
    start_game(state)

    state.phase = GamePhase.PLAYING
    state.trumper_seat = 0
    state.trump_suit = Suit.HEARTS
    state.trump_card = Card(Suit.HEARTS, Rank.JACK)
    state.trump_revealed = False

    # Non-trumper should not see trump suit
    view = get_player_view(state, 1)
    assert "trump_suit" not in view or view.get("trump_suit") is None

    # Trumper should see it
    view = get_player_view(state, 0)
    assert view["trump_suit"] == "hearts"


def test_player_view_shows_hand():
    state, _ = create_game(4, "Alice")
    join_game(state, "Bob")
    join_game(state, "Charlie")
    join_game(state, "Dave")
    start_game(state)

    view = get_player_view(state, 0)
    assert "your_hand" in view
    assert len(view["your_hand"]) == 8


def test_card_from_id_roundtrip():
    card = Card(Suit.HEARTS, Rank.JACK)
    assert card.id == "J_hearts"
    restored = Card.from_id("J_hearts")
    assert restored == card


def test_card_beats_same_suit():
    j = Card(Suit.SPADES, Rank.JACK)
    nine = Card(Suit.SPADES, Rank.NINE)
    assert j.beats(nine, None, False, Suit.SPADES)
    assert not nine.beats(j, None, False, Suit.SPADES)


def test_card_beats_trump():
    trump7 = Card(Suit.HEARTS, Rank.SEVEN)
    spadeJ = Card(Suit.SPADES, Rank.JACK)
    # Trump beats non-trump when revealed
    assert trump7.beats(spadeJ, Suit.HEARTS, True, Suit.SPADES)
    # But not when hidden
    assert not trump7.beats(spadeJ, Suit.HEARTS, False, Suit.SPADES)


def test_next_game_rotates_dealer():
    state, _ = create_game(4, "Alice")
    join_game(state, "Bob")
    join_game(state, "Charlie")
    join_game(state, "Dave")
    start_game(state)

    old_dealer = state.dealer_seat
    state.phase = GamePhase.SCORING  # Simulate game end
    success, _ = next_game(state)
    assert success
    assert state.dealer_seat == state.next_seat(old_dealer)
    assert state.phase == GamePhase.BIDDING
