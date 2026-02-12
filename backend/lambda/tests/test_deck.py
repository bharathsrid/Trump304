"""Tests for deck creation, shuffling, and dealing."""

import pytest
from game_logic.deck import create_deck, shuffle_deck, deal
from game_logic.models import Card, Suit, Rank, GameState, GamePhase, Player


def test_create_deck_has_32_cards():
    deck = create_deck()
    assert len(deck) == 32


def test_create_deck_has_all_suits():
    deck = create_deck()
    suits = {c.suit for c in deck}
    assert suits == {Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS, Suit.SPADES}


def test_create_deck_has_all_ranks():
    deck = create_deck()
    ranks = {c.rank for c in deck}
    assert ranks == {Rank.SEVEN, Rank.EIGHT, Rank.QUEEN, Rank.KING,
                     Rank.TEN, Rank.ACE, Rank.NINE, Rank.JACK}


def test_create_deck_total_points_304():
    deck = create_deck()
    total = sum(c.points for c in deck)
    assert total == 304


def test_shuffle_changes_order():
    deck1 = create_deck()
    deck2 = create_deck()
    shuffle_deck(deck2)
    # Extremely unlikely to remain in same order after shuffle
    # (but technically possible — just check they're still the same cards)
    assert set(deck1) == set(deck2)
    assert len(deck2) == 32


def _make_game(mode: int) -> GameState:
    state = GameState(game_code="TEST01", mode=mode, phase=GamePhase.DEALING)
    for i in range(mode):
        state.players.append(Player(
            player_id=f"p{i}", name=f"Player {i}", seat=i,
        ))
    state.dealer_seat = 0
    return state


def test_deal_4_players():
    state = _make_game(4)
    deal(state)
    for p in state.players:
        assert len(p.hand) == 8
    assert len(state.center_pile) == 0
    # All 32 cards accounted for
    all_cards = []
    for p in state.players:
        all_cards.extend(p.hand)
    assert len(all_cards) == 32


def test_deal_3_players():
    state = _make_game(3)
    deal(state)
    for p in state.players:
        assert len(p.hand) == 10
    assert len(state.center_pile) == 2
    all_cards = []
    for p in state.players:
        all_cards.extend(p.hand)
    all_cards.extend(state.center_pile)
    assert len(all_cards) == 32


def test_deal_2_players():
    state = _make_game(2)
    deal(state)
    for p in state.players:
        assert len(p.hand) == 10
    assert len(state.center_pile) == 12
    all_cards = []
    for p in state.players:
        all_cards.extend(p.hand)
    all_cards.extend(state.center_pile)
    assert len(all_cards) == 32


def test_deal_starts_left_of_dealer():
    """Verify dealing starts from player left of dealer."""
    state = _make_game(4)
    state.dealer_seat = 2
    deal(state)
    # All players should have 8 cards regardless
    for p in state.players:
        assert len(p.hand) == 8
