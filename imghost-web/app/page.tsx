"use client";

import React, { useState, useEffect } from "react";
import { Upload, Trash2, Copy, Check, AlertCircle, Loader2, Globe } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const API_BASE = process.env.NEXT_PUBLIC_API_URL;

interface UploadResponse {
  url: string;
  delete_token: string;
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [health, setHealth] = useState<"ok" | "error" | "loading">("loading");

  // Health Check
  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((res) => (res.ok ? setHealth("ok") : setHealth("error")))
      .catch(() => setHealth("error"));
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setError(null);
      setFile(selected);
    }
  };

  const onUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Upload failed");
      }

      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const onDelete = async () => {
    if (!result) return;
    try {
      const res = await fetch(`${API_BASE}/image/${result.delete_token}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setResult(null);
        setFile(null);
      } else {
        throw new Error("Delete failed");
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const copyToClipboard = () => {
    if (result) {
      navigator.clipboard.writeText(result.url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6 space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold tracking-tighter neon-glow">
          IMG<span className="text-accent">HOST</span>
        </h1>
        <div className="flex items-center justify-center space-x-2 text-[10px] uppercase tracking-widest text-zinc-500">
          <Globe className={`w-3 h-3 ${health === "ok" ? "text-green-500" : "text-accent"}`} />
          <span>System {health === "ok" ? "Operational" : "Degraded"}</span>
        </div>
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md bg-card border border-border rounded-2xl p-8 shadow-neon"
      >
        <AnimatePresence mode="wait">
          {!result ? (
            <motion.div key="upload" exit={{ opacity: 0, scale: 0.95 }}>
              <label className="group relative flex flex-col items-center justify-center w-full h-64 border-2 border-dashed border-zinc-800 rounded-xl cursor-pointer hover:border-accent transition-colors">
                {file ? (
                  <div className="text-center p-4">
                    <p className="text-accent font-medium truncate max-w-[250px]">{file.name}</p>
                    <p className="text-zinc-500 text-xs">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center space-y-3">
                    <Upload className="w-8 h-8 text-zinc-600 group-hover:text-accent transition-colors" />
                    <p className="text-zinc-400 text-sm">Drop image or click to browse</p>
                  </div>
                )}
                <input type="file" className="hidden" onChange={handleFileChange} accept="image/*" />
              </label>

              {error && (
                <div className="mt-4 flex items-center space-x-2 text-accent text-xs bg-accent/10 p-3 rounded-lg border border-accent/20">
                  <AlertCircle className="w-4 h-4" />
                  <span>{error}</span>
                </div>
              )}

              <button
                disabled={!file || uploading}
                onClick={onUpload}
                className="w-full mt-6 bg-accent hover:bg-red-700 disabled:bg-zinc-800 disabled:text-zinc-500 text-white font-bold py-3 rounded-xl transition-all flex items-center justify-center space-x-2 shadow-lg"
              >
                {uploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <span>INITIALIZE UPLOAD</span>}
              </button>
            </motion.div>
          ) : (
            <motion.div key="result" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="space-y-6">
              <div className="relative aspect-video rounded-lg overflow-hidden border border-zinc-800 bg-zinc-900">
                <img src={result.url} alt="Uploaded" className="object-contain w-full h-full" />
              </div>

              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <input
                    readOnly
                    value={result.url}
                    className="flex-1 bg-black border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-400 focus:outline-none"
                  />
                  <button onClick={copyToClipboard} className="p-2 hover:text-accent transition-colors">
                    {copied ? <Check className="w-5 h-5 text-green-500" /> : <Copy className="w-5 h-5" />}
                  </button>
                </div>

                <div className="bg-accent/5 p-4 rounded-lg border border-accent/10">
                  <p className="text-[10px] text-zinc-500 uppercase tracking-tighter mb-1">Private Delete Token</p>
                  <code className="text-xs text-accent font-mono break-all">{result.delete_token}</code>
                </div>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={onDelete}
                  className="flex-1 border border-accent/20 hover:bg-accent hover:text-white text-accent py-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center space-x-2"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>DELETE IMAGE</span>
                </button>
                <button
                  onClick={() => {setResult(null); setFile(null);}}
                  className="flex-1 bg-zinc-900 hover:bg-zinc-800 text-white py-3 rounded-xl text-xs font-bold transition-all"
                >
                  NEW UPLOAD
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      <footer className="text-[10px] text-zinc-700 uppercase tracking-[0.2em]">
        SPEEEEDDDDDDDDDD HAWKKKSS
      </footer>
    </main>
  );
}