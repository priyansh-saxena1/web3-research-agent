let chatHistory = [];
let messageCount = 0;
let useGemini = false; // Track current LLM choice

// Initialize Gemini toggle
document.addEventListener('DOMContentLoaded', function() {
    const geminiToggle = document.getElementById('geminiToggle');
    const toggleLabel = document.querySelector('.toggle-label');
    
    // Load saved preference
    useGemini = localStorage.getItem('useGemini') === 'true';
    geminiToggle.checked = useGemini;
    updateToggleLabel();
    
    // Handle toggle changes
    geminiToggle.addEventListener('change', function() {
        useGemini = this.checked;
        localStorage.setItem('useGemini', useGemini.toString());
        updateToggleLabel();
        console.log(`Switched to ${useGemini ? 'Gemini' : 'Ollama'} mode`);
        
        // Show confirmation
        showStatus(`Switched to ${useGemini ? 'Gemini (Cloud AI)' : 'Ollama (Local AI)'} mode`, 'info');
        
        // Refresh status to reflect changes
        checkStatus();
    });
});

function updateToggleLabel() {
    const toggleLabel = document.querySelector('.toggle-label');
    if (toggleLabel) {
        toggleLabel.textContent = `AI Model: ${useGemini ? 'Gemini' : 'Ollama'}`;
    }
}

async function checkStatus() {
    try {
        const response = await fetch('/status');
        const status = await response.json();
        
        const statusDiv = document.getElementById('status');
        
        if (status.enabled && status.gemini_configured) {
            statusDiv.className = 'status online';
            statusDiv.innerHTML = '<span>Research systems online</span>' +
                '<div style="margin-top: 0.5rem; font-size: 0.85rem; opacity: 0.8;">' +
                'Tools: ' + status.tools_available.join(' • ') + '</div>';
        } else {
            statusDiv.className = 'status offline';
            statusDiv.innerHTML = '<span>Limited mode - Configure GEMINI_API_KEY for full functionality</span>' +
                '<div style="margin-top: 0.5rem; font-size: 0.85rem; opacity: 0.8;">' +
                'Available: ' + status.tools_available.join(' • ') + '</div>';
        }
    } catch (error) {
        const statusDiv = document.getElementById('status');
        statusDiv.className = 'status offline';
        statusDiv.innerHTML = '<span>Connection error</span>';
    }
}

async function sendQuery() {
    const input = document.getElementById('queryInput');
    const sendBtn = document.getElementById('sendBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    const query = input.value.trim();

    if (!query) {
        showStatus('Please enter a research query', 'warning');
        return;
    }

    console.log('Sending research query');
    addMessage('user', query);
    input.value = '';

    // Update UI states
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<span class="loading">Processing</span>';
    loadingIndicator.classList.add('active');
    showStatus('Initializing research...', 'processing');

    try {
        console.log('Starting streaming API request...');
        const requestStart = Date.now();
        
        // Create an AbortController for manual timeout control
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            console.log('Manual timeout after 5 minutes');
            controller.abort();
        }, 300000); // 5 minute timeout instead of default browser timeout
        
        // Use fetch with streaming for POST requests with body
        const response = await fetch('/query/stream', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache'
            },
            body: JSON.stringify({ 
                query, 
                chat_history: chatHistory, 
                use_gemini: useGemini 
            }),
            signal: controller.signal,
            // Disable browser's default timeout behavior
            keepalive: true
        });

        // Clear the timeout since we got a response
        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error('Request failed with status ' + response.status);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.substring(6));
                        
                        if (data.type === 'status') {
                            showStatus(data.message, 'processing');
                            updateProgress(data.progress);
                            // Also update the loading text
                            const loadingText = document.getElementById('loadingText');
                            if (loadingText) {
                                loadingText.textContent = data.message;
                            }
                            console.log('Progress: ' + data.progress + '% - ' + data.message);
                        } else if (data.type === 'tools') {
                            showStatus(data.message, 'processing');
                            // Update loading text for tools
                            const loadingText = document.getElementById('loadingText');
                            if (loadingText) {
                                loadingText.textContent = data.message;
                            }
                            console.log('Tools: ' + data.message);
                        } else if (data.type === 'result') {
                            const result = data.data;
                            const requestTime = Date.now() - requestStart;
                            console.log('Request completed in ' + requestTime + 'ms');
                            
                            if (result.success) {
                                addMessage('assistant', result.response, result.sources, result.visualizations);
                                showStatus('Research complete', 'success');
                                console.log('Analysis completed successfully');
                            } else {
                                console.log('Analysis request failed');
                                addMessage('assistant', result.response || 'Analysis temporarily unavailable. Please try again.', [], []);
                                showStatus('Request failed', 'error');
                            }
                        } else if (data.type === 'complete') {
                            break;
                        } else if (data.type === 'error') {
                            throw new Error(data.message);
                        }
                    } catch (parseError) {
                        console.error('Parse error:', parseError);
                    }
                }
            }
        }

    } catch (error) {
        console.error('Streaming request error:', error);
        
        // More specific error handling
        if (error.name === 'AbortError') {
            addMessage('assistant', 'Request timed out after 5 minutes. Ollama may be processing a complex query. Please try a simpler question or wait and try again.');
            showStatus('Request timed out', 'error');
        } else if (error.message.includes('Failed to fetch') || error.message.includes('network error')) {
            addMessage('assistant', 'Network connection error. Please check your internet connection and try again.');
            showStatus('Connection error', 'error');
        } else if (error.message.includes('ERR_HTTP2_PROTOCOL_ERROR')) {
            addMessage('assistant', 'Ollama is still processing your request in the background. Please wait a moment and try again, or try a simpler query.');
            showStatus('Processing - please retry', 'warning');
        } else {
            addMessage('assistant', 'Connection error. Please check your network and try again.');
            showStatus('Connection error', 'error');
        }
    } finally {
        // Reset UI states
        sendBtn.disabled = false;
        sendBtn.innerHTML = 'Research';
        loadingIndicator.classList.remove('active');
        input.focus();
        console.log('Request completed');
        
        // Hide status after delay
        setTimeout(() => hideStatus(), 3000);
    }
}

function addMessage(sender, content, sources = [], visualizations = []) {
    const messagesDiv = document.getElementById('chatMessages');
    
    // Clear welcome message
    if (messageCount === 0) {
        messagesDiv.innerHTML = '';
    }
    messageCount++;

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ' + sender;

    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = `
            <div class="sources">
                Sources: ${sources.map(s => `<span>${s}</span>`).join('')}
            </div>
        `;
    }

    let visualizationHtml = '';
    if (visualizations && visualizations.length > 0) {
        console.log('Processing visualizations:', visualizations.length);
        visualizationHtml = visualizations.map((viz, index) => {
            console.log(`Visualization ${index}:`, viz.substring(0, 100));
            return `<div class="visualization-container" id="viz-${Date.now()}-${index}">${viz}</div>`;
        }).join('');
    }

    // Format content based on sender
    let formattedContent = content;
    if (sender === 'assistant') {
        // Convert markdown to HTML for assistant responses
        try {
            formattedContent = marked.parse(content);
        } catch (error) {
            // Fallback to basic formatting if marked.js fails
            console.warn('Markdown parsing failed, using fallback:', error);
            formattedContent = content
                .replace(/\n/g, '<br>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code>$1</code>');
        }
    } else {
        // Apply markdown parsing to user messages too
        try {
            formattedContent = marked.parse(content);
        } catch (error) {
            formattedContent = content.replace(/\n/g, '<br>');
        }
    }

    messageDiv.innerHTML = `
        <div class="message-content">
            ${formattedContent}
            ${sourcesHtml}
        </div>
        ${visualizationHtml}
        <div class="message-meta">${new Date().toLocaleTimeString()}</div>
    `;

    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    // Execute any scripts in the visualizations after DOM insertion
    if (visualizations && visualizations.length > 0) {
        console.log('Executing visualization scripts...');
        setTimeout(() => {
            const scripts = messageDiv.querySelectorAll('script');
            console.log(`Found ${scripts.length} scripts to execute`);
            
            scripts.forEach((script, index) => {
                console.log(`Executing script ${index}:`, script.textContent.substring(0, 200) + '...');
                try {
                    // Execute script in global context using Function constructor
                    const scriptFunction = new Function(script.textContent);
                    scriptFunction.call(window);
                    console.log(`Script ${index} executed successfully`);
                } catch (error) {
                    console.error(`Script ${index} execution error:`, error);
                    console.error(`Script content preview:`, script.textContent.substring(0, 500));
                }
            });
            console.log('All visualization scripts executed');
        }, 100);
    }

    chatHistory.push({ role: sender, content });
    if (chatHistory.length > 20) chatHistory = chatHistory.slice(-20);
}

function setQuery(query) {
    document.getElementById('queryInput').value = query;
    setTimeout(() => sendQuery(), 100);
}

// Status management functions
function showStatus(message, type = 'info') {
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    
    statusText.textContent = message;
    statusIndicator.className = `status-indicator show ${type}`;
}

function hideStatus() {
    const statusIndicator = document.getElementById('statusIndicator');
    statusIndicator.classList.remove('show');
}

function updateProgress(progress) {
    // Update progress bar if it exists
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
    }
    
    // Update loading indicator text with progress
    const loadingText = document.getElementById('loadingText');
    if (loadingText && progress) {
        loadingText.textContent = `Processing ${progress}%...`;
    }
}

// Theme toggle functionality
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    const themeIcon = document.querySelector('#themeToggle i');
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Update icon
    if (newTheme === 'light') {
        themeIcon.className = 'fas fa-sun';
    } else {
        themeIcon.className = 'fas fa-moon';
    }
}

// Initialize theme
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const themeIcon = document.querySelector('#themeToggle i');
    
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    if (savedTheme === 'light') {
        themeIcon.className = 'fas fa-sun';
    } else {
        themeIcon.className = 'fas fa-moon';
    }
}

// Event listeners
document.getElementById('queryInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendQuery();
});

document.getElementById('sendBtn').addEventListener('click', (e) => {
    console.log('Research button clicked');
    e.preventDefault();
    sendQuery();
});

document.getElementById('themeToggle').addEventListener('click', toggleTheme);

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Application initialized');
    initializeTheme();
    checkStatus();
    document.getElementById('queryInput').focus();
});
