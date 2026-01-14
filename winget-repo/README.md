# OpenLyst Winget Repository

This is a Winget manifest repository for Windows applications from [OpenLyst](https://openlyst.ink).

## Installation

To install packages from this repository, you can use the Winget command-line tool with direct package identifiers:

```powershell
# Install a specific OpenLyst application
winget install OpenLyst.AppName

# Search for available OpenLyst applications
winget search OpenLyst.

# Get information about a package
winget show OpenLyst.AppName
```

## Available Packages

The manifests are automatically generated from the OpenLyst API. Check the `manifests/OpenLyst/` directory for available applications.

## Package Structure

Each application follows the standard Winget manifest structure:
- `OpenLyst.AppName.installer.yaml` - Installer configuration
- `OpenLyst.AppName.locale.en-US.yaml` - Package metadata
- `OpenLyst.AppName.yaml` - Version information

## Usage Examples

```powershell
# Install Docan
winget install OpenLyst.Docan

# Install Doudou
winget install OpenLyst.Doudou

# Upgrade all OpenLyst packages
winget upgrade --source winget | findstr OpenLyst
```

## Contributing to Microsoft's Winget Repository

These manifests can be submitted to the official [Microsoft winget-pkgs repository](https://github.com/microsoft/winget-pkgs) to make them available through the default Winget source.

## Automated Updates

The manifests in this repository are automatically updated via GitHub Actions when the "Build Winget Repository" workflow runs.