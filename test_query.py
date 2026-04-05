#!/usr/bin/env python3
"""Script para probar queries manualmente"""

import httpx
import json
import time

API_BASE = "http://localhost:8000/api"

def test_query():
    print("=" * 60)
    print("PROBANDO QUERY AL API")
    print("=" * 60)
    
    question = "que dice el documento?"
    top_k = 5
    
    print(f"\nPregunta: {question}")
    print(f"Top-K: {top_k}")
    print("\nEnviando query...")
    
    start = time.time()
    
    try:
        resp = httpx.post(
            f"{API_BASE}/query",
            json={"q": question, "k": top_k},
            timeout=300.0,
        )
        
        elapsed = time.time() - start
        print(f"\n[OK] Respuesta recibida en {elapsed:.2f}s")
        print(f"Status code: {resp.status_code}")
        
        if resp.is_success:
            data = resp.json()
            print("\n" + "=" * 60)
            print("RESPUESTA:")
            print("=" * 60)
            print(data.get("answer", ""))
            print("\n" + "=" * 60)
            print(f"Referencias: {len(data.get('refs', []))}")
            print("=" * 60)
        else:
            print(f"\n[ERROR] HTTP {resp.status_code}")
            print(f"Respuesta: {resp.text}")
            
    except httpx.TimeoutException:
        elapsed = time.time() - start
        print(f"\n[ERROR] TIMEOUT despues de {elapsed:.2f}s")
    except Exception as e:
        elapsed = time.time() - start
        print(f"\n[ERROR] {e}")
        print(f"Tiempo transcurrido: {elapsed:.2f}s")

if __name__ == "__main__":
    test_query()
