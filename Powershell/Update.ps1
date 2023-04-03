function Update-LocalFileWithRemoteFile {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Url,
        [Parameter(Mandatory=$true)]
        [string]$LocalPath
    )

    # Download the remote file
    $response = Invoke-WebRequest $Url

    # Write the contents to the local file
    Set-Content -Path $LocalPath -Value $response.Content
}

$url = "https://raw.githubusercontent.com/stlenx/WhisperOSC/main/Powershell/version.json"
$onlineVER = Invoke-RestMethod $url

$jsonString = Get-Content -Path "Powershell\version.json" -Raw
$localVER = $jsonString | ConvertFrom-Json

if($localVER.version -lt $onlineVER.version) {
    Write-Host "New version available, downloading..."

    $onlinePYURL = "https://raw.githubusercontent.com/stlenx/WhisperOSC/main/Python/transcribe.py"
    $localPY = "Python\transcribe.py"
    Update-LocalFileWithRemoteFile -Url $onlinePYURL -LocalPath $localPY

    $onlineRequirementsTXT = "https://raw.githubusercontent.com/stlenx/WhisperOSC/main/Python/requirements.txt"
    $localRequirementsTXT = "Python\requirements.txt"
    Update-LocalFileWithRemoteFile -Url $onlineRequirementsTXT -LocalPath $localRequirementsTXT

    $onlineRequirementsBAT = "https://raw.githubusercontent.com/stlenx/WhisperOSC/main/INSTALLREQUIREMENTS.bat"
    $localRequirementsBAT = "INSTALLREQUIREMENTS.bat"
    Update-LocalFileWithRemoteFile -Url $onlineRequirementsBAT -LocalPath $localRequirementsBAT

    $localVersionJSON = "Powershell\version.json"
    Update-LocalFileWithRemoteFile -Url $url -LocalPath $localVersionJSON

    .\INSTALLREQUIREMENTS.bat

    Write-Host "Update done :)"
}