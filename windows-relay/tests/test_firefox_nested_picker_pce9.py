import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ADAPTER=ROOT/'firefox_tab_adapter.ps1'

class FirefoxNestedPickerPce9Tests(unittest.TestCase):
 def test_ensure_addon_falls_back_to_nested_firefox_file_picker(self):
  s=ADAPTER.read_text(encoding='utf-8')
  marker='# GPT_WINDOWS_FIREFOX_NESTED_FILE_PICKER_V1'
  self.assertIn(marker,s)
  tail=s[s.index(marker):]
  self.assertIn('$firefox.FindAll([Windows.Automation.TreeScope]::Descendants,$nestedWindowType)',tail)
  self.assertIn("$w.Current.ClassName -eq '#32770'",tail)
  self.assertLess(tail.index(marker),tail.index('FIREFOX_ADDON_FILE_DIALOG_NOT_FOUND'))

if __name__=='__main__': unittest.main()