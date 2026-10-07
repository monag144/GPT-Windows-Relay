from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_hud_uses_readable_opaque_system_text():
    t=(ROOT/'hud.py').read_text(encoding='utf-8'); assert 'GPT_RELAY_HUD_READABLE_V2' in t; assert "Segoe UI" in t; assert "-transparentcolor" not in t; assert 'W,H=400,116' in t; assert 'HUD_LAYOUT_VERSION=2' in t
