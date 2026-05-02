// Modal helpers
function openModal(id) {
    document.getElementById(id).classList.add('open');
}
function closeModal(id) {
    document.getElementById(id).classList.remove('open');
}
// Close modal on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) overlay.classList.remove('open');
    });
});

// Task filter
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const filter = btn.dataset.filter;
        document.querySelectorAll('.task-row-tr').forEach(row => {
            if (filter === 'all') {
                row.style.display = '';
            } else if (filter === 'overdue') {
                row.style.display = row.dataset.overdue === 'overdue' ? '' : 'none';
            } else {
                row.style.display = row.dataset.status === filter ? '' : 'none';
            }
        });
    });
});

// Auto-dismiss flash after 4s
setTimeout(() => {
    document.querySelectorAll('.flash').forEach(f => f.remove());
}, 4000);

// Load members for selected project (task form)
async function loadMembers(projectId) {
    if (!projectId) return;
    try {
        const res = await fetch(`/api/projects/${projectId}/members`);
        const members = await res.json();
        const select = document.getElementById('memberSelect');
        select.innerHTML = '<option value="">Unassigned</option>';
        members.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.id;
            opt.textContent = m.name;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error('Failed to load members', e);
    }
}
