package com.trump304.data.network

import android.util.Log
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.serialization.json.Json
import okhttp3.*
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class WebSocketClient @Inject constructor() {

    private val client = OkHttpClient.Builder()
        .pingInterval(java.time.Duration.ofSeconds(15))
        .build()

    private var webSocket: WebSocket? = null
    private val _messages = Channel<String>(Channel.BUFFERED)
    val messages: Flow<String> = _messages.receiveAsFlow()

    private val _connectionState = Channel<ConnectionState>(Channel.CONFLATED)
    val connectionState: Flow<ConnectionState> = _connectionState.receiveAsFlow()

    private var currentUrl: String? = null

    enum class ConnectionState { CONNECTING, CONNECTED, DISCONNECTED, ERROR }

    fun connect(wsUrl: String, gameCode: String, playerId: String) {
        disconnect()

        val url = "$wsUrl?game_code=$gameCode&player_id=$playerId"
        currentUrl = url
        _connectionState.trySend(ConnectionState.CONNECTING)

        val request = Request.Builder().url(url).build()
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                Log.d("WebSocket", "Connected")
                _connectionState.trySend(ConnectionState.CONNECTED)
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                Log.d("WebSocket", "Message: $text")
                _messages.trySend(text)
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                webSocket.close(1000, null)
                _connectionState.trySend(ConnectionState.DISCONNECTED)
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                Log.e("WebSocket", "Error: ${t.message}")
                _connectionState.trySend(ConnectionState.ERROR)
            }
        })
    }

    fun send(message: String) {
        webSocket?.send(message)
    }

    fun sendAction(action: String, extras: Map<String, Any> = emptyMap()) {
        val json = buildString {
            append("{\"action\":\"$action\"")
            extras.forEach { (key, value) ->
                when (value) {
                    is String -> append(",\"$key\":\"$value\"")
                    is Number -> append(",\"$key\":$value")
                    is List<*> -> {
                        val items = value.joinToString(",") { "\"$it\"" }
                        append(",\"$key\":[$items]")
                    }
                    else -> append(",\"$key\":\"$value\"")
                }
            }
            append("}")
        }
        send(json)
    }

    fun disconnect() {
        webSocket?.close(1000, "Client disconnect")
        webSocket = null
    }
}
