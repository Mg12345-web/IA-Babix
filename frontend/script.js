// script.js — versão corrigida e indentada

// Seletores principais
const chatContainer = document.getElementById('chatContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const quickBtns = document.querySelectorAll('.quick-btn');

// Ajusta altura dinâmica do textarea
messageInput.addEventListener('input', function () {
  this.style.height = 'auto';
  this.style.height = this.scrollHeight + 'px';
});

// Envio com Enter
messageInput.addEventListener('keydown', function (e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

sendBtn.addEventListener('click', sendMessage);

// Ações rápidas (botões iniciais)
quickBtns.forEach((btn) => {
  btn.addEventListener('click', function () {
    const action = this.textContent.trim();
    messageInput.value = action;
    sendMessage();
  });
});

// Adiciona mensagens ao chat
function addMessage(text, sender) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${sender}`;
  const icon =
    sender === 'user'
      ? '<i class="fas fa-user"></i>'
      : '<i class="fas fa-user-circle"></i>';
  messageDiv.innerHTML = `
    <div class="message-icon">${icon}</div>
    <div class="message-content">
      <div class="message-text">${formatMessage(text)}</div>
    </div>
  `;
  chatContainer.appendChild(messageDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Formata texto (markdown leve)
function formatMessage(text) {
  return text
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>');
}

// Indicador de digitação
function showTypingIndicator() {
  const typingDiv = document.createElement('div');
  typingDiv.className = 'message assistant typing-indicator';
  typingDiv.innerHTML = `
    <div class="message-icon"><i class="fas fa-user-circle"></i></div>
    <div class="message-content">
      <div class="message-text">Babix está digitando...</div>
    </div>
  `;
  chatContainer.appendChild(typingDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Remove indicador de digitação
function removeTypingIndicator() {
  const typingIndicator = chatContainer.querySelector('.typing-indicator');
  if (typingIndicator) typingIndicator.remove();
}

// Função principal de envio de mensagem
async function sendMessage() {
  const message = messageInput.value.trim();
  if (!message) return;

  const welcomeMsg = chatContainer.querySelector('.welcome-message');
  if (welcomeMsg) welcomeMsg.remove();

  addMessage(message, 'user');
  messageInput.value = '';
  messageInput.style.height = 'auto';
  sendBtn.disabled = true;
  showTypingIndicator();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    const data = await res.json();
    removeTypingIndicator();

    if (data.ok) {
      addMessage(
        `Confiança: ${data.confidence.toFixed(2)}\nFonte principal: ${data.top.source}\n\n${data.top.sample}`,
        'assistant'
      );
    } else {
      addMessage(
        `Sem evidência suficiente automaticamente.\nSugestão: revisão humana.`,
        'assistant'
      );
    }
  } catch (e) {
    removeTypingIndicator();
    addMessage('Erro ao contatar o servidor.', 'assistant');
  }
  sendBtn.disabled = false;
}

// Botão de nova conversa
document.querySelector('.new-chat-btn').addEventListener('click', function () {
  chatContainer.innerHTML = `
    <div class="welcome-message">
      <i class="fas fa-user-circle woman-icon-large"></i>
      <h2>Olá! Sou a Babix, sua assistente jurídica!</h2>
      <p>Como posso ajudar você hoje com seu caso de trânsito?</p>
      <div class="quick-actions">
        <button class="quick-btn"><i class="fas fa-file-invoice"></i> Analisar Auto de Infração</button>
        <button class="quick-btn"><i class="fas fa-book-open"></i> Consultar Artigo CTB</button>
        <button class="quick-btn"><i class="fas fa-pen"></i> Criar Defesa</button>
        <button class="quick-btn"><i class="fas fa-gavel"></i> Buscar Jurisprudência</button>
      </div>
    </div>
  `;

  document.querySelectorAll('.quick-btn').forEach((btn) => {
    btn.addEventListener('click', function () {
      const action = this.textContent.trim();
      messageInput.value = action;
      sendMessage();
    });
  });
});

// Navegação lateral
document.querySelectorAll('.nav-item').forEach((item) => {
  item.addEventListener('click', function (e) {
    e.preventDefault();
    document
      .querySelectorAll('.nav-item')
      .forEach((i) => i.classList.remove('active'));
    this.classList.add('active');
    if (this.getAttribute('href') === '/dashboard') {
      window.location.href = '/dashboard';
    }
  });
});
