package handler

import (
	"github.com/gorilla/mux"
	"github.com/jackc/pgx/v5/pgxpool"
	handler "server/internal/adapter/handler/station"
)

func NewHttpHandler(r *mux.Router, db *pgxpool.Pool) {
	handler.NewStationHandler(r, db)
}
