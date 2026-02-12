package com.trump304.ui.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.trump304.data.repository.GameRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class HomeUiState(
    val playerName: String = "",
    val selectedMode: Int = 4,
    val joinCode: String = "",
    val isLoading: Boolean = false,
    val error: String? = null,
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val repository: GameRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(HomeUiState())
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

    fun onPlayerNameChanged(name: String) {
        _uiState.value = _uiState.value.copy(playerName = name, error = null)
    }

    fun onModeSelected(mode: Int) {
        _uiState.value = _uiState.value.copy(selectedMode = mode)
    }

    fun onJoinCodeChanged(code: String) {
        _uiState.value = _uiState.value.copy(
            joinCode = code.uppercase().take(6),
            error = null,
        )
    }

    fun createGame(onSuccess: (String) -> Unit) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            val result = repository.createGame(
                mode = _uiState.value.selectedMode,
                playerName = _uiState.value.playerName,
            )
            result.fold(
                onSuccess = { code ->
                    _uiState.value = _uiState.value.copy(isLoading = false)
                    onSuccess(code)
                },
                onFailure = { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = e.message ?: "Failed to create game",
                    )
                },
            )
        }
    }

    fun joinGame(onSuccess: (String) -> Unit) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            val result = repository.joinGame(
                code = _uiState.value.joinCode,
                playerName = _uiState.value.playerName,
            )
            result.fold(
                onSuccess = { code ->
                    _uiState.value = _uiState.value.copy(isLoading = false)
                    onSuccess(code)
                },
                onFailure = { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = e.message ?: "Failed to join game",
                    )
                },
            )
        }
    }
}
