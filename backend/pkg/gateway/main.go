package main

import (
    "context"
    "log"
    "net/http"
    "time"
    
    "github.com/gin-gonic/gin"
    "github.com/redis/go-redis/v9"
)

type Gateway struct {
    router     *gin.Engine
    redisClient *redis.Client
    services   map[string]string
}

type TenantMiddleware struct {
    redis *redis.Client
}

func (tm *TenantMiddleware) ExtractTenant() gin.HandlerFunc {
    return func(c *gin.Context) {
        host := c.Request.Host
        subdomain := extractSubdomain(host)
        
        // Validate tenant exists
        tenantID, err := tm.redis.Get(c.Request.Context(), 
            fmt.Sprintf("tenant:%s", subdomain)).Result()
        if err != nil {
            c.JSON(404, gin.H{"error": "Tenant not found"})
            c.Abort()
            return
        }
        
        c.Set("tenant_id", tenantID)
        c.Set("subdomain", subdomain)
        c.Next()
    }
}

func (g *Gateway) setupRoutes() {
    v1 := g.router.Group("/api/v1")
    v1.Use(g.tenantMiddleware.ExtractTenant())
    
    // Route to microservices
    v1.Any("/auth/*path", g.proxyToService("auth-service"))
    v1.Any("/etsy/*path", g.proxyToService("etsy-service"))
    v1.Any("/designs/*path", g.proxyToService("design-service"))
    v1.Any("/analytics/*path", g.proxyToService("analytics-service"))
}