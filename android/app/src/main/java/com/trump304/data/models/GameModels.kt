package com.trump304.data.models

import kotlinx.serialization.Serializable

@Serializable
data class Card(
    val id: String // e.g. "J_hearts"
) {
    val rank: String get() = id.substringBefore("_")
    val suit: String get() = id.substringAfter("_")

    val points: Int get() = when (rank) {
        "J" -> 30; "9" -> 20; "A" -> 11; "10" -> 10
        "K" -> 3; "Q" -> 2; else -> 0
    }

    val displayName: String get() = "$rank of ${suit.replaceFirstChar { it.uppercase() }}"
}

@Serializable
data class PlayerInfo(
    val player_id: String,
    val name: String,
    val seat: Int,
)

@Serializable
data class BidInfo(
    val seat: Int,
    val amount: Int? = null, // null = pass
)

@Serializable
data class TrickCardInfo(
    val seat: Int,
    val card: String,
)

@Serializable
data class GameState(
    val game_code: String = "",
    val mode: Int = 4,
    val phase: String = "WAITING",
    val players: List<PlayerInfo> = emptyList(),
    val dealer_seat: Int = 0,
    val your_seat: Int = 0,
    val your_hand: List<String> = emptyList(),
    val bids: List<BidInfo> = emptyList(),
    val current_bid: BidInfo? = null,
    val trumper_seat: Int? = null,
    val trump_revealed: Boolean = false,
    val trump_suit: String? = null,
    val trump_card: String? = null,
    val current_trick: List<TrickCardInfo> = emptyList(),
    val turn_seat: Int? = null,
    val trick_number: Int = 0,
    val scores: Map<String, Int> = emptyMap(),
    val games_played: Int = 0,
    val valid_cards: List<String> = emptyList(),
    val bid_turn_seat: Int? = null,
    val team_tricks_points: Map<String, Int> = emptyMap(),
    val center_pile_count: Int = 0,
)

data class CreateGameResponse(
    val game_code: String,
    val player_id: String,
    val seat: Int,
    val websocket_url: String,
    val mode: Int,
)

data class JoinGameResponse(
    val game_code: String,
    val player_id: String,
    val seat: Int,
    val websocket_url: String,
    val mode: Int,
    val players: List<PlayerInfo>,
)

enum class GamePhase {
    WAITING, DEALING, BIDDING, TRUMP_SELECTION, CARD_EXCHANGE, PLAYING, SCORING;

    companion object {
        fun from(value: String): GamePhase = entries.find { it.name == value } ?: WAITING
    }
}
