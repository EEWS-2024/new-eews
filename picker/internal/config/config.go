package config

import (
	"github.com/joho/godotenv"
	"log"
	"os"
)

type Config struct {
	KafkaBootstrapServers  string
	KafkaGroupID           string
	KafkaConsumerTopic     string
	KafkaProducerTopic     string
	MachineLearningBaseUrl string
	DatabaseUrl            string
}

func LoadConfig() (*Config, error) {
	if err := godotenv.Load(); err != nil {
		log.Println("Warning: could not load .env file:", err)
	}

	config := &Config{
		KafkaBootstrapServers:  getEnv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
		KafkaGroupID:           getEnv("KAFKA_GROUP_ID", "group"),
		KafkaConsumerTopic:     getEnv("KAFKA_CONSUMER_TOPIC", "topic"),
		KafkaProducerTopic:     getEnv("KAFKA_PRODUCER_TOPIC", "topic"),
		MachineLearningBaseUrl: getEnv("MACHINE_LEARNING_BASE_URL", "http://192.168.99.100:8080"),
		DatabaseUrl:            getEnv("DATABASE_URL", "mongodb://localhost:27017/"),
	}

	return config, nil
}

func getEnv(key, fallback string) string {
	if value, exists := os.LookupEnv(key); exists && value != "" {
		return value
	}
	return fallback
}
