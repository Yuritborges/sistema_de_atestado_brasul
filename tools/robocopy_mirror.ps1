function Invoke-RobocopyMirror {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [int]$Retries = 20,
        [int]$WaitSeconds = 2
    )
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "robocopy.exe"
    $psi.Arguments = "`"$Source`" `"$Destination`" /MIR /R:$Retries /W:$WaitSeconds /NFL /NDL /NJH /NJS /NP"
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $p = [System.Diagnostics.Process]::Start($psi)
    $p.WaitForExit()
    return $p.ExitCode
}
