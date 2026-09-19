// AI Research Copilot - Dashboard & Library Client

let allPapers = [];
let selectedFile = null;

document.addEventListener('DOMContentLoaded', () => {
    loadPapers();
    initModalEvents();
    initDragAndDrop();
    initFilterSearch();
});

// 1. Fetch & Render Paper Library
async function loadPapers() {
    const loadingEl = document.getElementById('libraryLoading');
    const emptyEl = document.getElementById('libraryEmpty');
    const gridEl = document.getElementById('paperGrid');

    loadingEl.classList.remove('hidden');
    emptyEl.classList.add('hidden');
    gridEl.classList.add('hidden');

    try {
        const res = await fetch('/api/papers');
        const data = await res.json();

        loadingEl.classList.add('hidden');

        if (data.success && data.papers && data.papers.length > 0) {
            allPapers = data.papers;
            renderPaperGrid(allPapers);
            gridEl.classList.remove('hidden');
        } else {
            allPapers = [];
            emptyEl.classList.remove('hidden');
        }
    } catch (err) {
        loadingEl.classList.add('hidden');
        emptyEl.classList.remove('hidden');
        window.showToast('Failed to load paper library: ' + err.message, 'error');
    }
}

// 2. Render Cards in Grid
function renderPaperGrid(papers) {
    const gridEl = document.getElementById('paperGrid');
    gridEl.innerHTML = '';

    if (papers.length === 0) {
        gridEl.innerHTML = `<div class="col-span-full py-12 text-center text-sm text-slate-400">No matching research papers found.</div>`;
        return;
    }

    papers.forEach(paper => {
        const card = document.createElement('div');
        card.className = 'bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between group';

        const authorsText = paper.authors && paper.authors.length > 0 
            ? paper.authors.slice(0, 3).join(', ') + (paper.authors.length > 3 ? ' et al.' : '')
            : 'Unknown Authors';

        const sectionsBadges = (paper.sections || [])
            .slice(0, 4)
            .map(s => `<span class="px-2 py-0.5 text-[11px] font-medium bg-slate-100 text-slate-600 rounded-md">${s.name}</span>`)
            .join('');

        card.innerHTML = `
            <div>
                <div class="flex items-start justify-between gap-2 mb-2">
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold ${paper.arxiv_id ? 'bg-amber-50 text-amber-700 border border-amber-200/60' : 'bg-indigo-50 text-indigo-700 border border-indigo-200/60'}">
                        ${paper.arxiv_id ? `<i data-lucide="globe" class="w-3 h-3"></i> arXiv:${paper.arxiv_id}` : '<i data-lucide="file" class="w-3 h-3"></i> PDF'}
                    </span>
                    <button onclick="handleDeletePaper('${paper.paper_id}')" class="text-slate-300 hover:text-rose-500 transition p-1" title="Delete Paper">
                        <i data-lucide="trash-2" class="w-4 h-4"></i>
                    </button>
                </div>

                <h3 class="font-bold text-slate-900 text-base leading-snug line-clamp-2 group-hover:text-indigo-600 transition" title="${paper.title}">
                    ${paper.title}
                </h3>
                <p class="text-xs text-slate-500 mt-1.5 line-clamp-1">${authorsText}</p>
                
                ${paper.abstract ? `<p class="text-xs text-slate-600 mt-3 line-clamp-3 leading-relaxed bg-slate-50 p-2.5 rounded-lg border border-slate-100">${paper.abstract}</p>` : ''}

                <div class="flex flex-wrap gap-1.5 mt-3">
                    ${sectionsBadges}
                </div>
            </div>

            <div class="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between">
                <span class="text-xs font-medium text-slate-400">
                    ${paper.page_count} ${paper.page_count === 1 ? 'page' : 'pages'} • ${paper.chunk_count} chunks
                </span>

                <div class="flex items-center gap-2">
                    <a href="/api/papers/${paper.paper_id}/pdf" target="_blank" class="p-2 text-slate-500 hover:text-slate-800 rounded-lg hover:bg-slate-100 transition" title="Open PDF">
                        <i data-lucide="external-link" class="w-4 h-4"></i>
                    </a>
                    <a href="/reader/${paper.paper_id}" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 transition">
                        <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
                        <span>Read & Chat</span>
                    </a>
                </div>
            </div>
        `;

        gridEl.appendChild(card);
    });

    lucide.createIcons({ root: gridEl });
}

// 3. Filter Papers
function initFilterSearch() {
    const input = document.getElementById('paperSearchInput');
    if (!input) return;

    input.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        if (!query) {
            renderPaperGrid(allPapers);
            return;
        }

        const filtered = allPapers.filter(p => 
            p.title.toLowerCase().includes(query) ||
            (p.authors && p.authors.some(a => a.toLowerCase().includes(query))) ||
            (p.abstract && p.abstract.toLowerCase().includes(query)) ||
            (p.arxiv_id && p.arxiv_id.toLowerCase().includes(query))
        );

        renderPaperGrid(filtered);
    });
}

// 4. Modal Management
function openIngestModal() {
    document.getElementById('ingestModal').classList.remove('hidden');
}

function closeIngestModal() {
    document.getElementById('ingestModal').classList.add('hidden');
    resetUploadState();
}

function initModalEvents() {
    const openBtn = document.getElementById('openIngestModalBtn');
    if (openBtn) openBtn.addEventListener('click', openIngestModal);

    const modal = document.getElementById('ingestModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeIngestModal();
        });
    }
}

function switchIngestTab(tab) {
    const pdfBtn = document.getElementById('tabPdfBtn');
    const arxivBtn = document.getElementById('tabArxivBtn');
    const pdfContent = document.getElementById('tabPdfContent');
    const arxivContent = document.getElementById('tabArxivContent');

    if (tab === 'pdf') {
        pdfBtn.className = "px-4 py-2 text-sm font-semibold border-b-2 border-indigo-600 text-indigo-600 transition flex items-center gap-2";
        arxivBtn.className = "px-4 py-2 text-sm font-medium border-b-2 border-transparent text-slate-500 hover:text-slate-800 transition flex items-center gap-2";
        pdfContent.classList.remove('hidden');
        arxivContent.classList.add('hidden');
    } else {
        arxivBtn.className = "px-4 py-2 text-sm font-semibold border-b-2 border-indigo-600 text-indigo-600 transition flex items-center gap-2";
        pdfBtn.className = "px-4 py-2 text-sm font-medium border-b-2 border-transparent text-slate-500 hover:text-slate-800 transition flex items-center gap-2";
        arxivContent.classList.remove('hidden');
        pdfContent.classList.add('hidden');
    }
}

// 5. Drag & Drop & Upload Handling
function initDragAndDrop() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('pdfFileInput');
    if (!dropZone || !fileInput) return;

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('border-indigo-500', 'bg-indigo-50/40');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('border-indigo-500', 'bg-indigo-50/40');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-indigo-500', 'bg-indigo-50/40');
        if (e.dataTransfer.files.length > 0) {
            handleFileSelection(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });
}

function handleFileSelection(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        window.showToast('Please select a valid PDF file', 'error');
        return;
    }

    selectedFile = file;
    document.getElementById('selectedFileName').textContent = file.name;
    document.getElementById('selectedFileSize').textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
    document.getElementById('selectedFileInfo').classList.remove('hidden');

    const uploadBtn = document.getElementById('uploadBtn');
    uploadBtn.disabled = false;
}

function resetUploadState() {
    selectedFile = null;
    const fileInput = document.getElementById('pdfFileInput');
    if (fileInput) fileInput.value = '';
    const selectedFileInfo = document.getElementById('selectedFileInfo');
    if (selectedFileInfo) selectedFileInfo.classList.add('hidden');
    const uploadBtn = document.getElementById('uploadBtn');
    if (uploadBtn) {
        uploadBtn.disabled = true;
        document.getElementById('uploadBtnText').textContent = 'Parse & Index Paper';
    }
}

async function handlePdfUpload() {
    if (!selectedFile) return;

    const uploadBtn = document.getElementById('uploadBtn');
    const btnText = document.getElementById('uploadBtnText');
    uploadBtn.disabled = true;
    btnText.textContent = 'Parsing & Indexing (PyMuPDF)...';

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const res = await fetch('/api/papers/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (data.success) {
            window.showToast('Paper indexed into research vector library!', 'success');
            closeIngestModal();
            loadPapers();
        } else {
            window.showToast(data.error || 'Failed to upload paper', 'error');
            uploadBtn.disabled = false;
            btnText.textContent = 'Parse & Index Paper';
        }
    } catch (err) {
        window.showToast('Upload error: ' + err.message, 'error');
        uploadBtn.disabled = false;
        btnText.textContent = 'Parse & Index Paper';
    }
}

// 6. arXiv Search & Ingestion
async function handleArxivSearch() {
    const query = document.getElementById('arxivQueryInput').value.trim();
    if (!query) {
        window.showToast('Please enter an arXiv ID or search query', 'info');
        return;
    }

    const resultsContainer = document.getElementById('arxivResults');
    resultsContainer.innerHTML = `
        <div class="flex items-center justify-center py-8 text-indigo-600 gap-2">
            <div class="w-5 h-5 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
            <span class="text-xs text-slate-500 font-medium">Searching arXiv repository...</span>
        </div>
    `;

    try {
        const res = await fetch(`/api/papers/arxiv/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();

        if (data.success && data.results && data.results.length > 0) {
            resultsContainer.innerHTML = '';
            data.results.forEach(paper => {
                const item = document.createElement('div');
                item.className = 'p-3 rounded-xl border border-slate-200 bg-white hover:border-indigo-300 transition flex flex-col gap-1.5';
                item.innerHTML = `
                    <div class="flex items-start justify-between gap-2">
                        <span class="px-1.5 py-0.5 text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 rounded">
                            arXiv:${paper.arxiv_id}
                        </span>
                        <span class="text-[11px] text-slate-400">${paper.published_date || ''}</span>
                    </div>
                    <h4 class="font-semibold text-slate-900 text-xs line-clamp-2">${paper.title}</h4>
                    <p class="text-[11px] text-slate-500 line-clamp-1">${paper.authors.slice(0, 3).join(', ')}</p>
                    <button id="ingest-btn-${paper.arxiv_id}" onclick="handleArxivIngest('${paper.arxiv_id}')" class="mt-2 self-end px-3 py-1.5 bg-indigo-50 text-indigo-600 hover:bg-indigo-600 hover:text-white rounded-lg text-xs font-semibold transition flex items-center gap-1.5">
                        <i data-lucide="download" class="w-3.5 h-3.5"></i>
                        <span>Ingest & Index</span>
                    </button>
                `;
                resultsContainer.appendChild(item);
            });
            lucide.createIcons({ root: resultsContainer });
        } else {
            resultsContainer.innerHTML = `<p class="text-xs text-slate-400 text-center py-6">No matching arXiv papers found.</p>`;
        }
    } catch (err) {
        resultsContainer.innerHTML = `<p class="text-xs text-rose-500 text-center py-6">Search failed: ${err.message}</p>`;
    }
}

async function handleArxivIngest(arxivId) {
    const btn = document.getElementById(`ingest-btn-${arxivId}`);
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<div class="w-3 h-3 border-2 border-indigo-400 border-t-indigo-600 rounded-full animate-spin"></div><span>Downloading...</span>`;
    }

    try {
        const res = await fetch('/api/papers/arxiv/ingest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ arxiv_id: arxivId })
        });
        const data = await res.json();

        if (data.success) {
            window.showToast(`arXiv:${arxivId} downloaded and indexed!`, 'success');
            closeIngestModal();
            loadPapers();
        } else {
            window.showToast(data.error || 'Failed to ingest arXiv paper', 'error');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = `<i data-lucide="download" class="w-3.5 h-3.5"></i><span>Ingest & Index</span>`;
                lucide.createIcons({ root: btn });
            }
        }
    } catch (err) {
        window.showToast('Ingestion error: ' + err.message, 'error');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<i data-lucide="download" class="w-3.5 h-3.5"></i><span>Ingest & Index</span>`;
            lucide.createIcons({ root: btn });
        }
    }
}

// 7. Delete Paper
async function handleDeletePaper(paperId) {
    if (!confirm('Are you sure you want to delete this paper and its vector index?')) return;

    try {
        const res = await fetch(`/api/papers/${paperId}`, { method: 'DELETE' });
        const data = await res.json();

        if (data.success) {
            window.showToast('Paper deleted successfully', 'info');
            loadPapers();
        } else {
            window.showToast(data.error || 'Failed to delete paper', 'error');
        }
    } catch (err) {
        window.showToast('Delete error: ' + err.message, 'error');
    }
}
