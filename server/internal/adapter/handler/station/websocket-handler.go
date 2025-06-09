package handler

import (
	"encoding/json"
	"github.com/gorilla/websocket"
	"log"
	"net/http"
	"sync"
)

type Client struct {
	conn        *websocket.Conn
	stationCode string
}

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true },
}

var (
	clients   = make(map[*Client]bool)
	broadcast = make(chan []byte)
	mu        sync.Mutex
)

func Broadcast(w http.ResponseWriter, r *http.Request) {
	stationCode := r.URL.Query().Get("stationCode")
	if stationCode == "" {
		http.Error(w, "Missing stationCode parameter", http.StatusBadRequest)
		return
	}

	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket upgrade failed: %v", err)
		return
	}

	client := &Client{conn: conn, stationCode: stationCode}
	mu.Lock()
	clients[client] = true
	mu.Unlock()

	log.Printf("Client connected for stationCode=%s", stationCode)
}

func StartBroadcaster() {
	for {
		msg := <-broadcast

		// Decode the Kafka message to get stationCode
		var message struct {
			MessageType string         `json:"type"`
			Station     string         `json:"station"`
			Payload     map[string]any `json:"payload"`
		}

		if err := json.Unmarshal(msg, &message); err != nil {
			log.Printf("Invalid message: %v", err)
			continue
		}

		mu.Lock()
		for client := range clients {
			if client.stationCode == message.Station || message.MessageType != "trace" {
				err := client.conn.WriteMessage(websocket.TextMessage, msg)
				if err != nil {
					log.Printf("WebSocket write failed: %v", err)
					client.conn.Close()
					delete(clients, client)
				}
			}
		}
		mu.Unlock()
	}
}

func PushToClients(message []byte) {
	broadcast <- message
}
