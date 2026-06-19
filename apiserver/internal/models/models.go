package models

import "time"

type Task struct {
	ID             uint      `gorm:"primaryKey" json:"id"`
	TID            string    `gorm:"column:t_id;uniqueIndex;not null;size:64" json:"tid"`
	TargetIP       string    `json:"target_ip"`
	PID            int       `json:"pid"`
	DurationSec    int       `json:"duration_sec"`
	Hz             int       `json:"hz"`
	Collector      string    `json:"collector"`
	Status         string    `json:"status"`
	StatusReason   string    `json:"status_reason"`
	CosKey         string    `json:"cos_key"`
	AnalysisStatus string    `gorm:"default:pending" json:"analysis_status"`
	CreatedAt      time.Time `json:"created_at"`
	UpdatedAt      time.Time `json:"updated_at"`
}

type TaskStatusHistory struct {
	ID     uint      `gorm:"primaryKey"`
	TID    string    `gorm:"column:t_id;index"`
	FromSt string
	ToSt   string
	Reason string
	TS     time.Time
}

type AgentAudit struct {
	ID      uint      `gorm:"primaryKey"`
	AgentID string    `gorm:"index"`
	Event   string
	Detail  string
	TS      time.Time
}
