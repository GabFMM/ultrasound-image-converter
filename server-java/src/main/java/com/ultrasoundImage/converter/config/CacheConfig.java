package com.ultrasoundImage.converter.config;

import com.github.benmanes.caffeine.cache.Caffeine;
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.caffeine.CaffeineCacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Duration;

@Configuration
@EnableCaching
public class CacheConfig {

    // O Spring cria esse objeto automaticamente
    @Bean
    public CacheManager cacheManager(){
        CaffeineCacheManager manager = new CaffeineCacheManager();

        manager.setCaffeine(
                Caffeine.newBuilder()
                        // Duas matrizes modelos
                        .maximumSize(2)
                        // Esse temporizador é reiniciado a cada acesso de uma matriz
                        // Caso chegue a 0, então a matriz é removida do cache
                        .expireAfterAccess(Duration.ofMinutes(4))
        );

        return manager;
    }
}
