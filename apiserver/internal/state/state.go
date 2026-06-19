package state

// Task status constants aligned with Mini-Drop spec.
const (
	StatusPending   = "PENDING"
	StatusRunning   = "RUNNING"
	StatusUploading = "UPLOADING"
	StatusDone      = "DONE"
	StatusFailed    = "FAILED"
)

var allowed = map[string][]string{
	StatusPending:   {StatusRunning, StatusFailed},
	StatusRunning:   {StatusUploading, StatusFailed},
	StatusUploading: {StatusDone, StatusFailed},
	StatusDone:      {},
	StatusFailed:    {},
}

func CanTransition(from, to string) bool {
	next, ok := allowed[from]
	if !ok {
		return false
	}
	for _, n := range next {
		if n == to {
			return true
		}
	}
	return false
}
