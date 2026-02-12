# Trump304 Backend

Serverless backend for the 304 card game, running on AWS.

## Architecture

- **API Gateway REST** — create/join game endpoints
- **API Gateway WebSocket** — real-time game communication
- **Lambda (Python 3.12)** — game logic and connection management
- **DynamoDB** — game state and connection storage
- **EventBridge Scheduler** — 30-second turn timers

## Project Structure

```
backend/
├── cdk/                    # AWS CDK infrastructure
│   ├── app.py
│   ├── cdk.json
│   └── stacks/
│       └── trump304_stack.py
├── lambda/
│   ├── game_logic/         # Core game engine
│   │   ├── models.py       # Data models
│   │   ├── deck.py         # Card deck operations
│   │   ├── bidding.py      # Bidding rules
│   │   ├── trump.py        # Trump mechanics
│   │   ├── tricks.py       # Trick play & scoring
│   │   └── game.py         # Game state machine
│   ├── handlers/           # Lambda handlers
│   │   ├── rest.py         # REST API
│   │   ├── websocket.py    # WebSocket API
│   │   ├── timer.py        # Turn timeout
│   │   └── _serialization.py
│   └── tests/              # Unit tests
```

## Setup

```bash
cd backend/cdk
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cdk deploy
```

## Testing

```bash
cd backend/lambda
pip install pytest
PYTHONPATH=. pytest tests/ -v
```

## Region

Deployed to **ap-south-1 (Mumbai)** for lowest latency to Sri Lanka.
