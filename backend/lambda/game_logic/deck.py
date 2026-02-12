"""Deck creation, shuffling, and dealing for the 304 card game."""

import random
from .models import Card, Suit, Rank, GameState


def create_deck() -> list[Card]:
    """Create a full 32-card deck for 304."""
    return [Card(suit=s, rank=r) for s in Suit for r in Rank]


def shuffle_deck(deck: list[Card]) -> list[Card]:
    """Shuffle deck in-place and return it."""
    random.shuffle(deck)
    return deck


def deal(state: GameState) -> None:
    """Deal cards to all players based on game mode.

    Mutates state: sets player hands, deck, and center_pile.
    """
    deck = shuffle_deck(create_deck())
    mode = state.mode
    num_players = len(state.players)
    seats = sorted(p.seat for p in state.players)

    # Clear existing hands
    for p in state.players:
        p.hand = []
    state.center_pile = []

    # Determine dealing order starting from left of dealer
    dealer_idx = seats.index(state.dealer_seat)
    deal_order = [seats[(dealer_idx + 1 + i) % num_players] for i in range(num_players)]

    card_idx = 0

    if mode == 2:
        # 10 cards each: 4, 4, 2 rounds. 12 cards remain as center draw pile.
        for batch_size in (4, 4, 2):
            for seat in deal_order:
                player = state.get_player_by_seat(seat)
                player.hand.extend(deck[card_idx:card_idx + batch_size])
                card_idx += batch_size
        state.center_pile = deck[card_idx:]

    elif mode == 3:
        # 10 cards each: 4, 4, 2 rounds. 2 cards remain in center.
        for batch_size in (4, 4, 2):
            for seat in deal_order:
                player = state.get_player_by_seat(seat)
                player.hand.extend(deck[card_idx:card_idx + batch_size])
                card_idx += batch_size
        state.center_pile = deck[card_idx:]

    elif mode == 4:
        # 8 cards each: 4, 4 rounds. No center pile.
        for batch_size in (4, 4):
            for seat in deal_order:
                player = state.get_player_by_seat(seat)
                player.hand.extend(deck[card_idx:card_idx + batch_size])
                card_idx += batch_size

    state.deck = []  # All cards dealt out or in center pile
