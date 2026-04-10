# R6 Server Switcher - Feature Todo List

If you are rebuilding this app, here is the high-level checklist of features the application must support:

## Core Functionality
- [ ] Automatically locate Rainbow Six Siege player configuration directories (`GameSettings.ini`).
- [ ] Determine and display the current active server/datacenter for a selected account.
- [ ] Provide a selectable list of all available Rainbow Six Siege regional servers.
- [ ] Successfully modify the `GameSettings.ini` file to change the server to the newly selected region.
- [ ] Support a "Reset to Default" button to let the game automatically pick the best server again.
- [ ] Support switching between multiple player accounts if more than one is found on the machine.

## System Tray & Background Operation
- [ ] Start minimizing to the system tray instead of closing completely when the user hits 'X'.
- [ ] Create a system tray icon for the application.
- [ ] Provide a system tray menu with options to either "Show Switcher" (bring the window back) or "Quit" (fully close the app).
- [ ] Ensure the app stays alive in the background quietly without draining excessive resources.

## User Interface Requirements
- [ ] Display the currently loaded account and its active server setting clearly.
- [ ] Allow the user to sort the server list logically (e.g., A-Z, or grouped by Continent).
- [ ] Keep track of the 3 most recently chosen servers to allow quick 1-click swapping.
- [ ] Show non-intrusive "Toast" notifications for positive actions (e.g., "Saved: East US") and errors (e.g., "Error: Account not found").

## Lifecycle & Distribution
- [ ] Automatically check GitHub (or your chosen repo) on startup for a newer app version.
- [ ] Alert the user when an update is available and give them a button to start the update.
- [ ] Automatically download the new version, replace the old executable, and restart the app without manual user effort.
- [ ] Compile the application down into a single portable `.exe` file that requires no installation.
