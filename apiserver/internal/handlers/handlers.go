package handlers

import (
	"os"
	"os/exec"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/minidrop/apiserver/internal/dropclient"
	"github.com/minidrop/apiserver/internal/models"
	"github.com/minidrop/apiserver/internal/state"
	"gorm.io/gorm"
)

type API struct {
	DB   *gorm.DB
	Drop *dropclient.Client
}

type createTaskReq struct {
	TargetIP    string `json:"target_ip" binding:"required"`
	PID         int    `json:"pid" binding:"required"`
	DurationSec int    `json:"duration_sec"`
	Hz          int    `json:"hz"`
	Collector   string `json:"collector"`
}

func (a *API) transition(tid, to, reason string) error {
	var task models.Task
	if err := a.DB.Where("t_id = ?", tid).First(&task).Error; err != nil {
		return err
	}
	if !state.CanTransition(task.Status, to) {
		return gorm.ErrInvalidTransaction
	}
	from := task.Status
	task.Status = to
	task.StatusReason = reason
	if err := a.DB.Save(&task).Error; err != nil {
		return err
	}
	return a.DB.Create(&models.TaskStatusHistory{
		TID: tid, FromSt: from, ToSt: to, Reason: reason, TS: time.Now(),
	}).Error
}

func (a *API) Register(r *gin.Engine) {
	r.GET("/healthz", func(c *gin.Context) { c.JSON(200, gin.H{"ok": true}) })

	v1 := r.Group("/api/v1")
	v1.GET("/agents", a.listAgents)
	v1.POST("/tasks", a.createTask)
	v1.GET("/tasks", a.listTasks)
	v1.GET("/tasks/:tid", a.getTask)
	v1.POST("/tasks/:tid/analyze", a.runAnalysis)
	v1.POST("/internal/task_result", a.taskResult)
	v1.POST("/internal/agent_audit", a.agentAudit)
}

func (a *API) listAgents(c *gin.Context) {
	ip := c.Query("target_ip")
	if ip == "" {
		ip = "127.0.0.1"
	}
	if items, err := a.Drop.ListAgents(); err == nil {
		data := make([]gin.H, 0, len(items))
		for _, item := range items {
			agentIP, _ := item["ip"].(string)
			online, _ := item["online"].(bool)
			if ip != "" && agentIP != ip && !(ip == "127.0.0.1" && online) {
				continue
			}
			data = append(data, gin.H{
				"ip":        agentIP,
				"hostname":  item["hostname"],
				"online":    online,
				"last_seen": item["last_seen"],
			})
		}
		if len(data) > 0 {
			c.JSON(200, gin.H{"code": 0, "data": data})
			return
		}
	}
	online, last, agentIP, _ := a.Drop.StatAgent(ip)
	c.JSON(200, gin.H{"code": 0, "data": []gin.H{{"ip": agentIP, "online": online, "last_seen": last}}})
}

func (a *API) createTask(c *gin.Context) {
	var req createTaskReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"code": 400, "message": err.Error()})
		return
	}
	if req.DurationSec == 0 {
		req.DurationSec = 10
	}
	if req.Hz == 0 {
		req.Hz = 99
	}
	if req.Collector == "" {
		req.Collector = "perf"
	}
	tid := uuid.New().String()[:8]
	task := models.Task{
		TID: tid, TargetIP: req.TargetIP, PID: req.PID,
		DurationSec: req.DurationSec, Hz: req.Hz, Collector: req.Collector,
		Status: state.StatusPending, StatusReason: "created",
	}
	if err := a.DB.Create(&task).Error; err != nil {
		c.JSON(500, gin.H{"code": 500, "message": err.Error()})
		return
	}
	_ = a.DB.Create(&models.TaskStatusHistory{
		TID: tid, FromSt: "", ToSt: state.StatusPending, Reason: "created", TS: time.Now(),
	})
	if err := a.Drop.CreateTask(req.TargetIP, tid, req.PID, req.DurationSec, req.Hz, req.Collector); err != nil {
		_ = a.transition(tid, state.StatusFailed, "dispatch failed: "+err.Error())
		c.JSON(500, gin.H{"code": 500, "message": err.Error()})
		return
	}
	_ = a.transition(tid, state.StatusRunning, "dispatched to agent")
	c.JSON(200, gin.H{"code": 0, "data": gin.H{"tid": tid}})
}

func (a *API) taskResult(c *gin.Context) {
	var req struct {
		TID    string `json:"tid"`
		CosKey string `json:"cos_key"`
		Error  string `json:"error"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"code": 400})
		return
	}
	var task models.Task
	if err := a.DB.Where("t_id = ?", req.TID).First(&task).Error; err != nil {
		c.JSON(404, gin.H{"code": 404})
		return
	}
	if req.Error != "" {
		_ = a.transition(req.TID, state.StatusFailed, req.Error)
		c.JSON(200, gin.H{"code": 0})
		return
	}
	task.CosKey = req.CosKey
	a.DB.Save(&task)
	_ = a.transition(req.TID, state.StatusUploading, "artifact uploaded")
	_ = a.transition(req.TID, state.StatusDone, "collection complete")
	c.JSON(200, gin.H{"code": 0})
}

func (a *API) listTasks(c *gin.Context) {
	var tasks []models.Task
	a.DB.Order("id desc").Limit(50).Find(&tasks)
	c.JSON(200, gin.H{"code": 0, "data": tasks})
}

func (a *API) getTask(c *gin.Context) {
	tid := c.Param("tid")
	var task models.Task
	if err := a.DB.Where("t_id = ?", tid).First(&task).Error; err != nil {
		c.JSON(404, gin.H{"code": 404, "message": "not found"})
		return
	}
	var hist []models.TaskStatusHistory
	a.DB.Where("t_id = ?", tid).Order("id asc").Find(&hist)
	c.JSON(200, gin.H{"code": 0, "data": gin.H{"task": task, "history": hist}})
}

func (a *API) runAnalysis(c *gin.Context) {
	tid := c.Param("tid")
	var task models.Task
	if err := a.DB.Where("t_id = ?", tid).First(&task).Error; err != nil {
		c.JSON(404, gin.H{"code": 404})
		return
	}
	cmd := exec.Command("python3", "/analysis/hotmethod_analyzer.py",
		"--task-id", tid, "--cos-key", task.CosKey)
	cmd.Env = append(os.Environ(),
		"S3_ENDPOINT="+os.Getenv("S3_ENDPOINT"),
		"MINIO_ROOT_USER="+os.Getenv("MINIO_ROOT_USER"),
		"MINIO_ROOT_PASSWORD="+os.Getenv("MINIO_ROOT_PASSWORD"),
		"MINIO_BUCKET="+os.Getenv("MINIO_BUCKET"),
		"FLAMEGRAPH_DIR=/opt/FlameGraph",
	)
	if err := cmd.Run(); err != nil {
		c.JSON(500, gin.H{"code": 500, "message": err.Error()})
		return
	}
	task.AnalysisStatus = "done"
	a.DB.Save(&task)
	c.JSON(200, gin.H{"code": 0, "message": "analysis triggered"})
}

func (a *API) agentAudit(c *gin.Context) {
	var req struct {
		AgentID string `json:"agent_id" binding:"required"`
		Event   string `json:"event" binding:"required"`
		Detail  string `json:"detail"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"code": 400, "message": err.Error()})
		return
	}
	if err := a.DB.Create(&models.AgentAudit{
		AgentID: req.AgentID,
		Event:   req.Event,
		Detail:  req.Detail,
		TS:      time.Now(),
	}).Error; err != nil {
		c.JSON(500, gin.H{"code": 500, "message": err.Error()})
		return
	}
	c.JSON(200, gin.H{"code": 0})
}
