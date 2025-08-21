class NameRaisingProxy:
    """Proxy object that raises when __name__ is accessed."""

    def __getattr__(self, name: str):
        if name == "__name__":
            raise RuntimeError("boom")
        raise AttributeError(name)

    def __call__(self):
        pass


PROXY = NameRaisingProxy()
