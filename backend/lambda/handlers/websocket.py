"""WebSocket API handlers for real-time game communication."""

from __future__ import annotations

import json
import os
import time
import boto3

from game_logic.game import (
    start_game, handle_bid, handle_trump_selection,
    handle_card_exchange, handle_skip_exchange, handle_play_card,
    handle_ask_trump, handle_reveal_trump, get_player_view,
)
from game_logic.models import GamePhase

dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "ap-south-1"))
games_table = dynamodb.Table(os.environ.get("GAMES_TABLE", "Trump304Games"))
connections_table = dynamodb.Table(os.environ.get("CONNECTIONS_TABLE", "Trump304Connections"))

scheduler_client = boto3.client("scheduler", region_name=os.environ.get("AWS_REGION", "ap-south-1"))
TIMER_LAMBDA_ARN = os.environ.get("TIMER_LAMBDA_ARN", "")
TIMER_ROLE_ARN = os.environ.get("TIMER_ROLE_ARN", "")
TURN_TIMEOUT = 30


def handler(event, context):
    """Main WebSocket handler — routes by route key."""
    route_key = event.get("requestContext", {}).get("routeKey", "")
    connection_id = event["requestContext"]["connectionId"]
    domain = event["requestContext"]["domainName"]
    stage = event["requestContext"]["stage"]

    endpoint_url = f"https://{domain}/{stage}"
    apigw = boto3.client(
        "apigatewaymanagementapi",
        endpoint_url=endpoint_url,
    )

    try:
        if route_key == "$connect":
            return _on_connect(event, connection_id)
        elif route_key == "$disconnect":
            return _on_disconnect(connection_id)
        elif route_key == "$default" or route_key == "message":
            body = json.loads(event.get("body", "{}"))
            return _on_message(connection_id, body, apigw)
        else:
            return {"statusCode": 400}
    except Exception as e:
        print(f"Error: {e}")
        return {"statusCode": 500}


def _on_connect(event, connection_id: str) -> dict:
    """Handle new WebSocket connection."""
    params = event.get("queryStringParameters") or {}
    game_code = params.get("game_code", "").upper()
    player_id = params.get("player_id", "")

    if not game_code or not player_id:
        return {"statusCode": 400}

    # Load game and find player
    state = _load_game_state(game_code)
    if state is None:
        return {"statusCode": 404}

    player = state.get_player_by_id(player_id)
    if player is None:
        return {"statusCode": 403}

    # Store connection mapping
    connections_table.put_item(Item={
        "connection_id": connection_id,
        "game_code": game_code,
        "player_id": player_id,
        "seat": player.seat,
        "connected_at": int(time.time()),
    })

    # Update player's connection_id in game state
    player.connection_id = connection_id
    _save_game_state(state)

    return {"statusCode": 200}


def _on_disconnect(connection_id: str) -> dict:
    """Handle WebSocket disconnection."""
    # Look up connection
    resp = connections_table.get_item(Key={"connection_id": connection_id})
    conn = resp.get("Item")

    if conn:
        game_code = conn["game_code"]
        player_id = conn["player_id"]

        # Clear connection_id from game state (player can reconnect)
        state = _load_game_state(game_code)
        if state:
            player = state.get_player_by_id(player_id)
            if player:
                player.connection_id = None
                _save_game_state(state)

        connections_table.delete_item(Key={"connection_id": connection_id})

    return {"statusCode": 200}


def _on_message(connection_id: str, body: dict, apigw) -> dict:
    """Route incoming WebSocket messages to appropriate handler."""
    action = body.get("action", "")

    # Look up which game this connection belongs to
    resp = connections_table.get_item(Key={"connection_id": connection_id})
    conn = resp.get("Item")
    if not conn:
        return {"statusCode": 403}

    game_code = conn["game_code"]
    seat = int(conn["seat"])

    state = _load_game_state(game_code)
    if state is None:
        _send(apigw, connection_id, {"error": "Game not found"})
        return {"statusCode": 404}

    result = None

    if action == "start_game":
        success, msg = start_game(state)
        if success:
            _save_game_state(state)
            _broadcast_game_state(state, apigw)
            return {"statusCode": 200}
        else:
            _send(apigw, connection_id, {"error": msg})
            return {"statusCode": 200}

    elif action == "bid":
        amount = body.get("amount")
        success, result = handle_bid(state, seat, amount)

    elif action == "pass":
        success, result = handle_bid(state, seat, None)

    elif action == "select_trump":
        suit = body.get("suit", "")
        card = body.get("card", "")
        success, result = handle_trump_selection(state, seat, suit, card)

    elif action == "exchange_cards":
        cards = body.get("cards", [])
        success, result = handle_card_exchange(state, seat, cards)

    elif action == "skip_exchange":
        success, result = handle_skip_exchange(state, seat)

    elif action == "play_card":
        card = body.get("card", "")
        success, result = handle_play_card(state, seat, card)

    elif action == "ask_trump":
        success, result = handle_ask_trump(state, seat)
        if success:
            # After revealing, the player still needs to play a card
            _save_game_state(state)
            _broadcast_event(state, result, apigw)
            return {"statusCode": 200}

    elif action == "reveal_trump":
        success, result = handle_reveal_trump(state, seat)
        if success:
            _save_game_state(state)
            _broadcast_event(state, result, apigw)
            return {"statusCode": 200}

    else:
        _send(apigw, connection_id, {"error": f"Unknown action: {action}"})
        return {"statusCode": 200}

    if result is None:
        return {"statusCode": 200}

    if not success:
        _send(apigw, connection_id, result)
        return {"statusCode": 200}

    _save_game_state(state)

    # Broadcast result to all players
    _broadcast_event(state, result, apigw)

    # Broadcast updated game state to each player (personalized view)
    _broadcast_game_state(state, apigw)

    # Schedule turn timer if it's someone's turn
    if state.phase == GamePhase.PLAYING and state.turn_seat is not None:
        _schedule_turn_timer(state)

    return {"statusCode": 200}


def _broadcast_game_state(state, apigw) -> None:
    """Send personalized game state to each connected player."""
    for player in state.players:
        if player.connection_id:
            view = get_player_view(state, player.seat)
            _send(apigw, player.connection_id, {"event": "game_state", **view})


def _broadcast_event(state, event_data: dict, apigw) -> None:
    """Send an event to all connected players."""
    for player in state.players:
        if player.connection_id:
            _send(apigw, player.connection_id, event_data)


def _send(apigw, connection_id: str, data: dict) -> None:
    """Send a message to a WebSocket connection."""
    try:
        apigw.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(data).encode("utf-8"),
        )
    except apigw.exceptions.GoneException:
        # Connection no longer active — clean up
        try:
            connections_table.delete_item(Key={"connection_id": connection_id})
        except Exception:
            pass


def _schedule_turn_timer(state) -> None:
    """Schedule a turn timeout using EventBridge Scheduler."""
    from datetime import datetime, timezone, timedelta
    deadline = datetime.now(timezone.utc) + timedelta(seconds=TURN_TIMEOUT)
    state.turn_deadline = deadline.isoformat()

    schedule_name = f"turn-{state.game_code}-{state.trick_number}-{state.turn_seat}"

    try:
        scheduler_client.create_schedule(
            Name=schedule_name,
            GroupName="trump304-timers",
            ScheduleExpression=f"at({deadline.strftime('%Y-%m-%dT%H:%M:%S')})",
            FlexibleTimeWindow={"Mode": "OFF"},
            Target={
                "Arn": TIMER_LAMBDA_ARN,
                "RoleArn": TIMER_ROLE_ARN,
                "Input": json.dumps({
                    "game_code": state.game_code,
                    "seat": state.turn_seat,
                    "trick_number": state.trick_number,
                }),
            },
            ActionAfterCompletion="DELETE",
        )
    except Exception as e:
        print(f"Failed to schedule timer: {e}")


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
