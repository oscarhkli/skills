package orders

import "testing"

func TestTotal(t *testing.T) {
	if got := Total([]Item{{"a", 100}, {"b", 250}}); got != 350 {
		t.Fatalf("got %d", got)
	}
}
