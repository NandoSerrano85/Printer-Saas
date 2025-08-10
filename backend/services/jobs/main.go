// services/jobs/main.go
package main

import (
    "encoding/json"
    "net/http"
    "time"
    
    "github.com/gin-gonic/gin"
    "github.com/go-redis/redis/v8"
)

type JobService struct {
    redis  *redis.Client
    router *gin.Engine
}

type Job struct {
    ID          string                 `json:"id"`
    TenantID    string                 `json:"tenant_id"`
    Type        string                 `json:"type"`
    Status      string                 `json:"status"`
    Payload     map[string]interface{} `json:"payload"`
    Result      map[string]interface{} `json:"result,omitempty"`
    CreatedAt   time.Time              `json:"created_at"`
    CompletedAt *time.Time             `json:"completed_at,omitempty"`
    Error       string                 `json:"error,omitempty"`
}

func (js *JobService) queueJob(c *gin.Context) {
    tenantID := c.GetString("tenant_id")
    
    var jobRequest struct {
        Type     string                 `json:"type" binding:"required"`
        Payload  map[string]interface{} `json:"payload" binding:"required"`
        Priority string                 `json:"priority"` // high, normal, low
    }
    
    if err := c.ShouldBindJSON(&jobRequest); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }
    
    // Generate job ID
    jobID := generateJobID()
    
    job := Job{
        ID:        jobID,
        TenantID:  tenantID,
        Type:      jobRequest.Type,
        Status:    "queued",
        Payload:   jobRequest.Payload,
        CreatedAt: time.Now(),
    }
    
    // Store job metadata
    jobData, _ := json.Marshal(job)
    js.redis.Set(c.Request.Context(), 
        fmt.Sprintf("job:%s", jobID), jobData, 24*time.Hour)
    
    // Queue job based on type and priority
    queueName := js.getQueueForJob(jobRequest.Type, jobRequest.Priority)
    
    jobPayload := map[string]interface{}{
        "job_id":    jobID,
        "tenant_id": tenantID,
        "type":      jobRequest.Type,
        "payload":   jobRequest.Payload,
    }
    
    payloadJSON, _ := json.Marshal(jobPayload)
    
    err := js.redis.LPush(c.Request.Context(), queueName, payloadJSON).Err()
    if err != nil {
        c.JSON(500, gin.H{"error": "Failed to queue job"})
        return
    }
    
    c.JSON(202, gin.H{
        "job_id": jobID,
        "status": "queued",
        "message": fmt.Sprintf("Job queued in %s", queueName)
    })
}

func (js *JobService) getJobStatus(c *gin.Context) {
    tenantID := c.GetString("tenant_id")
    jobID := c.Param("job_id")
    
    // Get job data
    jobData, err := js.redis.Get(c.Request.Context(), 
        fmt.Sprintf("job:%s", jobID)).Result()
    if err == redis.Nil {
        c.JSON(404, gin.H{"error": "Job not found"})
        return
    }
    
    var job Job
    json.Unmarshal([]byte(jobData), &job)
    
    // Verify tenant access
    if job.TenantID != tenantID {
        c.JSON(403, gin.H{"error": "Access denied"})
        return
    }
    
    c.JSON(200, job)
}

func (js *JobService) listTenantJobs(c *gin.Context) {
    tenantID := c.GetString("tenant_id")
    
    // Get all job keys for tenant
    pattern := fmt.Sprintf("job:*")
    keys, err := js.redis.Keys(c.Request.Context(), pattern).Result()
    if err != nil {
        c.JSON(500, gin.H{"error": "Failed to fetch jobs"})
        return
    }
    
    var jobs []Job
    for _, key := range keys {
        jobData, err := js.redis.Get(c.Request.Context(), key).Result()
        if err != nil {
            continue
        }
        
        var job Job
        if err := json.Unmarshal([]byte(jobData), &job); err != nil {
            continue
        }
        
        // Filter by tenant
        if job.TenantID == tenantID {
            jobs = append(jobs, job)
        }
    }
    
    c.JSON(200, gin.H{
        "jobs": jobs,
        "total": len(jobs)
    })
}