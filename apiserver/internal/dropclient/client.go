package dropclient

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"
)

type Client struct {
	base string
	hc   *http.Client
}

func New() *Client {
	base := os.Getenv("DROP_SERVER")
	if base == "" {
		base = "http://drop_server:50051"
	}
	return &Client{base: base, hc: &http.Client{Timeout: 10 * time.Second}}
}

type CreateTaskPayload struct {
	TargetIP string                 `json:"target_ip"`
	TaskDesc map[string]interface{} `json:"task_desc"`
}

func (c *Client) CreateTask(targetIP, taskID string, pid, duration, hz int, collector string) error {
	body := CreateTaskPayload{
		TargetIP: targetIP,
		TaskDesc: map[string]interface{}{
			"task_id":    taskID,
			"target_ip":  targetIP,
			"collector":  collector,
			"sample_argv": map[string]interface{}{
				"pid":          pid,
				"duration_sec": duration,
				"hz":           hz,
			},
		},
	}
	b, _ := json.Marshal(body)
	resp, err := c.hc.Post(c.base+"/control/create_task", "application/json", bytes.NewReader(b))
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		return fmt.Errorf("drop create_task status %d", resp.StatusCode)
	}
	return nil
}

func (c *Client) StatAgent(ip string) (online bool, lastSeen string, err error) {
	resp, err := c.hc.Get(c.base + "/control/stat_agent?target_ip=" + ip)
	if err != nil {
		return false, "", err
	}
	defer resp.Body.Close()
	var out struct {
		Online   bool   `json:"online"`
		LastSeen string `json:"last_seen"`
	}
	json.NewDecoder(resp.Body).Decode(&out)
	return out.Online, out.LastSeen, nil
}
