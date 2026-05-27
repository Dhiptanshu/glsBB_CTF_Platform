
// UI Modal Component
const Modal = {
    overlay: null,
    msg: null,
    btnOk: null,
    btnCancel: null,
    resolve: null,

    init() {
        this.overlay = document.getElementById('custom-alert-overlay');
        this.msg = document.getElementById('custom-alert-message');
        this.btnOk = document.getElementById('custom-alert-ok');
        this.btnCancel = document.getElementById('custom-alert-cancel');

        if (this.btnOk) this.btnOk.onclick = () => this.close(true);
        if (this.btnCancel) this.btnCancel.onclick = () => this.close(false);
    },

    show(text, isConfirm = false) {
        return new Promise((resolve) => {
            this.resolve = resolve;
            if (this.msg) this.msg.textContent = text;
            if (this.overlay) this.overlay.style.display = 'flex';

            if (isConfirm) {
                if (this.btnCancel) this.btnCancel.style.display = 'inline-block';
                if (this.btnOk) this.btnOk.textContent = 'Yes';
            } else {
                if (this.btnCancel) this.btnCancel.style.display = 'none';
                if (this.btnOk) this.btnOk.textContent = 'OK';
            }
        });
    },

    close(result) {
        if (this.overlay) this.overlay.style.display = 'none';
        if (this.resolve) {
            this.resolve(result);
            this.resolve = null;
        }
    }
};

// ==========================================
// Category Management (Admin)
// ==========================================

async function saveCategoryUrl(id) {
    const input = document.getElementById(`cat-url-${id}`);
    const url = input.value;

    try {
        const response = await fetch(`/admin/update_category_url/${id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });
        const data = await response.json();
        if (data.status === 'success') {
            await Modal.show('URL Saved');
        } else {
            await Modal.show('Error: ' + data.message);
        }
    } catch (e) {
        console.error(e);
    }
}

async function toggleCategoryVisibility(id) {
    try {
        const response = await fetch(`/admin/toggle_category_visibility/${id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        if (data.status === 'success') {
            await Modal.show(data.message);
            location.reload();
        } else {
            await Modal.show('Error: ' + data.message);
        }
    } catch (e) {
        console.error(e);
    }
}

async function setAllVisibility(visible) {
    const action = visible ? "Publish All" : "Hide All";
    const confirmed = await Modal.show(`Are you sure you want to ${action} categories?`, true);
    if (!confirmed) return;

    try {
        const response = await fetch('/admin/set_all_categories_visibility', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ visible: visible })
        });
        const data = await response.json();
        if (data.status === 'success') {
            await Modal.show(data.message);
            location.reload();
        } else {
            await Modal.show('Error: ' + data.message);
        }
    } catch (e) {
        console.error(e);
    }
}

// ==========================================
// Tab Navigation
// ==========================================

function openTab(evt, catId) {
    // Hide all tab content
    const tabContents = document.getElementsByClassName("challenge-grid");
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].style.display = "none";
        tabContents[i].classList.remove("active");
    }

    // Remove active class from buttons
    const tabLinks = document.getElementsByClassName("tab-btn");
    for (let i = 0; i < tabLinks.length; i++) {
        tabLinks[i].className = tabLinks[i].className.replace(" active", "");
    }

    // Show current tab
    const selectedTab = document.getElementById(catId);
    if (selectedTab) {
        selectedTab.style.display = "grid";
        selectedTab.classList.add("active");
        if (evt) {
            evt.currentTarget.className += " active";
        } else {
            // If no event (page load), find the button and make it active
            for (let i = 0; i < tabLinks.length; i++) {
                if (tabLinks[i].getAttribute('onclick').includes(catId)) {
                    tabLinks[i].className += " active";
                }
            }
        }

        // Save to localStorage
        localStorage.setItem('activeTab', catId);
    }
}

// ==========================================
// Challenge Actions
// ==========================================

async function submitFlag(challengeId) {
    const input = document.getElementById(`flag-${challengeId}`);
    const card = document.getElementById(`card-${challengeId}`);
    const flag = input.value;

    if (!flag) return;

    try {
        const response = await fetch('/submit_flag', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ challenge_id: challengeId, flag: flag })
        });

        const data = await response.json();

        if (data.status === 'success') {
            card.classList.add('success-glow');
            card.classList.add('solved');
            input.parentElement.innerHTML = `<p style="color: var(--success-color); margin-top: 1rem; font-weight: bold;">Flag Captured! (+${data.points} pts)</p>`;
            setTimeout(() => { location.reload(); }, 1000);
        } else if (data.status === 'error') {
            input.classList.remove('shake');
            void input.offsetWidth; // trigger reflow
            input.classList.add('shake');
            await Modal.show(data.message);
        } else {
            await Modal.show(data.message);
        }
    } catch (e) {
        console.error("Error submitting flag", e);
    }
}

async function buyHint(challengeId, cost) {
    const confirmed = await Modal.show(`Unlock hint for ${cost} points?`, true);
    if (!confirmed) return;

    try {
        const response = await fetch('/buy_hint', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ challenge_id: challengeId })
        });

        const data = await response.json();

        if (data.status === 'success' || data.status === 'info') {
            await Modal.show(`Hint Unlocked: ${data.hint}`);
            location.reload();
        } else {
            await Modal.show(data.message);
        }
    } catch (e) {
        console.error("Error buying hint", e);
    }
}

// ==========================================
// Admin Actions
// ==========================================

async function deleteChallenge(id) {
    const confirmed = await Modal.show('Are you sure you want to delete this challenge?', true);
    if (!confirmed) return;

    const response = await fetch(`/admin/delete_challenge/${id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });

    const data = await response.json();
    if (data.status === 'success') {
        await Modal.show('Challenge deleted');
        location.reload();
    } else {
        await Modal.show('Error: ' + data.message);
    }
}
window.deleteChallenge = deleteChallenge;

async function manageUser(action, userId, username) {
    let url, confirmMsg;

    if (action === 'ban') {
        url = `/admin/ban_user/${userId}`;
        confirmMsg = `Are you sure you want to BAN ${username}?`;
    } else if (action === 'unban') {
        url = `/admin/unban_user/${userId}`;
        confirmMsg = `Unban ${username}?`;
    } else if (action === 'penalize') {
        url = `/admin/penalize_user/${userId}`;
        confirmMsg = `Give -5 Penalty points to ${username}?`;
    } else if (action === 'reset') {
        url = `/admin/reset_score/${userId}`;
        confirmMsg = `⚠️ WARNING: This will DELETE all progress (Solves & Hints) for ${username}. Reset to 0?`;
    } else if (action === 'delete') {
        url = `/admin/delete_user/${userId}`;
        confirmMsg = `🔴 DANGER: This will PERMANENTLY DELETE user ${username} and all their data. This cannot be undone. Confirm?`;
    }

    const confirmed = await Modal.show(confirmMsg, true);
    if (!confirmed) return;

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        if (data.status === 'success') {
            await Modal.show(data.message);
            location.reload();
        } else {
            await Modal.show('Error: ' + data.message);
        }
    } catch (e) {
        console.error("Error managing user", e);
    }
}

async function confirmFormSubmit(event, message) {
    event.preventDefault();
    const form = event.target;
    const confirmed = await Modal.show(message, true);
    if (confirmed) {
        form.submit();
    }
}

// ==========================================
// Admin Drag and Drop
// ==========================================

function setupDragAndDrop() {
    const cards = document.querySelectorAll('.challenge-card[draggable="true"]');
    const grids = document.querySelectorAll('.challenge-grid');

    cards.forEach(card => {
        card.addEventListener('dragstart', () => {
            card.classList.add('dragging');
        });

        card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
            const grid = card.closest('.challenge-grid');
            if (grid) {
                const newOrder = Array.from(grid.querySelectorAll('.challenge-card'))
                    .map(c => c.getAttribute('data-id'))
                    .filter(id => id);
                saveOrder(newOrder);
            }
        });
    });

    grids.forEach(grid => {
        grid.addEventListener('dragover', e => {
            e.preventDefault();
            const afterElement = getDragAfterElement(grid, e.clientY);
            const draggable = document.querySelector('.dragging');
            if (draggable) {
                if (afterElement == null) {
                    grid.appendChild(draggable);
                } else {
                    grid.insertBefore(draggable, afterElement);
                }
            }
        });
    });
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.challenge-card:not(.dragging)')];

    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

async function saveOrder(order) {
    try {
        const response = await fetch('/admin/reorder_challenges', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order: order }),
        });
        const data = await response.json();
        if (data.status === 'success') console.log('Order updated');
        else console.error('Failed to update order:', data.message);
    } catch (err) {
        console.error('Error saving order:', err);
    }
}

// ==========================================
// Initialization
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    console.log("GLS BB System Initialized v2.0");
    console.log("%c Welcome to GLS BB! flag{w3lc0me_to_c7bersh@de2}", "background: #222; color: #bada55; font-size: 14px");

    // Initialize Modal
    Modal.init();

    // Theme Toggle
    const themeBtn = document.getElementById('theme-toggle');
    const html = document.documentElement;
    const savedTheme = localStorage.getItem('theme') || 'dark';
    html.setAttribute('data-theme', savedTheme);

    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }

    // Admin Drag and Drop
    setupDragAndDrop();

    // Restore active tab
    const savedTab = localStorage.getItem('activeTab');
    if (savedTab) {
        if (document.getElementById(savedTab)) {
            openTab(null, savedTab);
        }
    }

    // User Search Filter
    const searchInput = document.getElementById('userSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', function () {
            const filter = this.value.toLowerCase();
            const rows = document.querySelectorAll('#userTableBody tr');
            rows.forEach(row => {
                const username = row.cells[1].textContent.toLowerCase();
                row.style.display = username.includes(filter) ? '' : 'none';
            });
        });
    }
});
