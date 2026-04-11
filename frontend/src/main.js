import './style.css';
import { GetAccounts, GetServers, GetFavorites, SetFavorite, ApplyServer } from '../wailsjs/go/main/App';
import { WindowHide, WindowMinimise } from '../wailsjs/runtime/runtime';

// Window events
document.addEventListener('keydown', (e) => {
    if (e.altKey && e.key === 'F4') {
        WindowHide();
    }
});

const accountSelect = document.getElementById('account-dropdown');
const serverSelect = document.getElementById('server-dropdown');
const saveBtn = document.getElementById('save-btn');
const defaultBtn = document.getElementById('default-btn');
const favoriteStar = document.getElementById('favorite-star');
const favoriteSlots = document.querySelectorAll('.favorite-slot');
const minBtn = document.getElementById('min-btn');
const closeBtn = document.getElementById('close-btn');

minBtn.addEventListener('click', WindowMinimise);
closeBtn.addEventListener('click', WindowHide);

let allServers = [];
let currentFavorites = ["", "", ""];

async function init() {
    try {
        allServers = await GetServers();
        serverSelect.innerHTML = allServers.map(s => `<option value="${s.id}">${s.name}</option>`).join('');

        const accounts = await GetAccounts();
        accountSelect.innerHTML = '<option value="All Accounts">All Accounts</option>' + 
            accounts.map(a => `<option value="${a}">${a}</option>`).join('');
            
        await refreshFavorites();
    } catch (err) {
        console.error("Init failed:", err);
    }
}

async function refreshFavorites() {
    currentFavorites = await GetFavorites();
    favoriteSlots.forEach((btn, index) => {
        const serverID = currentFavorites[index];
        const server = allServers.find(s => s.id === serverID);
        btn.innerText = server ? server.name : `Slot ${index + 1}`;
        btn.classList.toggle('has-favorite', !!server);
    });
    updateStarState();
}

function updateStarState() {
    const isFavorited = currentFavorites.includes(serverSelect.value);
    const starImg = favoriteStar.querySelector('.star-img');
    if (starImg) {
        starImg.classList.toggle('active', isFavorited);
    }
}

serverSelect.addEventListener('change', updateStarState);

// Set favorite on right-click, select on left-click
favoriteSlots.forEach(btn => {
    btn.addEventListener('click', () => {
        const slot = parseInt(btn.dataset.slot);
        const serverID = currentFavorites[slot];
        if (serverID) {
            serverSelect.value = serverID;
            updateStarState();
        }
    });

    btn.addEventListener('contextmenu', async (e) => {
        e.preventDefault();
        const slot = parseInt(btn.dataset.slot);
        const currentServerID = serverSelect.value;
        await SetFavorite(slot, currentServerID);
        await refreshFavorites();
    });
});

// Star click: Toggle favorite
favoriteStar.addEventListener('click', async () => {
    const currentServerID = serverSelect.value;
    const existingIndex = currentFavorites.indexOf(currentServerID);
    
    if (existingIndex !== -1) {
        // Untoggle (remove)
        await SetFavorite(existingIndex, "");
    } else {
        // Toggle (add to first empty slot)
        let slotToUse = currentFavorites.findIndex(f => f === "");
        if (slotToUse === -1) slotToUse = 0;
        await SetFavorite(slotToUse, currentServerID);
    }
    await refreshFavorites();
});

// Save Functionality
saveBtn.addEventListener('click', async () => {
    const account = accountSelect.value;
    const serverID = serverSelect.value;
    saveBtn.innerText = "Saving...";
    saveBtn.disabled = true;
    try {
        await ApplyServer(account, serverID);
        setTimeout(() => {
            saveBtn.innerText = "Saved!";
            setTimeout(() => {
                saveBtn.innerText = "Save";
                saveBtn.disabled = false;
            }, 1500);
        }, 500);
    } catch (err) {
        alert("Failed to save: " + err);
        saveBtn.innerText = "Error";
        saveBtn.disabled = false;
    }
});

defaultBtn.addEventListener('click', () => {
    serverSelect.value = 'default';
    updateStarState();
});

init();
