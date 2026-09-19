// AI Research Copilot - Literature Matrix Client

let currentMatrixData = [];

document.addEventListener('DOMContentLoaded', () => {
    updateSelectionCount();
});

function updateSelectionCount() {
    const checked = document.querySelectorAll('input[name="paperSelect"]:checked');
    const badge = document.getElementById('selectedCountBadge');
    const btn = document.getElementById('generateMatrixBtn');

    if (badge) {
        badge.textContent = `${checked.length} selected`;
        badge.className = checked.length >= 2 
            ? 'px-2 py-0.5 text-xs font-semibold bg-indigo-100 text-indigo-700 rounded-full' 
            : 'px-2 py-0.5 text-xs font-semibold bg-slate-100 text-slate-600 rounded-full';
    }

    if (btn) {
        btn.disabled = checked.length < 2;
    }
}

function selectAllPapers(select) {
    const checkboxes = document.querySelectorAll('input[name="paperSelect"]');
    checkboxes.forEach(cb => { cb.checked = select; });
    updateSelectionCount();
}

async function generateMatrix() {
    const checked = Array.from(document.querySelectorAll('input[name="paperSelect"]:checked')).map(cb => cb.value);
    if (checked.length < 2) {
        window.showToast('Please select at least 2 papers to compare.', 'info');
        return;
    }

    const loadingEl = document.getElementById('matrixLoading');
    const emptyEl = document.getElementById('matrixEmpty');
    const containerEl = document.getElementById('matrixContainer');
    const exportBar = document.getElementById('exportBar');
    const btn = document.getElementById('generateMatrixBtn');
    const btnText = document.getElementById('generateBtnText');

    loadingEl.classList.remove('hidden');
    emptyEl.classList.add('hidden');
    containerEl.classList.add('hidden');
    exportBar.classList.add('hidden');
    btn.disabled = true;
    btnText.textContent = 'Synthesizing...';

    try {
        const res = await fetch('/api/synthesis/matrix', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paper_ids: checked })
        });
        const data = await res.json();

        loadingEl.classList.add('hidden');
        btn.disabled = false;
        btnText.textContent = 'Generate Comparative Matrix';

        if (data.success && data.matrix) {
            currentMatrixData = data.matrix;
            renderMatrixTable(currentMatrixData);
            containerEl.classList.remove('hidden');
            exportBar.classList.remove('hidden');
            window.showToast('Comparative matrix synthesized successfully!', 'success');
        } else {
            emptyEl.classList.remove('hidden');
            window.showToast(data.error || 'Failed to synthesize matrix', 'error');
        }
    } catch (err) {
        loadingEl.classList.add('hidden');
        emptyEl.classList.remove('hidden');
        btn.disabled = false;
        btnText.textContent = 'Generate Comparative Matrix';
        window.showToast('Error: ' + err.message, 'error');
    }
}

function renderMatrixTable(matrix) {
    const table = document.getElementById('matrixTable');
    table.innerHTML = '';

    const dimensions = [
        { key: 'objective', label: '🎯 Objective & Problem', bg: 'bg-slate-50/70' },
        { key: 'methodology', label: '⚙️ Proposed Methodology', bg: 'bg-white' },
        { key: 'datasets', label: '📊 Datasets & Benchmarks', bg: 'bg-slate-50/70' },
        { key: 'results', label: '📈 Key Results & Metrics', bg: 'bg-white' },
        { key: 'strengths', label: '🌟 Key Strengths & Novelty', bg: 'bg-slate-50/70' },
        { key: 'limitations', label: '⚠️ Limitations & Gaps', bg: 'bg-white' }
    ];

    // Table Header
    let theadHtml = `
        <thead>
            <tr class="border-b border-slate-200 bg-slate-100/80">
                <th class="p-4 w-48 text-slate-700 font-bold uppercase text-[11px] tracking-wider sticky left-0 bg-slate-100 z-10">
                    Dimension
                </th>
    `;

    matrix.forEach(p => {
        theadHtml += `
            <th class="p-4 min-w-[280px] max-w-[340px] align-top">
                <h4 class="font-bold text-slate-900 text-xs line-clamp-2 leading-snug">${p.title}</h4>
                <div class="mt-2 flex items-center gap-2">
                    <a href="/reader/${p.paper_id}" class="text-[11px] text-indigo-600 hover:underline font-semibold flex items-center gap-1">
                        <span>Read Paper</span> &rarr;
                    </a>
                </div>
            </th>
        `;
    });
    theadHtml += `</tr></thead>`;

    // Table Body
    let tbodyHtml = `<tbody>`;
    dimensions.forEach(dim => {
        tbodyHtml += `
            <tr class="border-b border-slate-200/80 ${dim.bg} hover:bg-indigo-50/20 transition">
                <td class="p-4 font-semibold text-slate-900 text-xs align-top sticky left-0 ${dim.bg} z-10 border-r border-slate-200/60 shadow-2xs">
                    ${dim.label}
                </td>
        `;

        matrix.forEach(p => {
            const val = p[dim.key] || 'Not specified';
            tbodyHtml += `
                <td class="p-4 align-top text-slate-700 leading-relaxed border-r border-slate-200/40">
                    ${val}
                </td>
            `;
        });

        tbodyHtml += `</tr>`;
    });
    tbodyHtml += `</tbody>`;

    table.innerHTML = theadHtml + tbodyHtml;
}

// Export as Markdown Table
function exportMatrixAsMarkdown() {
    if (!currentMatrixData || currentMatrixData.length === 0) return;

    let md = `# Comparative Literature Matrix\n\n`;
    md += `| Dimension | ` + currentMatrixData.map(p => p.title.replace(/\|/g, '-')).join(' | ') + ` |\n`;
    md += `| :--- | ` + currentMatrixData.map(() => `:---`).join(' | ') + ` |\n`;

    const keys = ['objective', 'methodology', 'datasets', 'results', 'strengths', 'limitations'];
    const labels = ['Objective', 'Methodology', 'Datasets', 'Results', 'Strengths', 'Limitations'];

    keys.forEach((k, i) => {
        md += `| **${labels[i]}** | ` + currentMatrixData.map(p => (p[k] || '').replace(/\|/g, '-').replace(/\n/g, ' ')).join(' | ') + ` |\n`;
    });

    downloadBlob(md, 'literature_matrix.md', 'text/markdown');
}

// Export as CSV
function exportMatrixAsCSV() {
    if (!currentMatrixData || currentMatrixData.length === 0) return;

    let csv = `"Dimension",` + currentMatrixData.map(p => `"${escapeCsv(p.title)}"`).join(',') + `\n`;

    const keys = ['objective', 'methodology', 'datasets', 'results', 'strengths', 'limitations'];
    const labels = ['Objective', 'Methodology', 'Datasets', 'Results', 'Strengths', 'Limitations'];

    keys.forEach((k, i) => {
        csv += `"${labels[i]}",` + currentMatrixData.map(p => `"${escapeCsv(p[k] || '')}"`).join(',') + `\n`;
    });

    downloadBlob(csv, 'literature_matrix.csv', 'text/csv');
}

function escapeCsv(text) {
    return text.replace(/"/g, '""');
}

function downloadBlob(content, filename, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    window.showToast(`Exported ${filename}`, 'success');
}
