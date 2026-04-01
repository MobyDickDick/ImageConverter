def formatUserDiagnostic(exc: BaseException) -> str:
    """Render structured loader/runtime errors into one compact CLI message."""
    if isinstance(exc, DescriptionMappingError):
        if exc.span is not None:
            return f"{exc.message} Ort: {exc.span.format()}."
        return exc.message
    return str(exc)
