package com.trump304.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun CardView(
    cardId: String,
    isSelected: Boolean = false,
    isPlayable: Boolean = true,
    onClick: (() -> Unit)? = null,
    modifier: Modifier = Modifier,
) {
    val rank = cardId.substringBefore("_")
    val suit = cardId.substringAfter("_")
    val suitSymbol = when (suit) {
        "hearts" -> "\u2665"
        "diamonds" -> "\u2666"
        "clubs" -> "\u2663"
        "spades" -> "\u2660"
        else -> "?"
    }
    val isRed = suit == "hearts" || suit == "diamonds"
    val cardColor = if (isRed) Color(0xFFE53935) else Color.Black

    val elevation = if (isSelected) 8.dp else 2.dp
    val yOffset = if (isSelected) (-12).dp else 0.dp

    Card(
        modifier = modifier
            .width(56.dp)
            .height(80.dp)
            .offset(y = yOffset)
            .then(
                if (onClick != null && isPlayable) Modifier.clickable { onClick() }
                else Modifier
            ),
        shape = RoundedCornerShape(6.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (isPlayable) Color.White else Color(0xFFE0E0E0),
        ),
        border = if (isSelected) BorderStroke(2.dp, MaterialTheme.colorScheme.secondary)
        else BorderStroke(1.dp, Color.Gray),
        elevation = CardDefaults.cardElevation(defaultElevation = elevation),
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(4.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceBetween,
        ) {
            Text(
                text = rank,
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold,
                color = cardColor,
            )
            Text(
                text = suitSymbol,
                fontSize = 24.sp,
                color = cardColor,
            )
            Text(
                text = rank,
                fontSize = 10.sp,
                color = cardColor,
            )
        }
    }
}

@Composable
fun FaceDownCard(modifier: Modifier = Modifier) {
    Card(
        modifier = modifier
            .width(56.dp)
            .height(80.dp),
        shape = RoundedCornerShape(6.dp),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF1565C0),
        ),
        border = BorderStroke(1.dp, Color(0xFF0D47A1)),
    ) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = "304",
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White.copy(alpha = 0.5f),
            )
        }
    }
}
