"""
Generates an API endpoint map for a Django project (best-effort).

What it tries to detect:
  - DRF Routers and viewsets (inspect urlpatterns for routers)
  - Function/class-based views mapped under urlpatterns
  - For DRF viewsets: attempts to extract .action mapping, http methods, permission_classes, serializer_class

Outputs:
  - api_map.json with a list of endpoints and metadata
  - api_map.md (human-readable)

Usage:
  DJANGO_SETTINGS_MODULE=your_project.settings python scripts/generate_api_map.py

Limitations:
  - This is best-effort. Highly dynamic routing, custom router classes, or view factories may not be fully analyzable.
"""

import json
import os
import sys
import argparse
import inspect
import traceback
from collections import defaultdict


def setup():
    if "DJANGO_SETTINGS_MODULE" not in os.environ:
        print("ERROR: Set DJANGO_SETTINGS_MODULE environment variable before running.")
        sys.exit(2)
    try:
        import django
        django.setup()
    except Exception as e:
        print("Failed to setup Django:", e)
        traceback.print_exc()
        sys.exit(1)


def gather_urlpatterns():
    from django.urls import get_resolver, URLPattern, URLResolver
    resolver = get_resolver()
    patterns = []

    def _recurse(patterns_list, prefix=""):
        for entry in patterns_list:
            if isinstance(entry, URLPattern):
                route = prefix + (getattr(entry.pattern, "_route", None) or str(entry.pattern))
                patterns.append((route, entry.callback, entry))
            elif isinstance(entry, URLResolver):
                route = prefix + (getattr(entry.pattern, "_route", None) or str(entry.pattern))
                try:
                    _recurse(entry.url_patterns, route)
                except Exception:
                    patterns.append((route, entry, entry))
            else:
                patterns.append((prefix + str(entry), entry, entry))

    _recurse(resolver.url_patterns)
    return patterns


def extract_drf_info(callback):
    """Try to extract DRF-like metadata from a view or viewset callable."""
    info = {}
    try:
        # If it's a viewset class, callback may be 'SomeViewSet.as_view({...})' -> function with cls attrs
        view_cls = getattr(callback, "cls", None) or getattr(callback, "view_class", None)
        if view_cls is None and inspect.isfunction(callback):
            # For function-based DRF views decorated by api_view, there's an attribute 'cls'? not necessarily.
            view_cls = getattr(callback, "view_class", None)
        if view_cls is not None:
            # permission_classes
            perms = getattr(view_cls, "permission_classes", None)
            info["permission_classes"] = [getattr(p, "__name__", str(p)) for p in (perms or [])]
            info["serializer_class"] = getattr(view_cls, "serializer_class", None) and getattr(view_cls, "serializer_class").__name__ or None
            # try to detect actions
            if hasattr(view_cls, "actions"):
                info["actions"] = dict(view_cls.actions)
    except Exception:
        pass
    return info


def determine_methods(callback):
    """Return allowed HTTP methods for the callback (best effort)."""
    methods = []
    try:
        if hasattr(callback, "actions"):
            # DRF viewset .actions maps http method name to action name
            for m in callback.actions.keys():
                methods.append(m.upper())
        elif hasattr(callback, "cls"):
            # DRF as_view wrapper
            cls = callback.cls
            for m in ("get", "post", "put", "patch", "delete", "head", "options"):
                if hasattr(cls, m):
                    methods.append(m.upper())
        else:
            # naive: inspect function name or attributes
            if hasattr(callback, "allowed_methods"):
                methods = list(getattr(callback, "allowed_methods") or [])
            else:
                # fallback: common methods
                methods = ["GET"]
    except Exception:
        methods = ["GET"]
    return sorted(set(m.upper() for m in methods))


def build_api_map(out_json="api_map.json", out_md="api_map.md"):
    patterns = gather_urlpatterns()
    api_entries = []
    for route, callback, entry in patterns:
        try:
            view_name = None
            if hasattr(callback, "__name__"):
                view_name = callback.__name__
            elif hasattr(callback, "__class__"):
                view_name = callback.__class__.__name__
            else:
                view_name = str(callback)

            methods = determine_methods(callback)
            drf_info = extract_drf_info(callback)

            entry_data = {
                "route": route,
                "view": view_name,
                "methods": methods,
                "permissions": drf_info.get("permission_classes", []),
                "serializer": drf_info.get("serializer_class"),
                "notes": "",
            }

            # Try to read docstring for request/response format hints
            doc = inspect.getdoc(callback)
            if doc:
                entry_data["notes"] = doc.split("\n")[0]

            api_entries.append(entry_data)
        except Exception as e:
            api_entries.append({"route": route, "view": str(callback), "error": str(e)})

    # write json
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(api_entries, f, indent=2, ensure_ascii=False)

    # write markdown
    lines = ["# API Map", "", "Generated by scripts/generate_api_map.py", "", "| Route | Methods | View | Permissions | Serializer | Notes |",
             "|---|---|---|---|---|---|"]
    for e in api_entries:
        route = e.get("route")
        methods = ",".join(e.get("methods") or [])
        view = e.get("view")
        perms = ",".join(e.get("permissions") or [])
        ser = e.get("serializer") or ""
        notes = e.get("notes") or e.get("error", "")
        lines.append(f"| `{route}` | `{methods}` | `{view}` | `{perms}` | `{ser}` | {notes} |")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return out_json, out_md


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", help="Django settings module (DJANGO_SETTINGS_MODULE)")
    parser.add_argument("--out_json", default="api_map.json")
    parser.add_argument("--out_md", default="api_map.md")
    args = parser.parse_args()

    if args.settings:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", args.settings)

    setup()
    a, b = build_api_map(args.out_json, args.out_md)
    print(f"Wrote API map to: {a} and {b}")
    