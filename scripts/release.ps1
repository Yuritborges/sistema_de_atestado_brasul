# Atalho: chama tools\build_release.ps1 (releases + current no projeto na rede)
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
& (Join-Path $Root "tools\build_release.ps1")
