package com.trump304.ui.components

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun HandView(
    cards: List<String>,
    validCards: List<String>,
    selectedCard: String?,
    onCardClick: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    Row(
        modifier = modifier
            .horizontalScroll(rememberScrollState())
            .padding(horizontal = 8.dp),
        horizontalArrangement = Arrangement.spacedBy((-20).dp),
    ) {
        cards.forEach { cardId ->
            CardView(
                cardId = cardId,
                isSelected = cardId == selectedCard,
                isPlayable = validCards.isEmpty() || cardId in validCards,
                onClick = { onCardClick(cardId) },
            )
        }
    }
}
