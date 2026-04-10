using Microsoft.UI;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;
using Microsoft.UI.Xaml.Data;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Navigation;
using Microsoft.Windows.Storage.Pickers;
using Microsoft.WindowsAPICodePack.Dialogs;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Runtime.InteropServices.WindowsRuntime;
using System.Threading.Tasks;
using Windows.Foundation;
using Windows.Foundation.Collections;
using Windows.Storage;

// To learn more about WinUI, the WinUI project structure,
// and more about our project templates, see: http://aka.ms/winui-project-info.

namespace r6_server_switcher
{
    /// <summary>
    /// An empty page that can be used on its own or navigated to within a Frame.
    /// </summary>
    public sealed partial class MainPage : Page
    {
        private List<string>? _folderPaths;
        private async Task<List<string>> FindGameSettings()
        {
            List<string> folderPaths = new List<string>();
            var gameSettingsPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), @"My Games\Rainbow Six - Siege");

            if (Directory.Exists(gameSettingsPath))
            {
                StorageFolder rootFolder = await StorageFolder.GetFolderFromPathAsync(gameSettingsPath);
                IReadOnlyList<StorageFolder> subFolders = await rootFolder.GetFoldersAsync();

                foreach (StorageFolder folder in subFolders)
                {
                    string folderPath = folder.Path;
                    folderPaths.Add(folderPath);
                }
            }

            return folderPaths;
        }

        private void PopulateAccountDropdown(List<string> folderPaths)
        {
            AccountDropdown.Items.Clear();
            foreach (string path in folderPaths)
            {
                string folderName = Path.GetFileName(path);
                AccountDropdown.Items.Add(folderName);
            }
        }

        private async void InitializeAsync()
        {
            _folderPaths = await FindGameSettings();
            PopulateAccountDropdown(_folderPaths);
        }

        private void PopulateServerDropdown()
        {
            ServerDropdown.Items.Add("default");
            ServerDropdown.Items.Add("playfab/australiaeast");
            ServerDropdown.Items.Add("playfab/brazilsouth");
            ServerDropdown.Items.Add("playfab/centralus");
            ServerDropdown.Items.Add("playfab/eastasia");
            ServerDropdown.Items.Add("playfab/eastus");
            ServerDropdown.Items.Add("playfab/japaneast");
            ServerDropdown.Items.Add("playfab/northeurope");
            ServerDropdown.Items.Add("playfab/southafricanorth");
            ServerDropdown.Items.Add("playfab/southcentralus");
            ServerDropdown.Items.Add("playfab/southeastasia");
            ServerDropdown.Items.Add("playfab/uaenorth");
            ServerDropdown.Items.Add("playfab/westeurope");
            ServerDropdown.Items.Add("playfab/westus");
        }

        private void ChangeServer(IEnumerable<string> folderPaths)
        {
            if (ServerDropdown.SelectedItem == null || folderPaths == null)
                return;

            string selected = ServerDropdown.SelectedItem.ToString();

            foreach (string path in folderPaths)
            {
                string settingsFilePath = Path.Combine(path, "GameSettings.ini");
                if (File.Exists(settingsFilePath))
                {
                    string[] lines = File.ReadAllLines(settingsFilePath);
                    for (int i = 0; i < lines.Length; i++)
                    {
                        if (lines[i].StartsWith("DataCenterHint="))
                        {
                            lines[i] = "DataCenterHint=" + selected;
                            break;
                        }
                    }
                    File.WriteAllLines(settingsFilePath, lines);
                }
            }
        }

        public MainPage()
        {
            InitializeComponent();
            PopulateServerDropdown();
            InitializeAsync();
        }

        private async void Button_Click(object sender, RoutedEventArgs e)
        {
            if (_folderPaths == null)
            {
                _folderPaths = await FindGameSettings();
                PopulateAccountDropdown(_folderPaths);
            }

            ChangeServer(_folderPaths);
        }
    }
}
