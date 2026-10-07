import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import windows_relay as wr

def test_readiness_requires_live_content_integration(tmp_path):
    s=wr.State(tmp_path/'state.json'); s.mark_browser_seen('edge',False)
    assert s.browser_status('edge')['connected'] is False
    s.mark_browser_seen('edge',True)
    assert s.browser_status('edge')['connected'] is True

def test_heartbeat_ttl_covers_mv3_alarm_cadence():
    assert wr.BROWSER_HEARTBEAT_TTL_SECONDS > 30.0

def test_worker_reports_port_readiness():
    text=(ROOT/'extension/service_worker.js').read_text(encoding='utf-8')
    assert 'consumerMissionPorts.size>0' in text
    assert 'integration_connected=' in text
    assert text.count('browserHeartbeat(true);') >= 2

def test_cdp_reloads_chatgpt_after_extension_install():
    text=(ROOT/'chromium_extension_setup.ps1').read_text(encoding='utf-8')
    assert 'GPT_CHROMIUM_POSTLOAD_RELOAD_V1' in text
    assert text.index('Extensions.loadUnpacked') < text.index('Target.createTarget') < text.index('Target.attachToTarget') < text.index('Page.reload')
