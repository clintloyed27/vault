"""Compatibility layer for FastAPI 0.111.x & Starlette 1.x lifecycle arguments."""
import starlette.routing

_orig_router_init = starlette.routing.Router.__init__

def _patched_router_init(self, *args, **kwargs):
    kwargs.pop("on_startup", None)
    kwargs.pop("on_shutdown", None)
    _orig_router_init(self, *args, **kwargs)
    if not hasattr(self, "on_startup"):
        self.on_startup = []
    if not hasattr(self, "on_shutdown"):
        self.on_shutdown = []

starlette.routing.Router.__init__ = _patched_router_init
