#!/usr/bin/env python3
"""Script para probar la conectividad con las APIs de Groq y Cohere"""

import sys
import time
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

def test_groq():
    """Prueba la API de Groq"""
    print("=" * 60)
    print("PROBANDO API DE GROQ")
    print("=" * 60)
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key.strip().lower() == "changeme":
        print("[ERROR] GROQ_API_KEY no esta configurado en .env")
        return False
    
    print(f"[OK] API Key encontrada: {api_key[:20]}...")
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "user", "content": "Di 'hola' en una palabra"}
        ],
        "temperature": 0.7,
        "max_tokens": 100,
    }
    
    print("\nEnviando solicitud a Groq...")
    start = time.time()
    
    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=60.0)
        elapsed = time.time() - start
        
        if response.is_success:
            data = response.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"[OK] Respuesta recibida en {elapsed:.2f}s")
            print(f"  Respuesta: {text[:100]}...")
            return True
        else:
            print(f"[ERROR] HTTP {response.status_code}")
            print(f"  Respuesta: {response.text[:500]}")
            return False
            
    except httpx.TimeoutException:
        print(f"[ERROR] TIMEOUT despues de 60 segundos")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_cohere():
    """Prueba la API de Cohere"""
    print("\n" + "=" * 60)
    print("PROBANDO API DE COHERE")
    print("=" * 60)
    
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key or api_key.strip().lower() == "changeme":
        print("[ERROR] COHERE_API_KEY no esta configurado en .env")
        return False
    
    print(f"[OK] API Key encontrada: {api_key[:20]}...")
    
    url = "https://api.cohere.com/v1/embed"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "embed-multilingual-v3.0",
        "texts": ["texto de prueba"],
        "truncate": "NONE",
        "input_type": "search_document"
    }
    
    print("\nEnviando solicitud a Cohere...")
    start = time.time()
    
    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=60.0)
        elapsed = time.time() - start
        
        if response.is_success:
            data = response.json()
            embeddings = data.get("embeddings", [])
            print(f"[OK] Respuesta recibida en {elapsed:.2f}s")
            print(f"  Embeddings generados: {len(embeddings)}")
            if embeddings:
                print(f"  Dimension del vector: {len(embeddings[0])}")
            return True
        else:
            print(f"[ERROR] HTTP {response.status_code}")
            print(f"  Respuesta: {response.text[:500]}")
            return False
            
    except httpx.TimeoutException:
        print(f"[ERROR] TIMEOUT despues de 60 segundos")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def main():
    print("\n>>> DIAGNOSTICO DE CONECTIVIDAD CON APIS <<<\n")
    
    groq_ok = test_groq()
    cohere_ok = test_cohere()
    
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Groq API: {'[OK]' if groq_ok else '[FALLO]'}")
    print(f"Cohere API: {'[OK]' if cohere_ok else '[FALLO]'}")
    
    if groq_ok and cohere_ok:
        print("\n[OK] Todas las APIs estan funcionando correctamente")
        print("\nSi sigues teniendo problemas de lentitud, revisa:")
        print("  1. La cantidad de documentos en la base de datos")
        print("  2. Los logs de la aplicacion (usa logging.DEBUG)")
        print("  3. El rendimiento de tu conexion a internet")
        return 0
    else:
        print("\n[ERROR] Hay problemas con las APIs")
        print("\nPosibles soluciones:")
        print("  1. Verifica que las API keys sean correctas en el archivo .env")
        print("  2. Verifica tu conexion a internet")
        print("  3. Revisa si las APIs estan caidas")
        if not groq_ok:
            print("\nPara obtener API key de Groq (gratis):")
            print("  - Ve a: https://console.groq.com/keys")
            print("  - Crea una cuenta y genera una API key")
            print("  - Copia la key en .env como GROQ_API_KEY=tu_key_aqui")
        return 1


if __name__ == "__main__":
    sys.exit(main())
