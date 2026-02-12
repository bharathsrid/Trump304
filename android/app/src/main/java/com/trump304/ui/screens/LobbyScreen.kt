package com.trump304.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.trump304.ui.viewmodels.LobbyViewModel

@Composable
fun LobbyScreen(
    gameCode: String,
    onGameStarted: () -> Unit,
    viewModel: LobbyViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()

    LaunchedEffect(gameCode) {
        viewModel.connectToGame(gameCode)
    }

    LaunchedEffect(uiState.gameStarted) {
        if (uiState.gameStarted) onGameStarted()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Text("Game Code", style = MaterialTheme.typography.labelLarge)

        Text(
            text = gameCode,
            fontSize = 48.sp,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.secondary,
            letterSpacing = 8.sp,
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = "Share this code with friends!",
            color = MaterialTheme.colorScheme.onBackground.copy(alpha = 0.6f),
        )

        Spacer(modifier = Modifier.height(48.dp))

        // Player list
        Text(
            text = "Players (${uiState.players.size}/${uiState.mode})",
            style = MaterialTheme.typography.titleMedium,
        )

        Spacer(modifier = Modifier.height(16.dp))

        uiState.players.forEach { player ->
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp),
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = "Seat ${player.seat + 1}",
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.secondary,
                    )
                    Spacer(modifier = Modifier.width(16.dp))
                    Text(
                        text = player.name,
                        style = MaterialTheme.typography.bodyLarge,
                    )
                }
            }
        }

        // Empty slots
        val emptySlots = uiState.mode - uiState.players.size
        repeat(emptySlots) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.3f),
                ),
            ) {
                Row(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Waiting...",
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.4f),
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(32.dp))

        if (uiState.isHost && uiState.players.size == uiState.mode) {
            Button(
                onClick = viewModel::startGame,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("Start Game")
            }
        } else if (uiState.players.size < uiState.mode) {
            CircularProgressIndicator(
                modifier = Modifier.size(32.dp),
                color = MaterialTheme.colorScheme.secondary,
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text("Waiting for players...")
        }

        if (uiState.connectionStatus.isNotEmpty()) {
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = uiState.connectionStatus,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onBackground.copy(alpha = 0.5f),
            )
        }
    }
}
