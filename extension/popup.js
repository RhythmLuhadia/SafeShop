// ============================
// SAFESHOP POPUP v2.0
// ============================

const SUPPORTED_SITES = [
    "bigbasket.com", "amazon.in", "zeptonow.com", "blinkit.com", "swiggy.com"
];

const REGION_META = {
    global: { icon: "🌐", label: "Global" },
    india:  { icon: "🇮🇳", label: "FSSAI" },
    eu:     { icon: "🇪🇺", label: "EU/EFSA" },
    usa:    { icon: "🇺🇸", label: "FDA" },
};

let currentAllergies = [];

document.addEventListener('DOMContentLoaded', () => {

    // ── STEP 1: Load saved settings ──────────────────────────
    chrome.storage.local.get(['region', 'allergies'], (data) => {
        // Region picker
        if (data.region) {
            document.getElementById('region').value = data.region;
        }
        updateRegionCard(data.region || 'global');

        // Allergy chips
        if (data.allergies) {
            currentAllergies = data.allergies.split(',').map(s => s.trim()).filter(Boolean);
            renderAllergyChips();
        }
        updateAllergyCount();
    });

    // ── STEP 2: Live server status check ─────────────────────
    checkServerStatus();

    // ── STEP 3: Region dropdown live-update ──────────────────
    document.getElementById('region').addEventListener('change', (e) => {
        updateRegionCard(e.target.value);
    });

    // ── STEP 4: Allergen chip input ──────────────────────────
    document.getElementById('allergy-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            const val = e.target.value.trim().toLowerCase().replace(/,$/, '');
            if (val && !currentAllergies.includes(val)) {
                currentAllergies.push(val);
                renderAllergyChips();
                updateAllergyCount();
            }
            e.target.value = '';
        }
    });

    // ── STEP 5: Save button ───────────────────────────────────
    document.getElementById('saveBtn').addEventListener('click', () => {
        const region = document.getElementById('region').value;
        const allergiesStr = currentAllergies.join(', ');

        chrome.storage.local.set({ region, allergies: allergiesStr }, () => {
            const btn = document.getElementById('saveBtn');
            btn.innerText = "✓  Profile Saved!";
            btn.classList.add('saved');

            // BUG FIX #4: Reload any active supported site tab, not just BigBasket
            setTimeout(() => {
                chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                    if (tabs.length > 0) {
                        const tabUrl = tabs[0].url || '';
                        const isSupportedSite = SUPPORTED_SITES.some(site => tabUrl.includes(site));
                        if (isSupportedSite) {
                            chrome.tabs.reload(tabs[0].id);
                        }
                    }
                });
                window.close();
            }, 900);
        });
    });
});

// ── HELPERS ──────────────────────────────────────────────────

function checkServerStatus() {
    const pill = document.getElementById('status-pill');
    const text = document.getElementById('status-text');

    // Start in "Checking" state
    setPillState('checking', 'Checking...');

    fetch('http://127.0.0.1:8000/categories', { method: 'GET', signal: AbortSignal.timeout(3000) })
        .then(res => {
            if (res.ok) {
                setPillState('online', 'Server Online');
            } else {
                setPillState('offline', 'Server Error');
            }
        })
        .catch(() => {
            setPillState('offline', 'Server Offline');
        });
}

function setPillState(state, label) {
    const pill = document.getElementById('status-pill');
    const text = document.getElementById('status-text');
    pill.className = 'status-pill ' + state;
    text.innerText = label;
}

function updateRegionCard(regionKey) {
    const meta = REGION_META[regionKey] || REGION_META['global'];
    document.getElementById('stat-region').innerText = meta.icon;
    document.getElementById('stat-region-label').innerText = meta.label;
}

function updateAllergyCount() {
    const el = document.getElementById('stat-allergy-count');
    el.innerText = currentAllergies.length;
    el.style.color = currentAllergies.length > 0 ? '#ef4444' : '#f1f5f9';
}

function renderAllergyChips() {
    const container = document.getElementById('allergy-chips');
    container.innerHTML = '';
    currentAllergies.forEach((allergen, index) => {
        const chip = document.createElement('div');
        chip.className = 'allergy-chip';
        chip.innerHTML = `🦠 ${allergen} <span class="remove" title="Remove">✕</span>`;
        chip.querySelector('.remove').addEventListener('click', () => {
            currentAllergies.splice(index, 1);
            renderAllergyChips();
            updateAllergyCount();
        });
        container.appendChild(chip);
    });
}
