"""
A tiny stand-in for the `streamlit` module.

It lets the unit tests execute every page's Python code (form generation,
engine calls, result rendering) on machines where Streamlit is not installed.
Widgets simply return their default / current value, like an untouched page.
It checks Python-level correctness only, not Streamlit's real rendering.
"""
import sys
import types


class _Ctx:
    """Works both as a context manager and as an object with st-like methods."""
    def __init__(self, st):
        self._st = st

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __getattr__(self, name):
        return getattr(self._st, name)


class FakeStreamlit(types.ModuleType):
    def __init__(self):
        super().__init__("streamlit")
        self.session_state = {}
        self.calls = []
        self.keys = []          # every widget key used in the current page render
        self.sidebar = _Ctx(self)

    # ---- layout
    def columns(self, spec, **kw):
        n = spec if isinstance(spec, int) else len(spec)
        return [_Ctx(self) for _ in range(n)]

    def tabs(self, labels):
        return [_Ctx(self) for _ in labels]

    def expander(self, *a, **kw):
        return _Ctx(self)

    def container(self, *a, **kw):
        return _Ctx(self)

    def _key(self, kw):
        if kw.get("key") is not None:
            self.keys.append(kw["key"])

    # ---- widgets: return what an untouched widget would return
    def selectbox(self, label, options, index=0, **kw):
        self._key(kw)
        return options[index] if options else None

    def radio(self, label, options, index=0, **kw):
        self._key(kw)
        return options[index]

    def slider(self, label, min_value, max_value, value, step=1, **kw):
        self._key(kw)
        return value

    def number_input(self, label, min_value, max_value, value, step=1, **kw):
        self._key(kw)
        return value

    def checkbox(self, label, value=False, **kw):
        self._key(kw)
        return value

    def multiselect(self, label, options, default=None, **kw):
        self._key(kw)
        return list(default or [])

    def text_input(self, *a, **kw):
        self._key(kw)
        return ""

    def button(self, *a, **kw):
        self._key(kw)
        return False

    # ---- control flow
    def rerun(self):
        self.calls.append("rerun")

    def set_page_config(self, **kw):
        pass

    def Page(self, func, **kw):
        return types.SimpleNamespace(func=func, **kw)

    def navigation(self, pages):
        first = next(iter(pages.values()))[0]
        return types.SimpleNamespace(run=first.func, pages=pages)

    # ---- everything else (markdown, metric, dataframe, code, ...) is a no-op
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)

        def method(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return _Ctx(self)
        return method


def install():
    fake = FakeStreamlit()
    sys.modules["streamlit"] = fake
    return fake
