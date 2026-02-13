package com.trump304.ui.components

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.delay

@Composable
fun TimerBar(
    isMyTurn: Boolean,
    totalSeconds: Int = 30,
    modifier: Modifier = Modifier,
) {
    var secondsLeft by remember(isMyTurn) { mutableIntStateOf(totalSeconds) }

    LaunchedEffect(isMyTurn) {
        if (isMyTurn) {
            secondsLeft = totalSeconds
            while (secondsLeft > 0) {
                delay(1000L)
                secondsLeft--
            }
        }
    }

    val progress by animateFloatAsState(
        targetValue = if (isMyTurn) secondsLeft.toFloat() / totalSeconds else 1f,
        animationSpec = tween(durationMillis = 500),
        label = "timer",
    )

    val color = when {
        secondsLeft <= 5 -> Color(0xFFE53935)
        secondsLeft <= 10 -> Color(0xFFFF9800)
        else -> MaterialTheme.colorScheme.primary
    }

    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        if (isMyTurn) {
            Text(
                text = "${secondsLeft}s",
                style = MaterialTheme.typography.labelMedium,
                color = color,
            )
            Spacer(modifier = Modifier.height(4.dp))
        }
        LinearProgressIndicator(
            progress = progress,
            modifier = Modifier
                .fillMaxWidth()
                .height(4.dp),
            color = color,
            trackColor = MaterialTheme.colorScheme.surface,
        )
    }
}
