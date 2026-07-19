Set-StrictMode -Version Latest

$script:ProjectRoot = Split-Path -Parent $PSScriptRoot
$script:SecretStorePath = Join-Path $script:ProjectRoot ".project-secrets\project-secrets.json"

function Get-HomeWikiProjectSecret {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateSet("NasUsername", "NasPassword", "BackupEncryptionCode")]
        [string] $Name
    )

    if ($env:OS -ne "Windows_NT") {
        throw "Der zentrale Projekt-Speicher kann nur unter dem Windows-Benutzer entschlüsselt werden, der ihn angelegt hat."
    }

    if (-not (Test-Path -LiteralPath $script:SecretStorePath -PathType Leaf)) {
        throw "Der zentrale Projekt-Speicher fehlt: $script:SecretStorePath"
    }

    $store = Get-Content -LiteralPath $script:SecretStorePath -Raw | ConvertFrom-Json
    if ($store.Protection -ne "WindowsDPAPI-CurrentUser") {
        throw "Unbekannter Schutzmechanismus im zentralen Projekt-Speicher."
    }

    $encryptedValue = $store.Secrets.$Name
    if ([string]::IsNullOrWhiteSpace($encryptedValue)) {
        throw "Das Projektgeheimnis '$Name' fehlt oder ist leer."
    }

    $secureValue = ConvertTo-SecureString -String $encryptedValue
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureValue)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
        $secureValue.Dispose()
    }
}

function Get-HomeWikiProjectSecretStorePath {
    [CmdletBinding()]
    param()

    return $script:SecretStorePath
}

Export-ModuleMember -Function Get-HomeWikiProjectSecret, Get-HomeWikiProjectSecretStorePath
