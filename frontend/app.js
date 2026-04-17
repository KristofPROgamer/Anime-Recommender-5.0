// Anime Recommender v1.0 — Frontend Logic

// --- User Session Management ---
let currentUser = localStorage.getItem("anime_user_email") || null;
const STORAGE_KEY = "anime_rater_state";
let currentSearchQuery = "";

// Inline SVG placeholder — no external CDN dependency
const PLACEHOLDER_IMG = `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="150" height="220" viewBox="0 0 150 220">' +
    '<rect width="150" height="220" fill="#27272a"/>' +
    '<text x="75" y="100" font-family="sans-serif" font-size="12" fill="#71717a" text-anchor="middle">No Cover</text>' +
    '<text x="75" y="118" font-family="sans-serif" font-size="11" fill="#52525b" text-anchor="middle">Available</text>' +
    '</svg>'
)}`;

function normalizeSavedId(value) {
    if (typeof value === 'string' && /^\d+$/.test(value)) return parseInt(value, 10);
    return value;
}

function saveAppState() {
    const state = {
        included: Array.from(includedItems),
        excluded: Array.from(excludedItems),
        linked_groups: linkedGroups,
        logic_mode: document.getElementById('logic-mode').value,
        top_x: parseInt(document.getElementById('top-x').value, 10) || 10,
        min_score: parseFloat(document.getElementById('min-score').value) || 7.0,
        exclude_mal: document.getElementById('exclude-mal').checked,
        sort_select: document.getElementById('sort-select').value,
        search_query: currentSearchQuery
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function setLoadingState(isLoading) {
    const discoverBtn = document.getElementById('btn-discover');
    if (discoverBtn) {
        discoverBtn.disabled = isLoading;
        discoverBtn.innerText = isLoading ? 'Discovering...' : 'Discover Anime';
    }
}

function loadAppState() {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;

    try {
        const state = JSON.parse(raw);
        if (!state) return;

        document.getElementById('logic-mode').value = state.logic_mode || 'and';
        document.getElementById('top-x').value = state.top_x || 10;
        document.getElementById('min-score').value = state.min_score || 7.0;
        document.getElementById('exclude-mal').checked = state.exclude_mal !== false;
        document.getElementById('sort-select').value = state.sort_select || 'match';

        if (Array.isArray(state.included)) {
            state.included.map(normalizeSavedId).forEach(id => includedItems.add(id));
        }
        if (Array.isArray(state.excluded)) {
            state.excluded.map(normalizeSavedId).forEach(id => excludedItems.add(id));
        }
        if (Array.isArray(state.linked_groups)) {
            linkedGroups = state.linked_groups.map(group => group.map(normalizeSavedId));
        }

        currentSearchQuery = state.search_query || '';
        const searchInput = document.getElementById('search-input');
        if (searchInput) searchInput.value = currentSearchQuery;

        updateFilterButtonsFromState();
        renderFixedLines();
    } catch (err) {
        console.warn('Unable to load app state:', err);
    }
}

function updateFilterButtonsFromState() {
    Object.entries(btnElements).forEach(([key, btn]) => {
        const id = typeof btn.dataset.id === 'string' && /^\d+$/.test(btn.dataset.id)
            ? parseInt(btn.dataset.id, 10)
            : btn.dataset.id;
        btn.classList.remove('active', 'excluded', 'linked');

        if (includedItems.has(id)) btn.classList.add('active');
        if (excludedItems.has(id)) btn.classList.add('excluded');
    });

    linkedGroups.forEach(group => {
        group.forEach(id => {
            const btn = btnElements[id];
            if (btn) btn.classList.add('linked');
        });
    });
    updateSelectionSummary();
    updateFilterTags();
}

function updateFilterTags() {
    const container = document.getElementById('active-filters');
    if (!container) return;
    container.innerHTML = '';

    const tags = [];
    includedItems.forEach(id => {
        const btn = btnElements[id];
        if (btn) tags.push({ label: btn.innerText, id, type: 'include' });
    });
    excludedItems.forEach(id => {
        const btn = btnElements[id];
        if (btn) tags.push({ label: btn.innerText, id, type: 'exclude' });
    });

    tags.slice(0, 12).forEach(item => {
        const tag = document.createElement('div');
        tag.className = 'filter-tag';
        tag.innerHTML = `${item.label} <span title="Remove">×</span>`;
        tag.onclick = () => {
            if (item.type === 'include') {
                includedItems.delete(item.id);
            } else {
                excludedItems.delete(item.id);
            }
            const btn = btnElements[item.id];
            if (btn) btn.classList.remove('active', 'excluded');
            removeIdFromLinks(item.id);
            updateFilterTags();
            updateSelectionSummary();
            saveAppState();
        };
        container.appendChild(tag);
    });

    if (!tags.length) {
        container.innerHTML = '<div class="toolbar-caption">No active filters selected yet.</div>';
    }
}

function toggleModal(show) {
    document.getElementById('account-modal').style.display = show ? 'flex' : 'none';
    if (currentUser) {
        document.getElementById('modal-title').style.display = 'none';
        document.getElementById('auth-section').style.display = 'none';
        document.getElementById('settings-section').style.display = 'block';
        document.getElementById('logged-in-email').innerText = currentUser;
        document.getElementById('mal-username').value = localStorage.getItem("mal_username") || "";
        document.getElementById('mal-api').value = localStorage.getItem("mal_api") || "";
    } else {
        document.getElementById('modal-title').style.display = 'block';
        document.getElementById('auth-section').style.display = 'block';
        document.getElementById('settings-section').style.display = 'none';
        switchAuthTab('login');
    }
    updateUserUI();
}

function updateUserUI() {
    const status = document.getElementById('page-user-status');
    if (!status) return;
    status.innerText = currentUser ? `Logged in as ${currentUser}` : 'Not logged in';
}

function updateSelectionSummary() {
    document.getElementById('summary-included').innerText = includedItems.size;
    document.getElementById('summary-excluded').innerText = excludedItems.size;
    document.getElementById('summary-linked').innerText = linkedGroups.length;
}

function resetFilters() {
    includedItems.clear();
    excludedItems.clear();
    linkedGroups.forEach(group => group.forEach(id => {
        const btn = btnElements[id];
        if (btn) btn.classList.remove('linked');
    }));
    linkedGroups = [];
    Object.values(btnElements).forEach(btn => {
        btn.classList.remove('active', 'excluded', 'linked');
    });
    renderFixedLines();
    updateSelectionSummary();
    updateFilterTags();
    saveAppState();
    showToast('Filters reset successfully.');
}

function handleVerifyTokenInUrl() {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    if (!token) return;

    fetch('/api/verify_manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
        if (status === 200) {
            showToast('Email verified successfully! You can now log in.');
        } else {
            showToast(body.error || 'Verification failed.', true);
        }
        window.history.replaceState({}, document.title, window.location.pathname);
    })
    .catch(() => {
        showToast('Unable to verify token from URL.', true);
        window.history.replaceState({}, document.title, window.location.pathname);
    });
}

function switchAuthTab(tab) {
    const isLogin = tab === 'login';
    document.getElementById('tab-login').classList.toggle('active', isLogin);
    document.getElementById('tab-register').classList.toggle('active', !isLogin);
    document.getElementById('btn-login-submit').style.display = isLogin ? 'block' : 'none';
    document.getElementById('btn-register-submit').style.display = isLogin ? 'none' : 'block';
    document.getElementById('register-only-fields').style.display = isLogin ? 'none' : 'block';
    document.getElementById('verify-section').style.display = isLogin ? 'block' : 'none';
}

async function register() {
    const email   = document.getElementById('user-email').value;
    const pass    = document.getElementById('user-pass').value;
    const malUser = document.getElementById('reg-mal-username').value;
    const malApi  = document.getElementById('reg-mal-api').value;

    if (!email || !pass) { showToast("Please fill in Email and Password.", true); return; }

    const res  = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password: pass, mal_user: malUser, mal_api: malApi })
    });
    const data = await res.json();

    if (res.ok) {
        if (data.token) {
            // Email delivery failed — auto-populate the verify field and switch to login tab
            switchAuthTab('login');
            document.getElementById('verify-token-input').value = data.token;
            showToast("Registered! Token pasted below — click Verify to activate.");
        } else {
            showToast("Registered! Please check your email for the verification link.");
            switchAuthTab('login');
        }
    } else {
        showToast(data.error || "Registration failed.", true);
    }
}

async function verifyTokenManual() {
    const token = document.getElementById('verify-token-input').value.trim();
    if (!token) { showToast("Please paste your token first.", true); return; }

    const res  = await fetch('/api/verify_manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
    });
    const data = await res.json();

    if (res.ok) {
        showToast("Account verified! You can now log in.");
        document.getElementById('verify-token-input').value = "";
    } else {
        showToast(data.error || "Verification failed.", true);
    }
}

async function login() {
    const email = document.getElementById('user-email').value;
    const pass  = document.getElementById('user-pass').value;

    if (!email || !pass) { showToast("Please fill in all fields.", true); return; }

    const res  = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password: pass })
    });
    const data = await res.json();

    if (res.ok) {
        localStorage.setItem("anime_user_email", email);
        if (data.mal_user) localStorage.setItem("mal_username", data.mal_user);
        if (data.mal_api)  localStorage.setItem("mal_api",      data.mal_api);
        currentUser = email;
        showToast("Logged in!");
        toggleModal(false);
        updateUserUI();
    } else {
        showToast(data.error || "Login failed.", true);
    }
}

function logout() {
    localStorage.removeItem("anime_user_email");
    localStorage.removeItem("mal_username");
    localStorage.removeItem("mal_api");
    currentUser = null;
    document.getElementById('user-email').value         = "";
    document.getElementById('user-pass').value          = "";
    document.getElementById('reg-mal-username').value   = "";
    document.getElementById('reg-mal-api').value        = "";
    toggleModal(true);
    updateUserUI();
}

async function saveSettings() {
    const malUser = document.getElementById('mal-username').value;
    const malApi  = document.getElementById('mal-api').value;

    localStorage.setItem("mal_username", malUser);
    localStorage.setItem("mal_api",      malApi);

    try {
        const res = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: currentUser, mal_user: malUser, mal_api: malApi })
        });
        showToast(res.ok ? "Settings saved!" : "Settings saved locally (server sync failed).", !res.ok);
    } catch {
        showToast("Settings saved locally (offline).", true);
    }
    toggleModal(false);
}

// --- Filter Logic & Canvas ---
const genreMap = window.GENRE_MAP;
const genreSectionsContainer = document.getElementById('genre-sections');
const canvas = document.getElementById('line-canvas');

let includedItems  = new Set();
let excludedItems  = new Set();
let linkedGroups   = [];
let currentResults = [];

let isDragging  = false;
let startBtn    = null;
let currentLine = null;
const btnElements = {};

for (const [cat, items] of Object.entries(genreMap)) {
    const titleDiv = document.createElement('div');
    titleDiv.className = 'cat-title';
    titleDiv.innerText = cat;
    genreSectionsContainer.appendChild(titleDiv);

    const gridDiv = document.createElement('div');
    gridDiv.className = 'genre-grid';
    genreSectionsContainer.appendChild(gridDiv);

    for (const [name, rawId] of Object.entries(items)) {
        const id  = typeof rawId === 'string' ? rawId : parseInt(rawId);
        const btn = document.createElement('button');
        btn.className    = 'genre-btn';
        btn.innerText    = name;
        btn.dataset.id   = id;
        btnElements[id]  = btn;

        btn.onclick = (e) => {
            if (e.ctrlKey) return;

            if (includedItems.has(id)) {
                includedItems.delete(id);
                excludedItems.add(id);
                btn.classList.remove('active');
                btn.classList.add('excluded');
                removeIdFromLinks(id);
            } else if (excludedItems.has(id)) {
                excludedItems.delete(id);
                btn.classList.remove('excluded');
            } else {
                includedItems.add(id);
                btn.classList.add('active');
            }
            updateSelectionSummary();
            updateFilterTags();
            saveAppState();
        };

        btn.onmousedown = (e) => {
            if (e.ctrlKey && !excludedItems.has(id)) {
                isDragging = true;
                startBtn   = btn;
                includedItems.add(id);
                btn.classList.add('active');
                updateSelectionSummary();
                updateFilterTags();
                saveAppState();

                currentLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                currentLine.setAttribute('stroke', '#fbbf24');
                currentLine.setAttribute('stroke-width', '3');
                currentLine.setAttribute('stroke-dasharray', '5,5');
                canvas.appendChild(currentLine);
            }
        };

        btn.onmouseup = (e) => {
            if (isDragging && startBtn && startBtn !== btn && !excludedItems.has(id)) {
                const raw1 = startBtn.dataset.id;
                const id1  = isNaN(raw1) ? raw1 : parseInt(raw1);

                includedItems.add(id);
                btn.classList.add('active');

                linkedGroups.push([id1, id]);
                startBtn.classList.add('linked');
                btn.classList.add('linked');
                renderFixedLines();
                updateSelectionSummary();
                updateFilterTags();
                saveAppState();
            }
            isDragging = false;
            startBtn   = null;
            if (currentLine) { canvas.removeChild(currentLine); currentLine = null; }
        };

        gridDiv.appendChild(btn);
    }
}

loadAppState();
updateSelectionSummary();
updateFilterTags();
updateUserUI();
handleVerifyTokenInUrl();

window.addEventListener('beforeunload', saveAppState);
window.addEventListener('DOMContentLoaded', () => {
    const logicMode  = document.getElementById('logic-mode');
    const topX       = document.getElementById('top-x');
    const minScore   = document.getElementById('min-score');
    const excludeMal = document.getElementById('exclude-mal');
    const modalOverlay = document.querySelector('.modal-overlay');

    if (logicMode)    logicMode.addEventListener('change', saveAppState);
    if (topX)         topX.addEventListener('input', saveAppState);
    if (minScore)     minScore.addEventListener('input', saveAppState);
    if (excludeMal)   excludeMal.addEventListener('change', saveAppState);
    if (modalOverlay) {
        modalOverlay.addEventListener('click', (event) => {
            if (event.target === modalOverlay) toggleModal(false);
        });
    }
});

window.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') toggleModal(false);
});

window.onmousemove = (e) => {
    if (isDragging && startBtn && currentLine) {
        const rect = startBtn.getBoundingClientRect();
        currentLine.setAttribute('x1', rect.left + rect.width  / 2 + window.scrollX);
        currentLine.setAttribute('y1', rect.top  + rect.height / 2 + window.scrollY);
        currentLine.setAttribute('x2', e.pageX);
        currentLine.setAttribute('y2', e.pageY);
    }
};

window.onmouseup = () => {
    if (isDragging) {
        isDragging = false;
        startBtn   = null;
        if (currentLine) { canvas.removeChild(currentLine); currentLine = null; }
    }
};

window.addEventListener('resize', renderFixedLines);
window.addEventListener('scroll', renderFixedLines);

function renderFixedLines() {
    canvas.innerHTML = '';
    linkedGroups.forEach(group => {
        const b1 = btnElements[group[0]];
        const b2 = btnElements[group[1]];
        if (b1 && b2) {
            const r1   = b1.getBoundingClientRect();
            const r2   = b2.getBoundingClientRect();
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', r1.left + r1.width  / 2 + window.scrollX);
            line.setAttribute('y1', r1.top  + r1.height / 2 + window.scrollY);
            line.setAttribute('x2', r2.left + r2.width  / 2 + window.scrollX);
            line.setAttribute('y2', r2.top  + r2.height / 2 + window.scrollY);
            line.setAttribute('stroke', '#10b981');
            line.setAttribute('stroke-width', '2');
            canvas.appendChild(line);
        }
    });
}

function removeIdFromLinks(id) {
    const removedGroups = linkedGroups.filter(g => g.includes(id));
    linkedGroups = linkedGroups.filter(g => !g.includes(id));

    removedGroups.flat().forEach(memberId => {
        const btn = btnElements[memberId];
        if (!btn) return;
        const isStillLinked = linkedGroups.some(g => g.includes(memberId));
        if (!isStillLinked) btn.classList.remove('linked');
    });

    renderFixedLines();
    updateSelectionSummary();
    updateFilterTags();
    saveAppState();
}

function showToast(message, isError = false) {
    const toast = document.getElementById("toast");
    toast.innerText = message;
    toast.style.backgroundColor = isError ? "#f43f5e" : "#10b981";
    toast.className = "toast show";
    setTimeout(() => { toast.className = toast.className.replace("show", ""); }, 3500);
}

async function fetchRecommendations() {
    // Guests can discover anime; MAL exclusion is automatically disabled without a login.
    if (!currentUser) {
        const excludeToggle = document.getElementById('exclude-mal');
        if (excludeToggle && excludeToggle.checked) {
            excludeToggle.checked = false;
            showToast("Log in to enable MAL list exclusion. Discovering without it.", false);
        }
    }

    setLoadingState(true);
    document.getElementById('loader').style.display = 'block';
    document.getElementById('results').innerHTML = '';
    document.getElementById('results-toolbar').style.display = 'none';

    const linkedIds         = new Set(linkedGroups.flat());
    const standaloneIncludes = Array.from(includedItems).filter(id => !linkedIds.has(id));

    const payload = {
        included:      standaloneIncludes,
        excluded:      Array.from(excludedItems),
        linked_groups: linkedGroups,
        logic_mode:    document.getElementById('logic-mode').value,
        top_x:         parseInt(document.getElementById('top-x').value) || 10,
        exclude_mal:   document.getElementById('exclude-mal').checked,
        min_score:     parseFloat(document.getElementById('min-score').value),
        mal_user:      localStorage.getItem("mal_username"),
        mal_api:       localStorage.getItem("mal_api")
    };
    saveAppState();

    try {
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const apiData = await response.json().catch(() => null);
        if (!response.ok) {
            showToast(apiData?.error || 'Failed to fetch recommendations.', true);
            return;
        }

        currentResults = Array.isArray(apiData) ? apiData : [];
        document.getElementById('sort-select').value = 'match';
        sortAndRender();
        document.getElementById('results-toolbar').style.display = currentResults.length > 0 ? 'flex' : 'none';
    } catch (err) {
        showToast("Network error. Is the server running?", true);
    } finally {
        document.getElementById('loader').style.display = 'none';
        setLoadingState(false);
    }
}

function sortAndRender() {
    const sortBy = document.getElementById('sort-select').value;
    const query  = currentSearchQuery.trim().toLowerCase();

    let sortedData = [...currentResults];
    if (query) {
        sortedData = sortedData.filter(anime => {
            const title    = (anime.title    || '').toLowerCase();
            const synopsis = (anime.synopsis || '').toLowerCase();
            return title.includes(query) || synopsis.includes(query);
        });
    }

    if (sortBy === 'match') {
        sortedData.sort((a, b) => b.score - a.score);
    } else if (sortBy === 'score') {
        sortedData.sort((a, b) => b.raw_mean_score - a.raw_mean_score);
    } else if (sortBy === 'popularity') {
        sortedData.sort((a, b) =>
            (b.watching + b.completed + b.on_hold + b.dropped + b.plan) -
            (a.watching + a.completed + a.on_hold + a.dropped + a.plan)
        );
    }

    const summary = document.getElementById('results-summary');
    if (summary) {
        const total = currentResults.length;
        summary.innerText = `${sortedData.length} of ${total} results shown${query ? ` for "${query}"` : ''}`;
    }

    renderResults(sortedData);
    document.getElementById('results-toolbar').style.display = currentResults.length > 0 ? 'flex' : 'none';
}

function handleSearchInput() {
    currentSearchQuery = document.getElementById('search-input').value || '';
    sortAndRender();
    saveAppState();
}

function clearSearch() {
    currentSearchQuery = '';
    const searchInput = document.getElementById('search-input');
    if (searchInput) searchInput.value = '';
    sortAndRender();
    saveAppState();
}

function exportResults() {
    if (!currentResults || currentResults.length === 0) {
        showToast('No recommendations to export.', true);
        return;
    }
    const data = currentResults.map(anime => ({
        title:               anime.title,
        id:                  anime.id,
        mal_url:             `https://myanimelist.net/anime/${anime.id}`,
        algorithm_match_pct: parseFloat((anime.score * 100).toFixed(2)),
        mal_score:           parseFloat(anime.raw_mean_score.toFixed(2)),
        genres:              anime.genres,
        media_type:          anime.media_type,
        status:              anime.status,
        synopsis:            anime.synopsis
    }));
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const link = document.createElement('a');
    link.href     = URL.createObjectURL(blob);
    link.download = `anime_recommendations_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
}

function renderResults(animes) {
    const container = document.getElementById('results');
    container.innerHTML = '';

    if (animes.length === 0) {
        const message = currentSearchQuery
            ? `No results matched "${currentSearchQuery}".`
            : 'No anime met your criteria.';
        const detail = currentSearchQuery
            ? 'Try a broader search query or loosen your filters.'
            : 'Try reducing excluded filters, lowering the minimum score, or switching to OR logic.';
        container.innerHTML = `
            <div style="grid-column:1/-1;text-align:center;padding:4rem;background:var(--card);border-radius:20px;border:1px dashed #3f3f46;">
                <h2 style="color:var(--text-muted);margin:0;">${message}</h2>
                <p style="color:#71717a;">${detail}</p>
            </div>`;
        return;
    }

    animes.forEach((anime, i) => {
        const isGold = i === 0 ? "gold-card" : "";

        // FIX: include on_hold in total so all five segments fill to 100% of the bar.
        const total  = (anime.watching + anime.completed + anime.on_hold + anime.dropped + anime.plan) || 1;
        const wPct   = (anime.watching  / total) * 100;
        const cPct   = (anime.completed / total) * 100;
        const hPct   = (anime.on_hold   / total) * 100;  // on_hold segment (amber)
        const dPct   = (anime.dropped   / total) * 100;
        const pPct   = (anime.plan      / total) * 100;

        const matchPct   = Math.min(Math.max(anime.score * 100, 0), 99.9);
        const trailerHtml = anime.trailer
            ? `<a href="${anime.trailer}" target="_blank" rel="noopener noreferrer" class="btn-trailer">▶ Trailer</a>`
            : '';
        const coverImage = anime.picture || PLACEHOLDER_IMG;
        const genreTags  = Array.isArray(anime.genres)
            ? anime.genres.map(g => `<span class="genre-chip">${typeof g === 'string' ? g : g.name || g}</span>`).join(' ')
            : '';

        const html = `
            <div class="card ${isGold}" style="animation-delay:${i * 0.07}s">
                <div class="rank-badge">#${i + 1}</div>
                <div class="card-left">
                    <img src="${coverImage}" alt="${anime.title} cover" loading="lazy"
                         onerror="this.src='${PLACEHOLDER_IMG}'">
                    ${trailerHtml}
                </div>
                <div class="info">
                    <div style="padding-right:90px;">
                        <h2><a href="https://myanimelist.net/anime/${anime.id}" target="_blank"
                               rel="noopener noreferrer" title="${anime.title}">${anime.title}</a></h2>
                        <div class="genre-chip-row">${genreTags}</div>
                        <div style="font-size:0.85rem;color:#a1a1aa;margin-top:0.7rem;">
                            ${anime.media_type ? `Type: ${anime.media_type}` : ''}${anime.media_type && anime.status ? ' • ' : ''}${anime.status ? `Status: ${anime.status}` : ''}
                        </div>
                        <div style="font-size:0.9rem;color:#fbbf24;font-weight:800;display:flex;align-items:center;gap:6px;margin-top:0.6rem;">
                            ★ ${anime.raw_mean_score.toFixed(2)}
                            <span style="color:var(--text-muted);font-weight:normal;font-size:0.8rem;">(MAL Score)</span>
                        </div>
                    </div>
                    <div class="synopsis-box">${anime.synopsis || 'Synopsis not available.'}</div>
                    <div>
                        <div class="stat-bar-container">
                            <div class="stat-bar-w" style="width:${wPct}%" title="Watching"></div>
                            <div class="stat-bar-c" style="width:${cPct}%" title="Completed"></div>
                            <div class="stat-bar-h" style="width:${hPct}%" title="On Hold"></div>
                            <div class="stat-bar-d" style="width:${dPct}%" title="Dropped"></div>
                            <div class="stat-bar-p" style="width:${pPct}%" title="Plan to Watch"></div>
                        </div>
                        <div class="stats-grid">
                            <div class="badge"><span style="background:#10b981"></span>${anime.watching.toLocaleString()} Watching</div>
                            <div class="badge"><span style="background:#3b82f6"></span>${anime.completed.toLocaleString()} Completed</div>
                            <div class="badge"><span style="background:#f59e0b"></span>${anime.on_hold.toLocaleString()} On Hold</div>
                            <div class="badge"><span style="background:#f43f5e"></span>${anime.dropped.toLocaleString()} Dropped</div>
                            <div class="badge"><span style="background:#a855f7"></span>${anime.plan.toLocaleString()} Planning</div>
                        </div>
                    </div>
                </div>
                <div class="score-box">
                    <div class="score-value">${matchPct.toFixed(1)}<span style="font-size:1.2rem">%</span></div>
                    <div class="score-label">Alg Match</div>
                </div>
            </div>`;
        container.innerHTML += html;
    });
}
