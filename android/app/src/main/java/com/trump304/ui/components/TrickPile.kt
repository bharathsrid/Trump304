package com.trump304.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.trump304.data.models.TrickCardInfo

@Composable
fun TrickPile(
    trickCards: List<TrickCardInfo>,
    playerNames: Map<Int, String>,
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(160.dp),
        contentAlignment = Alignment.Center,
    ) {
        if (trickCards.isEmpty()) {
            Text(
                text = "Play area",
                color = MaterialTheme.colorScheme.onBackground.copy(alpha = 0.3f),
            )
        } else {
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                trickCards.forEach { tc ->
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                    ) {
                        Text(
                            text = playerNames[tc.seat] ?: "P${tc.seat + 1}",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onBackground.copy(alpha = 0.7f),
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        CardView(cardId = tc.card)
                    }
                }
            }
        }
    }
}
