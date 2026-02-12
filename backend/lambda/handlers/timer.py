"""Turn timeout handler — triggered by EventBridge Scheduler."""

from __future__ import annotations

import json
import os
import time
import boto3

from game_logic.game import handle_timeout, get_player_view
from game_logic.models import GamePhase

dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "ap-south-1"))
games_table = dynamodb.Table(os.environ.get("GAMES_TABLE", "Trump304Games"))
connections_table = dynamodb.Table(os.environ.get("CONNECTIONS_TABLE", "Trump304Connections"))

WEBSOCKET_ENDPOINT = os.environ.get("WEBSOCKET_ENDPOINT", "")


def handler(event, context):
    """Handle turn timeout from EventBridge Scheduler."""
    game_code = event.get("game_code", "")
    seat = int(event.get("seat", -1))
    trick_number = int(event.get("trick_number", -1))

    if not game_code or seat < 0:
        return {"statusCode": 400}

    state = _load_game_state(game_code)
    if state is None:
        return {"statusCode": 404}

    # Verify this timeout is still relevant
    # (player may have already played, or game may have moved on)
    if state.phase != GamePhase.PLAYING:
        return {"statusCode": 200}
    if state.turn_seat != seat:
        return {"statusCode": 200}
    if state.trick_number != trick_number:
        return {"statusCode": 200}

    # Auto-play
    success, result = handle_timeout(state, seat)
    if not success:
        return {"statusCode": 200}

    _save_game_state(state)

    # Broadcast to all players
    if WEBSOCKET_ENDPOINT:
        apigw = boto3.client(
            "apigatewaymanagementapi",
            endpoint_url=WEBSOCKET_ENDPOINT,
        )

        # Send timeout event
        timeout_event = {
            "event": "turn_timeout",
            "seat": seat,
            **result,
        }
        for player in state.players:
            if player.connection_id:
                _send(apigw, player.connection_id, timeout_event)

        # Send updated game state
        for player in state.players:
            if player.connection_id:
                view = get_player_view(state, player.seat)
                _send(apigw, player.connection_id, {"event": "game_state", **view})

    return {"statusCode": 200}


def _send(apigw, connection_id: str, data: dict) -> None:
    try:
        apigw.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(data).encode("utf-8"),
        )
    except Exception:
        pass


def _save_game_state(state) -> None:
    from _serialization import serialize_game_state
    item = serialize_game_state(state)
    item["ttl"] = int(time.time()) + 24 * 60 * 60
    games_table.put_item(Item=item)


def _load_game_state(code: str):
    response = games_table.get_item(Key={"game_code": code})
    item = response.get("Item")
    if not item:
        return None
    from _serialization import deserialize_game_state
    return deserialize_game_state(item)
