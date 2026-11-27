"""Servicio JWT HS256 puro, sin dependencias de Odoo ni bibliotecas externas."""
import base64
import hashlib
import hmac
import json
import os
import time

ISSUER = "netpulse"
TOKEN_TTL_SECONDS = 30 * 60
ALGORITHM = "HS256"
CLOCK_SKEW_SECONDS = 30


class InvalidToken(ValueError):
    """El token no cumple la estructura o las validaciones JWT."""


class NetpulseJwtService:
    """Emite y valida JWT HS256 usando la biblioteca estándar de Python."""

    TOKEN_TTL_SECONDS = TOKEN_TTL_SECONDS

    @staticmethod
    def _secret():
        secret = os.environ.get("NETPULSE_JWT_SECRET", "")
        if len(secret.encode("utf-8")) < 32:
            raise RuntimeError(
                "NETPULSE_JWT_SECRET debe tener al menos 32 bytes."
            )
        return secret.encode("utf-8")

    @staticmethod
    def _encode_segment(value):
        encoded = base64.urlsafe_b64encode(value).decode("ascii")
        return encoded.rstrip("=")

    @staticmethod
    def _decode_segment(value):
        padding = "=" * (-len(value) % 4)
        try:
            return base64.urlsafe_b64decode(value + padding)
        except (ValueError, base64.binascii.Error) as exc:
            raise InvalidToken("Segmento Base64 inválido.") from exc

    @classmethod
    def issue_token(cls, user):
        now = int(time.time())
        header = {"typ": "JWT", "alg": ALGORITHM}
        payload = {
            "sub": str(user.id),
            "iss": ISSUER,
            "iat": now,
            "exp": now + cls.TOKEN_TTL_SECONDS,
        }
        header_segment = cls._encode_segment(
            json.dumps(header, separators=(",", ":")).encode("utf-8")
        )
        payload_segment = cls._encode_segment(
            json.dumps(payload, separators=(",", ":")).encode("utf-8")
        )
        signing_input = "%s.%s" % (header_segment, payload_segment)
        signature = hmac.new(
            cls._secret(),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        signature_segment = cls._encode_segment(signature)
        return "%s.%s" % (signing_input, signature_segment)

    @classmethod
    def _decode_token(cls, token):
        secret = cls._secret()
        if not isinstance(token, str):
            raise InvalidToken("El token debe ser texto.")

        parts = token.split(".")
        if len(parts) != 3 or not all(parts):
            raise InvalidToken("Estructura JWT inválida.")

        try:
            header = json.loads(cls._decode_segment(parts[0]))
            payload = json.loads(cls._decode_segment(parts[1]))
            signature = cls._decode_segment(parts[2])
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
            raise InvalidToken("Contenido JWT inválido.") from exc

        if not isinstance(header, dict) or not isinstance(payload, dict):
            raise InvalidToken("Header y payload deben ser objetos JSON.")
        if header.get("typ") != "JWT" or header.get("alg") != ALGORITHM:
            raise InvalidToken("Algoritmo JWT no permitido.")

        signing_input = "%s.%s" % (parts[0], parts[1])
        expected_signature = hmac.new(
            secret,
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(signature, expected_signature):
            raise InvalidToken("Firma JWT inválida.")

        required_claims = {"sub", "iss", "iat", "exp"}
        if not required_claims.issubset(payload):
            raise InvalidToken("Faltan claims obligatorios.")

        now = int(time.time())
        if payload["iss"] != ISSUER:
            raise InvalidToken("Emisor JWT inválido.")
        if not isinstance(payload["exp"], int) or payload["exp"] <= now:
            raise InvalidToken("El token expiró.")
        if not isinstance(payload["iat"], int):
            raise InvalidToken("Fecha de emisión inválida.")
        if payload["iat"] > now + CLOCK_SKEW_SECONDS:
            raise InvalidToken("El token fue emitido en el futuro.")

        try:
            user_id = int(payload["sub"])
        except (TypeError, ValueError) as exc:
            raise InvalidToken("Identificador de usuario inválido.") from exc
        if user_id <= 0:
            raise InvalidToken("Identificador de usuario inválido.")

        return user_id

    @classmethod
    def authenticate_token(cls, token, user_model):
        user_id = cls._decode_token(token)
        user = user_model.sudo().browse(user_id).exists()
        if not user or not user.active:
            raise InvalidToken("La cuenta asociada al token no está activa.")
        return user
