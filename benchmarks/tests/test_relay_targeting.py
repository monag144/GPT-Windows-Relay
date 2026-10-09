"""PCE14 Firefox targeting regression matrix.

Uses observed HWND pairs; deliberately does not import Windows UI libraries.
A passing classifier test never means a live browser message was sent.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from relay_targeting import classify_target  # noqa: E402

FOREGROUND = 19466700
BACKGROUND = 5441214
WINDOWS = [FOREGROUND, BACKGROUND]


class TargetingBenchmark(unittest.TestCase):
    def test_actual_pce14_010_two_window_result_is_uncertified(self):
        report = classify_target(FOREGROUND, FOREGROUND, WINDOWS)
        self.assertTrue(report["matches_foreground"])
        self.assertEqual(report["visible_firefox_count"], 2)
        self.assertEqual(report["status"], "BLOCKED_INVOKING_WINDOW_UNVERIFIED")
        self.assertFalse(report["can_send"])

    def test_first_process_selects_background_window(self):
        report = classify_target(BACKGROUND, FOREGROUND, WINDOWS)
        self.assertEqual(report["status"], "FAIL_BACKGROUND_WINDOW_SELECTED")
        self.assertFalse(report["can_send"])

    def test_foreground_belongs_to_another_app(self):
        report = classify_target(FOREGROUND, 123456, WINDOWS)
        self.assertEqual(report["status"], "BLOCKED_FOREGROUND_NOT_FIREFOX")

    def test_unrecognized_selected_window(self):
        report = classify_target(123456, FOREGROUND, WINDOWS)
        self.assertEqual(report["status"], "FAIL_SELECTED_WINDOW_NOT_VISIBLE")

    def test_no_visible_firefox_window(self):
        report = classify_target(FOREGROUND, FOREGROUND, [])
        self.assertEqual(report["status"], "BLOCKED_NO_FIREFOX_WINDOW")

    def test_invoke_window_disagrees_with_selection(self):
        report = classify_target(FOREGROUND, FOREGROUND, WINDOWS,
                                 invoking_hwnd=BACKGROUND)
        self.assertEqual(report["status"], "FAIL_INVOKING_WINDOW_MISMATCH")

    def test_matching_hwnd_without_tab_proof_is_blocked(self):
        report = classify_target(FOREGROUND, FOREGROUND, WINDOWS,
                                 invoking_hwnd=FOREGROUND)
        self.assertEqual(report["status"], "BLOCKED_TAB_UNVERIFIED")

    def test_wrong_tab_inside_correct_firefox_hwnd_fails(self):
        report = classify_target(FOREGROUND, FOREGROUND, WINDOWS,
                                 invoking_hwnd=FOREGROUND,
                                 invoking_tab_id="tab-origin",
                                 active_tab_id="tab-other")
        self.assertEqual(report["status"], "FAIL_WRONG_TAB")

    def test_matching_tab_trace_is_not_real_send_authorization(self):
        report = classify_target(FOREGROUND, FOREGROUND, WINDOWS,
                                 invoking_hwnd=FOREGROUND,
                                 invoking_tab_id="tab-origin",
                                 active_tab_id="tab-origin")
        self.assertEqual(report["status"], "TRACE_TAB_MATCH_NOT_AUTHENTICATED")
        self.assertFalse(report["can_send"])

    def test_malformed_hwnds_do_not_count_as_positive_evidence(self):
        for handles in [[FOREGROUND, FOREGROUND], [True], ["19466700"]]:
            with self.subTest(handles=handles):
                with self.assertRaises(ValueError):
                    classify_target(FOREGROUND, FOREGROUND, handles)

    def test_invalid_tab_identity_rejected(self):
        with self.assertRaises(ValueError):
            classify_target(FOREGROUND, FOREGROUND, WINDOWS,
                            invoking_hwnd=FOREGROUND,
                            invoking_tab_id=" ", active_tab_id="tab-origin")


if __name__ == "__main__":
    unittest.main()
