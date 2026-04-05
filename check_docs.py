import httpx

resp = httpx.get('http://localhost:8000/api/documents')
docs = resp.json()

print(f"Documentos: {len(docs)}")
for d in docs:
    print(f"  ID: {d['id']}")
    print(f"  Filename: {d['filename']}")
    print(f"  Status: {d['status']}")
    print(f"  Size: {d.get('size', 0)} bytes")
    print()
