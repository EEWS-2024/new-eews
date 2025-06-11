package handler

import (
	"context"
	"encoding/json"
	"github.com/gorilla/mux"
	"github.com/jackc/pgx/v5/pgxpool"
	"net/http"
	adapter "server/internal/adapter/repository/station"
	app "server/internal/app/station"
	"server/internal/domain"
)

func NewStationHandler(r *mux.Router, db *pgxpool.Pool) {
	stationRepo := adapter.NewStationRepo(db)
	stationService := app.NewStationService(stationRepo)

	stationRouter := r.PathPrefix("/station").Subrouter()
	stationRouter.HandleFunc("", func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodGet {
			GetAllStations(w, r, stationService)
		}

		if r.Method == http.MethodPost {
			ToggleStation(w, r, stationService)
		}
	}).Methods("GET", "POST")
	stationRouter.HandleFunc("/{code}", func(w http.ResponseWriter, r *http.Request) {
		GetStation(w, r, stationService)
	}).Methods("GET")
}

func GetAllStations(w http.ResponseWriter, _ *http.Request, stationService *app.StationService) {
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

func ToggleStation(w http.ResponseWriter, r *http.Request, stationService *app.StationService) {
	var payload domain.TogglePayload

	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	if err := stationService.Toggle(context.Background(), payload.StationCode, payload.IsEnabled); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")

	if err := json.NewEncoder(w).Encode("OK"); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
}
