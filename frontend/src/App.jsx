
import React, { useState } from 'react'

const api = (path) => (import.meta.env.VITE_API_URL || 'http://localhost:8000') + path

export default function App(){
  const [pergunta, setPergunta] = useState('Explique nulidades do AIT no art. 280 do CTB.')
  const [resposta, setResposta] = useState('')
  const [fontes, setFontes] = useState([])
  const [perguntas, setPerguntas] = useState([])

  const handleAsk = async () => {
    const r = await fetch(api('/chat'), {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ pergunta })
    })
    const j = await r.json()
    setResposta(j.resposta || '')
    setFontes(j.fontes || [])
    setPerguntas(j.perguntas_faltantes || [])
  }

  return (
    <div style={{display:'grid', gridTemplateColumns:'260px 1fr', minHeight:'100vh'}}>
      <aside style={{background:'#111', color:'#fff', padding:'20px'}}>
        <h2 style={{color:'#f00'}}>IA Trânsito</h2>
        <p style={{opacity:.8}}>MVP — vermelho/preto</p>
        <hr style={{borderColor:'#333'}}/>
        <p>Chat • Casos • Conhecimento • Jurisprudências</p>
      </aside>
      <main style={{padding:'24px', background:'#1a1a1a', color:'#eee'}}>
        <h1 style={{color:'#f33'}}>Chat Jurídico</h1>
        <div style={{display:'flex', gap:12, marginTop:12}}>
          <input value={pergunta} onChange={e=>setPergunta(e.target.value)} style={{flex:1, padding:10, borderRadius:8, border:'1px solid #333', background:'#000', color:'#fff'}}/>
          <button onClick={handleAsk} style={{background:'#f00', color:'#fff', border:'none', padding:'10px 16px', borderRadius:8}}>Perguntar</button>
        </div>
        {resposta && (
          <div style={{marginTop:20, background:'#0d0d0d', padding:16, borderRadius:10, border:'1px solid #333'}}>
            <h3 style={{color:'#f55'}}>Resposta</h3>
            <pre style={{whiteSpace:'pre-wrap'}}>{resposta}</pre>
          </div>
        )}
        {!!fontes.length && (
          <div style={{marginTop:20}}>
            <h3 style={{color:'#f55'}}>Fontes (MVP)</h3>
            <ul>{fontes.map((f,i)=><li key={i}>{f}</li>)}</ul>
          </div>
        )}
        {!!perguntas.length && (
          <div style={{marginTop:20}}>
            <h3 style={{color:'#f55'}}>Perguntas Faltantes</h3>
            <ol>{perguntas.map((p,i)=><li key={i}>{p}</li>)}</ol>
          </div>
        )}
      </main>
    </div>
  )
}
