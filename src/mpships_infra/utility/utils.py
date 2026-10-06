import logging
from functools import wraps
from importlib.util import find_spec

import requests
from mp_api.client import MPRester

logger = logging.getLogger(__name__)

_session = requests.Session()


def get_rester(use_document_model: bool = True, **kwargs) -> MPRester:
    """Get an instance of MPRester with one session per worker.

    If other kwargs are needed, add these to `get_rester`

    Args:
        use_document_model (bool) : Whether to use pydantic models
    Returns:
        Instance of MPRester with one session per worker.
    """
    return MPRester(session=_session, use_document_model=use_document_model, **kwargs)


def check_mp_ui_available():
    return find_spec("mp_ui") is not None


MP_UI_INSTALLED = check_mp_ui_available()


def require_mp_ui(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not check_mp_ui_available:
            raise RuntimeError(
                "mp_ui is not available. Please check your installation."
            )
        return func(*args, **kwargs)

    return wrapper


@require_mp_ui
def get_login_endpoints():
    from mp_ui.core.utils import get_login_endpoints as _get_login_endpoints

    return _get_login_endpoints()
