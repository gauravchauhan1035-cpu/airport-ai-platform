import requests
import time
import os
import fitz  # PyMuPDF

BASE_URL = "http://localhost:8000"
ADMIN_CREDS = {"username": "admin", "password": "Admin123!"}

def create_pdf(filename, text):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    doc.save(filename)
    doc.close()

def run_test():
    print("1. Logging in as Admin...")
    r = requests.post(f"{BASE_URL}/login", json=ADMIN_CREDS)
    r.raise_for_status()
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("2. Creating PDF v1...")
    create_pdf("sop_v1.pdf", "This is the OLD emergency SOP. Evacuate to Zone A.")
    
    print("3. Uploading PDF v1...")
    with open("sop_v1.pdf", "rb") as f:
        r = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files={"file": ("Emergency_SOP.pdf", f, "application/pdf")})
    r.raise_for_status()
    doc_v1 = r.json()
    doc_id_v1 = doc_v1["id"]
    print(f"Uploaded: ID={doc_id_v1}, Version={doc_v1['version']}, Status={doc_v1['status']}")
    
    print("4. Testing Semantic Search (should find Zone A)...")
    time.sleep(1) # wait for index save
    r = requests.post(f"{BASE_URL}/documents/search", headers=headers, json={"query": "where to evacuate?", "top_k": 3})
    results = r.json()["results"]
    print(f"Search results: {len(results)}")
    for res in results:
        print(f" - {res['content']} (Score: {res['score']})")
        
    print("5. Creating PDF v2...")
    create_pdf("sop_v2.pdf", "This is the NEW emergency SOP. Evacuate to Zone B immediately.")
    
    print("6. Replacing Document (v1 -> v2)...")
    with open("sop_v2.pdf", "rb") as f:
        r = requests.put(f"{BASE_URL}/documents/{doc_id_v1}/replace", headers=headers, files={"file": ("Emergency_SOP.pdf", f, "application/pdf")})
    r.raise_for_status()
    doc_v2 = r.json()
    doc_id_v2 = doc_v2["id"]
    print(f"Replaced: ID={doc_id_v2}, Version={doc_v2['version']}, Status={doc_v2['status']}")
    
    print("7. Testing Semantic Search (should find Zone B, NOT Zone A)...")
    time.sleep(1)
    r = requests.post(f"{BASE_URL}/documents/search", headers=headers, json={"query": "where to evacuate?", "top_k": 3})
    results = r.json()["results"]
    print(f"Search results: {len(results)}")
    found_v1 = False
    for res in results:
        print(f" - {res['content']} (Score: {res['score']})")
        if "Zone A" in res['content']:
            found_v1 = True
            
    if found_v1:
        print("FAIL: Found old version in search results!")
    else:
        print("PASS: Old version successfully removed from RAG search!")
        
    print("8. Archiving Document v2...")
    r = requests.post(f"{BASE_URL}/documents/{doc_id_v2}/archive", headers=headers)
    r.raise_for_status()
    print("Archived successfully.")
    
    print("9. Testing Semantic Search (should be empty)...")
    time.sleep(1)
    r = requests.post(f"{BASE_URL}/documents/search", headers=headers, json={"query": "where to evacuate?", "top_k": 3})
    results = r.json()["results"]
    print(f"Search results after archive: {len(results)}")
    if len(results) == 0:
        print("PASS: Archived document is not searchable.")
    else:
        print("FAIL: Archived document is still searchable!")
        
    # Cleanup
    os.remove("sop_v1.pdf")
    os.remove("sop_v2.pdf")

if __name__ == "__main__":
    run_test()
