"""Warning classes for blockparty.

These follow the standard ``warnings`` module pattern used by libraries like
urllib3 and SQLAlchemy.  Consumers can control behavior via
``warnings.filterwarnings`` or ``logging.captureWarnings(True)``.
"""


class BlockpartyWarning(UserWarning):
    """Base warning for all blockparty warnings."""


class FallbackWarning(BlockpartyWarning):
    """A request fell back to another explorer due to a transient error.

    Emitted by :class:`~blockparty.pool.AsyncBlockpartyPool` (and its sync
    counterpart) when a provider fails and the pool retries with the next
    provider in the credential list.
    """


class AuthFallbackWarning(FallbackWarning):
    """A request fell back due to an authentication failure on the preferred provider.

    This is a subclass of :class:`FallbackWarning` so that filtering on
    ``FallbackWarning`` catches both transient and auth-triggered fallbacks.
    A more targeted filter on ``AuthFallbackWarning`` catches only auth issues.
    """
