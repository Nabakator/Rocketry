"""DRIFT application package."""

from importlib.metadata import PackageNotFoundError, version

APP_NAME = "DRIFT"
APP_FULL_NAME = "DRIFT - Deployment and Recovery Integrated Flight Tool"
PACKAGE_NAME = "drift"

try:
    APP_VERSION = version(PACKAGE_NAME)
except PackageNotFoundError:
    APP_VERSION = "0+unknown"

APP_WINDOW_NAME = f"{APP_NAME} (v{APP_VERSION})"

__all__ = [
    "APP_NAME",
    "APP_FULL_NAME",
    "APP_VERSION",
    "APP_WINDOW_NAME",
    "PACKAGE_NAME",
]
