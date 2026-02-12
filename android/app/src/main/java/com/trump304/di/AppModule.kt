package com.trump304.di

import com.trump304.data.network.RestClient
import com.trump304.data.network.WebSocketClient
import com.trump304.data.repository.GameRepository
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideRestClient(): RestClient = RestClient()

    @Provides
    @Singleton
    fun provideWebSocketClient(): WebSocketClient = WebSocketClient()

    @Provides
    @Singleton
    fun provideGameRepository(
        restClient: RestClient,
        wsClient: WebSocketClient,
    ): GameRepository = GameRepository(restClient, wsClient)
}
