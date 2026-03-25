from __future__ import annotations

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import settings

request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
doc_id_var: ContextVar[Optional[str]] = ContextVar("doc_id", default=None)


def bind_context(*, request_id: Optional[str] = None, user_id: Optional[str] = None, doc_id: Optional[str] = None) -> None:
    if request_id is not None:
        request_id_var.set(request_id)
    if user_id is not None:
        user_id_var.set(user_id)
    if doc_id is not None:
        doc_id_var.set(doc_id)


def clear_context() -> None:
    request_id_var.set(None)
    user_id_var.set(None)
    doc_id_var.set(None)


def new_request_id() -> str:
    return uuid.uuid4().hex


class _ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.user_id = user_id_var.get()
        record.doc_id = doc_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "user_id": getattr(record, "user_id", None),
            "doc_id": getattr(record, "doc_id", None),
        }

        for k, v in record.__dict__.items():
            if k in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "request_id",
                "user_id",
                "doc_id",
            }:
                continue
            try:
                json.dumps(v)
                payload[k] = v
            except Exception:
                payload[k] = str(v)

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    level_name = (settings.LOG_LEVEL or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    root.addFilter(_ContextFilter())

    logging.getLogger("uvicorn.access").handlers = [handler]
    logging.getLogger("uvicorn.access").propagate = False


def init_sentry() -> None:
    if not settings.SENTRY_DSN:
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    except Exception:
        logging.getLogger(__name__).warning("sentry_sdk_not_available")
        return

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        traces_sample_rate=0.0,
    )


def _extract_user_id_from_bearer(token: str) -> Optional[str]:
    try:
        from jose import JWTError, jwt
    except Exception:
        return None

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except Exception:
        return None

    user_id = payload.get("sub") or payload.get("user_id")
    return str(user_id) if user_id else None


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or new_request_id()
        uid: Optional[str] = None

        auth = request.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            uid = _extract_user_id_from_bearer(auth.split(" ", 1)[1].strip())

        bind_context(request_id=rid, user_id=uid)
        try:
            response = await call_next(request)
        except Exception as e:
            logging.getLogger(__name__).exception(
                f"unhandled_exception request_id={rid}",
                extra={"event": "unhandled_exception", "request_id": rid},
            )
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error", "request_id": rid})
        finally:
            clear_context()

        response.headers["X-Request-ID"] = rid
        return response
