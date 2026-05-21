# app/rag_engine_v2.py - Motor RAG completo con FAISS + Ollama Mistral
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.modules.chatbot.llm_wrapper import llm
from app.modules.scraping.product_scraper import get_products_catalog

class RAGEngineV2:
    """
    Motor RAG (Retrieval-Augmented Generation) completo con:
    - Búsqueda vectorial usando FAISS
    - Embeddings con sentence-transformers
    - Generación con Ollama Mistral
    - Integración con sistema experto
    """
    
    def __init__(self, catalog_path: str = "data/products_catalog.json"):
        """Inicializa el motor RAG"""
        print("Inicializando RAG Engine V2...")
        
        # Cargar catálogo de productos
        self.products = self._load_catalog(catalog_path)
        print(f"  Catálogo cargado: {len(self.products)} productos")
        
        # Inicializar modelo de embeddings
        print("  Cargando modelo de embeddings...")
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        print("  Modelo de embeddings listo")
        
        # Crear índice FAISS
        print("  Creando índice vectorial...")
        self.index, self.product_texts = self._create_index()
        print("  Índice FAISS creado")
        
        # Referencia al motor experto (se inyecta después)
        self.expert_engine = None
        
        print("RAG Engine V2 inicializado correctamente\n")
    
    def _load_catalog(self, catalog_path: str) -> List[Dict]:
        """Carga el catálogo de productos"""
        try:
            if Path(catalog_path).exists():
                with open(catalog_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"  Archivo {catalog_path} no encontrado, usando catálogo por defecto")
                return get_products_catalog()
        except Exception as e:
            print(f"  Error cargando catálogo: {e}")
            return get_products_catalog()
    
    def _create_index(self):
        """Crea el índice FAISS con embeddings de productos"""
        # Crear textos descriptivos de productos
        product_texts = []
        for product in self.products:
            text = self._product_to_text(product)
            product_texts.append(text)
        
        # Generar embeddings
        embeddings = self.embedding_model.encode(product_texts, show_progress_bar=False)
        embeddings = np.array(embeddings).astype('float32')
        
        # Normalizar para búsqueda por similitud coseno
        faiss.normalize_L2(embeddings)
        
        # Crear índice FAISS
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner Product (cosine similarity)
        index.add(embeddings)
        
        return index, product_texts
    
    def _product_to_text(self, product: Dict) -> str:
        """Convierte un producto a texto para embedding"""
        parts = [
            f"Producto: {product.get('model', '')}",
            f"Familia: {product.get('family', '')}",
            f"Tipo: {product.get('type', '')}",
            f"Descripción: {product.get('description', '')}",
        ]
        
        if product.get('features'):
            parts.append(f"Características: {', '.join(product['features'])}")
        
        if product.get('applications'):
            parts.append(f"Aplicaciones: {', '.join(product['applications'])}")
        
        parts.append(f"Potencia: {product.get('power_w', 0)} W")
        
        return " ".join(parts)
    
    def set_expert_engine(self, expert_engine):
        """Inyecta el motor experto para enriquecimiento mutuo"""
        self.expert_engine = expert_engine
        print("Expert Engine conectado al RAG")
    
    async def query(self, question: str, expert_context: Optional[Dict[str, Any]] = None, top_k: int = 3) -> Dict[str, Any]:
        """
        Procesa una consulta usando RAG
        
        Args:
            question: Pregunta del usuario
            expert_context: Contexto del sistema experto (opcional)
            top_k: Número de productos a recuperar
            
        Returns:
            Diccionario con respuesta y metadatos
        """
        print(f"\nRAG Query: '{question[:50]}...'")
        
        # 1. Búsqueda vectorial
        relevant_products = self.search_products(question, top_k)
        print(f"  Encontrados {len(relevant_products)} productos relevantes")
        
        # 2. Filtrar por contexto experto si existe
        if expert_context:
            relevant_products = self._filter_by_expert_context(relevant_products, expert_context)
            print(f"  Filtrados por contexto: {len(relevant_products)} productos")
        
        # 3. Generar respuesta con Ollama Mistral
        answer = llm.generate(question, relevant_products)
        
        # 4. NO sugerir flujo experto en modo chat - mantener conversación fluida
        # El usuario puede cambiar de modo manualmente si lo desea
        
        return {
            'answer': answer,
            'products': relevant_products[:2],  # Solo top 2 para no saturar
            'sources': [p['model'] for p in relevant_products[:2]],
            'expert_suggestion': None,  # No interrumpir el chat
            'context_used': expert_context is not None,
            'mode': 'rag',
            'type': 'chat_response'  # Indicar que es respuesta de chat continuo
        }
    
    def search_products(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """
        Búsqueda vectorial de productos usando FAISS
        
        Args:
            query_text: Texto de búsqueda
            top_k: Número de resultados
            
        Returns:
            Lista de productos relevantes
        """
        # Generar embedding de la consulta
        query_embedding = self.embedding_model.encode([query_text])
        query_embedding = np.array(query_embedding).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        # Buscar en el índice
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Recuperar productos
        results = []
        for idx, score in zip(indices[0], distances[0]):
            if idx < len(self.products):
                product = self.products[idx].copy()
                product['relevance_score'] = float(score)
                results.append(product)
        
        return results
    
    def _filter_by_expert_context(self, products: List[Dict], context: Dict[str, Any]) -> List[Dict]:
        """Filtra productos según el contexto del sistema experto"""
        filtered = products.copy()
        
        # Filtrar por tipo de calefacción si está en el contexto
        if 'tipo_calefaccion' in context:
            tipo = context['tipo_calefaccion'].lower()
            filtered = [p for p in filtered if tipo in p.get('family', '').lower()]
        
        # Filtrar por potencia si hay carga térmica calculada
        if 'carga_termica' in context:
            carga = context['carga_termica']
            # Buscar productos con potencia similar (±20%)
            filtered = [p for p in filtered 
                       if p.get('power_w', 0) > 0 and 
                       abs(p['power_w'] - carga) / carga < 0.3]
        
        # Si el filtrado eliminó todos los productos, devolver los originales
        return filtered if filtered else products
    
    def _should_suggest_expert_flow(self, question: str, expert_context: Optional[Dict]) -> bool:
        """Determina si debería sugerir el flujo experto"""
        # No sugerir si ya está en flujo experto
        if expert_context:
            return False
        
        # Palabras clave que indican necesidad de cálculo
        calc_keywords = ['calcular', 'dimensionar', 'necesito', 'cuánto', 'qué potencia', 
                        'cuántos', 'tamaño', 'superficie', 'm2', 'metros']
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in calc_keywords)
    
    async def get_context_for_expert(self, query: str, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Obtiene contexto relevante para enriquecer el sistema experto
        
        Args:
            query: Consulta o contexto actual
            filters: Filtros adicionales
            
        Returns:
            Diccionario con información contextual
        """
        products = self.search_products(query, top_k=3)
        
        return {
            'recommended_products': products,
            'families': list(set([p.get('family', '') for p in products])),
            'avg_power': np.mean([p.get('power_w', 0) for p in products if p.get('power_w', 0) > 0])
        }

# Instancia global (se inicializa cuando se importa)
try:
    rag_engine_v2 = RAGEngineV2()
except Exception as e:
    print(f"Error inicializando RAG Engine V2: {e}")
    rag_engine_v2 = None
