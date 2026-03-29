/**
 * Chat widget client — communicates with the chatbot microservice.
 */
(function () {
    'use strict';

    const CHATBOT_API_URL = 'http://localhost:8001/api/v1/chat';

    // DOM elements
    const toggle = document.getElementById('chat-toggle');
    const panel = document.getElementById('chat-panel');
    const closeBtn = document.getElementById('chat-close');
    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('chat-messages');
    const typingIndicator = document.getElementById('chat-typing');
    const iconOpen = toggle.querySelector('.chat-icon-open');
    const iconClose = toggle.querySelector('.chat-icon-close');

    // Session ID — new on every page load/refresh
    let sessionId = sessionStorage.getItem('chat_session_id');
    if (!sessionId) {
        sessionId = crypto.randomUUID();
        sessionStorage.setItem('chat_session_id', sessionId);
    }

    let isOpen = false;
    let isSending = false;

    // Toggle chat panel
    function toggleChat() {
        isOpen = !isOpen;
        panel.style.display = isOpen ? 'flex' : 'none';
        iconOpen.style.display = isOpen ? 'none' : 'block';
        iconClose.style.display = isOpen ? 'block' : 'none';

        if (isOpen) {
            input.focus();
            scrollToBottom();
        }
    }

    toggle.addEventListener('click', toggleChat);
    closeBtn.addEventListener('click', toggleChat);

    // Scroll messages to bottom
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Create a message element
    function addMessage(text, isUser, sources) {
        const wrapper = document.createElement('div');
        wrapper.className = 'chat-message ' + (isUser ? 'chat-message-user' : 'chat-message-bot');

        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble ' + (isUser ? 'chat-bubble-user' : 'chat-bubble-bot');
        bubble.textContent = text;

        wrapper.appendChild(bubble);

        // Add source citations for bot messages
        if (!isUser && sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'chat-sources';

            const label = document.createElement('div');
            label.className = 'chat-sources-label';
            label.textContent = 'Sources';
            sourcesDiv.appendChild(label);

            sources.forEach(function (src) {
                const link = document.createElement('a');
                link.className = 'chat-source-link';
                link.textContent = '\u{1F4F0} Edition #' + src.edition_number + ' — ' + src.section_title;
                link.href = '#';
                link.title = 'Published: ' + src.published_at;
                link.addEventListener('click', function (e) {
                    e.preventDefault();
                });
                sourcesDiv.appendChild(link);
            });

            bubble.appendChild(sourcesDiv);
        }

        messagesContainer.appendChild(wrapper);
        scrollToBottom();
    }

    // Show/hide typing indicator
    function setTyping(show) {
        typingIndicator.style.display = show ? 'block' : 'none';
        if (show) scrollToBottom();
    }

    // Send message to the chatbot API
    async function sendMessage(text) {
        if (isSending || !text.trim()) return;
        isSending = true;

        addMessage(text, true);
        input.value = '';
        input.disabled = true;
        setTyping(true);

        try {
            const response = await fetch(CHATBOT_API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    session_id: sessionId,
                }),
            });

            if (!response.ok) {
                throw new Error('Server returned ' + response.status);
            }

            const data = await response.json();

            // Update session ID if server provides one
            if (data.session_id) {
                sessionId = data.session_id;
                sessionStorage.setItem('chat_session_id', sessionId);
            }

            setTyping(false);
            addMessage(data.answer, false, data.sources);
        } catch (err) {
            setTyping(false);
            addMessage('Sorry, I could not connect to the assistant. Please make sure the chatbot service is running.', false);
            console.error('Chat error:', err);
        } finally {
            isSending = false;
            input.disabled = false;
            input.focus();
        }
    }

    // Handle form submission
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        sendMessage(input.value);
    });

    // Allow Enter to send (already handled by form submit)
    // Shift+Enter could be used for multiline in the future
})();
