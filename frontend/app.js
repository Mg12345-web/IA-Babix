async function fetchExample() {
  try {
    const res = await fetch('/api/quick-answers');
    const data = await res.json();
    const example = document.getElementById('example-answer');
    const belt = data.belt_fine;
    example.textContent = `A infração por dirigir sem cinto de segurança é ${belt.gravity.toLowerCase()}, com multa de R$ ${belt.fine.toFixed(2)} e ${belt.points} pontos na CNH.`;
  } catch (e) {
    document.getElementById('example-answer').textContent = 'Exemplo indisponível no momento.';
  }
}
fetchExample();

document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    document.getElementById('question').value = chip.dataset.fill || '';
    document.getElementById('question').focus();
  });
});

document.getElementById('askForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const input = document.getElementById('question');
  const q = input.value.trim();
  if (!q) return;

  const convo = document.getElementById('conversation');

  // 1. Adiciona a bolha do usuário
  const user = document.createElement('div');
  user.className = 'bubble user';
  user.textContent = q;
  convo.appendChild(user);

  input.value = '';
  convo.scrollTop = convo.scrollHeight; // Rola para a pergunta

  // 2. Adiciona a bolha de "digitando..."
  const typing = document.createElement('div');
  typing.className = 'bubble bot typing'; // Usa a nova classe CSS
  convo.appendChild(typing);
  convo.scrollTop = convo.scrollHeight; // Rola para o indicador

  try {
    // 3. Faz a requisição
    const res = await fetch('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q })
    });
    const data = await res.json();

    // 4. Substitui o "digitando" pela resposta real
    typing.textContent = data.answer || 'Sem resposta.';
    typing.classList.remove('typing'); // Remove a animação

  } catch (error) {
    // 5. Trata o erro
    typing.textContent = 'Erro ao conectar. Tente novamente.';
    typing.classList.remove('typing');
    // Opcional: Adiciona uma cor de erro
    // typing.style.borderColor = 'var(--red)'; 
  }

  convo.scrollTop = convo.scrollHeight; // Rola para a resposta final
});

document.getElementById('newChat').addEventListener('click', () => {
  document.getElementById('conversation').innerHTML = '';
});
