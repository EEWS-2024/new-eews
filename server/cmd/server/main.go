package main

import (
	"context"
	"fmt"
	"github.com/gorilla/mux"
	"github.com/jackc/pgx/v5/pgxpool"
	"log"
	"net/http"
	"server/internal/adapter/handler"
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
	handler.NewHandler(router, dbPool)

	fmt.Printf("Server is up and listening on %s\n", cfg.HTTPPort)
	if err = http.ListenAndServe(cfg.HTTPPort, router); err != nil {
		return
	}
}
