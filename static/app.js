/* ============================================================
   Web3 Research Co-Pilot — app.js
   Optimised streaming chat client with inline tool activity
   ============================================================ */
// ── State ────────────────────────────────────────────────────
let chatHistory = [];
let useGemini   = false;
// ── Tool icon map ─────────────────────────────────────────────
const TOOL_ICONS = {
    coingecko:     'fa-coins',
    defillama:     'fa-droplet',
    cryptocompare: 'fa-chart-bar',
    etherscan:     'fa-magnifying-glass',
    chart:         'fa-chart-line',
    price:         'fa-dollar-sign',
    market:        'fa-chart-area',
    gas:           'fa-gas-pump',
    whale:         'fa-fish',
    'default':     'fa-gear',
};
// ── Marked.js setup ───────────────────────────────────────────
try {
    marked.use({ breaks: true, gfm: true });
} catch(e) { /* older marked version — ignore */ }
// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initModel();
    initTextarea();
    checkStatus();
    document.getElementById('queryInput').focus();
});
// ── Textarea auto-grow ───────────────────────────────────────
function initTextarea() {
    const ta = document.getElementById('queryInput');
    ta.addEventListener('input', () => {
        ta.style.height = 'auto';
        ta.style.height = Math.min(ta.scrollHeight, 130) + 'px';
        document.getElementById('charCount').textContent =
            `${ta.value.length} / 1000`;
    });
    ta.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendQuery();
        }
    });
}
// ── Model selection ──────────────────────────────────────────
function setModel(model) {
    useGemini = model === 'gemini';
    localStorage.setItem('useGemini', useGemini);
    document.getElementById('btnOllama').classList.toggle('active', !useGemini);
    document.getElementById('btnGemini').classList.toggle('active', useGemini);
    showToast(`Switched to ${useGemini ? 'Gemini (Cloud)' : 'Ollama (Local)'}`, 'info');
    checkStatus();
}
function initModel() {
    useGemini = localStorage.getItem('useGemini') === 'true';
    document.getElementById('btnOllama').classList.toggle('active', !useGemini);
    document.getElementById('btnGemini').classList.toggle('active', useGemini);
}
// ── Status check ─────────────────────────────────────────────
async function checkStatus() {
    const badge = document.getElementById('statusBadge');
    const text  = document.getElementById('statusBadgeText');
    try {
        const res  = await fetch('/status');
        const data = await res.json();
        if (data.enabled) {
            badge.className = 'status-badge online';
            text.textContent = 'Online';
        } else {
            badge.className = 'status-badge offline';
            text.textContent = 'Limited';
        }
    } catch {
        badge.className = 'status-badge offline';
        text.textContent = 'Offline';
    }
}
// ── Send query ───────────────────────────────────────────────
async function sendQuery() {
    const ta      = document.getElementById('queryInput');
    const sendBtn = document.getElementById('sendBtn');
    const query   = ta.value.trim();
    if (!query) return;
    addMessage('user', query);
    ta.value = '';
    ta.style.height = 'auto';
    document.getElementById('charCount').textContent = '0 / 1000';
    const thinkingId = showThinking();
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
    try {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 300000);
        const res = await fetch('/query/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
            body: JSON.stringify({ query, chat_history: chatHistory, use_gemini: useGemini }),
            signal: controller.signal,
        });
        clearTimeout(timer);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const reader  = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer    = '';
        outer: while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // keep incomplete line
            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                try {
                    const evt = JSON.parse(line.slice(6));
                    if (handleStreamEvent(evt, thinkingId) === 'done') break outer;
                } catch { /* skip malformed JSON */ }
            }
        }
    } catch (err) {
        removeThinking(thinkingId);
        if (err.name === 'AbortError') {
            addMessage('assistant', 'Request timed out after 5 minutes. Try a shorter or simpler query.');
        } else if (err.message.includes('Failed to fetch')) {
            addMessage('assistant', 'Network error — please check your connection.');
        } else {
            addMessage('assistant', 'An unexpected error occurred. Please try again.');
        }
    } finally {
        sendBtn.disabled = false;
        sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        ta.focus();
    }
}
// ── Handle SSE events ────────────────────────────────────────
function handleStreamEvent(data, thinkingId) {
    switch (data.type) {
        case 'status':
            updateThinking(thinkingId, data.message, data.progress);
            break;
        case 'tools':
            addToolStep(thinkingId, data.message);
            break;
        case 'result':
            removeThinking(thinkingId);
            if (data.data && data.data.success) {
                addMessage('assistant', data.data.response, data.data.sources, data.data.visualizations);
            } else {
                const msg = (data.data && data.data.response) || 'Analysis temporarily unavailable.';
                addMessage('assistant', msg);
            }
            return 'done';
        case 'complete':
            return 'done';
        case 'error':
            removeThinking(thinkingId);
            addMessage('assistant', data.message || 'An error occurred.');
            return 'done';
    }
}
// ── Thinking bubble ──────────────────────────────────────────
function showThinking() {
    const id   = 'thinking-' + Date.now();
    const msgs = document.getElementById('chatMessages');
    clearWelcome();
    const div = document.createElement('div');
    div.className = 'message assistant';
    div.id = id;
    div.innerHTML = `
        <div class="thinking-bubble">
            <div class="thinking-header">
                <div class="thinking-spinner"></div>
                <span class="thinking-label" id="${id}-label">Analyzing query…</span>
            </div>
            <div class="tool-steps" id="${id}-steps"></div>
            <div class="progress-strip"><div class="progress-fill" id="${id}-bar"></div></div>
        </div>
        <div class="message-time">${fmtTime()}</div>`;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    return id;
}
function updateThinking(id, message, progress) {
    const label = document.getElementById(`${id}-label`);
    if (label) label.textContent = message;
    const bar = document.getElementById(`${id}-bar`);
    if (bar && progress != null) bar.style.width = `${progress}%`;
}
function addToolStep(id, message) {
    const steps = document.getElementById(`${id}-steps`);
    if (!steps) return;

    // Parse "Available tools: ['CoinGecko', 'DeFiLlama', ...]" into individual rows
    const listMatch = message.match(/\[(.+)\]/);
    const toolNames = listMatch
        ? [...listMatch[1].matchAll(/'([^']+)'/g)].map(m => m[1])
        : null;

    if (toolNames && toolNames.length > 0) {
        toolNames.forEach(name => {
            const step = document.createElement('div');
            step.className = 'tool-step';
            step.innerHTML = `<i class="fas ${getToolIcon(name)}"></i><span>${escapeHtml(name)}</span>`;
            steps.appendChild(step);
        });
    } else {
        const step = document.createElement('div');
        step.className = 'tool-step';
        step.innerHTML = `<i class="fas ${getToolIcon(message)}"></i><span>${escapeHtml(message)}</span>`;
        steps.appendChild(step);
    }

    document.getElementById('chatMessages').scrollTop = 9999;
}
function removeThinking(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}
// ── Add message ──────────────────────────────────────────────
function addMessage(sender, content, sources = [], visualizations = []) {
    clearWelcome();
    const msgs = document.getElementById('chatMessages');
    const div  = document.createElement('div');
    div.className = `message ${sender}`;
    // Render content
    let bodyHtml = '';
    if (sender === 'assistant') {
        try   { bodyHtml = `<div class="md-content">${marked.parse(String(content))}</div>`; }
        catch { bodyHtml = `<div class="md-content">${escapeHtml(String(content)).replace(/\n/g, '<br>')}</div>`; }
    } else {
        bodyHtml = `<div class="md-content">${escapeHtml(String(content))}</div>`;
    }
    // Sources
    let srcHtml = '';
    if (sources && sources.length > 0) {
        const tags = sources.map(s => `<span class="source-tag">${escapeHtml(s)}</span>`).join('');
        srcHtml = `<div class="sources-list"><span class="sources-label">Sources</span>${tags}</div>`;
    }
    // Visualizations
    const vizHtml = (visualizations || []).map((v, i) =>
        `<div class="viz-container" id="viz-${Date.now()}-${i}">${v}</div>`
    ).join('');
    div.innerHTML = `
        <div class="message-bubble">${bodyHtml}${srcHtml}</div>
        ${vizHtml}
        <div class="message-time">${fmtTime()}</div>`;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    // Apply syntax highlighting to code blocks
    if (sender === 'assistant') {
        requestAnimationFrame(() => {
            if (typeof hljs !== 'undefined') {
                div.querySelectorAll('pre code').forEach(b => hljs.highlightElement(b));
            }
        });
    }
    // Execute embedded Plotly scripts
    if (visualizations && visualizations.length > 0) {
        setTimeout(() => {
            div.querySelectorAll('script').forEach(s => {
                try { new Function(s.textContent).call(window); }
                catch (e) { console.warn('Viz script error:', e); }
            });
        }, 120);
    }
    // Maintain rolling chat history (last 20 turns)
    chatHistory.push({ role: sender, content });
    if (chatHistory.length > 20) chatHistory = chatHistory.slice(-20);
}
// ── Helpers ──────────────────────────────────────────────────
function clearWelcome() {
    const w = document.querySelector('.welcome-screen');
    if (w) w.remove();
}
function setQuery(query) {
    const ta = document.getElementById('queryInput');
    ta.value = query;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 130) + 'px';
    document.getElementById('charCount').textContent = `${query.length} / 1000`;
    setTimeout(sendQuery, 50);
}
function getToolIcon(message) {
    const m = message.toLowerCase();
    for (const [key, icon] of Object.entries(TOOL_ICONS)) {
        if (key !== 'default' && m.includes(key)) return icon;
    }
    return TOOL_ICONS.default;
}
function escapeHtml(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
function fmtTime() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
// ── Toast ─────────────────────────────────────────────────────
let toastTimer = null;
function showToast(message, type = 'info') {
    const toast = document.getElementById('statusIndicator');
    const text  = document.getElementById('statusText');
    const icon  = toast.querySelector('.toast-icon');
    const icons = {
        info:       'fa-circle-info',
        processing: 'fa-circle-notch fa-spin',
        success:    'fa-circle-check',
        error:      'fa-circle-xmark',
        warning:    'fa-triangle-exclamation',
    };
    text.textContent = message;
    toast.className  = `toast show ${type}`;
    if (icon) icon.className = `fas ${icons[type] || icons.info} toast-icon`;
    clearTimeout(toastTimer);
    if (type !== 'processing') {
        toastTimer = setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
}
// ── Theme ─────────────────────────────────────────────────────
function initTheme() {
    const theme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', theme);
    syncThemeIcon(theme);
}
function toggleTheme() {
    const cur  = document.documentElement.getAttribute('data-theme');
    const next = cur === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    syncThemeIcon(next);
}
function syncThemeIcon(theme) {
    const icon = document.querySelector('#themeToggle i');
    if (icon) icon.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
}
// ── Event listeners ───────────────────────────────────────────
document.getElementById('sendBtn').addEventListener('click', sendQuery);
document.getElementById('themeToggle').addEventListener('click', toggleTheme);
