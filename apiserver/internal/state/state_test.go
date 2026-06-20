package state

import "testing"

func TestCanTransition(t *testing.T) {
	cases := []struct {
		from, to string
		want     bool
	}{
		{StatusPending, StatusRunning, true},
		{StatusPending, StatusFailed, true},
		{StatusPending, StatusDone, false},
		{StatusRunning, StatusUploading, true},
		{StatusRunning, StatusFailed, true},
		{StatusUploading, StatusDone, true},
		{StatusDone, StatusRunning, false},
		{StatusFailed, StatusPending, false},
		{"UNKNOWN", StatusRunning, false},
	}
	for _, c := range cases {
		got := CanTransition(c.from, c.to)
		if got != c.want {
			t.Fatalf("%s->%s want %v got %v", c.from, c.to, c.want, got)
		}
	}
}
