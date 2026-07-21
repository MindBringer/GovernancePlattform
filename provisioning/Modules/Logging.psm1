function Write-GPLog {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Message,[ValidateSet('INFO','WARN','ERROR','SUCCESS','DRYRUN','PLAN','SKIP')][string]$Level='INFO')
    $line='[{0}] [{1}] {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'),$Level,$Message
    Write-Host $line
    if($global:GPContext -and $global:GPContext.LogFile){
        $dir=Split-Path $global:GPContext.LogFile -Parent
        if(-not(Test-Path $dir)){New-Item -ItemType Directory -Path $dir -Force|Out-Null}
        Add-Content -Path $global:GPContext.LogFile -Value $line -Encoding utf8
    }
}
function Invoke-GPChange {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Description,[Parameter(Mandatory)][scriptblock]$Action)
    if($global:GPContext.DryRun){Write-GPLog $Description DRYRUN;return}
    Write-GPLog $Description INFO
    & $Action
}
Export-ModuleMember -Function Write-GPLog,Invoke-GPChange
