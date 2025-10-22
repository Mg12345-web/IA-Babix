
async function fetchExample(){
  try{
    const res = await fetch('/api/quick-answers');
    const data = await res.json();
    const example = document.getElementById('example-answer');
    const belt = data.belt_fine;
    example.textContent = `A infração por dirigir sem cinto de segurança é ${belt.gravity.toLowerCase()}, com multa de R$ ${belt.fine.toFixed(2)} e ${belt.points} pontos na CNH.`;
  }catch(e){
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
  if(!q) return;

  const convo = document.getElementById('conversation');
  const user = document.createElement('div');
  user.className = 'bubble user';
  user.textContent = q;
  convo.appendChild(user);

  input.value='';

  const res = await fetch('/api/ask', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({question:q})
  });
  const data = await res.json();

  const bot = document.createElement('div');
  bot.className = 'bubble bot';
  bot.textContent = data.answer || 'Sem resposta.';
  convo.appendChild(bot);

  convo.scrollTop = convo.scrollHeight;
});

document.getElementById('newChat').addEventListener('click', () => {
  document.getElementById('conversation').innerHTML='';
});
