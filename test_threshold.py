import httpx

resp = httpx.post(
    'http://localhost:8000/api/query',
    json={"q": "¿Qué temas se cubren?", "k": 5, "threshold": 0.3},
    timeout=300.0
)

print(f"Status: {resp.status_code}")
if resp.is_success:
    data = resp.json()
    print(f"\nRespuesta: {data['answer'][:200]}...")
    print(f"\nReferencias encontradas: {len(data.get('refs', []))}")
    for ref in data.get('refs', [])[:3]:
        print(f"  - Score: {ref['score']:.4f}, Chunk: {ref['text'][:100]}...")
else:
    print(f"Error: {resp.text}")
