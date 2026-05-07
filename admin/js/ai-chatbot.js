document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('ai-input');
    const sendBtn = document.getElementById('send-msg');
    const chatHistory = document.getElementById('chat-history');
    const typingIndicator = document.getElementById('typing-indicator');
    const clearBtn = document.getElementById('clear-chat');
    
    const modelSelector = document.getElementById('model-selector');
    const activeModelName = document.getElementById('active-model-name');
    const activeModelVersion = document.getElementById('active-model-version');

    if (!input || !sendBtn || !chatHistory) return;

    async function loadModels() {
        try {
            const res = await fetch('/api/models');
            if (!res.ok) throw new Error('API Error');
            const models = await res.json();
            
            const textModels = models.filter(m => m.category === 'Text Generation');
            
            modelSelector.innerHTML = '';
            if (textModels.length === 0) {
                modelSelector.innerHTML = '<option value="">No Text Models</option>';
                activeModelName.textContent = 'Offline';
                activeModelVersion.textContent = 'No models available';
                return;
            }
            
            textModels.forEach((m) => {
                const opt = document.createElement('option');
                opt.value = m.id;
                opt.textContent = m.name;
                opt.dataset.version = m.version;
                modelSelector.appendChild(opt);
            });
            
            updateActiveModel();
        } catch (err) {
            console.error('Failed fetching models:', err);
            modelSelector.innerHTML = '<option value="">Error Fetching API</option>';
            activeModelName.textContent = 'Disconnected';
            activeModelVersion.textContent = 'Network error';
        }
    }

    function updateActiveModel() {
        const selectedOpt = modelSelector.options[modelSelector.selectedIndex];
        if (selectedOpt) {
            activeModelName.textContent = selectedOpt.textContent || 'Unknown Model';
            activeModelVersion.textContent = 'Version — ' + (selectedOpt.dataset.version || 'unknown');
        }
    }

    if (modelSelector) {
        modelSelector.addEventListener('change', updateActiveModel);
        loadModels();
    }

    input.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (!this.value) this.style.height = '3.5rem';
    });

    const userAvatarHtml = '<div class="w-8 h-8 rounded-full bg-hcs-amber/20 border border-hcs-amber/40 flex flex-shrink-0 items-center justify-center text-hcs-amber font-cormorant font-medium text-base">A</div>';
    const aiAvatarHtml = '<div class="w-8 h-8 rounded-full bg-hcs-bg3 border border-hcs-amber/20 flex flex-shrink-0 items-center justify-center text-hcs-amber"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="7"/><path d="M8 3v5l3 3"/></svg></div>';

    const scrollToBottom = () => {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    };

    const handleSend = async () => {
        const val = input.value.trim();
        if (!val) return;

        const msgDiv = document.createElement('div');
        msgDiv.className = 'flex items-start gap-4 flex-row-reverse stagger-item';
        msgDiv.innerHTML = userAvatarHtml + 
            '<div class="bg-hcs-amber/10 rounded-2xl rounded-tr-sm px-5 py-4 border border-hcs-amber/20 text-hcs-cream text-right ml-12">' + 
            val.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\\n/g, "<br>") + 
            '</div>';
        
        chatHistory.insertBefore(msgDiv, typingIndicator);
        
        input.value = '';
        input.style.height = '3.5rem';
        scrollToBottom();

        typingIndicator.classList.remove('hidden');
        scrollToBottom();

        try {
            const selectedModelId = modelSelector ? modelSelector.value : 'llava';
            
            const reqRes = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: val,
                    model: selectedModelId
                })
            });
            
            if (!reqRes.ok) {
                throw new Error('API call failed');
            }
            
             const data = await reqRes.json();
             
             typingIndicator.classList.add('hidden');
            
             const aiDiv = document.createElement('div');
             aiDiv.className = 'flex items-start gap-4 stagger-item';
             
             const safeResponse = data.response
                ? data.response.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, '<br/>')
                : JSON.stringify(data);
                  
             aiDiv.innerHTML = aiAvatarHtml + 
                 '<div class="bg-hcs-bg2/80 rounded-2xl rounded-tl-sm px-5 py-4 border border-white/5 text-hcs-cream flex-1 font-jost font-light text-[0.85rem]">' +
                 '<p>' + safeResponse + '</p>' +
                 '</div>';
             chatHistory.insertBefore(aiDiv, typingIndicator);
             scrollToBottom();
             
        } catch (error) {
             typingIndicator.classList.add('hidden');
             const errDiv = document.createElement('div');
             errDiv.className = 'flex items-start gap-4 stagger-item';
             errDiv.innerHTML = aiAvatarHtml + 
                 '<div class="bg-red-500/10 rounded-2xl rounded-tl-sm px-5 py-4 border border-red-500/20 text-red-200 flex-1 font-jost font-light text-[0.85rem]">' +
                 '<p>System Error: ' + error.message + '</p>' +
                 '</div>';
             chatHistory.insertBefore(errDiv, typingIndicator);
             scrollToBottom();
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
        clearBtn.addEventListener('click', () => {
            Array.from(chatHistory.children).forEach(child => {
                if (child !== typingIndicator) {
                    chatHistory.removeChild(child);
                }
            });
        });
    }
});
