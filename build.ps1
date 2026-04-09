# Build script for R6 Server Switcher
# Added version info and extra data for icon
uv run pyinstaller `
    --noconsole `
    --onefile `
    --name "R6ServerSwitcher" `
    --icon "icon.ico" `
    --version-file "file_version_info.txt" `
    --add-data "ui;ui" `
    --add-data "icon.ico;." `
    --add-data "icon.png;." `
    --clean `
    main.py
