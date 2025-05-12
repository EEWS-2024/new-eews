package config

import (
	"github.com/joho/godotenv"
	"log"
	"os"
)

type Config struct {
	KafkaBootstrapServers string
	KafkaGroupID          string
	KafkaTopic            string
}

func LoadConfig() (*Config, error) {
	if err := godotenv.Load(); err != nil {
		log.Println("Warning: could not load .env file:", err)
	}

	config := &Config{
		KafkaBootstrapServers: getEnv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
		KafkaGroupID:          getEnv("KAFKA_GROUP_ID", "group"),
		KafkaTopic:            getEnv("KAFKA_TOPIC", "topic"),
	}

	return config, nil
}

func getEnv(key, fallback string) string {
	if value, exists := os.LookupEnv(key); exists && value != "" {
		return value
	}
	return fallback
}
