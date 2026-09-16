def retry(operation, attempts: int = 3):
    for attempt in range(attempts - 1):
        try:
            return operation()
        except ValueError:
            if attempt == attempts - 2:
                raise
