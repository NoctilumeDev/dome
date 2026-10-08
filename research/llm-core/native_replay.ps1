param([ValidateSet('pilot','core')][string]$Phase='pilot')
$ErrorActionPreference='Stop'
$researchRoot=$PSScriptRoot
$workspaceRoot=Split-Path (Split-Path $researchRoot)
$pythonExecutable='C:\Users\lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$mavenExecutable='D:\Maven\apache-maven-3.9.11-bin\apache-maven-3.9.11\bin\mvn.cmd'
$env:JAVA_HOME='D:\IDEA\JDK17'
Push-Location $researchRoot
try {
 & $pythonExecutable -B prepare_native.py $Phase
 if($LASTEXITCODE -ne 0){throw 'Replay input failed'}
 $nativeOutputRoot=Join-Path $researchRoot ('results\'+$Phase+'\native-v2')
 New-Item -ItemType Directory -Path $nativeOutputRoot -Force | Out-Null
 foreach($systemName in @('qingye','library')) {
  if($systemName -eq 'qingye') {
   $backendPath=Join-Path $workspaceRoot 'qingye\backend'
   $className='QingyeResearchReplayTest'
   $testFile=Join-Path $backendPath ('src\test\java\cn\qingye\'+$className+'.java')
  } else {
   $backendPath=Join-Path $workspaceRoot 'coursework\library-management-system\backend'
   $className='LibraryResearchReplayTest'
   $testFile=Join-Path $backendPath ('src\test\java\cn\kmbeast\'+$className+'.java')
  }
  Copy-Item -LiteralPath (Join-Path $researchRoot ('native\'+$className+'.java')) -Destination $testFile -Force
  $env:RESEARCH_NATIVE_INPUT=Join-Path $researchRoot ('results\'+$Phase+'\native-input.json')
  $env:RESEARCH_NATIVE_OUTPUT=Join-Path $nativeOutputRoot ('native-'+$systemName+'.jsonl')
  $env:RESEARCH_NATIVE_SNAPSHOT=Join-Path $nativeOutputRoot ('snapshot-'+$systemName+'.json')
  Push-Location $backendPath
  try {
   & $mavenExecutable -B -ntp ('-Dtest='+$className+'#nativeFrozenReplay') test *> (Join-Path $nativeOutputRoot ('native-'+$systemName+'.log'))
   $runExitCode=$LASTEXITCODE
  } finally { Pop-Location }
  if($runExitCode -ne 0){throw ('Native replay failed: '+$systemName)}
  Write-Output ('Native '+$systemName+' PASS')
 }
} finally {
 Pop-Location
 Remove-Item Env:RESEARCH_NATIVE_INPUT,Env:RESEARCH_NATIVE_OUTPUT,Env:RESEARCH_NATIVE_SNAPSHOT -ErrorAction SilentlyContinue
}
