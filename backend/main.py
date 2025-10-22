# main.py
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from raciocinio import evaluate_topic
from memoria import Memoria
from utils import ensure_db, log_action
import os
from jinja2 import Environment, FileSystemLoader
DB_PATH = os.environ.get('DB_PATH', 'db/conhecimento.db')
ensure_db(DB_PATH)
mem = Memoria(DB_PATH)
app = FastAPI(title='Babix IA - Backend')
# servir frontend estático
app.mount('/static', StaticFiles(directory='frontend'), name='static')
# Endpoint chat (simples) — recebe texto e keywords
@app.post('/api/chat')
async def api_chat(payload: dict):
text = payload.get('message','')
# extrair keywords simples (split) — ideal: NER
8
keywords = [w for w in text.split() if len(w) > 3][:8]
res = evaluate_topic(DB_PATH, keywords)
log_action(DB_PATH, 'chat_query', text)
return JSONResponse(content=res)
# Endpoint para iniciar aprendizado a partir do seed_urls
@app.post('/api/learn')
async def api_learn(mode: str = Form('web')):
# executa indexação em background (simples: chamamos script)
from subprocess import Popen
if mode not in ('web','local'):
return JSONResponse({'ok':False,'msg':'mode invalid'})
Popen(['python','backend/aprendizado.py','--db',DB_PATH,'--mode','web'])
return JSONResponse({'ok':True,'msg':'indexing started'})
# Dashboard para visualização do que a IA aprendeu
@app.get('/dashboard', response_class=HTMLResponse)
async def dashboard(request: Request):
env = Environment(loader=FileSystemLoader('frontend'))
tmpl = env.get_template('dashboard.html')
sources = mem.list_sources()
chunks = mem.list_chunks(limit=200)
html = tmpl.render(sources=sources, chunks=chunks)
return HTMLResponse(content=html)
# API para obter texto completo de um chunk
@app.get('/api/chunk/{chunk_id}')
async def get_chunk(chunk_id: str):
text = mem.get_chunk_text(chunk_id)
return JSONResponse({'id':chunk_id,'text':text})
if __name__ == '__main__':
uvicorn.run('backend.main:app', host='0.0.0.0',
port=int(os.environ.get('PORT',8000)), reload=True)
