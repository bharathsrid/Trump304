package com.trump304.ui.theme

import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val DarkColorScheme = darkColorScheme(
    primary = Color(0xFF4CAF50),       // Green — card table feel
    secondary = Color(0xFFFFD700),     // Gold — for highlights
    tertiary = Color(0xFFE53935),      // Red — for hearts/diamonds
    background = Color(0xFF1B5E20),    // Dark green table
    surface = Color(0xFF2E7D32),       // Slightly lighter green
    onPrimary = Color.White,
    onSecondary = Color.Black,
    onBackground = Color.White,
    onSurface = Color.White,
)

@Composable
fun Trump304Theme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = DarkColorScheme,
        content = content,
    )
}
