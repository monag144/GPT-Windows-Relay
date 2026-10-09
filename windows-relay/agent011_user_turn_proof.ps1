# Agent011 PCE11->PCE12 delivered-user-turn proof. No UI effect or navigation.
# A role label and multiple unique handoff markers must belong to the SAME
# per-message accessible Group. No conversation body is written to receipts.
function Test-Agent011TurnGroupProof(
 [string[]]$RoleLabels,
 [string[]]$TextNodes
){
 if($null -eq $RoleLabels -or $null -eq $TextNodes){return $false}
 $users=0
 $assistants=0
 foreach($role in $RoleLabels){
  if($role -ceq 'You said:' -or $role -ceq 'You said' -or $role -ceq 'User:'){$users++}
  if($role -ceq 'ChatGPT said:' -or $role -ceq 'ChatGPT said' -or $role -ceq 'Assistant:'){$assistants++}
 }
 if($users -ne 1 -or $assistants -ne 0){return $false}
 # UIA Markdown rendering can split the payload among Text descendants.
 $joined=[string]::Join([char]10,$TextNodes)
 foreach($needle in @(
  '[GPT_ENGINEERING_ROTATION_HANDOFF_V1]',
  'PCE12 takeover',
  'PCE12.000',
  '[/GPT_ENGINEERING_ROTATION_HANDOFF_V1]'
 )){
  if(-not $joined.Contains($needle)){return $false}
 }
 return $true
}
function Test-Agent011DeliveredUserTurn($Window){
 $condition=New-Object Windows.Automation.PropertyCondition(
  [Windows.Automation.AutomationElement]::ControlTypeProperty,
  [Windows.Automation.ControlType]::Text
 )
 $all=$Window.FindAll([Windows.Automation.TreeScope]::Descendants,$condition)
 if($all.Count -gt 12000){throw 'USER_TURN_TEXT_TREE_TOO_LARGE'}
 $proved=0
 for($i=0;$i -lt $all.Count;$i++){
  $label=[string]$all[$i].Current.Name
  if($label -cne 'You said:' -and $label -cne 'You said' -and $label -cne 'User:'){continue}
  $parent=[Windows.Automation.TreeWalker]::ControlViewWalker.GetParent($all[$i])
  if($null -eq $parent -or $parent.Current.ControlType -ne [Windows.Automation.ControlType]::Group){continue}
  # Only the direct per-message Group, never Window/Document/global descendants.
  $texts=$parent.FindAll([Windows.Automation.TreeScope]::Descendants,$condition)
  if($texts.Count -gt 2000){throw 'USER_TURN_GROUP_TOO_LARGE'}
  $names=New-Object System.Collections.Generic.List[string]
  $roles=New-Object System.Collections.Generic.List[string]
  for($j=0;$j -lt $texts.Count;$j++){
   $name=[string]$texts[$j].Current.Name
   if($name.Length -gt 0){$names.Add($name)}
   if($name -ceq 'You said:' -or $name -ceq 'You said' -or $name -ceq 'User:' -or
      $name -ceq 'ChatGPT said:' -or $name -ceq 'ChatGPT said' -or $name -ceq 'Assistant:'){$roles.Add($name)}
  }
  if(Test-Agent011TurnGroupProof -RoleLabels $roles.ToArray() -TextNodes $names.ToArray()){$proved++}
 }
 if($proved -gt 1){throw 'DELIVERED_HANDOFF_USER_TURN_AMBIGUOUS'}
 return ($proved -eq 1)
}
