package com.trump304.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.trump304.data.models.GamePhase
import com.trump304.ui.components.*
import com.trump304.ui.viewmodels.GameViewModel

@Composable
fun GameScreen(
    viewModel: GameViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()
    val gs = uiState.gameState
    val phase = uiState.phase
    val isMyTurn = gs.turn_seat == gs.your_seat
    val playerNames = gs.players.associate { it.seat to it.name }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(8.dp),
    ) {
        // Top bar — game info
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text(
                text = "Game: ${gs.game_code}",
                style = MaterialTheme.typography.labelMedium,
            )
            Text(
                text = "Trick ${gs.trick_number}",
                style = MaterialTheme.typography.labelMedium,
            )
            if (gs.trump_revealed && gs.trump_suit != null) {
                val suitSymbol = when (gs.trump_suit) {
                    "hearts" -> "\u2665"; "diamonds" -> "\u2666"
                    "clubs" -> "\u2663"; "spades" -> "\u2660"
                    else -> "?"
                }
                Text(
                    text = "Trump: $suitSymbol",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.secondary,
                )
            }
        }

        // Score display
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 4.dp),
            horizontalArrangement = Arrangement.SpaceEvenly,
        ) {
            val trumperPts = gs.team_tricks_points["trumper"] ?: 0
            val opposingPts = gs.team_tricks_points["opposing"] ?: 0
            Text("Trumper: $trumperPts pts", style = MaterialTheme.typography.bodySmall)
            gs.current_bid?.let {
                Text("Target: ${it.amount}", style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.secondary)
            }
            Text("Opposing: $opposingPts pts", style = MaterialTheme.typography.bodySmall)
        }

        Spacer(modifier = Modifier.height(4.dp))

        // Timer
        TimerBar(isMyTurn = isMyTurn && phase == GamePhase.PLAYING)

        Spacer(modifier = Modifier.weight(1f))

        // Main play area
        when (phase) {
            GamePhase.BIDDING -> {
                BidSelector(
                    currentBid = gs.current_bid?.amount,
                    bidAmount = uiState.bidAmount,
                    isMyTurn = gs.bid_turn_seat == gs.your_seat,
                    onBidChanged = viewModel::setBidAmount,
                    onBid = viewModel::placeBid,
                    onPass = viewModel::passBid,
                )
            }

            GamePhase.TRUMP_SELECTION -> {
                if (gs.trumper_seat == gs.your_seat) {
                    TrumpSelectionView(
                        hand = gs.your_hand,
                        selectedSuit = uiState.selectedTrumpSuit,
                        selectedCard = uiState.selectedCard,
                        onSuitSelected = viewModel::selectTrumpSuit,
                        onCardSelected = viewModel::selectCard,
                        onConfirm = viewModel::confirmTrumpSelection,
                    )
                } else {
                    Box(
                        modifier = Modifier.fillMaxWidth(),
                        contentAlignment = Alignment.Center,
                    ) {
                        Text("Waiting for trumper to select trump...")
                    }
                }
            }

            GamePhase.CARD_EXCHANGE -> {
                if (gs.trumper_seat == gs.your_seat) {
                    Text("Exchange 2 cards with center pile or skip")
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(onClick = viewModel::skipExchange) {
                            Text("Skip")
                        }
                    }
                } else {
                    Text("Waiting for trumper to exchange cards...")
                }
            }

            GamePhase.PLAYING -> {
                TrickPile(
                    trickCards = gs.current_trick,
                    playerNames = playerNames,
                )

                Spacer(modifier = Modifier.height(8.dp))

                // Action buttons
                if (isMyTurn) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.Center,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Button(
                            onClick = viewModel::playSelectedCard,
                            enabled = uiState.selectedCard != null,
                        ) {
                            Text("Play Card")
                        }

                        if (!gs.trump_revealed) {
                            Spacer(modifier = Modifier.width(8.dp))
                            if (gs.trumper_seat == gs.your_seat) {
                                OutlinedButton(onClick = viewModel::revealTrump) {
                                    Text("Reveal Trump")
                                }
                            } else {
                                OutlinedButton(onClick = viewModel::askTrump) {
                                    Text("Ask Trump")
                                }
                            }
                        }
                    }
                } else {
                    Box(
                        modifier = Modifier.fillMaxWidth(),
                        contentAlignment = Alignment.Center,
                    ) {
                        val turnPlayer = playerNames[gs.turn_seat] ?: "Player"
                        Text("Waiting for $turnPlayer...")
                    }
                }
            }

            GamePhase.SCORING -> {
                ScoreView(
                    scores = gs.scores,
                    playerNames = playerNames,
                )
            }

            else -> {
                Box(
                    modifier = Modifier.fillMaxWidth(),
                    contentAlignment = Alignment.Center,
                ) {
                    Text("Loading...")
                }
            }
        }

        Spacer(modifier = Modifier.weight(1f))

        // Player hand at bottom
        HandView(
            cards = gs.your_hand,
            validCards = gs.valid_cards,
            selectedCard = uiState.selectedCard,
            onCardClick = viewModel::selectCard,
            modifier = Modifier.fillMaxWidth(),
        )

        Spacer(modifier = Modifier.height(8.dp))
    }
}

@Composable
private fun TrumpSelectionView(
    hand: List<String>,
    selectedSuit: String?,
    selectedCard: String?,
    onSuitSelected: (String) -> Unit,
    onCardSelected: (String) -> Unit,
    onConfirm: () -> Unit,
) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("Select Trump Suit", style = MaterialTheme.typography.titleMedium)
        Spacer(modifier = Modifier.height(8.dp))

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf(
                "hearts" to "\u2665",
                "diamonds" to "\u2666",
                "clubs" to "\u2663",
                "spades" to "\u2660",
            ).forEach { (suit, symbol) ->
                if (selectedSuit == suit) {
                    Button(onClick = { onSuitSelected(suit) }) {
                        Text(symbol, style = MaterialTheme.typography.titleLarge)
                    }
                } else {
                    OutlinedButton(onClick = { onSuitSelected(suit) }) {
                        Text(symbol, style = MaterialTheme.typography.titleLarge)
                    }
                }
            }
        }

        if (selectedSuit != null) {
            Spacer(modifier = Modifier.height(16.dp))
            Text("Select a ${selectedSuit} card to place face-down:")
            Spacer(modifier = Modifier.height(8.dp))

            Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                hand.filter { it.endsWith("_$selectedSuit") }.forEach { cardId ->
                    CardView(
                        cardId = cardId,
                        isSelected = selectedCard == cardId,
                        onClick = { onCardSelected(cardId) },
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        Button(
            onClick = onConfirm,
            enabled = selectedSuit != null && selectedCard != null,
        ) {
            Text("Confirm Trump")
        }
    }
}

@Composable
private fun ScoreView(
    scores: Map<String, Int>,
    playerNames: Map<Int, String>,
) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("Game Over!", style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(16.dp))

        scores.forEach { (seatStr, points) ->
            val seat = seatStr.toIntOrNull() ?: return@forEach
            val name = playerNames[seat] ?: "Player ${seat + 1}"
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(name)
                Text("$points points", color = MaterialTheme.colorScheme.secondary)
            }
        }
    }
}
