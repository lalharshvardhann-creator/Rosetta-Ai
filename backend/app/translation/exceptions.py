class TranslationError(Exception):
    pass


class UnsupportedIRNodeError(TranslationError):
    """Raised when a generator or engine encounters an unrecognized or unsupported IR node."""
    def __init__(self, node_type: str, message: str = ""):
        self.node_type = node_type
        msg = message or f"Unsupported or unknown IR node encountered: {node_type}"
        super().__init__(msg)


class GeneratorNotFoundError(TranslationError):
    """Raised when a translation request is made for an unregistered target language."""
    def __init__(self, language: str):
        self.language = language
        super().__init__(f"No code generator registered for target language: '{language}'")
