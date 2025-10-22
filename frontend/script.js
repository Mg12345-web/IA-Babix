document.addEventListener('DOMContentLoaded', () => {
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-btn');
    const messagesContainer = document.getElementById('messages-container');

    // Função para adicionar uma nova mensagem ao chat
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);
        
        // Simples substituição para negrito (para o balão vermelho da IA)
        const formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        messageDiv.innerHTML = `<p>${formattedText}</p>`;
        messagesContainer.appendChild(messageDiv);
        
        // Rola para a mensagem mais recente
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Função que simula a resposta da IA (você substituirá isso pela sua lógica real)
    function generateAiResponse(userText) {
        userText = userText.toLowerCase();

        if (userText.includes('multa') && userText.includes('recurso')) {
            return "Para gerar o recurso, preciso de mais informações. Qual é o **artigo da infração** e a **data** do ocorrido?";
        } else if (userText.includes('suspensão') || userText.includes('cnh')) {
            return "A suspensão da CNH pode ocorrer por atingir o limite de pontos ou por infrações **auto-suspensivas** (como dirigir embriagado ou se recusar a fazer o teste do bafômetro). Qual é o seu caso?";
        } else if (userText.includes('ctb') || userText.includes('legislação')) {
            return "Qual **artigo** ou **tema** específico do Código de Trânsito Brasileiro (CTB) você gostaria de consultar?";
        } else {
            return "Entendido. No que mais posso te auxiliar sobre Direito de Trânsito?";
        }
    }

    // Função que gerencia o envio de mensagem
    function handleSendMessage() {
        const userText = userInput.value.trim();

        if (userText === '') return;

        // 1. Adiciona a mensagem do usuário
        addMessage(userText, 'user');
        
        // 2. Limpa a caixa de entrada
        userInput.value = '';

        // 3. Simula um pequeno delay e gera a resposta da IA
        setTimeout(() => {
            const aiResponse = generateAiResponse(userText);
            addMessage(aiResponse, 'ai');
        }, 800);
    }

    // Adiciona o evento de clique no botão de envio
    sendButton.addEventListener('click', handleSendMessage);

    // Adiciona o evento de pressionar 'Enter' na caixa de texto
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSendMessage();
        }
    });
    
    // Simula o envio de uma sugestão pelo usuário (Usado pelos botões de sugestão no HTML)
    window.simulateUserMessage = function(prompt) {
        addMessage(prompt, 'user');
        
        // Remove os botões de sugestão após o primeiro uso para limpar a tela
        const suggestionButtons = messagesContainer.querySelector('.suggestion-buttons');
        if(suggestionButtons) {
            suggestionButtons.style.display = 'none';
        }

        setTimeout(() => {
            const aiResponse = generateAiResponse(prompt);
            addMessage(aiResponse, 'ai');
        }, 800);
    };
});
