import requests
import json

BASE_URL = "http://localhost:8000"

def test_step_by_step():
    # Create test CSV
    csv_content = "ID,Name,Email\n1,John,john@test.com\n2,Jane,jane@test.com"
    with open('test-2.csv', 'w') as f:
        f.write(csv_content)
    
    # Step 1: Upload file
    print("Step 1: Upload file")
    with open('test-2.csv', 'rb') as f:
        response = requests.post(f"{BASE_URL}/upload/", files={'file': f})
    
    print(f"Upload Status: {response.status_code}")
    print(f"Upload Response: {response.text}")
    
    if response.status_code != 200:
        print("❌ Upload failed, stopping here")
        return
    
    result = response.json()
    file_id = result['file_id']
    print(f"✅ Upload successful! File ID: {file_id}")
    
    # # Step 2: Preview file
    print(f"\nStep 2: Preview file {file_id}")
    response = requests.get(f"{BASE_URL}/preview/{file_id}/")
    
    print(f"Preview Status: {response.status_code}")
    print(f"Preview Response: {response.text}")
    
    if response.status_code != 200:
        print("❌ Preview failed - check Django console for error")
        print("Common issues:")
        print("- File path doesn't exist")
        print("- Pandas can't read the file")
        print("- Database record not found")
        return
    
    print("✅ Preview successful!")
    
    # Step 3: Process file (without LLM call for now)
    print(f"\nStep 3: Process file {file_id}")
    data = {
        "file_id": file_id,
        "text": "Find emails and turn them to the number 1000",
        
    }
    
    response = requests.post(f"{BASE_URL}/process/{file_id}/", 
                           json=data,
                           headers={'Content-Type': 'application/json'})
    
    print(f"Process Status: {response.status_code}")
    print(f"Process Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ All endpoints working!")
    else:
        print("❌ Process failed - check Django console")

if __name__ == "__main__":
    test_step_by_step()