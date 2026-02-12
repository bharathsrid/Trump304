package com.trump304.data.repository

import com.trump304.data.models.GameState
import com.trump304.data.network.RestClient
import com.trump304.data.network.WebSocketClient
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.json.Json
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class GameRepository @Inject constructor(
    private val restClient: RestClient,
    private val wsClient: WebSocketClient,
) {
    private val json = Json { ignoreUnknownKeys = true }

    private val _gameState = MutableStateFlow(GameState())
    val gameState: StateFlow<GameState> = _gameState.asStateFlow()

    private var _gameCode: String = ""
    val gameCode: String get() = _gameCode

    private var _playerId: String = ""
    val playerId: String get() = _playerId

    private var _wsUrl: String = ""

    val wsMessages: Flow<String> = wsClient.messages
    val connectionState: Flow<WebSocketClient.ConnectionState> = wsClient.connectionState

    suspend fun createGame(mode: Int, playerName: String): Result<String> {
        val result = restClient.createGame(mode, playerName)
        return result.map { response ->
            _gameCode = response["game_code"].toString()
            _playerId = response["player_id"].toString()
            _wsUrl = response["websocket_url"].toString()
            _gameCode
        }
    }

    suspend fun joinGame(code: String, playerName: String): Result<String> {
        val result = restClient.joinGame(code, playerName)
        return result.map { response ->
            _gameCode = response["game_code"].toString()
            _playerId = response["player_id"].toString()
            _wsUrl = response["websocket_url"].toString()
            _gameCode
        }
    }

    fun connectWebSocket() {
        wsClient.connect(_wsUrl, _gameCode, _playerId)
    }

    fun updateGameState(state: GameState) {
        _gameState.value = state
    }

    fun parseGameState(message: String): GameState? {
        return try {
            val parsed = json.decodeFromString<GameState>(message)
            if (parsed.game_code.isNotEmpty()) parsed else null
        } catch (e: Exception) {
            null
        }
    }

    // Game actions
    fun startGame() = wsClient.sendAction("start_game")
    fun placeBid(amount: Int) = wsClient.sendAction("bid", mapOf("amount" to amount))
    fun passBid() = wsClient.sendAction("pass")
    fun selectTrump(suit: String, card: String) =
        wsClient.sendAction("select_trump", mapOf("suit" to suit, "card" to card))
    fun exchangeCards(cards: List<String>) =
        wsClient.sendAction("exchange_cards", mapOf("cards" to cards))
    fun skipExchange() = wsClient.sendAction("skip_exchange")
    fun playCard(cardId: String) =
        wsClient.sendAction("play_card", mapOf("card" to cardId))
    fun askTrump() = wsClient.sendAction("ask_trump")
    fun revealTrump() = wsClient.sendAction("reveal_trump")

    fun disconnect() {
        wsClient.disconnect()
    }
}
