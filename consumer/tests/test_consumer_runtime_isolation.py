from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

class ConsumerRuntimeIsolationTests(unittest.TestCase):
    def test_consumer_owns_dedicated_config_state_and_port(self):
        bootstrap=(ROOT/"consumer"/"bootstrap.ps1").read_text(encoding="utf-8-sig")
        app=(ROOT/"consumer"/"consumer_app.py").read_text(encoding="utf-8-sig")
        bm=(ROOT/"consumer"/"browser_manager.py").read_text(encoding="utf-8-sig")
        updater=(ROOT/"consumer"/"updater.py").read_text(encoding="utf-8-sig")
        run=(ROOT/"windows-relay"/"run.ps1").read_text(encoding="utf-8-sig")
        consumer_run=(ROOT/"windows-relay"/"run-consumer.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("GPTWindowsRelayConsumer",bootstrap)
        self.assertIn("$port=8767",bootstrap)
        self.assertIn("GPTWindowsRelayConsumer",app)
        self.assertIn("8767",app)
        self.assertIn("GPTWindowsRelayConsumer",bm)
        self.assertIn("GPTWindowsRelayConsumer",updater)
        self.assertIn("GPT_CONSUMER_DEDICATED_RUNNER_V1",bootstrap)
        self.assertIn("run-consumer.ps1",bootstrap)
        self.assertIn("Local\\GPTWindowsRelayConsumerSupervisor",consumer_run)
        self.assertIn("--config $config --state-dir $stateDir server",consumer_run)
        self.assertNotIn("Local\\GPTWindowsRelaySupervisor",consumer_run)
        self.assertIn("Local\\GPTWindowsRelaySupervisor",run)
        self.assertNotIn("GPTWindowsRelayConsumer",run)
        self.assertIn("& $py $server server",run)
    def test_consumer_extension_can_reach_isolated_relay_port(self):
        import json
        manifest=json.loads((ROOT/"windows-relay"/"extension"/"manifest.json").read_text(encoding="utf-8-sig"))
        self.assertIn("http://127.0.0.1:8767/*",manifest.get("host_permissions",[]))
        if (ROOT/"windows-relay"/"extension-persistent"/"manifest.json").is_file():
            persistent=json.loads((ROOT/"windows-relay"/"extension-persistent"/"manifest.json").read_text(encoding="utf-8-sig"))
            self.assertIn("http://127.0.0.1:8767/*",persistent.get("host_permissions",[]))

    def test_consumer_extension_has_mv3_safe_browser_heartbeat(self):
        import json
        root=ROOT/"windows-relay"/"extension"
        manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8-sig"))
        self.assertIn("alarms",manifest.get("permissions",[]))
        worker=(root/"service_worker.js").read_text(encoding="utf-8-sig")
        self.assertIn("GPT_BROWSER_HEARTBEAT_ALARM_V1",worker)
        self.assertIn("periodInMinutes:0.5",worker)
        self.assertIn("const alarms=chrome?.alarms;",worker)
        self.assertIn("alarms.onAlarm.addListener",worker)
        self.assertIn("function installScannerRecoveryAlarm()",worker)
        self.assertIn("try{chrome.alarms.onAlarm.addListener",worker)
        self.assertLess(worker.index("chrome.runtime.onConnect.addListener"),worker.index("installScannerRecoveryAlarm();",worker.index("chrome.runtime.onConnect.addListener")))
        self.assertIn("installBrowserHeartbeatLifecycle();",worker)
        self.assertIn("chrome.runtime.onStartup.addListener",worker)

    def test_chromium_setup_fresh_reloads_matching_unpacked_extension(self):
        helper=(ROOT/"windows-relay"/"chromium_extension_setup.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("GPT_CHROMIUM_FRESH_UNPACKED_RELOAD_V1",helper)
        inspect_pos=helper.index("'Extensions.getExtensions'")
        uninstall_pos=helper.index("'Extensions.uninstall'")
        load_pos=helper.index("'Extensions.loadUnpacked'")
        self.assertLess(inspect_pos,uninstall_pos)
        self.assertLess(uninstall_pos,load_pos)
        self.assertIn("entryFull.TrimEnd",helper)
        self.assertIn("resolvedExtension.TrimEnd",helper)
        self.assertIn("-ieq",helper)

    def test_current_chatgpt_message_role_is_accepted_by_assistant_validator(self):
        text=(ROOT/"windows-relay"/"extension"/"content.js").read_text(encoding="utf-8-sig")
        self.assertIn("GPT_CHATGPT_DATA_MESSAGE_ROLE_VALIDATOR_V1",text)
        self.assertIn("node.matches('[data-message-role=\"assistant\"]')",text)
        self.assertIn("node.matches('[data-message-role=\"user\"]')",text)
        self.assertIn("'[data-message-role=\"assistant\"],[data-message-author-role=\"assistant\"]",text)
        self.assertIn("'[data-message-role=\"user\"],[data-message-author-role=\"user\"]",text)

    def test_consumer_extension_supports_current_chatgpt_message_role_dom(self):
        content=(ROOT/"windows-relay"/"extension"/"content.js").read_text(encoding="utf-8-sig")
        self.assertIn("GPT_CHATGPT_DATA_MESSAGE_ROLE_COMPAT_V1",content)
        self.assertIn("'[data-message-role=\"user\"]'",content)
        self.assertIn("'[data-message-role=\"assistant\"]'",content)
        self.assertIn("'[data-message-author-role=\"user\"]'",content)
        self.assertIn("'[data-message-author-role=\"assistant\"]'",content)
        self.assertLess(content.index("'[data-message-role=\"user\"]'"),content.index("'[data-message-author-role=\"user\"]'"))
        self.assertLess(content.index("'[data-message-role=\"assistant\"]'"),content.index("'[data-message-author-role=\"assistant\"]'"))

    def test_consumer_package_uses_extension_content_as_single_source_of_truth(self):
        build=(ROOT/"consumer"/"build-package.ps1").read_text(encoding="utf-8-sig")
        manager=(ROOT/"consumer"/"browser_manager.py").read_text(encoding="utf-8-sig")
        self.assertIn("GPT_CONSUMER_CANONICAL_CONTENT_SOURCE_V1",build)
        self.assertIn("Join-Path $relay 'extension\\content.js'",build)
        self.assertNotIn("Join-Path $runtime 'content.js') -Destination (Join-Path $runtime 'extension\\content.js'",build)
        self.assertIn('HERE / "runtime" / "extension" / "content.js"',manager)
        self.assertIn('HERE.parent / "windows-relay" / "extension" / "content.js"',manager)
        self.assertNotIn('HERE.parent / "windows-relay" / "content.js"',manager)

    def test_updater_source_tree_install_uses_canonical_extension_content(self):
        import importlib.util
        import tempfile
        import hashlib
        updater_path=ROOT/"consumer"/"updater.py"
        spec=importlib.util.spec_from_file_location("oneclick_updater_r24_test",updater_path)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        source=(ROOT/"windows-relay"/"extension"/"content.js").read_bytes()
        with tempfile.TemporaryDirectory(prefix="oneclick-updater-r24-") as td:
            module.HERE=Path(td)
            result=module._install_from_source_tree(ROOT)
            runtime=(Path(td)/"runtime"/"content.js").read_bytes()
            extension=(Path(td)/"runtime"/"extension"/"content.js").read_bytes()
            self.assertEqual(runtime,source)
            self.assertEqual(extension,source)
            self.assertEqual(
                result.get("revision"),
                module.load_release(ROOT / "consumer" / "release.json").get("revision"),
            )
        text=updater_path.read_text(encoding="utf-8-sig")
        self.assertIn("GPT_UPDATER_CANONICAL_CONTENT_SOURCE_V1",text)
        self.assertIn('    "content.js",\n    "chromium_extension_setup.ps1"',text)
        self.assertIn('if name == "content.js":\n            continue',text)
        self.assertIn('_copy_file(canonical_content, target_runtime / "content.js")',text)
        self.assertNotIn('_copy_file(target_runtime / "content.js", target_ext / "content.js")',text)

    def test_shared_bridge_is_not_migrated(self):
        bootstrap=(ROOT/"consumer"/"bootstrap.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("legacySettings",bootstrap)
        self.assertNotIn("legacyBridge",bootstrap)

if __name__=="__main__": unittest.main()
