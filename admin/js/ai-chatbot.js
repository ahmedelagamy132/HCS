document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('ai-input');
    const sendBtn = document.getElementById('send-msg');
    const chatHistory = document.getElementById('chat-history');
    const typingIndicator = document.getElementById('typing-indicator');
    const clearBtn = document.getElementById('clear-chat');

    const toggleRag = document.getElementById('toggle-rag');
    const toggleSensors = document.getElementById('toggle-sensors');
    const toggleBehavior = document.getElementById('toggle-behavior');
    const modeBadge = document.getElementById('mode-badge');

    if (!input || !sendBtn || !chatHistory) return;

    if (typeof marked !== 'undefined') {
        marked.setOptions({ breaks: true, gfm: true });
    }

    function updateModeBadge() {
        const allOff = !toggleRag.checked && !toggleSensors.checked && !toggleBehavior.checked;
        if (modeBadge) modeBadge.classList.toggle('hidden', !allOff);
    }

    if (toggleRag) toggleRag.addEventListener('change', updateModeBadge);
    if (toggleSensors) toggleSensors.addEventListener('change', updateModeBadge);
    if (toggleBehavior) toggleBehavior.addEventListener('change', updateModeBadge);

    function getActiveMode() {
        return {
            use_rag:      toggleRag ? toggleRag.checked : true,
            use_sensors:  toggleSensors ? toggleSensors.checked : false,
            use_behavior: toggleBehavior ? toggleBehavior.checked : false,
        };
    }

    async function loadChatbotHealth() {
        const activeModelName = document.getElementById('active-model-name');
        const activeModelVersion = document.getElementById('active-model-version');
        try {
            const res = await fetch('/api/chatbot/health');
            if (!res.ok) throw new Error('API Error');
            const data = await res.json();
            if (activeModelName) activeModelName.textContent = 'Horse Expert Agent';
            if (activeModelVersion) activeModelVersion.textContent = data.status === 'healthy' ? 'Online' : 'Starting up...';
        } catch {
            if (activeModelName) activeModelName.textContent = 'Horse Expert Agent';
            if (activeModelVersion) activeModelVersion.textContent = 'Connecting...';
        }
    }

    loadChatbotHealth();

    input.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
        if (!this.value) this.style.height = '3.5rem';
    });

    const userAvatarHtml = '<div class="w-8 h-8 rounded-full bg-hcs-amber/20 border border-hcs-amber/40 flex flex-shrink-0 items-center justify-center text-hcs-amber font-cormorant font-medium text-base">A</div>';
    const aiAvatarHtml = '<div class="w-8 h-8 rounded-full bg-hcs-bg3 border border-hcs-amber/20 flex flex-shrink-0 items-center justify-center text-hcs-amber"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="7"/><path d="M8 3v5l3 3"/></svg></div>';

    const scrollToBottom = () => { chatHistory.scrollTop = chatHistory.scrollHeight; };

    function renderMarkdown(text) {
        if (typeof marked !== 'undefined') {
            return marked.parse(text);
        }
        return text.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br/>');
    }

    const handleSend = async () => {
        const val = input.value.trim();
        if (!val) return;

        const msgDiv = document.createElement('div');
        msgDiv.className = 'flex items-start gap-4 flex-row-reverse stagger-item';
        msgDiv.innerHTML = userAvatarHtml +
            '<div class="bg-hcs-amber/10 rounded-2xl rounded-tr-sm px-5 py-4 border border-hcs-amber/20 text-hcs-cream text-right ml-12">' +
            val.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>') +
            '</div>';

        chatHistory.insertBefore(msgDiv, typingIndicator);

        input.value = '';
        input.style.height = '3.5rem';
        scrollToBottom();

        typingIndicator.classList.remove('hidden');
        scrollToBottom();

        input.disabled = true;
        sendBtn.disabled = true;

        const aiDiv = document.createElement('div');
        aiDiv.className = 'flex items-start gap-4 stagger-item';
        const aiContent = document.createElement('div');
        aiContent.className = 'bg-hcs-bg2/80 rounded-2xl rounded-tl-sm px-5 py-4 border border-white/5 text-hcs-cream flex-1 font-jost font-light text-[0.85rem] prose prose-invert prose-sm max-w-none';

        try {
            const mode = getActiveMode();

            const res = await fetch('/api/chatbot/chat-stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: val, ...mode }),
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);

            typingIndicator.classList.add('hidden');
            aiDiv.innerHTML = '';
            aiDiv.appendChild(document.createTextNode(''));
            aiDiv.className = 'flex items-start gap-4 stagger-item';
            aiDiv.appendChild(document.createElement('span')).remove();
            aiDiv.innerHTML = aiAvatarHtml;
            aiDiv.appendChild(aiContent);
            chatHistory.insertBefore(aiDiv, typingIndicator);

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let fullText = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                fullText += chunk;
                aiContent.innerHTML = renderMarkdown(fullText);
                scrollToBottom();
            }

        } catch (error) {
            typingIndicator.classList.add('hidden');

            if (!aiDiv.parentNode) {
                aiDiv.innerHTML = aiAvatarHtml;
                aiDiv.appendChild(aiContent);
                chatHistory.insertBefore(aiDiv, typingIndicator);
            }

            aiContent.className = 'bg-red-500/10 rounded-2xl rounded-tl-sm px-5 py-4 border border-red-500/20 text-red-200 flex-1 font-jost font-light text-[0.85rem]';
            aiContent.textContent = 'System Error: ' + error.message;
            scrollToBottom();
        } finally {
            input.disabled = false;
            sendBtn.disabled = false;
            input.focus();
        }
    };

    sendBtn.addEventListener('click', handleSend);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    if (clearBtn) {
        clearBtn.addEventListener('click', async () => {
            try {
                await fetch('/api/chatbot/clear-history', { method: 'POST' });
            } catch { /* silent */ }
            Array.from(chatHistory.children).forEach(child => {
                if (child !== typingIndicator) chatHistory.removeChild(child);
            });
        });
    }
});
