"""Provider-neutral OIDC/OAuth2 identity adapter interface + StubIdentityProvider.

Phase 1A ships ONLY the stub. The stub is clearly labeled "AUTH STUB — NOT PRODUCTION"
everywhere. No real IdP (e.g. Auth0) is created, purchased, or connected. The IdP is
identity-only: it authenticates a subject and returns identity claims. It confers NO
roles or permissions — CAUL authorization is resolved server-side from PostgreSQL.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


STUB_LABEL = "AUTH STUB — NOT PRODUCTION"


@dataclass
class IdentityClaims:
    subject: str
    email: str
    display_name: str
    # Identity only. No roles/permissions. Authorization comes from PostgreSQL RBAC.
    provider: str
    is_stub: bool


class IdentityProvider(ABC):
    """Provider-neutral interface a future OIDC/OAuth2 provider (Phase 1B) must implement."""

    name: str = "abstract"
    is_stub: bool = True

    @abstractmethod
    def authenticate(self, *, email: str, credential: str) -> IdentityClaims | None:
        """Return IdentityClaims on success, else None. Identity only."""
        raise NotImplementedError

    @abstractmethod
    def describe(self) -> dict:
        raise NotImplementedError


class StubIdentityProvider(IdentityProvider):
    """Development/staging-only stub. Validates against seeded synthetic stub users.

    Credential verification is delegated to the caller (bcrypt against the PostgreSQL
    users table); this adapter models the provider-neutral contract and marks every
    identity as a stub identity.
    """

    name = "stub"
    is_stub = True

    def authenticate(self, *, email: str, credential: str) -> IdentityClaims | None:
        # The actual credential check happens in the auth router against PostgreSQL.
        # This method exists to satisfy the interface; the router builds claims.
        raise NotImplementedError("StubIdentityProvider claims are built by the auth router")

    def build_claims(self, *, subject: str, email: str, display_name: str) -> IdentityClaims:
        return IdentityClaims(
            subject=subject, email=email, display_name=display_name,
            provider=self.name, is_stub=True,
        )

    def describe(self) -> dict:
        return {
            "provider": self.name,
            "is_stub": True,
            "label": STUB_LABEL,
            "mfa": False,
            "note": (
                "Development/staging authentication stub. Not production. No MFA. "
                "No external identity provider is connected. Roles and permissions are "
                "resolved from PostgreSQL RBAC, not from this provider."
            ),
        }


# Single provider instance for Phase 1A.
identity_provider: IdentityProvider = StubIdentityProvider()
