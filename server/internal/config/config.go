package config

import (
	"github.com/joho/godotenv"
	"log"
	"os"
)

type Config struct {
	HTTPPort              string
	DatabaseUrl           string
	KafkaBootstrapServers string
	KafkaGroupID          string
	KafkaConsumerTopic    string
	LiveUrl               string
	ArchiveUrl            string
}

func LoadConfig() (*Config, error) {
	if err := godotenv.Load(); err != nil {
		log.Println("Warning: could not load .env file:", err)
	}

	config := &Config{
		HTTPPort:              getEnv("PORT", ":8080"),
		DatabaseUrl:           getEnv("DATABASE_URL", "mongodb://localhost:27017/"),
		KafkaBootstrapServers: getEnv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
		KafkaGroupID:          getEnv("KAFKA_GROUP_ID", "group"),
		KafkaConsumerTopic:    getEnv("KAFKA_CONSUMER_TOPIC", "predict"),
		LiveUrl:               getEnv("LIVE_URL", "http://85.209.163.202:9207"),
		ArchiveUrl:            getEnv("ARCHIVE_URL", "http://85.209.163.202:9207"),
	}

	return config, nil
}

func getEnv(key, fallback string) string {
	if value, exists := os.LookupEnv(key); exists && value != "" {
		return value
	}
	return fallback
}
