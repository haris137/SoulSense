"""
Smoke tests for the Streamlit layer.

* If Streamlit is installed, the real app is executed with Streamlit's own
  AppTest harness.
* Otherwise a fake `streamlit` module (tests/fake_streamlit.py) is used so every
  page function still runs end to end.
"""
import importlib
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))

try:
    import streamlit  # noqa: F401
    REAL = hasattr(streamlit, "__version__")
except ImportError:
    REAL = False


@unittest.skipIf(REAL, "real Streamlit installed - AppTest class below is used instead")
class FakeStreamlitPageTests(unittest.TestCase):
    PAGES = ["home", "profile", "combat_advisor", "shell_advisor", "boss_advisor",
             "progression_advisor", "diagnosis", "knowledge_explorer"]

    def setUp(self):
        import fake_streamlit
        for name in list(sys.modules):
            if name.split(".")[0] in ("components", "pages", "streamlit"):
                del sys.modules[name]
        self.st = fake_streamlit.install()

    def render_all(self):
        for name in self.PAGES:
            module = importlib.import_module(f"pages.{name}")
            module.render()

    def test_every_page_renders_with_empty_session(self):
        self.render_all()

    def test_every_page_renders_for_every_scenario(self):
        from knowledge_base.scenarios import SCENARIOS
        for scenario in SCENARIOS.values():
            self.st.session_state["facts"] = dict(scenario["facts"])
            self.render_all()

    def test_forms_round_trip_stored_answers(self):
        """Rendering the forms must not change answers the user already gave."""
        from knowledge_base.scenarios import SCENARIOS
        for scenario in SCENARIOS.values():
            original = dict(scenario["facts"])
            original.pop("encounter_type", None)       # boss page forces this one
            self.st.session_state["facts"] = dict(original)
            self.render_all()
            after = self.st.session_state["facts"]
            for key, value in original.items():
                self.assertEqual(after.get(key), value, key)

    def test_no_duplicate_widget_keys_on_any_page(self):
        """Streamlit raises DuplicateWidgetID when two widgets on a page share a key."""
        from knowledge_base.scenarios import SCENARIOS
        for scenario in list(SCENARIOS.values()) + [{"facts": {}}]:
            for name in self.PAGES:
                self.st.session_state["facts"] = dict(scenario["facts"])
                self.st.keys.clear()
                importlib.import_module(f"pages.{name}").render()
                self.assertEqual(len(self.st.keys), len(set(self.st.keys)),
                                 f"duplicate widget key on page {name}")

    def test_app_entrypoint_runs(self):
        import runpy
        runpy.run_path(os.path.join(ROOT, "app.py"), run_name="__main__")

    def test_navigation_has_all_pages(self):
        from components.navigation import build_navigation
        nav = build_navigation()
        titles = [p.title for pages in nav.pages.values() for p in pages]
        self.assertEqual(len(titles), 8)


@unittest.skipUnless(REAL, "needs real Streamlit")
class RealStreamlitAppTests(unittest.TestCase):
    def test_app_starts_without_exception(self):
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=30).run()
        self.assertFalse(at.exception)


if __name__ == "__main__":
    unittest.main()
