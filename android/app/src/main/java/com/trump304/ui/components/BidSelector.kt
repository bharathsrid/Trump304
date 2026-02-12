package com.trump304.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun BidSelector(
    currentBid: Int?,
    bidAmount: Int,
    isMyTurn: Boolean,
    onBidChanged: (Int) -> Unit,
    onBid: () -> Unit,
    onPass: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        if (currentBid != null) {
            Text(
                text = "Current bid: $currentBid",
                style = MaterialTheme.typography.titleMedium,
            )
            Spacer(modifier = Modifier.height(8.dp))
        }

        if (isMyTurn) {
            Text(
                text = "Your bid: $bidAmount",
                fontSize = 32.sp,
                color = MaterialTheme.colorScheme.secondary,
            )

            Spacer(modifier = Modifier.height(8.dp))

            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Button(
                    onClick = { onBidChanged((bidAmount - 10).coerceAtLeast(150)) },
                    enabled = bidAmount > 150,
                ) {
                    Text("-10")
                }

                Button(
                    onClick = { onBidChanged((bidAmount + 10).coerceAtMost(304)) },
                    enabled = bidAmount < 304,
                ) {
                    Text("+10")
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                horizontalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                Button(
                    onClick = onBid,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.primary,
                    ),
                ) {
                    Text("Bid $bidAmount")
                }

                OutlinedButton(onClick = onPass) {
                    Text("Pass")
                }
            }
        } else {
            Text(
                text = "Waiting for other players to bid...",
                color = MaterialTheme.colorScheme.onBackground.copy(alpha = 0.6f),
            )
        }
    }
}
