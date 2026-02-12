# Trump304 — API Specification

## REST API

Base URL: `https://<api-id>.execute-api.ap-south-1.amazonaws.com/prod`

### POST /games
Create a new game.

**Request Body:**
```json
{
  "mode": 4,
  "player_name": "Alice"
}
```

**Response (201):**
```json
{
  "game_code": "A3K9F2",
  "player_id": "uuid",
  "seat": 0,
  "websocket_url": "wss://...",
  "mode": 4
}
```

### POST /games/{code}/join
Join an existing game.

**Request Body:**
```json
{
  "player_name": "Bob"
}
```

**Response (200):**
```json
{
  "game_code": "A3K9F2",
  "player_id": "uuid",
  "seat": 1,
  "websocket_url": "wss://...",
  "mode": 4,
  "players": [{"player_id": "...", "name": "Alice", "seat": 0}, ...]
}
```

### GET /games/{code}
Get public game info.

**Response (200):**
```json
{
  "game_code": "A3K9F2",
  "mode": 4,
  "phase": "WAITING",
  "player_count": 2,
  "players": [...]
}
```

---

## WebSocket API

Connect URL: `wss://<api-id>.execute-api.ap-south-1.amazonaws.com/prod?game_code=A3K9F2&player_id=<uuid>`

### Client → Server Messages

#### Start game (host only)
```json
{"action": "start_game"}
```

#### Place bid
```json
{"action": "bid", "amount": 160}
```

#### Pass (bidding)
```json
{"action": "pass"}
```

#### Select trump
```json
{"action": "select_trump", "suit": "hearts", "card": "J_hearts"}
```

#### Exchange cards (3-player only)
```json
{"action": "exchange_cards", "cards": ["8_spades", "7_clubs"]}
```

#### Skip exchange (3-player only)
```json
{"action": "skip_exchange"}
```

#### Play card
```json
{"action": "play_card", "card": "J_hearts"}
```

#### Ask trump reveal (non-trumper, for cutting)
```json
{"action": "ask_trump"}
```

#### Reveal trump (trumper, voluntary)
```json
{"action": "reveal_trump"}
```

### Server → Client Messages

#### Full game state (sent after every action)
```json
{
  "event": "game_state",
  "game_code": "A3K9F2",
  "mode": 4,
  "phase": "PLAYING",
  "players": [...],
  "dealer_seat": 0,
  "your_seat": 2,
  "your_hand": ["J_hearts", "9_spades", ...],
  "bids": [{"seat": 1, "amount": 160}, {"seat": 2, "amount": null}],
  "current_bid": {"seat": 1, "amount": 160},
  "trumper_seat": 1,
  "trump_revealed": false,
  "current_trick": [{"seat": 1, "card": "J_spades"}],
  "turn_seat": 2,
  "trick_number": 3,
  "scores": {"0": 0, "1": 5, "2": 0, "3": 0},
  "games_played": 1,
  "valid_cards": ["9_spades", "7_spades"],
  "bid_turn_seat": null,
  "team_tricks_points": {"trumper": 80, "opposing": 45},
  "center_pile_count": 0
}
```

#### Trump revealed
```json
{
  "trump_revealed": true,
  "suit": "hearts",
  "trump_card": "J_hearts"
}
```

#### Turn timeout
```json
{
  "event": "turn_timeout",
  "seat": 1,
  "card_played": "7_clubs",
  "timeout": true
}
```

#### Error
```json
{
  "error": "Not your turn"
}
```

---

## Card ID Format

Cards are identified as `{rank}_{suit}`:
- Ranks: `7`, `8`, `Q`, `K`, `10`, `A`, `9`, `J`
- Suits: `hearts`, `diamonds`, `clubs`, `spades`

Examples: `J_hearts`, `9_spades`, `10_clubs`, `7_diamonds`

## Game Phases

`WAITING` → `DEALING` → `BIDDING` → `TRUMP_SELECTION` → [`CARD_EXCHANGE`] → `PLAYING` → `SCORING`

The `CARD_EXCHANGE` phase only occurs in 3-player games.
