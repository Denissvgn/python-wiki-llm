from retry import retry  # type: ignore[reportMissingModuleSource]

def fetch(operation):
    return retry(operation, attempts=3)  # type: ignore[reportCallIssue]
