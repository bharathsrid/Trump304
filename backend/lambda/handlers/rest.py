"""REST API handlers for creating and joining games."""

from __future__ import annotations

import json
import os
import time
import boto3
from boto3.dynamodb.conditions import Key

from game_logic.game import create_game, join_game, generate_game_code
from game_logic.models import GamePhase

dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "ap-south-1"))
games_table = dynamodb.Table(os.environ.get("GAMES_TABLE", "Trump304Games"))

WEBSOCKET_URL = os.environ.get("WEBSOCKET_URL", "")
TTL_SECONDS = 24 * 60 * 60  # 24 hours


def handler(event, context):
    """Main REST handler — routes by HTTP method and path."""
    http_method = event.get("httpMethod", "")
    path = event.get("path", "")
    body = json.loads(event.get("body") or "{}")

    try:
        if http_method == "POST" and path == "/games":
            return _create_game(body)
        elif http_method == "POST" and "/join" in path:
            # /games/{code}/join
            code = event.get("pathParameters", {}).get("code", "").upper()
            return _join_game(code, body)
        elif http_method == "GET" and "/games/" in path:
            code = event.get("pathParameters", {}).get("code", "").upper()
            return _get_game(code)
        else:
            return _response(404, {"error": "Not found"})
    except Exception as e:
        return _response(500, {"error": str(e)})


def _create_game(body: dict) -> dict:
    """Create a new game session."""
    mode = body.get("mode", 4)
    player_name = body.get("player_name", "Player 1")

    if mode not in (2, 3, 4):
        return _response(400, {"error": "Mode must be 2, 3, or 4"})

    state, player = create_game(mode, player_name)

    # Ensure unique game code
    for _ in range(10):
        try:
            _save_game_state(state)
            break
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            state.game_code = generate_game_code()

    return _response(201, {
        "game_code": state.game_code,
        "player_id": player.player_id,
        "seat": player.seat,
        "websocket_url": WEBSOCKET_URL,
        "mode": mode,
    })


def _join_game(code: str, body: dict) -> dict:
    """Join an existing game."""
    if not code:
        return _response(400, {"error": "Game code required"})

    player_name = body.get("player_name", "Player")

    state = _load_game_state(code)
    if state is None:
        return _response(404, {"error": "Game not found"})

    success, result = join_game(state, player_name)
    if not success:
        return _response(400, {"error": result})

    player = result
    _save_game_state(state)

    return _response(200, {
        "game_code": code,
        "player_id": player.player_id,
        "seat": player.seat,
        "websocket_url": WEBSOCKET_URL,
        "mode": state.mode,
        "players": [p.to_public_dict() for p in state.players],
    })


def _get_game(code: str) -> dict:
    """Get public game info."""
    state = _load_game_state(code)
    if state is None:
        return _response(404, {"error": "Game not found"})

    return _response(200, {
        "game_code": code,
        "mode": state.mode,
        "phase": state.phase.value,
        "player_count": len(state.players),
        "players": [p.to_public_dict() for p in state.players],
    })


def _save_game_state(state) -> None:
    """Serialize and save game state to DynamoDB."""
    from _serialization import serialize_game_state
    item = serialize_game_state(state)
    item["ttl"] = int(time.time()) + TTL_SECONDS
    games_table.put_item(Item=item)


def _load_game_state(code: str):
    """Load game state from DynamoDB."""
    response = games_table.get_item(Key={"game_code": code})
    item = response.get("Item")
    if not item:
        return None
    from _serialization import deserialize_game_state
    return deserialize_game_state(item)


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }
