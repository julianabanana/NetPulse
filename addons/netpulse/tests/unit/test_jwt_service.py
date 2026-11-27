import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from netpulse_core.jwt_service import InvalidToken, NetpulseJwtService


class FakeUsers:
    def __init__(self, user):
        self.user = user

    def sudo(self):
        return self

    def browse(self, user_id):
        if self.user.id == user_id:
            return self

        return FakeUsers(None)

    def exists(self):
        return self if self.user else False

    @property
    def active(self):
        return self.user.active


class TestJwtService(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(
            os.environ,
            {
                "NETPULSE_JWT_SECRET": (
                    "a-secret-key-with-more-than-thirty-two-bytes"
                ),
            },
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.user = SimpleNamespace(id=17, active=True)

    def test_issued_token_contains_valid_user_identity(self):
        token = NetpulseJwtService.issue_token(self.user)
        user = NetpulseJwtService.authenticate_token(
            token,
            FakeUsers(self.user),
        )

        self.assertEqual(user.user.id, 17)

    def test_tampered_signature_is_rejected(self):
        token = NetpulseJwtService.issue_token(self.user)
        header, payload, signature = token.split(".")
        replacement = "A" if signature[0] != "A" else "B"
        tampered_token = ".".join(
            (header, payload, replacement + signature[1:])
        )

        with self.assertRaises(InvalidToken):
            NetpulseJwtService.authenticate_token(
                tampered_token,
                FakeUsers(self.user),
            )

    def test_malformed_token_is_rejected(self):
        with self.assertRaises(InvalidToken):
            NetpulseJwtService.authenticate_token(
                "not.a.jwt",
                FakeUsers(self.user),
            )

    def test_short_signing_secret_fails_closed(self):
        with patch.dict(os.environ, {"NETPULSE_JWT_SECRET": "short"}):
            with self.assertRaises(RuntimeError):
                NetpulseJwtService.issue_token(self.user)


if __name__ == "__main__":
    unittest.main()
