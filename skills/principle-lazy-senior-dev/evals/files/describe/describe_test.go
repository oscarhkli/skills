package describe

import "testing"

func TestDescribe(t *testing.T) {
	cases := map[int]string{-5: "invalid", 0: "none", 1: "one", 2: "many", 99: "many"}
	for n, want := range cases {
		if got := Describe(n); got != want {
			t.Errorf("Describe(%d) = %q, want %q", n, got, want)
		}
	}
}
