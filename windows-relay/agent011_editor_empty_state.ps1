# Agent011 safe empty-state recognition for an already-verified ChatGPT editor.
# Observed Firefox UIAutomation ValuePattern and TextPattern may report the
# placeholder "Ask ChatGPT" + LF as writable Edit value. This is NOT a draft.
# This helper never selects a window, types into an editor, or submits content.
# Always verify exact window URL/tab, unique composer and STOP before use.
function Test-Agent011EmptyEditorValue([AllowNull()][string]$Value) {
 if ([string]::IsNullOrWhiteSpace($Value)) { return $true }
 return [string]::Equals(
  $Value,
  ('Ask ChatGPT' + [char]10),
  [StringComparison]::Ordinal
 )
}
function Test-Agent011DestinationReady(
 [AllowNull()][string]$Value,
 [bool]$HomeIdentityVerified,
 [int]$EnabledSendButtonCount
) {
 if (-not $HomeIdentityVerified) { return $false }
 if ($EnabledSendButtonCount -ne 0) { return $false }
 return (Test-Agent011EmptyEditorValue $Value)
}
