"""Credit / usage-limiting logic.

Rules (from the build spec):
- New users get `free_signup_credits` design credits on signup (handled at signup).
- Each successful design consumes exactly 1 credit.
- Credits are consumed ON SUCCESS ONLY. A failed analysis must not deduct.
"""
from app.models import User


class OutOfCreditsError(Exception):
    """Raised when a user has no credits remaining."""


def has_credits(user: User) -> bool:
    return user.credits_remaining > 0


def ensure_credits(user: User) -> None:
    """Raise OutOfCreditsError if the user cannot create a design."""
    if not has_credits(user):
        raise OutOfCreditsError("User has no credits remaining")


def consume_credit(user: User) -> None:
    """Deduct one credit. Call ONLY after a successful design.

    Does not commit — the caller commits within the same transaction that
    saves the completed design, so credit + design persist atomically.
    """
    if user.credits_remaining <= 0:
        raise OutOfCreditsError("Cannot consume credit: none remaining")
    user.credits_remaining -= 1
