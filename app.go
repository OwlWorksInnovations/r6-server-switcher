package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// ServerInfo represents a server location and ID.
type ServerInfo struct {
	ID   string `json:"id"`
	Name string `json:"name"`
}

// App struct represents the core application logic.
type App struct {
	ctx context.Context
}

// NewApp creates a new application instance.
func NewApp() *App {
	return &App{}
}

// startup is called on application initialization.
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
}

// GetAccounts scans the user's Siege settings folder for account directories
func (a *App) GetAccounts() ([]string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return nil, err
	}

	siegePath := filepath.Join(home, "Documents", "My Games", "Rainbow Six - Siege")
	entries, err := os.ReadDir(siegePath)
	if err != nil {
		return nil, err
	}

	var accounts []string
	for _, entry := range entries {
		if entry.IsDir() && len(entry.Name()) > 20 {
			accounts = append(accounts, entry.Name())
		}
	}

	return accounts, nil
}

// GetServers returns the list of available servers with their display names
func (a *App) GetServers() []ServerInfo {
	return []ServerInfo{
		{"default", "Default (Auto)"},
		{"playfab/australiaeast", "Australia East"},
		{"playfab/brazilsouth", "Brazil South"},
		{"playfab/centralus", "Central US"},
		{"playfab/eastasia", "East Asia"},
		{"playfab/eastus", "East US"},
		{"playfab/japaneast", "Japan East"},
		{"playfab/northeurope", "North Europe"},
		{"playfab/southafricanorth", "South Africa"},
		{"playfab/southcentralus", "South Central US"},
		{"playfab/southeastasia", "Southeast Asia"},
		{"playfab/uaenorth", "UAE North"},
		{"playfab/westeurope", "West Europe"},
		{"playfab/westus", "West US"},
	}
}

func (a *App) GetFavorites() ([]string, error) {
	configDir, err := os.UserConfigDir()
	if err != nil {
		return []string{"", "", ""}, nil
	}

	configPath := filepath.Join(configDir, "r6-server-switcher", "favorites.json")
	data, err := os.ReadFile(configPath)
	if err != nil {
		return []string{"", "", ""}, nil
	}

	var favorites []string
	if err := json.Unmarshal(data, &favorites); err != nil {
		return []string{"", "", ""}, nil
	}

	// Pad favorites to ensure 3 slots
	for len(favorites) < 3 {
		favorites = append(favorites, "")
	}
	return favorites[:3], nil
}

// SetFavorite saves a server ID to a specific favorite slot (0-2)
func (a *App) SetFavorite(slot int, serverID string) error {
	if slot < 0 || slot > 2 {
		return fmt.Errorf("invalid slot index")
	}

	favorites, _ := a.GetFavorites()
	favorites[slot] = serverID

	configDir, err := os.UserConfigDir()
	if err != nil {
		return err
	}

	appConfigDir := filepath.Join(configDir, "r6-server-switcher")
	if err := os.MkdirAll(appConfigDir, 0755); err != nil {
		return err
	}

	configPath := filepath.Join(appConfigDir, "favorites.json")
	data, err := json.Marshal(favorites)
	if err != nil {
		return err
	}

	return os.WriteFile(configPath, data, 0644)
}

// ApplyServer updates the GameSettings.ini for the target accounts.
func (a *App) ApplyServer(accountID string, serverID string) error {
	home, err := os.UserHomeDir()
	if err != nil {
		return err
	}

	siegePath := filepath.Join(home, "Documents", "My Games", "Rainbow Six - Siege")
	
	var targets []string
	if accountID == "" || accountID == "All Accounts" {
		entries, _ := os.ReadDir(siegePath)
		for _, e := range entries {
			if e.IsDir() && len(e.Name()) > 20 {
				targets = append(targets, e.Name())
			}
		}
	} else {
		targets = append(targets, accountID)
	}

	for _, target := range targets {
		iniPath := filepath.Join(siegePath, target, "GameSettings.ini")
		if err := a.updateIniFile(iniPath, serverID); err != nil {
			fmt.Printf("Error updating %s: %v\n", target, err)
		}
	}

	return nil
}

func (a *App) updateIniFile(path string, serverID string) error {
	file, err := os.Open(path)
	if err != nil {
		return err
	}
	defer file.Close()

	var lines []string
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		if strings.HasPrefix(line, "DataCenterHint=") {
			line = "DataCenterHint=" + serverID
		}
		lines = append(lines, line)
	}

	return os.WriteFile(path, []byte(strings.Join(lines, "\n")), 0644)
}
