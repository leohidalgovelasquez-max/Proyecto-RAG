document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatViewport = document.getElementById('chat-viewport');
    const chunksContainer = document.getElementById('chunks-container');
    const promptPreview = document.getElementById('prompt-preview');
    const loader = document.getElementById('loader');
    const statusBadge = document.getElementById('status-badge');
    const docCount = document.getElementById('doc-count');
    const chunkCount = document.getElementById('chunk-count');
    const clearChatBtn = document.getElementById('clear-chat');

    // Fetch initial status
    async function updateStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            if (data.index_ready) {
                statusBadge.textContent = 'En Línea';
                statusBadge.className = 'badge status-ready';
            } else {
                statusBadge.textContent = 'Sin Datos';
                statusBadge.className = 'badge status-error';
            }

            docCount.textContent = data.documents_loaded;
            chunkCount.textContent = data.chunks_generated;
        } catch (error) {
            console.error('Error fetching status:', error);
            statusBadge.textContent = 'Error Servidor';
            statusBadge.className = 'badge status-error';
        }
    }

    updateStatus();

    // Handle Form submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = userInput.value.trim();
        const apiKey = document.getElementById('api-key-input').value.trim();

        if (!query) return;

        // Add user message to UI
        appendMessage('user', query);
        userInput.value = '';

        // Show loader
        loader.classList.remove('hidden');

        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, api_key: apiKey })
            });

            if (!response.ok) throw new Error('Error en la respuesta del servidor');

            const data = await response.json();

            // Add bot message
            appendMessage('bot', data.answer);

            // Update Inspection Panel
            updateInspectionPanel(data);

        } catch (error) {
            console.error(error);
            appendMessage('bot', 'Lo siento, hubo un error al procesar tu consulta. Asegúrate de que el servidor esté encendido.');
        } finally {
            loader.classList.add('hidden');
            // Devolver el foco al input para la siguiente pregunta
            setTimeout(() => userInput.focus(), 100);
        }
    });

    function appendMessage(role, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        msgDiv.innerHTML = `<div class="content">${text}</div>`;
        chatViewport.appendChild(msgDiv);
        chatViewport.scrollTop = chatViewport.scrollHeight;
    }

    function updateInspectionPanel(data) {
        // Clear previous chunks
        chunksContainer.innerHTML = '';
        document.querySelector('#retrieved-data .empty-state')?.remove();

        // Add new chunks
        data.context.forEach((chunk, index) => {
            const chunkDiv = document.createElement('div');
            chunkDiv.className = 'chunk-card';
            chunkDiv.innerHTML = `
                <div class="chunk-header">Fragmento #${index + 1}</div>
                <div class="chunk-content">${chunk}</div>
            `;
            chunksContainer.appendChild(chunkDiv);
        });

        // Update Prompt Preview
        promptPreview.textContent = data.prompt;
    }

    clearChatBtn.addEventListener('click', () => {
        chatViewport.innerHTML = '<div class="message system"><div class="content">Chat limpiado. ¿En qué puedo ayudarte?</div></div>';
        chunksContainer.innerHTML = '';
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state';
        emptyState.textContent = 'Realiza una pregunta para ver los fragmentos recuperados.';
        document.querySelector('#retrieved-data').appendChild(emptyState);
        promptPreview.textContent = 'El prompt aparecerá aquí...';
    });
});
