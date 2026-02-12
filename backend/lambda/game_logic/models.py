"""Data models for the 304 card game."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional


class Suit(str, enum.Enum):
    HEARTS = "hearts"
    DIAMONDS = "diamonds"
    CLUBS = "clubs"
    SPADES = "spades"


class Rank(str, enum.Enum):
    SEVEN = "7"
    EIGHT = "8"
    QUEEN = "Q"
    KING = "K"
    TEN = "10"
    ACE = "A"
    NINE = "9"
    JACK = "J"


# Points per rank — this also defines the card hierarchy (higher = stronger)
RANK_POINTS: dict[Rank, int] = {
    Rank.SEVEN: 0,
    Rank.EIGHT: 0,
    Rank.QUEEN: 2,
    Rank.KING: 3,
    Rank.TEN: 10,
    Rank.ACE: 11,
    Rank.NINE: 20,
    Rank.JACK: 30,
}

# For tie-breaking within the same point value (7 vs 8, both 0 points)
RANK_ORDER: dict[Rank, int] = {
    Rank.SEVEN: 0,
    Rank.EIGHT: 1,
    Rank.QUEEN: 2,
    Rank.KING: 3,
    Rank.TEN: 4,
    Rank.ACE: 5,
    Rank.NINE: 6,
    Rank.JACK: 7,
}


class GamePhase(str, enum.Enum):
    WAITING = "WAITING"
    DEALING = "DEALING"
    BIDDING = "BIDDING"
    TRUMP_SELECTION = "TRUMP_SELECTION"
    CARD_EXCHANGE = "CARD_EXCHANGE"  # 3-player only
    PLAYING = "PLAYING"
    SCORING = "SCORING"


@dataclass(frozen=True)
class Card:
    suit: Suit
    rank: Rank

    @property
    def points(self) -> int:
        return RANK_POINTS[self.rank]

    @property
    def order(self) -> int:
        return RANK_ORDER[self.rank]

    @property
    def id(self) -> str:
        return f"{self.rank.value}_{self.suit.value}"

    @staticmethod
    def from_id(card_id: str) -> Card:
        rank_str, suit_str = card_id.rsplit("_", 1)
        return Card(suit=Suit(suit_str), rank=Rank(rank_str))

    def beats(self, other: Card, trump_suit: Optional[Suit], trump_revealed: bool, calling_suit: Suit) -> bool:
        """Return True if self beats other in a trick context."""
        # Trump beats non-trump (only if trump is revealed)
        if trump_revealed and trump_suit:
            if self.suit == trump_suit and other.suit != trump_suit:
                return True
            if self.suit != trump_suit and other.suit == trump_suit:
                return False

        # Same suit — higher rank wins
        if self.suit == other.suit:
            if self.points != other.points:
                return self.points > other.points
            return self.order > other.order

        # Different suits, neither is (revealed) trump — lead suit wins
        if other.suit == calling_suit:
            return False
        if self.suit == calling_suit:
            return True
        return False

    def __str__(self) -> str:
        return self.id


@dataclass
class Player:
    player_id: str
    name: str
    seat: int
    connection_id: Optional[str] = None
    hand: list[Card] = field(default_factory=list)

    def to_public_dict(self) -> dict:
        return {
            "player_id": self.player_id,
            "name": self.name,
            "seat": self.seat,
        }


@dataclass
class Bid:
    seat: int
    amount: Optional[int]  # None = pass

    def to_dict(self) -> dict:
        return {"seat": self.seat, "amount": self.amount}


@dataclass
class TrickCard:
    seat: int
    card: Card

    def to_dict(self) -> dict:
        return {"seat": self.seat, "card": self.card.id}


@dataclass
class GameState:
    game_code: str
    mode: int  # 2, 3, or 4
    phase: GamePhase = GamePhase.WAITING
    players: list[Player] = field(default_factory=list)
    dealer_seat: int = 0

    # Deck & center pile
    deck: list[Card] = field(default_factory=list)
    center_pile: list[Card] = field(default_factory=list)

    # Bidding
    bids: list[Bid] = field(default_factory=list)
    current_bid: Optional[Bid] = None
    bid_turn_seat: Optional[int] = None

    # Trump
    trumper_seat: Optional[int] = None
    trump_suit: Optional[Suit] = None
    trump_card: Optional[Card] = None
    trump_revealed: bool = False
    exchange_done: bool = False

    # Play
    current_trick: list[TrickCard] = field(default_factory=list)
    tricks_won: dict[int, list[Card]] = field(default_factory=dict)  # seat -> won cards
    turn_seat: Optional[int] = None
    turn_deadline: Optional[str] = None
    trick_number: int = 0
    lead_seat: Optional[int] = None

    # Scoring
    scores: dict[int, int] = field(default_factory=dict)  # seat -> cumulative score points
    games_played: int = 0

    # Metadata
    created_at: Optional[str] = None
    ttl: Optional[int] = None

    def get_player_by_seat(self, seat: int) -> Optional[Player]:
        for p in self.players:
            if p.seat == seat:
                return p
        return None

    def get_player_by_id(self, player_id: str) -> Optional[Player]:
        for p in self.players:
            if p.player_id == player_id:
                return p
        return None

    def get_player_by_connection(self, connection_id: str) -> Optional[Player]:
        for p in self.players:
            if p.connection_id == connection_id:
                return p
        return None

    def next_seat(self, seat: int) -> int:
        """Return next active seat clockwise."""
        seats = sorted(p.seat for p in self.players)
        idx = seats.index(seat)
        return seats[(idx + 1) % len(seats)]

    def get_team(self, seat: int) -> list[int]:
        """Return list of seats on the same team."""
        if self.mode == 4:
            # Opposite seats are teammates (0&2, 1&3)
            partner = (seat + 2) % 4
            return [seat, partner]
        # 2 or 3 player: each player is their own "team" for scoring,
        # but in 3-player, non-trumper seats form a team
        if self.mode == 3 and self.trumper_seat is not None:
            if seat == self.trumper_seat:
                return [seat]
            return [s for s in range(3) if s != self.trumper_seat]
        return [seat]

    def get_trumper_team_seats(self) -> list[int]:
        """Return seats on trumper's team."""
        if self.trumper_seat is None:
            return []
        return self.get_team(self.trumper_seat)

    def get_opposing_team_seats(self) -> list[int]:
        """Return seats opposing the trumper."""
        if self.trumper_seat is None:
            return []
        trumper_team = set(self.get_trumper_team_seats())
        return [p.seat for p in self.players if p.seat not in trumper_team]
