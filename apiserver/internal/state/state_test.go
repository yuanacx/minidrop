package state

import "testing"

func TestCanTransition(t *testing.T) {
	if !CanTransition(StatusPending, StatusRunning) {
		t.Fatal("pending->running")
	}
	if CanTransition(StatusDone, StatusRunning) {
		t.Fatal("done->running should fail")
	}
}
