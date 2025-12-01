"""Module for special marker of not provided field"""


class _NotProvided:
    """Unique marker used to distinguish 'not provided' from None."""

    def __repr__(self):
        return "<NOT_PROVIDED>"


NOT_PROVIDED = _NotProvided()
