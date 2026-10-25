import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  AlertCircle,
  ShieldCheck,
  ArrowRight,
  Lock,
  Eye,
  EyeOff,
  KeyRound,
  X,
  HelpCircle,
} from 'lucide-react';

export default function FileUpload({ onUploadSuccess, loading, setLoading, error, setError }) {
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  // Password modal states
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);
  const [passwordValue, setPasswordValue] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [passwordError, setPasswordError] = useState(null);
  const [pendingFile, setPendingFile] = useState(null);
  const [isConnectionError, setIsConnectionError] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = async (file, password = null) => {
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'csv', 'xlsx', 'xls'].includes(ext)) {
      setError(`Unsupported file type (.${ext}). Please upload a PDF, CSV, or Excel file.`);
      return;
    }

    setLoading(true);
    setError(null);
    setIsConnectionError(false);
    if (!password) {
      setPasswordError(null);
    }

    const formData = new FormData();
    formData.append('file', file);
    if (password) {
      formData.append('password', password);
    }

    const apiBase =
      import.meta.env.VITE_API_URL !== undefined
        ? import.meta.env.VITE_API_URL
        : window.location.port === '5173'
        ? 'http://localhost:8000'
        : '';

    try {
      const response = await fetch(`${apiBase}/api/parse`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));

        // Handle password protected PDFs
        if (
          response.status === 401 &&
          (errorData.error === 'PASSWORD_REQUIRED' || errorData.error === 'INVALID_PASSWORD')
        ) {
          setPendingFile(file);
          setPasswordModalOpen(true);
          if (errorData.error === 'INVALID_PASSWORD') {
            setPasswordError('Incorrect password. Please verify and try again.');
          } else {
            setPasswordError(null);
          }
          return;
        }

        throw new Error(errorData.detail || 'Failed to parse bank statement');
      }

      const data = await response.json();
      setPasswordModalOpen(false);
      setPasswordValue('');
      setPasswordError(null);
      setPendingFile(null);
      onUploadSuccess(data, file.name);
    } catch (err) {
      const isNetwork =
        err.name === 'TypeError' || (err.message && err.message.toLowerCase().includes('fetch'));
      setIsConnectionError(isNetwork);
      setError(err.message || 'Error connecting to local backend at http://localhost:8000');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordSubmit = (e) => {
    e.preventDefault();
    if (!passwordValue) {
      setPasswordError('Please enter a password');
      return;
    }
    if (pendingFile) {
      processFile(pendingFile, passwordValue);
    }
  };

  const closePasswordModal = () => {
    setPasswordModalOpen(false);
    setPasswordValue('');
    setPasswordError(null);
    setPendingFile(null);
  };

  return (
    <div className="w-full max-w-2xl mx-auto py-12 px-4">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-sky-100 text-sky-700 mb-4 shadow-sm">
          <FileText className="w-8 h-8" />
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Bank Statement Summarizer
        </h1>
        <p className="mt-2 text-slate-600 max-w-md mx-auto">
          Extract account details, view interactive charts, filter and group all your transactions completely offline.
        </p>
      </div>

      {error && !passwordModalOpen && (
        <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-3 shadow-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-600" />
          <div className="text-sm">
            <span className="font-semibold">Error:</span> {error}
            {isConnectionError && (
              <div className="mt-1 text-xs text-rose-600">
                Ensure your Python backend is running locally at{' '}
                <code className="bg-rose-100 px-1 py-0.5 rounded font-mono">http://localhost:8000</code>
              </div>
            )}
          </div>
        </div>
      )}

      <div
        className={`relative border-2 border-dashed rounded-3xl p-8 sm:p-12 text-center transition-all cursor-pointer bg-white ${
          dragActive
            ? 'border-sky-500 bg-sky-50/50 scale-[1.01] shadow-lg ring-4 ring-sky-100'
            : 'border-slate-300 hover:border-sky-400 hover:shadow-md'
        } ${loading && !passwordModalOpen ? 'opacity-60 pointer-events-none' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.csv,.xlsx,.xls"
          className="hidden"
          onChange={handleChange}
        />

        {loading && !passwordModalOpen ? (
          <div className="py-6 flex flex-col items-center">
            <div className="w-12 h-12 border-4 border-sky-600 border-t-transparent rounded-full animate-spin mb-4" />
            <h3 className="text-lg font-semibold text-slate-800">Processing statement...</h3>
            <p className="text-xs text-slate-500 mt-1">Extracting headers, balances, and categorizing transactions</p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <div className="w-14 h-14 rounded-full bg-sky-50 text-sky-600 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <UploadCloud className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-slate-800">
              Drop your bank statement here, or <span className="text-sky-600 hover:underline">browse</span>
            </h3>
            <p className="text-xs text-slate-500 mt-2 font-medium">
              Supports PDF (including password protected), CSV, XLSX, XLS (Up to 20MB)
            </p>

            <button
              type="button"
              className="mt-6 inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-sky-600 text-white font-medium hover:bg-sky-700 transition-colors shadow-sm text-sm"
            >
              Choose File <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      <div className="mt-8 flex items-center justify-center gap-2 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200/80 rounded-xl py-2.5 px-4">
        <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
        <span>100% Offline & Private — Your statement is processed locally and never leaves this machine.</span>
      </div>

      {/* Password Unlock Modal */}
      {passwordModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full p-6 sm:p-8 border border-slate-200 relative animate-in fade-in zoom-in-95 duration-200">
            <button
              onClick={closePasswordModal}
              className="absolute top-5 right-5 p-1.5 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition-colors"
              title="Close"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center shadow-sm">
                <Lock className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-900">Protected Statement</h3>
                <p className="text-xs text-slate-500 truncate max-w-[240px]">
                  {pendingFile?.name || 'Bank Statement PDF'}
                </p>
              </div>
            </div>

            <p className="text-xs text-slate-600 mb-4 leading-relaxed">
              This statement is encrypted by your bank. Enter your password to decrypt and summarize it completely offline.
            </p>

            {passwordError && (
              <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-rose-600" />
                <span>{passwordError}</span>
              </div>
            )}

            <form onSubmit={handlePasswordSubmit}>
              <div className="relative mb-4">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <KeyRound className="w-4 h-4" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={passwordValue}
                  onChange={(e) => setPasswordValue(e.target.value)}
                  placeholder="Enter PDF password"
                  autoFocus
                  className="w-full pl-10 pr-11 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white text-slate-800 placeholder-slate-400"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>

              {/* Bank Password Tips */}
              <div className="mb-6 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600">
                <div className="flex items-center gap-1.5 font-semibold text-slate-700 mb-1.5">
                  <HelpCircle className="w-3.5 h-3.5 text-sky-600" />
                  <span>Common Bank Password Formats:</span>
                </div>
                <ul className="space-y-1 text-[11px] list-disc list-inside text-slate-500 leading-tight">
                  <li>
                    <strong className="text-slate-700">SBI:</strong> Date of birth (DDMMYYYY) or registered mobile number.
                  </li>
                  <li>
                    <strong className="text-slate-700">HDFC:</strong> Customer ID or PAN (UPPERCASE).
                  </li>
                  <li>
                    <strong className="text-slate-700">ICICI / Axis:</strong> Date of birth (DDMMYYYY) or mobile number.
                  </li>
                  <li>
                    <strong className="text-slate-700">Others:</strong> Last 4 digits of A/C or DOB (DDMMYYYY).
                  </li>
                </ul>
              </div>

              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={closePasswordModal}
                  className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 text-xs font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || !passwordValue}
                  className="px-5 py-2 rounded-xl bg-sky-600 text-white text-xs font-semibold hover:bg-sky-700 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {loading ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Decrypting...</span>
                    </>
                  ) : (
                    <span>Unlock & Summarize</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
