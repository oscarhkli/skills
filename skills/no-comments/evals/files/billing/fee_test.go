package billing

import "testing"

func TestFeeIsFlatPlusPercent(t *testing.T) {
	if got := Fee(10000); got != 320 {
		t.Fatalf("got %d", got)
	}
}
