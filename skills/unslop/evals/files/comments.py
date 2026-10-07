def retry(fn):
    # Certainly! This wrapper retries fn up to three times — it's not just a loop, it's a robust safety net.
    for attempt in range(3):
        # Increment the attempt counter
        attempt += 1
        try:
            return fn()
        except OSError:
            pass
    raise RuntimeError("gave up")
