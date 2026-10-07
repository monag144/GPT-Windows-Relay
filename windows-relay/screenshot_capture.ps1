param(
 [Parameter(Mandatory=$true)][ValidateSet('screen','window','region')][string]$Target,
 [Parameter(Mandatory=$true)][string]$Output,
 [string]$WindowTitle,
 [int]$ProcessId=0,
 [int]$X=0,[int]$Y=0,[int]$Width=0,[int]$Height=0
)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
if($Target -eq 'screen'){
 $r=[System.Windows.Forms.SystemInformation]::VirtualScreen
 $x=$r.X;$y=$r.Y;$w=$r.Width;$h=$r.Height;$label='virtual_screen'
}elseif($Target -eq 'region'){
 if($Width -le 0 -or $Height -le 0){throw 'region width and height must be positive'}
 $x=$X;$y=$Y;$w=$Width;$h=$Height;$label='region'
}else{
 if([string]::IsNullOrWhiteSpace($WindowTitle)){throw 'window title is required'}
 $root=[Windows.Automation.AutomationElement]::RootElement
 $all=$root.FindAll([Windows.Automation.TreeScope]::Children,[Windows.Automation.Condition]::TrueCondition)
 $m=@()
 foreach($e in $all){try{if($e.Current.Name -eq $WindowTitle -and -not $e.Current.IsOffscreen -and ($ProcessId -le 0 -or $e.Current.ProcessId -eq $ProcessId)){$m+=,$e}}catch{}}
 if($m.Count -ne 1){throw ('WINDOW_MATCH_COUNT_'+$m.Count)}
 $r=$m[0].Current.BoundingRectangle
 $x=[int][Math]::Floor($r.X);$y=[int][Math]::Floor($r.Y);$w=[int][Math]::Ceiling($r.Width);$h=[int][Math]::Ceiling($r.Height)
 if($w -le 0 -or $h -le 0){throw 'window bounds invalid'}
 $label='window'
}
$dir=Split-Path -Parent $Output;[IO.Directory]::CreateDirectory($dir)|Out-Null
$bmp=[System.Drawing.Bitmap]::new($w,$h,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$g=[System.Drawing.Graphics]::FromImage($bmp)
try{$g.CopyFromScreen($x,$y,0,0,(New-Object System.Drawing.Size $w,$h),[System.Drawing.CopyPixelOperation]::SourceCopy);$bmp.Save($Output,[System.Drawing.Imaging.ImageFormat]::Png)}finally{$g.Dispose();$bmp.Dispose()}
@{ok=$true;target=$label;x=$x;y=$y;width=$w;height=$h;path=[IO.Path]::GetFullPath($Output)}|ConvertTo-Json -Compress
