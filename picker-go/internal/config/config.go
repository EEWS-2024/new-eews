package config

import (
	"github.com/joho/godotenv"
	"log"
	"os"
	"strconv"
)

type Config struct {
	KafkaBootstrapServers  string
	KafkaGroupID           string
	KafkaConsumerTopic     string
	KafkaProducerTopic     string
	MachineLearningBaseUrl string
	DatabaseUrl            string
	RedisHost              string
	RedisPort              int
	RedisDB                int
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
		RedisHost:              getEnv("REDIS_HOST", "localhost"),
		RedisPort:              convertString(getEnv("REDIS_PORT", "6379")),
		RedisDB:                convertString(getEnv("REDIS_DB", "0")),
	}

	return config, nil
}

func getEnv(key, fallback string) string {
	if value, exists := os.LookupEnv(key); exists && value != "" {
		return value
	}
	return fallback
}

func convertString(v string) int {
	i, err := strconv.Atoi(v)
	if err != nil {
		return 0
	}
	return i
}
