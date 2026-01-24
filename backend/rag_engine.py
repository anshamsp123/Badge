import os
from typing import List, Dict, Optional
import config
from models import QueryRequest, QueryResponse, SourceChunk
from vector_store import VectorStore
from embedder import Embedder


class RAGEngine:
    """RAG-based query engine for answering questions from documents."""
    
    def __init__(self, vector_store: VectorStore, embedder: Embedder):
        """
        Initialize the RAG engine.
        
        Args:
            vector_store: Vector store instance
            embedder: Embedder instance
        """
        self.vector_store = vector_store
        self.embedder = embedder
        
        # Initialize LLM
        if config.USE_OPENAI and config.OPENAI_API_KEY:
            self.llm_type = "openai"
            from openai import OpenAI
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            print("Using OpenAI for LLM")
        else:
            self.llm_type = "ollama"
            print("Using Ollama for LLM (make sure Ollama is running)")
    
    def query(
        self,
        question: str,
        doc_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> QueryResponse:
        """
        Answer a question using RAG.
        
        Args:
            question: User's question
            doc_ids: Optional list of document IDs to search within
            top_k: Number of chunks to retrieve
            
        Returns:
            QueryResponse with answer and sources
        """
        # Step 1: Generate embedding for the question
        question_embedding = self.embedder.embed_text(question)
        
        # Step 2: Retrieve relevant chunks from vector store
        search_results = self.vector_store.search(
            query_embedding=question_embedding,
            top_k=top_k,
            doc_ids=doc_ids
        )
        
        if not search_results:
            return QueryResponse(
                question=question,
                answer="I don't have enough information to answer this question. Please upload relevant documents first.",
                sources=[],
                confidence=0.0
            )
        
        # Step 3: Prepare context from retrieved chunks
        context_chunks = []
        sources = []
        
        for metadata, similarity in search_results:
            context_chunks.append(metadata['text'])
            sources.append(SourceChunk(
                text=metadata['text'],
                doc_id=metadata['doc_id'],
                filename=metadata['filename'],
                doc_type=metadata['doc_type'],
                page_number=metadata.get('page_number'),
                similarity_score=similarity
            ))
        
        context = "\n\n".join([f"[Source {i+1}]: {chunk}" for i, chunk in enumerate(context_chunks)])
        
        # Step 4: Generate answer using LLM
        answer = self._generate_answer(question, context)
        
        # Step 5: Calculate confidence based on similarity scores
        avg_similarity = sum(s.similarity_score for s in sources) / len(sources)
        confidence = min(avg_similarity * 1.2, 1.0)  # Scale up slightly, cap at 1.0
        
        return QueryResponse(
            question=question,
            answer=answer,
            sources=sources,
            confidence=confidence
        )
    
    def _generate_answer(self, question: str, context: str) -> str:
        """
        Generate answer using LLM.
        
        Args:
            question: User's question
            context: Retrieved context from documents
            
        Returns:
            Generated answer
        """
        # Create prompt
        prompt = self._create_prompt(question, context)
        
        try:
            if self.llm_type == "openai":
                return self._generate_with_openai(prompt)
            else:
                return self._generate_with_ollama(prompt)
        except Exception as e:
            print(f"Error generating answer with LLM: {e}")
            # Fallback to simple extraction-based answer
            return self._generate_fallback_answer(question, context)
    
    def _create_prompt(self, question: str, context: str) -> str:
        """Create prompt for LLM."""
        prompt = f"""You are an AI assistant helping with insurance claim analysis. Answer the question based ONLY on the provided context from insurance documents.

Context from documents:
{context}

Question: {question}

Instructions:
1. Answer based ONLY on the information in the context above
2. If the context doesn't contain enough information, say so clearly
3. Be specific and cite relevant details from the documents
4. Keep your answer concise and factual
5. If mentioning amounts, dates, or policy numbers, quote them exactly as they appear

Answer:"""
        return prompt
    
    def _generate_with_openai(self, prompt: str) -> str:
        """Generate answer using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for insurance claim analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")
    
    def _generate_with_ollama(self, prompt: str) -> str:
        """Generate answer using Ollama."""
        try:
            import requests
            
            print(f"Sending request to Ollama at {config.OLLAMA_BASE_URL}")
            
            response = requests.post(
                f"{config.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": config.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": config.LLM_TEMPERATURE,
                        "num_predict": config.LLM_MAX_TOKENS
                    }
                },
                timeout=120  # Increased timeout to 2 minutes
            )
            
            print(f"Ollama response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if 'response' in result:
                    return result['response'].strip()
                else:
                    print(f"Unexpected Ollama response format: {result}")
                    raise Exception(f"Ollama response missing 'response' field")
            else:
                error_text = response.text
                print(f"Ollama error response: {error_text}")
                raise Exception(f"Ollama returned status {response.status_code}: {error_text}")
        
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error to Ollama: {e}")
            raise Exception("Ollama is not running. Please start Ollama or configure OpenAI API key.")
        except requests.exceptions.Timeout as e:
            print(f"Ollama request timed out: {e}")
            raise Exception("Ollama request timed out. The model might be loading or the prompt is too long.")
        except Exception as e:
            print(f"Ollama error: {e}")
            raise Exception(f"Ollama error: {e}")
    
    def _generate_fallback_answer(self, question: str, context: str) -> str:
        """
        Generate a simple answer by extracting information from context.
        Used as fallback when LLM is unavailable.
        """
        import re
        
        question_lower = question.lower()
        
        # Extract first 500 characters of context for answer
        context_preview = context[:500]
        
        # Try to extract specific information based on question keywords
        if "policy number" in question_lower:
            match = re.search(r'Policy\s*(?:No|Number|#)?[:\s]+([A-Z]{3}-\d{4}-[A-Z]{2}-\d{6})', context, re.IGNORECASE)
            if not match:
                match = re.search(r'Policy\s*(?:No|Number|#)?[:\s]+([A-Z0-9\-/]{10,})', context, re.IGNORECASE)
            if match:
                return f"Based on the documents, the policy number is {match.group(1)}."
        
        elif "claim amount" in question_lower or "claim" in question_lower and "amount" in question_lower:
            match = re.search(r'(?:Claim\s*Amount|Total\s*Claim|TOTAL\s*PAYABLE)[:\s]*₹?\s*([\d,]+(?:\.\d{2})?)', context, re.IGNORECASE)
            if match:
                return f"Based on the documents, the claim amount is ₹{match.group(1)}."
        
        elif "hospital" in question_lower:
            match = re.search(r'Hospital\s*(?:Name)?[:\s]*([A-Z][a-zA-Z\s&]+(?:Hospital|Medical|Clinic))', context, re.IGNORECASE)
            if match:
                return f"Based on the documents, the hospital mentioned is {match.group(1).strip()}."
        
        elif "diagnosis" in question_lower:
            match = re.search(r'Diagnosis[:\s]*([A-Z][a-zA-Z\s]+)', context, re.IGNORECASE)
            if match:
                return f"Based on the documents, the diagnosis is {match.group(1).strip()}."
        
        elif "sum assured" in question_lower or "coverage" in question_lower:
            match = re.search(r'Sum\s*Assured[:\s]*₹?\s*([\d,]+)', context, re.IGNORECASE)
            if match:
                return f"Based on the documents, the sum assured is ₹{match.group(1)}."
        
        elif "patient" in question_lower or "name" in question_lower:
            match = re.search(r'Patient\s*Name[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', context, re.IGNORECASE)
            if match:
                return f"Based on the documents, the patient name is {match.group(1).strip()}."
        
        elif "summarize" in question_lower or "summary" in question_lower:
            # Extract key information for summary
            policy_num = re.search(r'Policy\s*(?:No|Number)?[:\s]*([A-Z0-9\-/]+)', context, re.IGNORECASE)
            claim_amt = re.search(r'(?:Claim\s*Amount|TOTAL)[:\s]*₹?\s*([\d,]+)', context, re.IGNORECASE)
            hospital = re.search(r'Hospital[:\s]*([A-Z][a-zA-Z\s&]+Hospital)', context, re.IGNORECASE)
            
            summary_parts = []
            if policy_num:
                summary_parts.append(f"Policy Number: {policy_num.group(1)}")
            if claim_amt:
                summary_parts.append(f"Claim Amount: ₹{claim_amt.group(1)}")
            if hospital:
                summary_parts.append(f"Hospital: {hospital.group(1).strip()}")
            
            if summary_parts:
                return "Based on the documents, here's a summary:\n" + "\n".join(summary_parts)
        
        # Default: return first part of context
        return f"Based on the retrieved documents: {context_preview}...\n\n(Note: LLM is currently unavailable. This is a basic extraction from the documents. For better answers, please configure OpenAI API key or ensure Ollama is running with llama2 model loaded.)"

