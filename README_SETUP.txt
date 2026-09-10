NEW LAXMI MEDICAL & GENERAL STORE - NORMAL WINDOWS INSTALLER

This package is prepared to create a normal Setup.exe installer.

The installer will create:
- Desktop shortcut
- Start Menu shortcut
- Uninstaller
- MedicalStore.exe installed under Program Files
- User data/database under %LOCALAPPDATA%\NewLaxmiMedicalStore\medical_store.db

BUILD ON WINDOWS:
1. Install Python 3.10+ and tick "Add Python to PATH".
2. Install Inno Setup 6.
3. Double-click build_setup.bat.
4. The final installer will be Output\MedicalStoreSetup.exe.

The end user of MedicalStoreSetup.exe does NOT need Python or Inno Setup.

IMPORTANT: This environment is Linux, so a genuine Windows PE .exe cannot be compiled here. The included GitHub Actions workflow can compile the installer on a Windows runner if this folder is placed in a GitHub repository.
