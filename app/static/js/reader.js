// AI Research Copilot - Reader & Synchronized Chat Client

let isStreaming = false;

document.addEventListener('DOMContentLoaded', () => {
    initChat();
    initMathRendering();
});

// 1. PDF Page Jump & Synchronization
window.jumpToPage = function(pageNum) {
    const page = parseInt(pageNum, 10);
    if (!page || isNaN(page)) return;

    const iframe = document.getElementById('pdfIframe');
    const input = document.getElementById('pageJumpInput');
    if (input) input.value = page;

    if (iframe) {
        // Update hash to trigger in-browser PDF viewer navigation
        const baseSrc = `/api/papers/${window.CURRENT_PAPER_ID}/pdf`;
        iframe.src = `${baseSrc}#page=${page}&toolbar=1`;
    }

    window.showToast(`Navigated to Page ${page}`, 'info');
};

// 2. Chat Management
function initChat() {
    const input = document.getElementById('chatInput');
    if (input) input.focus();
}

window.sendQuickPrompt = function(promptText) {
    const input = document.getElementById('chatInput');
    if (input) {
        input.value = promptText;
        handleChatSubmit(new Event('submit'));
    }
};

window.handleChatSubmit = async function(event) {
    if (event) event.preventDefault();
    if (isStreaming) return;

    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;

    input.value = '';
    appendMessage('user', message);

    isStreaming = true;
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;
    sendBtn.innerHTML = `<div class="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin"></div>`;

    // Create AI response container
    const aiMessageEl = appendMessage('assistant', '');
    const contentEl = aiMessageEl.querySelector('.message-content');
    contentEl.innerHTML = '<span class="inline-flex items-center gap-1 text-slate-400"><span class="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span> Thinking & searching paper chunks...</span>';

    let fullResponse = '';

    try {
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                paper_id: window.CURRENT_PAPER_ID,
                message: message
            })
        });

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }

        contentEl.innerHTML = '';
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop(); // Keep incomplete chunk

            for (const block of lines) {
                if (!block.trim()) continue;

                const eventMatch = block.match(/^event:\s*(.+)$/m);
                const dataMatch = block.match(/^data:\s*(.+)$/m);

                if (!dataMatch) continue;

                const eventType = eventMatch ? eventMatch[1].trim() : 'message';
                const data = JSON.parse(dataMatch[1]);

                if (eventType === 'metadata') {
                    // Update citations tray
                    renderCitationsTray(data.citations || []);
                } else if (eventType === 'token') {
                    fullResponse += data.chunk;
                    renderFormattedResponse(contentEl, fullResponse);
                    scrollToBottom();
                } else if (eventType === 'done') {
                    // Final formatting & math rendering pass
                    renderFormattedResponse(contentEl, fullResponse, true);
                }
            }
        }
    } catch (err) {
        contentEl.innerHTML = `<div class="text-rose-600 font-medium text-xs">Error retrieving response: ${err.message}</div>`;
    } finally {
        isStreaming = false;
        sendBtn.disabled = false;
        sendBtn.innerHTML = `<i data-lucide="send" class="w-4 h-4"></i>`;
        lucide.createIcons({ root: sendBtn });
        scrollToBottom();
    }
};

// 3. Render Message in DOM
function appendMessage(role, text) {
    const container = document.getElementById('chatMessages');
    const msg = document.createElement('div');
    msg.className = `flex items-start gap-2.5 ${role === 'user' ? 'justify-end' : ''}`;

    if (role === 'user') {
        msg.innerHTML = `
            <div class="max-w-[85%] bg-indigo-600 text-white p-3 rounded-2xl rounded-tr-sm text-xs shadow-2xs">
                ${escapeHtml(text)}
            </div>
            <div class="h-6 w-6 rounded-md bg-slate-200 text-slate-600 flex items-center justify-center flex-shrink-0 text-xs font-semibold">
                U
            </div>
        `;
    } else {
        msg.innerHTML = `
            <div class="h-6 w-6 rounded-md bg-indigo-600 text-white flex items-center justify-center flex-shrink-0 mt-0.5 shadow-2xs">
                <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
            </div>
            <div class="flex-1 max-w-[92%] bg-white p-3.5 rounded-2xl rounded-tl-sm border border-slate-200 shadow-2xs text-xs text-slate-800 space-y-2">
                <div class="message-content prose prose-xs max-w-none prose-slate">
                    ${text ? marked.parse(text) : ''}
                </div>
            </div>
        `;
    }

    container.appendChild(msg);
    lucide.createIcons({ root: msg });
    scrollToBottom();
    return msg;
}

// 4. Formatter & Interactive Citation Badges
function renderFormattedResponse(container, markdownText, isFinal = false) {
    if (typeof marked !== 'undefined') {
        let html = marked.parse(markdownText);

        // Transform citation patterns [Page X] or [p. X] into clickable buttons
        html = html.replace(/\[(?:Page|p\.?)\s*(\d+)\]/gi, (match, pageNum) => {
            return `<button onclick="jumpToPage(${pageNum})" class="inline-flex items-center gap-0.5 px-1.5 py-0.2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold rounded border border-indigo-200/80 cursor-pointer text-[11px] transition" title="Jump to Page ${pageNum}">📄 Page ${pageNum}</button>`;
        });

        container.innerHTML = html;

        if (isFinal) {
            initMathRendering(container);
        }
    } else {
        container.textContent = markdownText;
    }
}

// 5. LaTeX Math Formula Rendering with KaTeX
function initMathRendering(element = document.body) {
    if (typeof renderMathInElement !== 'undefined') {
        renderMathInElement(element, {
            delimiters: [
                { left: "$$", right: "$$", display: true },
                { left: "$", right: "$", display: false },
                { left: "\\(", right: "\\)", display: false },
                { left: "\\[", right: "\\]", display: true }
            ],
            throwOnError: false
        });
    }
}

// 6. Citations Tray
function renderCitationsTray(citations) {
    const tray = document.getElementById('citationsTray');
    const list = document.getElementById('citationBadgesList');
    if (!tray || !list) return;

    if (!citations || citations.length === 0) {
        tray.classList.add('hidden');
        return;
    }

    tray.classList.remove('hidden');
    list.innerHTML = '';

    // De-duplicate by page number
    const seenPages = new Set();
    citations.forEach(c => {
        if (!seenPages.has(c.page)) {
            seenPages.add(c.page);
            const badge = document.createElement('button');
            badge.className = 'px-2 py-0.5 rounded-md bg-white border border-indigo-200 text-indigo-700 hover:bg-indigo-600 hover:text-white transition font-medium text-[11px] flex items-center gap-1 shadow-2xs';
            badge.innerHTML = `<span>p. ${c.page}</span> <span class="text-[9px] opacity-70">(${c.section})</span>`;
            badge.onclick = () => window.jumpToPage(c.page);
            list.appendChild(badge);
        }
    });
}

function scrollToBottom() {
    const container = document.getElementById('chatMessages');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 7. BibTeX Modal
window.copyBibtex = async function(paperId) {
    try {
        const res = await fetch(`/api/chat/bibtex/${paperId}`);
        const data = await res.json();
        if (data.success && data.bibtex) {
            document.getElementById('bibtexContent').textContent = data.bibtex;
            document.getElementById('bibtexModal').classList.remove('hidden');
        } else {
            window.showToast('Could not generate BibTeX', 'error');
        }
    } catch (err) {
        window.showToast('Error: ' + err.message, 'error');
    }
};

window.closeBibtexModal = function() {
    document.getElementById('bibtexModal').classList.add('hidden');
};

window.copyBibtexToClipboard = function() {
    const text = document.getElementById('bibtexContent').textContent;
    navigator.clipboard.writeText(text).then(() => {
        const btnText = document.getElementById('copyBibtexBtnText');
        btnText.textContent = 'Copied!';
        setTimeout(() => { btnText.textContent = 'Copy to Clipboard'; }, 2000);
        window.showToast('BibTeX copied to clipboard!', 'success');
    });
};
