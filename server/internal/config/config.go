package config

import (
	"github.com/joho/godotenv"
	"log"
	"os"
)

type Config struct {
	HTTPPort    string
	DatabaseUrl string
}

func LoadConfig() (*Config, error) {
	if err := godotenv.Load(); err != nil {
		log.Println("Warning: could not load .env file:", err)
	}

	config := &Config{
		HTTPPort:    getEnv("PORT", ":8080"),
		DatabaseUrl: getEnv("DATABASE_URL", "mongodb://localhost:27017/"),
	}

	return config, nil
}

func getEnv(key, fallback string) string {
	if value, exists := os.LookupEnv(key); exists && value != "" {
		return value
	}
	return fallback
}
