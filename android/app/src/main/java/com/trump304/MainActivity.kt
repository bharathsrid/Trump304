package com.trump304

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.Composable
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.trump304.ui.screens.GameScreen
import com.trump304.ui.screens.HomeScreen
import com.trump304.ui.screens.LobbyScreen
import com.trump304.ui.theme.Trump304Theme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            Trump304Theme {
                Trump304Navigation()
            }
        }
    }
}

@Composable
fun Trump304Navigation() {
    val navController = rememberNavController()

    NavHost(navController = navController, startDestination = "home") {
        composable("home") {
            HomeScreen(
                onGameCreated = { code ->
                    navController.navigate("lobby/$code")
                },
                onGameJoined = { code ->
                    navController.navigate("lobby/$code")
                },
            )
        }

        composable(
            route = "lobby/{gameCode}",
            arguments = listOf(navArgument("gameCode") { type = NavType.StringType }),
        ) { backStackEntry ->
            val gameCode = backStackEntry.arguments?.getString("gameCode") ?: ""
            LobbyScreen(
                gameCode = gameCode,
                onGameStarted = {
                    navController.navigate("game") {
                        popUpTo("home")
                    }
                },
            )
        }

        composable("game") {
            GameScreen()
        }
    }
}
