function Test-GPPreflight {
    if($PSVersionTable.PSEdition -ne 'Core' -or $PSVersionTable.PSVersion -lt [version]'7.4'){throw 'PowerShell 7.4 or newer is required.'}
    $pnp=Get-Module -ListAvailable PnP.PowerShell|Sort-Object Version -Descending|Select-Object -First 1
    if(-not $pnp){throw 'PnP.PowerShell is not installed. Run: Install-Module PnP.PowerShell -Scope CurrentUser'}
    Import-Module PnP.PowerShell -Force
    Write-GPLog "PowerShell $($PSVersionTable.PSVersion); PnP.PowerShell $($pnp.Version)" SUCCESS
}
function Connect-GPSite {
    $modes=@(
      [bool]$global:GPContext.Interactive,
      [bool]$global:GPContext.DeviceLogin,
      [bool]$global:GPContext.OSLogin
    )|Where-Object{$_}
    if($modes.Count -gt 1){throw 'Choose only one authentication mode: -Interactive, -DeviceLogin, or -OSLogin.'}

    $params=@{
      Url=$global:GPContext.SiteUrl
      ClientId=$global:GPContext.ClientId
      ValidateConnection=$true
      ErrorAction='Stop'
    }
    if($global:GPContext.DeviceLogin){
      $params.DeviceLogin=$true
      $mode='DeviceLogin'
      Write-GPLog 'Authentication mode: DeviceLogin. Follow the device-code instructions shown by PnP.PowerShell.' INFO
    }elseif($global:GPContext.OSLogin){
      $params.OSLogin=$true
      $mode='OSLogin'
      Write-GPLog 'Authentication mode: OSLogin. Waiting for the operating-system sign-in dialog.' INFO
    }else{
      $params.Interactive=$true
      $mode='Interactive'
      Write-GPLog 'Authentication mode: Interactive. Waiting for the Microsoft sign-in window; it may open behind the current terminal.' INFO
    }
    Write-GPLog ("Connecting to SharePoint site '{0}' using {1}." -f $global:GPContext.SiteUrl,$mode) INFO
    Connect-PnPOnline @params
    $web=Get-PnPWeb -Includes Title,Url -ErrorAction Stop
    Write-GPLog ("Connected to {0} ({1})." -f $web.Title,$web.Url) SUCCESS
}
function Test-GPWritePermission {
    if($global:GPContext.DryRun -or $global:GPContext.SkipWritePermissionTest){return}
    $name='GP5PermissionTest'
    try{
      if(-not(Get-PnPField -Identity $name -ErrorAction SilentlyContinue)){Add-PnPField -DisplayName $name -InternalName $name -Type Text -Group $global:GPContext.FieldGroup|Out-Null}
      Remove-PnPField -Identity $name -Force
    }catch{throw "Write permission test failed: $($_.Exception.Message)"}
}
function Set-GPSchemaVersion {
    param([string]$Version)
    $values=@{Title='Platform.SchemaVersion';SettingKey='Platform.SchemaVersion';SettingValue=$Version;SettingType='Version';Category='Platform';IsActive=$true}
    if($global:GPContext.DryRun){Write-GPLog "Set schema version to $Version" DRYRUN;return}
    $q="<View><Query><Where><Eq><FieldRef Name='SettingKey'/><Value Type='Text'>Platform.SchemaVersion</Value></Eq></Where></Query></View>"
    $item=Get-PnPListItem -List AppSettings -Query $q -ErrorAction SilentlyContinue|Select-Object -First 1
    if($item){Set-PnPListItem -List AppSettings -Identity $item.Id -Values $values|Out-Null}else{Add-PnPListItem -List AppSettings -Values $values|Out-Null}
}
Export-ModuleMember -Function Test-GPPreflight,Connect-GPSite,Test-GPWritePermission,Set-GPSchemaVersion
