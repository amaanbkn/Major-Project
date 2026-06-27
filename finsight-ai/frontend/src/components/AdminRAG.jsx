import React, { useState, useEffect } from 'react';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { Loader2, Database, Upload, FileText, CheckCircle, AlertTriangle } from 'lucide-react';
import { getRAGStats, ingestRAG } from '../api';

export default function AdminRAG() {
  const [stats, setStats] = useState({ document_count: 0, collection_name: '' });
  const [loadingStats, setLoadingStats] = useState(true);
  
  // Tabs
  const [activeTab, setActiveTab] = useState('file'); // 'file' or 'text'
  
  // Ingest state
  const [ingesting, setIngesting] = useState(false);
  const [result, setResult] = useState(null);
  
  // File upload fields
  const [file, setFile] = useState(null);
  const [fileDocId, setFileDocId] = useState('');
  
  // Text upload fields
  const [rawText, setRawText] = useState('');
  const [textDocId, setTextDocId] = useState('');

  const fetchStats = async () => {
    try {
      setLoadingStats(true);
      const res = await getRAGStats();
      setStats(res);
    } catch (err) {
      console.error("Failed to load RAG stats", err);
    } finally {
      setLoadingStats(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      // Auto fill docId from filename without extension
      const name = selectedFile.name.substring(0, selectedFile.name.lastIndexOf('.')) || selectedFile.name;
      setFileDocId(name.replace(/[^a-zA-Z0-9_-]/g, '_'));
    }
  };

  const handleFileSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setIngesting(true);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);
    if (fileDocId) {
      formData.append('doc_id', fileDocId);
    }

    try {
      const res = await ingestRAG(formData);
      setResult({
        success: true,
        message: `Successfully ingested file "${file.name}". ${res.chunks || 0} chunks added.`,
      });
      setFile(null);
      setFileDocId('');
      fetchStats();
    } catch (err) {
      setResult({
        success: false,
        message: err.message || "Failed to ingest file.",
      });
    } finally {
      setIngesting(false);
    }
  };

  const handleTextSubmit = async (e) => {
    e.preventDefault();
    if (!rawText.trim() || !textDocId.trim()) return;

    setIngesting(true);
    setResult(null);

    const formData = new FormData();
    formData.append('text', rawText);
    formData.append('doc_id', textDocId.replace(/[^a-zA-Z0-9_-]/g, '_'));

    try {
      const res = await ingestRAG(formData);
      setResult({
        success: true,
        message: `Successfully ingested text "${textDocId}". ${res.chunks || 0} chunks added.`,
      });
      setRawText('');
      setTextDocId('');
      fetchStats();
    } catch (err) {
      setResult({
        success: false,
        message: err.message || "Failed to ingest text.",
      });
    } finally {
      setIngesting(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 pb-10">
      <div>
        <h1 className="text-[28px] font-bold text-[#111111] leading-tight">RAG Knowledge Ingestion</h1>
        <p className="text-[#6B7280] text-sm mt-1">Upload financial documents and PDFs to populate the ChromaDB vector store</p>
      </div>

      {/* Stats Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Card className="px-5 py-5 border-[#E5E7EB] flex items-center justify-between">
          <div>
            <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-[#6B7280]">
              Total Document Chunks
            </span>
            <p className="text-[28px] font-bold tabular-nums text-[#111111] mt-1 leading-none">
              {loadingStats ? (
                <Loader2 className="w-6 h-6 animate-spin text-[#6B7280]" />
              ) : (
                stats.document_count || 0
              )}
            </p>
          </div>
          <div className="p-3 bg-[#F3F4F6] rounded-full">
            <Database className="w-6 h-6 text-[#111111]" />
          </div>
        </Card>

        <Card className="px-5 py-5 border-[#E5E7EB] flex items-center justify-between">
          <div>
            <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-[#6B7280]">
              Vector Collection
            </span>
            <p className="text-md font-semibold text-[#111111] mt-1.5 leading-none">
              {loadingStats ? "Loading..." : stats.collection_name || "finsight_corpus"}
            </p>
          </div>
          <Badge variant="success">ChromaDB</Badge>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-[#F3F4F6] rounded-[12px] w-fit">
        <button
          onClick={() => { setActiveTab('file'); setResult(null); }}
          className={`flex items-center gap-2 px-4 py-2 rounded-[8px] text-sm font-medium transition-all cursor-pointer ${
            activeTab === 'file'
              ? 'bg-white text-[#111111] shadow-[0_1px_3px_rgba(0,0,0,0.06)]'
              : 'text-[#6B7280] hover:text-[#111111]'
          }`}
        >
          <Upload className="w-4 h-4" />
          File Upload
        </button>
        <button
          onClick={() => { setActiveTab('text'); setResult(null); }}
          className={`flex items-center gap-2 px-4 py-2 rounded-[8px] text-sm font-medium transition-all cursor-pointer ${
            activeTab === 'text'
              ? 'bg-white text-[#111111] shadow-[0_1px_3px_rgba(0,0,0,0.06)]'
              : 'text-[#6B7280] hover:text-[#111111]'
          }`}
        >
          <FileText className="w-4 h-4" />
          Raw Text Ingestion
        </button>
      </div>

      {/* Forms */}
      <Card className="p-6">
        {result && (
          <div className={`mb-6 p-4 rounded-[12px] flex items-start gap-3 border ${
            result.success ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'
          }`}>
            {result.success ? (
              <CheckCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
            ) : (
              <AlertTriangle className="w-5 h-5 mt-0.5 flex-shrink-0" />
            )}
            <div>
              <p className="text-sm font-semibold">{result.success ? 'Success' : 'Error'}</p>
              <p className="text-xs mt-1 leading-relaxed">{result.message}</p>
            </div>
          </div>
        )}

        {activeTab === 'file' ? (
          <form onSubmit={handleFileSubmit} className="space-y-5">
            <div>
              <label className="block text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6B7280] mb-2">
                Document File (.pdf, .txt, .md)
              </label>
              <div className="border-2 border-dashed border-[#E5E7EB] hover:border-[#111111] rounded-[16px] p-8 text-center cursor-pointer transition-colors relative bg-white">
                <input
                  type="file"
                  accept=".pdf,.txt,.md"
                  onChange={handleFileChange}
                  className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                  required
                />
                <div className="flex flex-col items-center gap-3">
                  <Upload className="w-10 h-10 text-[#6B7280]" />
                  {file ? (
                    <div>
                      <p className="text-sm font-semibold text-[#111111]">{file.name}</p>
                      <p className="text-xs text-[#6B7280] mt-1">{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                  ) : (
                    <div>
                      <p className="text-sm font-semibold text-[#111111]">Drag and drop your file here, or click to browse</p>
                      <p className="text-xs text-[#6B7280] mt-1">Supports PDF, TXT and Markdown files (Max 15MB)</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6B7280] mb-2">
                Document ID / Friendly Name (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. quarterly_report_2026"
                value={fileDocId}
                onChange={(e) => setFileDocId(e.target.value)}
                className="w-full px-4 py-2.5 rounded-[12px] border border-[#E5E7EB] bg-white text-sm text-[#111111] focus:outline-none focus:border-[#111111] transition-colors"
              />
            </div>

            <div className="flex justify-end pt-3">
              <Button type="submit" variant="primary" disabled={!file || ingesting} className="w-full md:w-auto">
                {ingesting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Ingesting to Vector Store...
                  </>
                ) : (
                  'Ingest Document'
                )}
              </Button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleTextSubmit} className="space-y-5">
            <div>
              <label className="block text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6B7280] mb-2">
                Document ID / Title
              </label>
              <input
                type="text"
                placeholder="e.g. sebi_circular_june_2026"
                value={textDocId}
                onChange={(e) => setTextDocId(e.target.value)}
                required
                className="w-full px-4 py-2.5 rounded-[12px] border border-[#E5E7EB] bg-white text-sm text-[#111111] focus:outline-none focus:border-[#111111] transition-colors"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold tracking-[0.08em] uppercase text-[#6B7280] mb-2">
                Plain Text Content
              </label>
              <textarea
                placeholder="Paste the financial document content here..."
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                required
                rows={10}
                className="w-full px-4 py-3 rounded-[16px] border border-[#E5E7EB] bg-white text-sm text-[#111111] focus:outline-none focus:border-[#111111] transition-colors resize-y min-h-[150px]"
              />
            </div>

            <div className="flex justify-end pt-3">
              <Button type="submit" variant="primary" disabled={!rawText.trim() || !textDocId.trim() || ingesting} className="w-full md:w-auto">
                {ingesting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Ingesting Text Block...
                  </>
                ) : (
                  'Ingest Text Block'
                )}
              </Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
}
