package cfg

import (
	"errors"
	"os"
	"path/filepath"
	"testing"
)

func TestLoad(t *testing.T) {
	p := filepath.Join(t.TempDir(), "c.txt")
	os.WriteFile(p, []byte("a\n\n b \n"), 0o600)
	got, err := Load(p)
	if err != nil || len(got) != 2 || got[1] != "b" {
		t.Fatalf("got %v, %v", got, err)
	}
	if _, err := Load(p + ".missing"); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("want wrapped ErrNotExist, got %v", err)
	}
}
