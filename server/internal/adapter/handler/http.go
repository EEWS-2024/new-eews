package handler

import (
	"github.com/gorilla/mux"
	"github.com/jackc/pgx/v5/pgxpool"
	stationHandler "server/internal/adapter/handler/station"
	streamHandler "server/internal/adapter/handler/stream"
	"server/internal/config"
)

func NewHttpHandler(r *mux.Router, db *pgxpool.Pool, cfg *config.Config) {
	stationHandler.NewStationHandler(r, db)
	streamHandler.NewStreamHandler(r, db, cfg)
}
