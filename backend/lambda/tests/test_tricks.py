"""Tests for trick play, cutting, and scoring."""

import pytest
from game_logic.tricks import (
    get_calling_suit, get_valid_cards, validate_play,
    play_card, calculate_team_points, check_spoilt_trump,
    auto_play,
)
from game_logic.models import (
    GameState, GamePhase, Player, Card, Suit, Rank, TrickCard, Bid,
)


def _make_playing_game(mode: int = 4) -> GameState:
    """Create a game in PLAYING phase with known hands."""
    state = GameState(game_code="TEST01", mode=mode, phase=GamePhase.PLAYING)
    for i in range(mode):
        state.players.append(Player(
            player_id=f"p{i}", name=f"Player {i}", seat=i,
        ))
    state.dealer_seat = 0
    state.trumper_seat = 0
    state.trump_suit = Suit.HEARTS
    state.trump_revealed = False
    state.current_bid = Bid(seat=0, amount=160)
    state.trick_number = 1
    state.turn_seat = 1  # Left of dealer leads
    state.lead_seat = 1
    return state


def test_calling_suit_empty_trick():
    state = _make_playing_game()
    assert get_calling_suit(state) is None


def test_calling_suit_after_lead():
    state = _make_playing_game()
    card = Card(Suit.SPADES, Rank.JACK)
    state.current_trick.append(TrickCard(seat=1, card=card))
    assert get_calling_suit(state) == Suit.SPADES


def test_must_follow_suit():
    state = _make_playing_game()
    state.current_trick.append(TrickCard(
        seat=1, card=Card(Suit.SPADES, Rank.JACK),
    ))
    state.turn_seat = 2
    # Give seat 2 cards including spades
    p2 = state.get_player_by_seat(2)
    p2.hand = [
        Card(Suit.SPADES, Rank.SEVEN),
        Card(Suit.HEARTS, Rank.JACK),
        Card(Suit.CLUBS, Rank.ACE),
    ]
    valid = get_valid_cards(state, 2)
    assert len(valid) == 1
    assert valid[0].suit == Suit.SPADES


def test_can_play_any_card_when_no_suit():
    state = _make_playing_game()
    state.current_trick.append(TrickCard(
        seat=1, card=Card(Suit.SPADES, Rank.JACK),
    ))
    state.turn_seat = 2
    p2 = state.get_player_by_seat(2)
    p2.hand = [
        Card(Suit.HEARTS, Rank.JACK),
        Card(Suit.CLUBS, Rank.ACE),
    ]
    valid = get_valid_cards(state, 2)
    assert len(valid) == 2


def test_leading_can_play_any():
    state = _make_playing_game()
    p1 = state.get_player_by_seat(1)
    p1.hand = [
        Card(Suit.SPADES, Rank.JACK),
        Card(Suit.HEARTS, Rank.NINE),
        Card(Suit.CLUBS, Rank.ACE),
    ]
    valid = get_valid_cards(state, 1)
    assert len(valid) == 3


def test_higher_card_wins_trick():
    state = _make_playing_game()
    state.turn_seat = 1
    p1 = state.get_player_by_seat(1)
    p1.hand = [Card(Suit.SPADES, Rank.JACK)]
    p2 = state.get_player_by_seat(2)
    p2.hand = [Card(Suit.SPADES, Rank.NINE)]
    p3 = state.get_player_by_seat(3)
    p3.hand = [Card(Suit.SPADES, Rank.SEVEN)]
    p0 = state.get_player_by_seat(0)
    p0.hand = [Card(Suit.SPADES, Rank.TEN)]

    play_card(state, 1, Card(Suit.SPADES, Rank.JACK))
    play_card(state, 2, Card(Suit.SPADES, Rank.NINE))
    play_card(state, 3, Card(Suit.SPADES, Rank.SEVEN))
    result = play_card(state, 0, Card(Suit.SPADES, Rank.TEN))

    assert result.get("trick_won")
    assert result["winner_seat"] == 1  # J(30) beats all


def test_trump_cut_wins():
    state = _make_playing_game()
    state.trump_revealed = True

    p1 = state.get_player_by_seat(1)
    p1.hand = [Card(Suit.SPADES, Rank.JACK)]
    p2 = state.get_player_by_seat(2)
    p2.hand = [Card(Suit.HEARTS, Rank.SEVEN)]  # Trump cut
    p3 = state.get_player_by_seat(3)
    p3.hand = [Card(Suit.SPADES, Rank.NINE)]
    p0 = state.get_player_by_seat(0)
    p0.hand = [Card(Suit.SPADES, Rank.ACE)]

    state.turn_seat = 1
    play_card(state, 1, Card(Suit.SPADES, Rank.JACK))
    play_card(state, 2, Card(Suit.HEARTS, Rank.SEVEN))
    play_card(state, 3, Card(Suit.SPADES, Rank.NINE))
    result = play_card(state, 0, Card(Suit.SPADES, Rank.ACE))

    assert result["winner_seat"] == 2  # Trump 7 beats all non-trump


def test_hidden_trump_not_a_cut():
    """If trump is not revealed, playing a trump card doesn't count as a cut."""
    state = _make_playing_game()
    state.trump_revealed = False  # Hidden

    p1 = state.get_player_by_seat(1)
    p1.hand = [Card(Suit.SPADES, Rank.JACK)]
    p2 = state.get_player_by_seat(2)
    p2.hand = [Card(Suit.HEARTS, Rank.JACK)]  # This is trump suit but hidden
    p3 = state.get_player_by_seat(3)
    p3.hand = [Card(Suit.SPADES, Rank.SEVEN)]
    p0 = state.get_player_by_seat(0)
    p0.hand = [Card(Suit.SPADES, Rank.EIGHT)]

    state.turn_seat = 1
    play_card(state, 1, Card(Suit.SPADES, Rank.JACK))
    play_card(state, 2, Card(Suit.HEARTS, Rank.JACK))
    play_card(state, 3, Card(Suit.SPADES, Rank.SEVEN))
    result = play_card(state, 0, Card(Suit.SPADES, Rank.EIGHT))

    # Spade J should win because hearts J doesn't count as trump cut
    assert result["winner_seat"] == 1


def test_calculate_team_points():
    state = _make_playing_game()
    # Trumper team = seats 0, 2 (4-player)
    state.tricks_won = {
        0: [Card(Suit.SPADES, Rank.JACK), Card(Suit.CLUBS, Rank.NINE)],  # 30 + 20
        1: [Card(Suit.HEARTS, Rank.ACE)],  # 11
    }
    points = calculate_team_points(state)
    assert points["trumper_points"] == 50
    assert points["opposing_points"] == 11


def test_spoilt_trump_detection():
    state = _make_playing_game()
    state.trump_suit = Suit.HEARTS
    # All 8 hearts cards in trumper team's trick piles (seats 0, 2)
    hearts_cards = [Card(Suit.HEARTS, r) for r in Rank]
    state.tricks_won = {
        0: hearts_cards[:4],
        2: hearts_cards[4:],
    }
    assert check_spoilt_trump(state) is True


def test_not_spoilt_when_split():
    state = _make_playing_game()
    state.trump_suit = Suit.HEARTS
    hearts = [Card(Suit.HEARTS, r) for r in Rank]
    # Split between both teams
    state.tricks_won = {
        0: hearts[:6],
        1: hearts[6:],
    }
    assert check_spoilt_trump(state) is False


def test_auto_play():
    state = _make_playing_game()
    state.turn_seat = 1
    p1 = state.get_player_by_seat(1)
    p1.hand = [Card(Suit.SPADES, Rank.SEVEN), Card(Suit.CLUBS, Rank.EIGHT)]
    result = auto_play(state, 1)
    assert "card_played" in result
    assert len(p1.hand) == 1


def test_validate_play_wrong_turn():
    state = _make_playing_game()
    state.turn_seat = 1
    p2 = state.get_player_by_seat(2)
    p2.hand = [Card(Suit.SPADES, Rank.JACK)]
    valid, err = validate_play(state, 2, Card(Suit.SPADES, Rank.JACK))
    assert not valid
    assert "Not your turn" in err
