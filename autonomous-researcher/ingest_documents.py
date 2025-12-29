"""
Script to ingest documents from data/raw/ into the vector database.
Run this script after adding new documents to data/raw/
"""
import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.rag import rag_service
from app.services.vector_db import vector_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    print("=" * 60)
    print("Document Ingestion Script")
    print("=" * 60)
    print()
    
    # Check if data/raw exists
    raw_dir = os.path.join("data", "raw")
    if not os.path.exists(raw_dir):
        print(f"❌ Directory '{raw_dir}' does not exist!")
        print(f"   Creating it now...")
        os.makedirs(raw_dir, exist_ok=True)
        print(f"   ✓ Created '{raw_dir}'")
        print()
        print("   Please add your .txt, .md, or .pdf files to this directory")
        print("   and run this script again.")
        return
    
    # List files in data/raw
    files = []
    for ext in ['.txt', '.md', '.pdf']:
        files.extend([f for f in os.listdir(raw_dir) if f.lower().endswith(ext)])
    
    if not files:
        print(f"📁 No documents found in '{raw_dir}'")
        print()
        print("   Supported file types: .txt, .md, .pdf")
        print(f"   Please add files to: {os.path.abspath(raw_dir)}")
        return
    
    print(f"📄 Found {len(files)} document(s) to ingest:")
    for f in files:
        print(f"   - {f}")
    print()
    
    print("🔄 Starting ingestion process...")
    print("   This may take a few minutes depending on document size...")
    print()
    
    try:
        # Ingest documents
        await rag_service.ingest_data_folder()
        
        # Save the vector database
        vector_db.save()
        
        print()
        print("=" * 60)
        print("✅ Ingestion completed successfully!")
        print("=" * 60)
        print()
        print(f"   Documents indexed: {len(files)}")
        print(f"   Vector database saved to: data/vector_store/")
        print()
        print("   Your documents are now ready to be searched during research!")
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ Error during ingestion:")
        print("=" * 60)
        print(f"   {str(e)}")
        print()
        logger.exception("Ingestion failed")

if __name__ == "__main__":
    asyncio.run(main())

