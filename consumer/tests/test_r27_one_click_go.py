from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SOURCE = (HERE / "consumer_app.py").read_text(encoding="utf-8")

def test_one_click_go_is_default_enabled_and_visible():
    assert 'text="One-click GO upon entering prompt"' in SOURCE
    assert 'settings.get("one_click_go", True)' in SOURCE

def test_auto_go_can_setup_disconnected_browser_before_send():
    assert 'browser_manager.open_extension_setup(browser["id"])' in SOURCE
    assert 'mission_id = self._send_mission(mission, browser)' in SOURCE

def test_manual_mode_preserves_connected_gate():
    assert 'if not self.one_click_go.get()' in SOURCE
    assert 'if not self._browser_connected(browser)' in SOURCE

def test_go_work_runs_off_tk_main_thread():
    assert 'threading.Thread(target=worker, name="oneclick-go", daemon=True).start()' in SOURCE
