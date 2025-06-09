package main

import (
	"context"
	"fmt"
	"github.com/gorilla/mux"
	"github.com/jackc/pgx/v5/pgxpool"
	"log"
	"net/http"
	"server/internal/adapter/handler"
	ws "server/internal/adapter/handler/station"
	"server/internal/config"
)

func main() {
	cfg, err := config.LoadConfig()
	if err != nil {
		log.Fatal(err)
	}

	dbPool, err := pgxpool.New(context.Background(), cfg.DatabaseUrl)
	if err != nil {
		log.Fatalf("Failed to connect to DB: %v", err)
	}
	defer dbPool.Close()

	router := mux.NewRouter()
	handler.NewHttpHandler(router, dbPool)
	handler.NewWebsocketHandler(router)

	go ws.StartBroadcaster()

	go func() {
		if err = handler.NewConsumer(
			cfg.KafkaBootstrapServers,
			cfg.KafkaGroupID,
			[]string{cfg.KafkaConsumerTopic},
		); err != nil {
			log.Fatal(err)
		}
	}()

	fmt.Printf("Server is up and listening on %s\n", cfg.HTTPPort)
	if err = http.ListenAndServe(cfg.HTTPPort, router); err != nil {
		return
	}
}
