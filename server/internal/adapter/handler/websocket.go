package handler

import (
	"github.com/gorilla/mux"
	handler "server/internal/adapter/handler/station"
)

func NewWebsocketHandler(mux *mux.Router) {
	mux.HandleFunc("/ws", handler.Broadcast)
}
