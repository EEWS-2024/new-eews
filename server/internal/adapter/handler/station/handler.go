package handler

import (
	"context"
	"encoding/json"
	"github.com/gorilla/mux"
	"github.com/jackc/pgx/v5/pgxpool"
	"net/http"
	adapter "server/internal/adapter/repository/station"
	app "server/internal/app/station"
)

func NewStationHandler(r *mux.Router, db *pgxpool.Pool) {
	stationRepo := adapter.NewStationRepo(db)
	stationService := app.NewStationService(stationRepo)

	stationRouter := r.PathPrefix("/station").Subrouter()
	stationRouter.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		GetAllStations(w, r, stationService)
	}).Methods("GET")
	stationRouter.HandleFunc("/{code}", func(w http.ResponseWriter, r *http.Request) {
		GetStation(w, r, stationService)
	})
}

func GetAllStations(w http.ResponseWriter, r *http.Request, stationService *app.StationService) {
	stations, err := stationService.GetAll(context.Background())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")

	if err = json.NewEncoder(w).Encode(stations); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
}

func GetStation(w http.ResponseWriter, r *http.Request, stationService *app.StationService) {
	station, err := stationService.Get(context.Background(), mux.Vars(r)["code"])
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")

	if err = json.NewEncoder(w).Encode(station); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
}
