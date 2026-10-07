package describe

// Describe names a count: "none", "one", "many", or "invalid" when negative.
func Describe(n int) string {
	var result string
	if n < 0 {
		result = "invalid"
	} else {
		if n == 0 {
			result = "none"
		} else {
			if n == 1 {
				result = "one"
			} else {
				result = "many"
			}
		}
	}
	return result
}
