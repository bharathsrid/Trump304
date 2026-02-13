package com.trump304.data.network

import com.trump304.BuildConfig
import io.ktor.client.*
import io.ktor.client.engine.okhttp.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class RestClient @Inject constructor() {

    private val json = Json { ignoreUnknownKeys = true }

    private val client = HttpClient(OkHttp) {
        install(ContentNegotiation) {
            json(json)
        }
    }

    private val baseUrl = BuildConfig.REST_BASE_URL

    suspend fun createGame(mode: Int, playerName: String): Result<Map<String, Any>> {
        return try {
            val response = client.post("$baseUrl/games") {
                contentType(ContentType.Application.Json)
                setBody(buildJsonObject {
                    put("mode", mode)
                    put("player_name", playerName)
                }.toString())
            }
            val body = json.decodeFromString<Map<String, kotlinx.serialization.json.JsonElement>>(
                response.bodyAsText()
            )
            @Suppress("UNCHECKED_CAST")
            Result.success(body.mapValues { it.value.toString().trim('"') } as Map<String, Any>)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun joinGame(code: String, playerName: String): Result<Map<String, Any>> {
        return try {
            val response = client.post("$baseUrl/games/${code.uppercase()}/join") {
                contentType(ContentType.Application.Json)
                setBody(buildJsonObject {
                    put("player_name", playerName)
                }.toString())
            }
            val body = json.decodeFromString<Map<String, kotlinx.serialization.json.JsonElement>>(
                response.bodyAsText()
            )
            @Suppress("UNCHECKED_CAST")
            Result.success(body.mapValues { it.value.toString().trim('"') } as Map<String, Any>)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    fun close() {
        client.close()
    }
}
