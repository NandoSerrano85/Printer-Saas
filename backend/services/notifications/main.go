// services/notifications/main.go
package main

import (
    "encoding/json"
    "log"
    "net/http"
    
    "github.com/gin-gonic/gin"
    "github.com/gorilla/websocket"
)

type NotificationService struct {
    clients    map[string]map[*websocket.Conn]bool // tenant_id -> connections
    broadcast  chan NotificationMessage
    register   chan *Client
    unregister chan *Client
    router     *gin.Engine
}

type Client struct {
    TenantID string
    Conn     *websocket.Conn
    Send     chan NotificationMessage
}

type NotificationMessage struct {
    TenantID  string      `json:"tenant_id"`
    Type      string      `json:"type"`
    Title     string      `json:"title"`
    Message   string      `json:"message"`
    Data      interface{} `json:"data,omitempty"`
    Timestamp int64       `json:"timestamp"`
}

var upgrader = websocket.Upgrader{
    CheckOrigin: func(r *http.Request) bool {
        return true // Configure proper origin checking in production
    },
}

func (ns *NotificationService) handleWebSocket(c *gin.Context) {
    tenantID := c.GetString("tenant_id")
    
    conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
    if err != nil {
        log.Printf("WebSocket upgrade failed: %v", err)
        return
    }
    
    client := &Client{
        TenantID: tenantID,
        Conn:     conn,
        Send:     make(chan NotificationMessage, 256),
    }
    
    ns.register <- client
    
    go client.writePump()
    go client.readPump(ns.unregister)
}

func (c *Client) writePump() {
    defer c.Conn.Close()
    
    for {
        select {
        case message, ok := <-c.Send:
            if !ok {
                c.Conn.WriteMessage(websocket.CloseMessage, []byte{})
                return
            }
            
            if err := c.Conn.WriteJSON(message); err != nil {
                log.Printf("WebSocket write error: %v", err)
                return
            }
        }
    }
}

func (ns *NotificationService) run() {
    for {
        select {
        case client := <-ns.register:
            if ns.clients[client.TenantID] == nil {
                ns.clients[client.TenantID] = make(map[*websocket.Conn]bool)
            }
            ns.clients[client.TenantID][client.Conn] = true
            log.Printf("Client connected for tenant: %s", client.TenantID)
            
        case client := <-ns.unregister:
            if clients, ok := ns.clients[client.TenantID]; ok {
                if _, ok := clients[client.Conn]; ok {
                    delete(clients, client.Conn)
                    close(client.Send)
                    client.Conn.Close()
                }
            }
            
        case message := <-ns.broadcast:
            if clients, ok := ns.clients[message.TenantID]; ok {
                for conn := range clients {
                    select {
                    case conn.WriteJSON(message):
                    default:
                        close(conn.Send)
                        delete(clients, conn)
                        conn.Close()
                    }
                }
            }
        }
    }
}

// Notification triggers
func (ns *NotificationService) sendJobCompletion(tenantID, jobID, jobType string, result interface{}) {
    message := NotificationMessage{
        TenantID:  tenantID,
        Type:      "job_completed",
        Title:     "Job Completed",
        Message:   fmt.Sprintf("%s job completed successfully", jobType),
        Data:      map[string]interface{}{"job_id": jobID, "result": result},
        Timestamp: time.Now().Unix(),
    }
    
    ns.broadcast <- message
}