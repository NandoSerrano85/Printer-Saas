// services/design/main.go
package main

import (
    "context"
    "fmt"
    "io"
    "path/filepath"
    
    "github.com/gin-gonic/gin"
    "github.com/minio/minio-go/v7"
    "gorm.io/gorm"
)

type DesignService struct {
    db          *gorm.DB
    minioClient *minio.Client
    router      *gin.Engine
}

type Design struct {
    ID          uint   `gorm:"primaryKey"`
    TenantID    string `gorm:"index"`
    Name        string
    FilePath    string
    FileSize    int64
    ContentType string
    Tags        []string `gorm:"serializer:json"`
    CreatedAt   time.Time
}

func (ds *DesignService) uploadDesign(c *gin.Context) {
    tenantID := c.GetString("tenant_id")
    
    file, header, err := c.Request.FormFile("design")
    if err != nil {
        c.JSON(400, gin.H{"error": "Invalid file"})
        return
    }
    defer file.Close()
    
    // Generate tenant-scoped file path
    fileName := fmt.Sprintf("%s/%s/%s", 
        tenantID, "designs", header.Filename)
    
    // Upload to MinIO
    _, err = ds.minioClient.PutObject(
        context.Background(),
        "tenant-designs",
        fileName,
        file,
        header.Size,
        minio.PutObjectOptions{
            ContentType: header.Header.Get("Content-Type"),
        },
    )
    
    if err != nil {
        c.JSON(500, gin.H{"error": "Upload failed"})
        return
    }
    
    // Save metadata to database
    design := Design{
        TenantID:    tenantID,
        Name:        header.Filename,
        FilePath:    fileName,
        FileSize:    header.Size,
        ContentType: header.Header.Get("Content-Type"),
    }
    
    ds.db.Create(&design)
    
    c.JSON(201, design)
}

func (ds *DesignService) generateMockup(c *gin.Context) {
    tenantID := c.GetString("tenant_id")
    designID := c.Param("id")
    
    // Get design from database
    var design Design
    result := ds.db.Where("tenant_id = ? AND id = ?", 
        tenantID, designID).First(&design)
    
    if result.Error != nil {
        c.JSON(404, gin.H{"error": "Design not found"})
        return
    }
    
    // Queue mockup generation
    job := MockupGenerationJob{
        TenantID: tenantID,
        DesignID: designID,
        FilePath: design.FilePath,
    }
    
    // Submit to job queue (Redis/RQ)
    jobID, err := ds.queueMockupJob(job)
    if err != nil {
        c.JSON(500, gin.H{"error": "Failed to queue job"})
        return
    }
    
    c.JSON(202, gin.H{
        "job_id": jobID,
        "status": "queued",
        "message": "Mockup generation started"
    })
}