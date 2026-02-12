package com.trump304.ui.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.trump304.data.models.GamePhase
import com.trump304.data.models.GameState
import com.trump304.data.repository.GameRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class GameUiState(
    val gameState: GameState = GameState(),
    val phase: GamePhase = GamePhase.WAITING,
    val selectedCard: String? = null,
    val selectedTrumpSuit: String? = null,
    val bidAmount: Int = 150,
    val showTrumpSelector: Boolean = false,
    val showScoreDialog: Boolean = false,
    val lastEvent: Map<String, Any>? = null,
)

@HiltViewModel
class GameViewModel @Inject constructor(
    private val repository: GameRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(GameUiState())
    val uiState: StateFlow<GameUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            repository.gameState.collect { state ->
                _uiState.value = _uiState.value.copy(
                    gameState = state,
                    phase = GamePhase.from(state.phase),
                )
            }
        }

        viewModelScope.launch {
            repository.wsMessages.collect { message ->
                val gameState = repository.parseGameState(message)
                if (gameState != null) {
                    repository.updateGameState(gameState)
                }
            }
        }
    }

    fun selectCard(cardId: String) {
        val current = _uiState.value.selectedCard
        _uiState.value = _uiState.value.copy(
            selectedCard = if (current == cardId) null else cardId
        )
    }

    // Bidding
    fun setBidAmount(amount: Int) {
        _uiState.value = _uiState.value.copy(bidAmount = amount.coerceIn(150, 304))
    }

    fun placeBid() {
        repository.placeBid(_uiState.value.bidAmount)
    }

    fun passBid() {
        repository.passBid()
    }

    // Trump selection
    fun showTrumpSelector() {
        _uiState.value = _uiState.value.copy(showTrumpSelector = true)
    }

    fun selectTrumpSuit(suit: String) {
        _uiState.value = _uiState.value.copy(selectedTrumpSuit = suit)
    }

    fun confirmTrumpSelection() {
        val suit = _uiState.value.selectedTrumpSuit ?: return
        val card = _uiState.value.selectedCard ?: return
        repository.selectTrump(suit, card)
        _uiState.value = _uiState.value.copy(
            showTrumpSelector = false,
            selectedTrumpSuit = null,
            selectedCard = null,
        )
    }

    // Card exchange (3-player)
    fun exchangeCards(cards: List<String>) {
        repository.exchangeCards(cards)
    }

    fun skipExchange() {
        repository.skipExchange()
    }

    // Play
    fun playSelectedCard() {
        val card = _uiState.value.selectedCard ?: return
        repository.playCard(card)
        _uiState.value = _uiState.value.copy(selectedCard = null)
    }

    fun askTrump() {
        repository.askTrump()
    }

    fun revealTrump() {
        repository.revealTrump()
    }

    fun dismissScoreDialog() {
        _uiState.value = _uiState.value.copy(showScoreDialog = false)
    }

    override fun onCleared() {
        repository.disconnect()
    }
}
