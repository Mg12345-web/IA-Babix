from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

def chunk_pdf(pdf_path, chunk_size=1000, chunk_overlap=200):
    """
    Divide um PDF em chunks menores mantendo contexto
    """
    try:
        print(f"📖 Carregando PDF: {pdf_path}")
        
        # Carregar PDF
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        
        print(f"📄 Total de páginas: {len(pages)}")
        
        # Configurar divisor de texto
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )
        
        # Dividir em chunks
        chunks = text_splitter.split_documents(pages)
        
        print(f"✂️ PDF dividido em {len(chunks)} chunks")
        
        # Extrair texto e metadados
        texts = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            texts.append(chunk.page_content)
            metadatas.append({
                "chunk_id": i,
                "page": chunk.metadata.get("page", 0),
                "source": chunk.metadata.get("source", ""),
                "total_chunks": len(chunks)
            })
        
        return texts, metadatas
        
    except Exception as e:
        print(f"❌ Erro ao dividir PDF: {e}")
        import traceback
        traceback.print_exc()
        return [], []
