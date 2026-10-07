from pathlib import Path

helper = Path(__file__).with_name("pce7_445_apply.py")
source = helper.read_text(encoding="utf-8")

old_snapshot = "    new_snapshot = '''def snapshot():\n"
new_snapshot = "    new_snapshot = r'''def snapshot():\n"
count = source.count(old_snapshot)
if count != 1:
    raise SystemExit(f"PCE7.445V2_GUARD_FAILED expected 1 snapshot marker, found {count}")
source = source.replace(old_snapshot, new_snapshot, 1)

old_marker = "# GPT_RELAY_HUD_OPERATOR_CONTROL_V2\ndef relay_control(action):"
new_marker = "# GPT_RELAY_HUD_OPERATOR_STOP_START_V1\n# GPT_RELAY_HUD_OPERATOR_CONTROL_V2\ndef relay_control(action):"
count = source.count(old_marker)
if count != 1:
    raise SystemExit(f"PCE7.445V2_GUARD_FAILED expected 1 control marker, found {count}")
source = source.replace(old_marker, new_marker, 1)

namespace = {"__name__": "__main__", "__file__": str(helper), "__package__": None}
exec(compile(source, str(helper), "exec"), namespace, namespace)
