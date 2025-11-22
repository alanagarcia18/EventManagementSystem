// Main JavaScript functionality for Event Management System

// Theme Management
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        themeIcon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        themeIcon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

// AI Chat Management
function toggleAI() {
    const widget = document.getElementById('aiChatWidget');
    if (widget) {
        widget.classList.toggle('show');
    }
}

// AI Chat Form Submission
async function sendAIMessage(message) {
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        if (response.ok) {
            return data.response;
        } else {
            throw new Error(data.error || 'Failed to get AI response');
        }
    } catch (error) {
        throw error;
    }
}

function addMessageToChat(message, isUser = false, isError = false) {
    const aiMessages = document.getElementById('aiChatMessages');
    if (!aiMessages) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `ai-message ${isUser ? 'user' : 'ai'}${isError ? ' error' : ''}`;
    
    if (isUser) {
        messageDiv.innerHTML = `
            <div class="ai-message-content">${escapeHtml(message)}</div>
            <div class="ai-message-avatar">
                <i class="fas fa-user"></i>
            </div>
        `;
    } else {
        const icon = isError ? 'fas fa-exclamation-triangle' : 'fas fa-robot';
        messageDiv.innerHTML = `
            <div class="ai-message-avatar">
                <i class="${icon}"></i>
            </div>
            <div class="ai-message-content">${escapeHtml(message)}</div>
        `;
    }
    
    aiMessages.appendChild(messageDiv);
    aiMessages.scrollTop = aiMessages.scrollHeight;
}

// Utility Functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function setLoadingState(isLoading) {
    const aiInput = document.getElementById('aiChatInput');
    const aiSend = document.getElementById('aiChatSend');
    
    if (aiInput && aiSend) {
        aiInput.disabled = isLoading;
        aiSend.disabled = isLoading;
        aiSend.innerHTML = isLoading ? 
            '<i class="fas fa-spinner fa-spin"></i>' : 
            '<i class="fas fa-paper-plane"></i>';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Load theme
    loadTheme();

    // Setup AI Chat
    const aiForm = document.getElementById('aiChatForm');
    const aiInput = document.getElementById('aiChatInput');

    if (aiForm && aiInput) {
        aiForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const message = aiInput.value.trim();
            if (!message) return;

            // Set loading state
            setLoadingState(true);

            // Add user message
            addMessageToChat(message, true);
            
            // Clear input
            aiInput.value = '';

            try {
                const response = await sendAIMessage(message);
                addMessageToChat(response, false);
            } catch (error) {
                addMessageToChat('Sorry, I\'m having trouble responding right now. Please try again later.', false, true);
            }

            // Reset loading state
            setLoadingState(false);
            aiInput.focus();
        });
    }

    // Auto-hide flash messages
    setTimeout(() => {
        const flashMessages = document.querySelectorAll('.flash-message');
        flashMessages.forEach(message => {
            message.style.animation = 'slideOut 0.3s ease-in forwards';
            setTimeout(() => message.remove(), 300);
        });
    }, 5000);

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

// Global functions for onclick handlers
window.toggleTheme = toggleTheme;
window.toggleAI = toggleAI;
window.toggleAIAssistant = toggleAI;
