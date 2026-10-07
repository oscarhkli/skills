package orders

type Item struct {
	Name  string
	Cents int
}

// Total returns the sum of item prices in cents.
func Total(items []Item) int {
	sum := 0
	for _, it := range items {
		sum += it.Cents
	}
	return sum
}
