"""Serialization/deserialization of GameState for DynamoDB."""

from __future__ import annotations

from game_logic.models import (
    GameState, GamePhase, Player, Card, Suit, Rank, Bid, TrickCard,
)


def serialize_game_state(state: GameState) -> dict:
    """Convert GameState to a DynamoDB-compatible dict."""
    return {
        "game_code": state.game_code,
        "mode": state.mode,
        "phase": state.phase.value,
        "players": [_serialize_player(p) for p in state.players],
        "dealer_seat": state.dealer_seat,
        "deck": [c.id for c in state.deck],
        "center_pile": [c.id for c in state.center_pile],
        "bids": [b.to_dict() for b in state.bids],
        "current_bid": state.current_bid.to_dict() if state.current_bid else None,
        "bid_turn_seat": state.bid_turn_seat,
        "trumper_seat": state.trumper_seat,
        "trump_suit": state.trump_suit.value if state.trump_suit else None,
        "trump_card": state.trump_card.id if state.trump_card else None,
        "trump_revealed": state.trump_revealed,
        "exchange_done": state.exchange_done,
        "current_trick": [tc.to_dict() for tc in state.current_trick],
        "tricks_won": {
            str(seat): [c.id for c in cards]
            for seat, cards in state.tricks_won.items()
        },
        "turn_seat": state.turn_seat,
        "turn_deadline": state.turn_deadline,
        "trick_number": state.trick_number,
        "lead_seat": state.lead_seat,
        "scores": {str(k): v for k, v in state.scores.items()},
        "games_played": state.games_played,
        "created_at": state.created_at,
    }


def _serialize_player(player: Player) -> dict:
    return {
        "player_id": player.player_id,
        "name": player.name,
        "seat": player.seat,
        "connection_id": player.connection_id,
        "hand": [c.id for c in player.hand],
    }


def deserialize_game_state(item: dict) -> GameState:
    """Reconstruct GameState from a DynamoDB item."""
    state = GameState(
        game_code=item["game_code"],
        mode=int(item["mode"]),
        phase=GamePhase(item["phase"]),
        dealer_seat=int(item["dealer_seat"]),
        trump_revealed=bool(item.get("trump_revealed", False)),
        exchange_done=bool(item.get("exchange_done", False)),
        trick_number=int(item.get("trick_number", 0)),
        games_played=int(item.get("games_played", 0)),
        created_at=item.get("created_at"),
    )

    # Players
    for p_data in item.get("players", []):
        player = Player(
            player_id=p_data["player_id"],
            name=p_data["name"],
            seat=int(p_data["seat"]),
            connection_id=p_data.get("connection_id"),
            hand=[Card.from_id(cid) for cid in p_data.get("hand", [])],
        )
        state.players.append(player)

    # Deck & center pile
    state.deck = [Card.from_id(cid) for cid in item.get("deck", [])]
    state.center_pile = [Card.from_id(cid) for cid in item.get("center_pile", [])]

    # Bids
    state.bids = [
        Bid(seat=int(b["seat"]), amount=b["amount"])
        for b in item.get("bids", [])
    ]
    if item.get("current_bid"):
        cb = item["current_bid"]
        state.current_bid = Bid(seat=int(cb["seat"]), amount=cb["amount"])
    state.bid_turn_seat = int(item["bid_turn_seat"]) if item.get("bid_turn_seat") is not None else None

    # Trump
    state.trumper_seat = int(item["trumper_seat"]) if item.get("trumper_seat") is not None else None
    state.trump_suit = Suit(item["trump_suit"]) if item.get("trump_suit") else None
    state.trump_card = Card.from_id(item["trump_card"]) if item.get("trump_card") else None

    # Trick
    state.current_trick = [
        TrickCard(seat=int(tc["seat"]), card=Card.from_id(tc["card"]))
        for tc in item.get("current_trick", [])
    ]
    state.tricks_won = {
        int(seat): [Card.from_id(cid) for cid in cards]
        for seat, cards in item.get("tricks_won", {}).items()
    }

    state.turn_seat = int(item["turn_seat"]) if item.get("turn_seat") is not None else None
    state.turn_deadline = item.get("turn_deadline")
    state.lead_seat = int(item["lead_seat"]) if item.get("lead_seat") is not None else None

    # Scores
    state.scores = {int(k): int(v) for k, v in item.get("scores", {}).items()}

    return state
