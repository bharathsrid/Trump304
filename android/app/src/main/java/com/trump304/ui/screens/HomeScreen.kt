package com.trump304.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.trump304.ui.viewmodels.HomeViewModel

@Composable
fun HomeScreen(
    onGameCreated: (String) -> Unit,
    onGameJoined: (String) -> Unit,
    viewModel: HomeViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Text(
            text = "304",
            fontSize = 72.sp,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.secondary,
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = "Trump Card Game",
            fontSize = 18.sp,
            color = MaterialTheme.colorScheme.onBackground.copy(alpha = 0.7f),
        )

        Spacer(modifier = Modifier.height(48.dp))

        // Player name
        OutlinedTextField(
            value = uiState.playerName,
            onValueChange = viewModel::onPlayerNameChanged,
            label = { Text("Your Name") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )

        Spacer(modifier = Modifier.height(24.dp))

        // Create Game section
        Text("Player Mode", style = MaterialTheme.typography.labelLarge)
        Spacer(modifier = Modifier.height(8.dp))

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf(2, 3, 4).forEach { mode ->
                if (uiState.selectedMode == mode) {
                    Button(onClick = { viewModel.onModeSelected(mode) }) {
                        Text("${mode}P")
                    }
                } else {
                    OutlinedButton(onClick = { viewModel.onModeSelected(mode) }) {
                        Text("${mode}P")
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        Button(
            onClick = {
                viewModel.createGame { code -> onGameCreated(code) }
            },
            modifier = Modifier.fillMaxWidth(),
            enabled = uiState.playerName.isNotBlank() && !uiState.isLoading,
        ) {
            Text("Create Game")
        }

        Spacer(modifier = Modifier.height(32.dp))

        Divider()

        Spacer(modifier = Modifier.height(32.dp))

        // Join Game section
        OutlinedTextField(
            value = uiState.joinCode,
            onValueChange = viewModel::onJoinCodeChanged,
            label = { Text("Game Code") },
            singleLine = true,
            keyboardOptions = KeyboardOptions(capitalization = KeyboardCapitalization.Characters),
            modifier = Modifier.fillMaxWidth(),
        )

        Spacer(modifier = Modifier.height(16.dp))

        Button(
            onClick = {
                viewModel.joinGame { code -> onGameJoined(code) }
            },
            modifier = Modifier.fillMaxWidth(),
            enabled = uiState.playerName.isNotBlank()
                    && uiState.joinCode.length == 6
                    && !uiState.isLoading,
        ) {
            Text("Join Game")
        }

        if (uiState.error != null) {
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = uiState.error!!,
                color = MaterialTheme.colorScheme.error,
            )
        }
    }
}
