package main

import (
	"context"
	"embed"
	std_runtime "runtime"

	"github.com/energye/systray"
	"github.com/wailsapp/wails/v2"
	"github.com/wailsapp/wails/v2/pkg/options"
	"github.com/wailsapp/wails/v2/pkg/options/assetserver"
	wails_runtime "github.com/wailsapp/wails/v2/pkg/runtime"
)

//go:embed all:frontend/dist
var assets embed.FS

//go:embed build/windows/icon.ico
var icon []byte

var (
	ctxChan = make(chan context.Context, 1)
)

func main() {
	// Initialize systray in a background goroutine
	go setupSystray()

	app := NewApp()

	err := wails.Run(&options.App{
		Title:  "r6-server-switcher",
		Width:  1024,
		Height: 768,
		AssetServer: &assetserver.Options{
			Assets: assets,
		},
		BackgroundColour: &options.RGBA{R: 37, G: 36, B: 34, A: 1},
		OnStartup: func(ctx context.Context) {
			app.startup(ctx)
			ctxChan <- ctx // Pass context to systray handler
		},
		HideWindowOnClose: true,
		Frameless:         true,
		Bind: []interface{}{
			app,
		},
	})

	if err != nil {
		println("Error:", err.Error())
	}
}

func setupSystray() {
	// Lock OS thread for Windows-specific systray message loop
	std_runtime.LockOSThread()
	systray.Run(onSystrayReady, func() {})
}

func onSystrayReady() {
	systray.SetIcon(icon)
	systray.SetTitle("R6 Server Switcher")
	systray.SetTooltip("Rainbow Six Siege Server Switcher")

	mShow := systray.AddMenuItem("Show", "Show the window")
	mHide := systray.AddMenuItem("Hide", "Hide the window")

	systray.AddSeparator()
	mQuit := systray.AddMenuItem("Quit", "Quit the application")

	// Listen for menu interactions in a separate routine once context is available
	go func() {
		ctx := <-ctxChan
		mShow.Click(func() {
			go wails_runtime.WindowShow(ctx)
		})
		mHide.Click(func() {
			go wails_runtime.WindowHide(ctx)
		})
		mQuit.Click(func() {
			systray.Quit()
			go wails_runtime.Quit(ctx)
		})

		// Handle tray click events
		systray.SetOnClick(func(menu systray.IMenu) {
			go wails_runtime.WindowShow(ctx)
		})

		systray.SetOnRClick(func(menu systray.IMenu) {
			menu.ShowMenu()
		})
	}()
}
