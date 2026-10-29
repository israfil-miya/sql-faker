const toast = document.getElementById('toast');

function showToast(msg) {
    if (!toast) return;
    toast.textContent = msg || 'Copied to clipboard';
    toast.classList.add('visible');
    setTimeout(() => toast.classList.remove('visible'), 1600);
}

document.querySelectorAll('.copyable').forEach(el => {
    el.addEventListener('click', () => {
        const val = el.getAttribute('data-copy') || el.innerText;
        navigator.clipboard.writeText(val).then(() => {
            showToast('Copied: ' + val.substring(0, 24) + (val.length > 24 ? '…' : ''));
        });
    });
});

const seedInput = document.getElementById('seed');
const randomBtn = document.getElementById('randomizeSeedBtn');
if (randomBtn && seedInput) {
    randomBtn.addEventListener('click', () => {
        seedInput.value = Math.floor(Math.random() * 2000000000);
        const batchInput = document.getElementById('batch');
        if (batchInput) batchInput.value = 0;
    });
}

function getTableData() {
    const rows = Array.from(document.querySelectorAll('#usersTable tbody tr'));
    return rows.map(tr => {
        const cells = tr.querySelectorAll('td');
        if (!cells.length) return null;
        const metricCells = tr.querySelectorAll('.metric-cell');
        return {
            id: cells[0] ? cells[0].innerText.trim() : '',
            full_name: tr.querySelector('.user-name-cell span:last-child')?.innerText.trim() || '',
            address: tr.querySelector('.address-cell .copyable')?.getAttribute('data-copy') || tr.querySelector('.address-cell')?.innerText.trim() || '',
            coordinates: tr.querySelector('.coord-link span')?.innerText.trim() || '',
            height_cm: metricCells[0] ? metricCells[0].innerText.replace('cm', '').trim() : '',
            weight_kg: metricCells[1] ? metricCells[1].innerText.replace('kg', '').trim() : '',
            eye_color: tr.querySelector('.eye-tag span:last-child')?.innerText.trim() || '',
            phone: tr.querySelector('.mono-val[title*="phone"]')?.getAttribute('data-copy') || '',
            email: tr.querySelector('.mono-val[title*="email"]')?.getAttribute('data-copy') || ''
        };
    }).filter(Boolean);
}

const copyJsonBtn = document.getElementById('copyJsonBtn');
if (copyJsonBtn) {
    copyJsonBtn.addEventListener('click', () => {
        const data = getTableData();
        navigator.clipboard.writeText(JSON.stringify(data, null, 2)).then(() => {
            showToast('Batch JSON copied to clipboard');
        });
    });
}

const copyContentBtn = document.getElementById('copyContentBtn');
if (copyContentBtn) {
    copyContentBtn.addEventListener('click', () => {
        const textEl = document.getElementById('markovTextBody');
        if (textEl) {
            navigator.clipboard.writeText(textEl.innerText.trim()).then(() => {
                showToast('Text copied to clipboard');
            });
        }
    });
}

const downloadCsvBtn = document.getElementById('downloadCsvBtn');
if (downloadCsvBtn) {
    downloadCsvBtn.addEventListener('click', () => {
        const data = getTableData();
        if (!data.length) return;
        const headers = Object.keys(data[0]);
        const csvRows = [
            headers.join(','),
            ...data.map(row =>
                headers.map(field => {
                    const val = (row[field] === null || row[field] === undefined) ? '' : String(row[field]);
                    return `"${val.replace(/"/g, '""')}"`;
                }).join(',')
            )
        ];
        const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const localeVal = document.getElementById('locale')?.value || 'data';
        const seedVal = document.getElementById('seed')?.value || '0';
        const batchVal = document.getElementById('batch')?.value || '0';
        a.download = `fake_users_${localeVal}_seed${seedVal}_batch${batchVal}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('CSV downloaded');
    });
}

document.addEventListener('keydown', (e) => {
    if (['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
        return;
    }

    if (e.key === 'r' || e.key === 'R') {
        if (randomBtn) randomBtn.click();
    } else if (e.key === 'ArrowRight' || e.key === 'n' || e.key === 'N') {
        const nextLink = document.getElementById('nextBatchLink');
        if (nextLink) nextLink.click();
    } else if (e.key === 'ArrowLeft' || e.key === 'p' || e.key === 'P') {
        const prevLink = document.getElementById('prevBatchLink');
        if (prevLink) prevLink.click();
    }
});

