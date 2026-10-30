# UberLLM installer for Claude Code — https://uberllm.dev
#
#   irm https://uberllm.dev/install/claude-code.ps1 | iex
#
# Writes the gateway variables into %USERPROFILE%\.claude\settings.json, which
# is where Claude Code looks before its first-run setup.
#Requires -Version 5.1
$ErrorActionPreference = 'Stop'

$ApiBase = 'https://api.uberllm.dev'
$Site    = 'https://uberllm.dev'
$Key     = ''
$Model   = ''
$Haiku   = ''

if ($env:UBERLLM_API_KEY) { $Key = $env:UBERLLM_API_KEY }

$ConfigDir = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE '.claude' }
$SettingsPath = Join-Path $ConfigDir 'settings.json'

Write-Host ''
Write-Host '  UberLLM -> Claude Code' -ForegroundColor Cyan

# --- Link this machine when no key was baked into the download ---------------
if (-not $Key) {
  $body = @{ client_name = $env:COMPUTERNAME; client_platform = 'windows' } | ConvertTo-Json
  $start = Invoke-RestMethod -Method Post -Uri "$ApiBase/api/v1/cli/link/start" -ContentType 'application/json' -Body $body

  Write-Host ''
  Write-Host '  Connect Claude Code to your UberLLM account - open this link, sign in, press Connect:'
  Write-Host ''
  Write-Host "    $($start.verification_url)" -ForegroundColor White
  Write-Host ''
  Write-Host "    Your code: $($start.link_code)" -ForegroundColor White
  Write-Host ''
  Start-Process $start.verification_url | Out-Null

  $pollBody = @{ device_code = $start.device_code } | ConvertTo-Json
  for ($i = 0; $i -lt 300; $i++) {
    Start-Sleep -Seconds 3
    try {
      $poll = Invoke-RestMethod -Method Post -Uri "$ApiBase/api/v1/cli/link/poll" -ContentType 'application/json' -Body $pollBody
    } catch { continue }
    if ($poll.status -eq 'approved') {
      $Key = $poll.api_key
      if ($poll.base_url) { $ApiBase = $poll.base_url }
      Write-Host '  Connected.' -ForegroundColor Green
      break
    }
    if ($poll.status -eq 'denied')  { throw 'The request was denied in the browser. Nothing was changed.' }
    if ($poll.status -eq 'expired') { throw 'The link expired. Run the installer again for a fresh code.' }
  }
  if (-not $Key) { throw 'Timed out waiting for approval. Nothing was changed.' }
}

# --- Merge into settings.json, preserving whatever is already there ----------
New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null

$cfg = [ordered]@{}
if (Test-Path $SettingsPath) {
  Copy-Item $SettingsPath "$SettingsPath.bak-$(Get-Date -Format yyyyMMddHHmmss)"
  try {
    $existing = Get-Content $SettingsPath -Raw | ConvertFrom-Json
    foreach ($p in $existing.PSObject.Properties) { $cfg[$p.Name] = $p.Value }
  } catch {
    Write-Warning 'Existing settings.json could not be parsed; it has been backed up and will be replaced.'
  }
}

$envBlock = [ordered]@{}
if ($cfg['env']) {
  foreach ($p in $cfg['env'].PSObject.Properties) { $envBlock[$p.Name] = $p.Value }
}
$envBlock['ANTHROPIC_BASE_URL'] = $ApiBase
$envBlock['ANTHROPIC_AUTH_TOKEN'] = $Key
$envBlock['CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY'] = '1'
foreach ($pair in @(
  @('ANTHROPIC_MODEL', $Model),
  @('ANTHROPIC_DEFAULT_OPUS_MODEL', $Model),
  @('ANTHROPIC_DEFAULT_SONNET_MODEL', $Model),
  @('ANTHROPIC_DEFAULT_HAIKU_MODEL', $Haiku)
)) {
  if ($pair[1]) { $envBlock[$pair[0]] = $pair[1] } else { $envBlock.Remove($pair[0]) | Out-Null }
}
$cfg['env'] = $envBlock

($cfg | ConvertTo-Json -Depth 20) | Set-Content -Path $SettingsPath -Encoding UTF8
Write-Host "  Configured Claude Code." -ForegroundColor Green

# --- Prove it works before declaring success --------------------------------
try {
  $verify = @{ model = 'claude-haiku-4-5'; max_tokens = 1; messages = @(@{ role = 'user'; content = '.' }) } | ConvertTo-Json -Depth 5
  Invoke-RestMethod -Method Post -Uri "$ApiBase/v1/messages" `
    -Headers @{ 'Authorization' = "Bearer $Key"; 'anthropic-version' = '2023-06-01' } `
    -ContentType 'application/json' -Body $verify | Out-Null
  Write-Host '  Verified a live request through the gateway.' -ForegroundColor Green
} catch {
  Write-Warning "Settings were written, but a test request did not succeed. Check your balance at $Site/dashboard/credits"
}

if ($env:ANTHROPIC_API_KEY) {
  Write-Warning 'ANTHROPIC_API_KEY is set in your environment - remove it to avoid an auth-conflict warning.'
}

Write-Host ''
Write-Host "  Done. Restart Claude Code (quit it, then run 'claude') - it now runs on UberLLM."
Write-Host ''
