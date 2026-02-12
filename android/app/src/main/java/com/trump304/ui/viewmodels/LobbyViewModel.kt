package com.trump304.ui.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.trump304.data.models.GamePhase
import com.trump304.data.models.PlayerInfo
import com.trump304.data.network.WebSocketClient
import com.trump304.data.repository.GameRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class LobbyUiState(
    val players: List<PlayerInfo> = emptyList(),
    val mode: Int = 4,
    val isHost: Boolean = false,
    val gameStarted: Boolean = false,
    val connectionStatus: String = "",
)

@HiltViewModel
class LobbyViewModel @Inject constructor(
    private val repository: GameRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(LobbyUiState())
    val uiState: StateFlow<LobbyUiState> = _uiState.asStateFlow()

    fun connectToGame(gameCode: String) {
        repository.connectWebSocket()

        viewModelScope.launch {
            repository.connectionState.collect { state ->
                _uiState.value = _uiState.value.copy(
                    connectionStatus = when (state) {
                        WebSocketClient.ConnectionState.CONNECTING -> "Connecting..."
                        WebSocketClient.ConnectionState.CONNECTED -> "Connected"
                        WebSocketClient.ConnectionState.DISCONNECTED -> "Disconnected"
                        WebSocketClient.ConnectionState.ERROR -> "Connection error"
                    }
                )
            }
        }

        viewModelScope.launch {
            repository.wsMessages.collect { message ->
                val gameState = repository.parseGameState(message)
                if (gameState != null) {
                    repository.updateGameState(gameState)
                    _uiState.value = _uiState.value.copy(
                        players = gameState.players,
                        mode = gameState.mode,
                        isHost = gameState.your_seat == 0,
                    )
                    val phase = GamePhase.from(gameState.phase)
                    if (phase != GamePhase.WAITING) {
                        _uiState.value = _uiState.value.copy(gameStarted = true)
                    }
                }
            }
        }
    }

    fun startGame() {
        repository.startGame()
    }
}
