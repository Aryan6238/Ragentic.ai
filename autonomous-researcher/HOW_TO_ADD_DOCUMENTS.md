# How to Add Custom Documents for Research

This guide explains exactly how to add your own documents so the research system can use them when generating reports.

## 📁 Step 1: Locate the Data Directory

The documents folder is located at:
```
autonomous-researcher/data/raw/
```

**Full path on your system:**
```
C:\Users\Aryan\Downloads\google_antigravity\agent\autonomous-researcher\data\raw\
```

## 📄 Step 2: Supported File Types

You can add documents in these formats:
- **.txt** - Plain text files
- **.md** - Markdown files  
- **.pdf** - PDF files (basic support)

## 📝 Step 3: Add Your Documents

### Option A: Using File Explorer (Windows)
1. Open File Explorer
2. Navigate to: `C:\Users\Aryan\Downloads\google_antigravity\agent\autonomous-researcher\data\raw\`
3. Copy and paste your `.txt`, `.md`, or `.pdf` files into this folder

### Option B: Using Command Line
```powershell
# Copy a file to the data/raw directory
Copy-Item "C:\path\to\your\document.txt" "C:\Users\Aryan\Downloads\google_antigravity\agent\autonomous-researcher\data\raw\"
```

## 🔄 Step 4: Ingest the Documents

After adding files, you need to run the ingestion script to index them:

### Using Command Line:
```powershell
cd C:\Users\Aryan\Downloads\google_antigravity\agent\autonomous-researcher
python ingest_documents.py
```

This script will:
1. Find all documents in `data/raw/`
2. Split them into chunks
3. Create embeddings (vector representations)
4. Store them in the vector database
5. Make them searchable for research

## ✅ Step 5: Verify Ingestion

The script will show you:
- How many documents were found
- The ingestion progress
- Success confirmation

Example output:
```
📄 Found 3 document(s) to ingest:
   - research_paper.txt
   - company_report.pdf
   - notes.md

🔄 Starting ingestion process...
✅ Ingestion completed successfully!
```

## 🚀 Step 6: Use in Research

Once ingested, when you run a research topic:
1. The system will automatically search your documents
2. Relevant sections will be included in the research
3. The report will reference information from your documents

## 📋 Example Workflow

1. **Add documents:**
   ```
   data/raw/
   ├── quantum_computing_paper.txt
   ├── ai_research_notes.md
   └── industry_report.pdf
   ```

2. **Run ingestion:**
   ```powershell
   python ingest_documents.py
   ```

3. **Start research:**
   - Go to http://localhost:8000
   - Enter a topic related to your documents
   - The system will use your documents in the research!

## ⚠️ Important Notes

- **File Encoding:** Make sure text files are in UTF-8 encoding
- **File Size:** Very large files may take longer to process
- **PDF Support:** Basic PDF support - complex PDFs may need conversion to .txt first
- **Re-ingestion:** If you add new files, run the ingestion script again
- **Updates:** If you modify existing files, delete the old vector store and re-ingest:
  ```powershell
  Remove-Item data\vector_store\* -Force
  python ingest_documents.py
  ```

## 🎯 Best Practices

1. **Organize by topic:** Group related documents together
2. **Use descriptive filenames:** Makes it easier to identify sources
3. **Keep documents focused:** Shorter, focused documents work better
4. **Regular updates:** Re-ingest when you add new documents

## ❓ Troubleshooting

**No documents found?**
- Check that files are in `data/raw/` (not `data/`)
- Verify file extensions are `.txt`, `.md`, or `.pdf`
- Check file permissions

**Ingestion fails?**
- Check your API key is set in `.env`
- Verify documents are readable (not corrupted)
- Check the error message for specific issues

**Documents not appearing in research?**
- Make sure ingestion completed successfully
- Verify the research topic is related to your documents
- Check that the vector database was saved

