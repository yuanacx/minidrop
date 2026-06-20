package handlers

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/minidrop/apiserver/internal/dropclient"
	"github.com/minidrop/apiserver/internal/models"
	"github.com/minidrop/apiserver/internal/state"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

func setupTestAPI(t *testing.T, dropHandler http.HandlerFunc) *API {
	t.Helper()
	gin.SetMode(gin.TestMode)
	db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
	if err != nil {
		t.Fatal(err)
	}
	if err := db.AutoMigrate(&models.Task{}, &models.TaskStatusHistory{}, &models.AgentAudit{}); err != nil {
		t.Fatal(err)
	}
	ts := httptest.NewServer(dropHandler)
	t.Cleanup(ts.Close)
	return &API{DB: db, Drop: dropclient.NewWithBase(ts.URL)}
}

func mockDropServer() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/control/create_task":
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write([]byte(`{"ok":true}`))
		case "/control/list_agents":
			_, _ = w.Write([]byte(`{"items":[{"hostname":"test","ip":"127.0.0.1","online":true,"last_seen":"2026-01-01T00:00:00Z"}]}`))
		case "/control/stat_agent":
			_, _ = w.Write([]byte(`{"online":true,"last_seen":"2026-01-01T00:00:00Z","ip_addr":"127.0.0.1"}`))
		default:
			http.NotFound(w, r)
		}
	}
}

func TestCreateTask(t *testing.T) {
	api := setupTestAPI(t, mockDropServer())
	r := gin.New()
	api.Register(r)

	body, _ := json.Marshal(map[string]interface{}{
		"target_ip": "127.0.0.1", "pid": 1234, "duration_sec": 5, "hz": 99,
	})
	req := httptest.NewRequest(http.MethodPost, "/api/v1/tasks", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("status=%d body=%s", w.Code, w.Body.String())
	}
	var resp map[string]interface{}
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
		t.Fatal(err)
	}
	data := resp["data"].(map[string]interface{})
	tid := data["tid"].(string)
	var task models.Task
	if err := api.DB.Where("t_id = ?", tid).First(&task).Error; err != nil {
		t.Fatal(err)
	}
	if task.Status != state.StatusRunning {
		t.Fatalf("expected RUNNING got %s", task.Status)
	}
}

func TestCreateTaskBadRequest(t *testing.T) {
	api := setupTestAPI(t, mockDropServer())
	r := gin.New()
	api.Register(r)
	req := httptest.NewRequest(http.MethodPost, "/api/v1/tasks", bytes.NewReader([]byte(`{}`)))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusBadRequest {
		t.Fatalf("expected 400 got %d", w.Code)
	}
}

func TestGetTask(t *testing.T) {
	api := setupTestAPI(t, mockDropServer())
	task := models.Task{TID: "abc12345", TargetIP: "127.0.0.1", PID: 1, Status: state.StatusDone}
	if err := api.DB.Create(&task).Error; err != nil {
		t.Fatal(err)
	}
	r := gin.New()
	api.Register(r)
	req := httptest.NewRequest(http.MethodGet, "/api/v1/tasks/abc12345", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("status=%d", w.Code)
	}
}

func TestGetTaskNotFound(t *testing.T) {
	api := setupTestAPI(t, mockDropServer())
	r := gin.New()
	api.Register(r)
	req := httptest.NewRequest(http.MethodGet, "/api/v1/tasks/missing1", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusNotFound {
		t.Fatalf("expected 404 got %d", w.Code)
	}
}

func TestListTasks(t *testing.T) {
	api := setupTestAPI(t, mockDropServer())
	for i, tid := range []string{"tid00001", "tid00002"} {
		_ = api.DB.Create(&models.Task{TID: tid, TargetIP: "127.0.0.1", PID: i + 1, Status: state.StatusDone}).Error
	}
	r := gin.New()
	api.Register(r)
	req := httptest.NewRequest(http.MethodGet, "/api/v1/tasks", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("status=%d", w.Code)
	}
	var resp struct {
		Data []models.Task `json:"data"`
	}
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
		t.Fatal(err)
	}
	if len(resp.Data) < 2 {
		t.Fatalf("expected >=2 tasks got %d", len(resp.Data))
	}
}

func TestListAgents(t *testing.T) {
	api := setupTestAPI(t, mockDropServer())
	r := gin.New()
	api.Register(r)
	req := httptest.NewRequest(http.MethodGet, "/api/v1/agents?target_ip=127.0.0.1", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("status=%d body=%s", w.Code, w.Body.String())
	}
}

func TestRunAnalysisNotFound(t *testing.T) {
	api := setupTestAPI(t, mockDropServer())
	r := gin.New()
	api.Register(r)
	req := httptest.NewRequest(http.MethodPost, "/api/v1/tasks/nope1234/analyze", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusNotFound {
		t.Fatalf("expected 404 got %d", w.Code)
	}
}

func TestAgentAudit(t *testing.T) {
	api := setupTestAPI(t, mockDropServer())
	r := gin.New()
	api.Register(r)
	body, _ := json.Marshal(map[string]string{
		"agent_id": "agent-1", "event": "agent_online", "detail": "127.0.0.1",
	})
	req := httptest.NewRequest(http.MethodPost, "/api/v1/internal/agent_audit", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("status=%d body=%s", w.Code, w.Body.String())
	}
	var count int64
	api.DB.Model(&models.AgentAudit{}).Count(&count)
	if count != 1 {
		t.Fatalf("expected 1 audit row got %d", count)
	}
}

func TestTaskResultDone(t *testing.T) {
	api := setupTestAPI(t, mockDropServer())
	_ = api.DB.Create(&models.Task{
		TID: "res12345", TargetIP: "127.0.0.1", PID: 1, Status: state.StatusRunning,
	}).Error
	r := gin.New()
	api.Register(r)
	body, _ := json.Marshal(map[string]string{"tid": "res12345", "cos_key": "res12345/perf.data"})
	req := httptest.NewRequest(http.MethodPost, "/api/v1/internal/task_result", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("status=%d", w.Code)
	}
	var task models.Task
	api.DB.Where("t_id = ?", "res12345").First(&task)
	if task.Status != state.StatusDone {
		t.Fatalf("expected DONE got %s", task.Status)
	}
}
