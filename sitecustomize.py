"""
sitecustomize: runtime patches applied at Python startup.

Purpose: make Basicsr registry idempotent so duplicate imports
(e.g., Real-ESRGAN arch modules re-imported by runpy) do not crash
with "already registered" assertion.

This file is auto-imported by Python if its directory is on sys.path.
We'll ensure that by injecting the repo root into PYTHONPATH before
launching the Real-ESRGAN subprocess.
"""

from __future__ import annotations


def _patch_basicsr_registry() -> None:
    try:
        from basicsr.utils import registry as _registry_mod  # type: ignore
    except Exception:
        # basicsr not installed or import failed; nothing to patch
        return

    Registry = getattr(_registry_mod, "Registry", None)
    if Registry is None:
        return

    original = getattr(Registry, "_do_register", None)
    if not callable(original):
        return

    # Avoid double-patching
    if getattr(original, "__patched_by_aporto__", False):
        return

    def _do_register(self, name, func_or_class, suffix=""):
        # Derive key consistent with upstream
        if name is None:
            name = getattr(func_or_class, "__name__", name)
        key = f"{name}{suffix}" if suffix else name

        existing = self._obj_map.get(key)
        if existing is not None:
            # Idempotent: same object => no-op
            if existing is func_or_class:
                return func_or_class
            # Consider objects equivalent across reloads if module+name match
            if (
                getattr(existing, "__module__", None)
                == getattr(func_or_class, "__module__", None)
                and getattr(existing, "__name__", None)
                == getattr(func_or_class, "__name__", None)
            ):
                return func_or_class
            # Different object under the same name: keep protective error
            raise KeyError(
                f"An object named '{key}' was already registered in '{self._name}' registry "
                f"with a different object ({existing} != {func_or_class})."
            )

        # First time registration
        self._obj_map[key] = func_or_class
        return func_or_class

    # Mark and apply patch
    _do_register.__patched_by_aporto__ = True  # type: ignore[attr-defined]
    Registry._do_register = _do_register  # type: ignore[assignment]


# Execute patches at import
_patch_basicsr_registry()
