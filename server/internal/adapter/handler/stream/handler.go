package handler

import (
	"context"
	"encoding/json"
	"github.com/gorilla/mux"
	"github.com/jackc/pgx/v5/pgxpool"
	"net/http"
	stationAdapter "server/internal/adapter/repository/station"
	streamAdapter "server/internal/adapter/repository/stream"
	app "server/internal/app/stream"
	"server/internal/config"
	"server/internal/domain"
)

func NewStreamHandler(r *mux.Router, db *pgxpool.Pool, cfg *config.Config) {
	stationRepo := stationAdapter.NewStationRepo(db)
	streamRepo := streamAdapter.NewStreamRepo(db)
	streamService := app.NewStreamService(stationRepo, streamRepo)

	stationRouter := r.PathPrefix("/stream").Subrouter()
	stationRouter.HandleFunc("/start", func(w http.ResponseWriter, r *http.Request) {
		StartStream(w, r, streamService, cfg)
	}).Methods("POST")
	stationRouter.HandleFunc("/stop", func(w http.ResponseWriter, r *http.Request) {
		StopStream(w, r, streamService, cfg)
	}).Methods("POST")
	stationRouter.HandleFunc("/status", func(w http.ResponseWriter, r *http.Request) {
		GetStreamStatus(w, r, streamService)
	}).Methods("GET")
}

func StartStream(w http.ResponseWriter, r *http.Request, streamService *app.StreamService, cfg *config.Config) {
	var payload domain.StartStreamPayload

	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	if err := streamService.StartStream(context.Background(), payload, cfg); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")

	if err := json.NewEncoder(w).Encode("OK"); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func StopStream(w http.ResponseWriter, r *http.Request, streamService *app.StreamService, cfg *config.Config) {
	var payload domain.StopStreamPayload

	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	if err := streamService.StopStream(context.Background(), payload, cfg); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")

	if err := json.NewEncoder(w).Encode("OK"); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func GetStreamStatus(w http.ResponseWriter, _ *http.Request, streamService *app.StreamService) {
	result, err := streamService.GetStream(context.Background())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")

	if err = json.NewEncoder(w).Encode(result); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
}
