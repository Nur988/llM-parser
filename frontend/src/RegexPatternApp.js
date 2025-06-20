import React, { useState } from 'react';
import { Upload, FileText, Wand2, Download, AlertCircle, CheckCircle, Loader } from 'lucide-react';

const RegexPatternApp = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [file, setFile] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [naturalLanguageInput, setNaturalLanguageInput] = useState('');
  const [processedResult, setProcessedResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const API_BASE = 'http://localhost:8000';

  // Step 1: File Upload
  const handleFileUpload = async (event) => {
    const selectedFile = event.target.files[0];
    if (!selectedFile) return;

    if (!selectedFile.name.endsWith('.csv') && !selectedFile.name.endsWith('.xlsx')) {
      setError('Please upload a CSV or Excel file');
      return;
    }

    setFile(selectedFile);
    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch(`${API_BASE}/upload/`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      
      if (result.success) {
        setFileId(result.file_id);
        await loadPreview(result.file_id);
        setCurrentStep(2);
      } else {
        setError('Failed to upload file');
      }
    } catch (err) {
      setError('Upload failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Load file preview
  const loadPreview = async (id) => {
    try {
      const response = await fetch(`${API_BASE}/preview/${id}/`);
      const result = await response.json();
      
      if (result.success) {
        setPreviewData(result);
      }
    } catch (err) {
      setError('Failed to load preview');
    }
  };

  // Step 2: Process with natural language
  const handleProcess = async () => {
    if (!naturalLanguageInput.trim()) {
      setError('Please enter instructions');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/process/${fileId}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: naturalLanguageInput
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        setProcessedResult(result);
        setCurrentStep(3);
      } else {
        setError('Processing failed');
      }
    } catch (err) {
      setError('Processing failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const resetApp = () => {
    setCurrentStep(1);
    setFile(null);
    setFileId(null);
    setPreviewData(null);
    setNaturalLanguageInput('');
    setProcessedResult(null);
    setError('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-600 rounded-lg">
              <Wand2 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Regex Pattern Matcher</h1>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="flex items-center justify-center mb-12">
          <div className="flex items-center space-x-8">
            {[
              { num: 1, label: 'Upload File', icon: Upload },
              { num: 2, label: 'Process Data', icon: Wand2 },
              { num: 3, label: 'Results', icon: CheckCircle }
            ].map(({ num, label, icon: Icon }) => (
              <div key={num} className="flex items-center">
                <div className={`flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all duration-300 ${
                  currentStep >= num 
                    ? 'bg-blue-600 border-blue-600 text-white' 
                    : 'bg-white border-gray-300 text-gray-400'
                }`}>
                  {currentStep > num ? <CheckCircle className="w-6 h-6" /> : <Icon className="w-6 h-6" />}
                </div>
                <span className={`ml-3 font-medium ${currentStep >= num ? 'text-blue-600' : 'text-gray-400'}`}>
                  {label}
                </span>
                {num < 3 && (
                  <div className={`w-16 h-0.5 ml-6 ${currentStep > num ? 'bg-blue-600' : 'bg-gray-300'}`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {/* Step 1: File Upload */}
        {currentStep === 1 && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <Upload className="w-8 h-8 text-blue-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Upload Your Data File</h2>
              <p className="text-gray-600 mb-8">Choose a CSV or Excel file to process</p>
              
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 hover:border-blue-400 transition-colors">
                <input
                  type="file"
                  id="fileInput"
                  className="hidden"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileUpload}
                  disabled={loading}
                />
                <label htmlFor="fileInput" className="cursor-pointer">
                  {loading ? (
                    <Loader className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
                  ) : (
                    <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  )}
                  <p className="text-lg font-medium text-gray-700">
                    {loading ? 'Uploading...' : 'Click to upload or drag and drop'}
                  </p>
                  <p className="text-gray-500">CSV, XLSX files only</p>
                </label>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Data Processing */}
        {currentStep === 2 && previewData && (
          <div className="space-y-6">
            {/* File Preview */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Data Preview</h3>
              <div className="text-sm text-gray-600 mb-4">
                {previewData.total_rows} rows • {previewData.columns.length} columns
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-gray-50">
                      {previewData.columns.map((col) => (
                        <th key={col} className="border border-gray-200 px-4 py-2 text-left font-medium text-gray-700">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.preview_data.slice(0, 5).map((row, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        {previewData.columns.map((col) => (
                          <td key={col} className="border border-gray-200 px-4 py-2 text-gray-600">
                            {String(row[col] || '')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Natural Language Input */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Describe What You Want to Do</h3>
              <p className="text-gray-600 mb-6">
                Use natural language to describe the pattern you want to find and replace
              </p>
              
              <div className="space-y-4">
                <textarea
                  value={naturalLanguageInput}
                  onChange={(e) => setNaturalLanguageInput(e.target.value)}
                  placeholder="e.g., Find email addresses and replace them with HIDDEN&#10;e.g., Find names and replace them with PERSON&#10;e.g., Find phone numbers and replace with XXX-XXX-XXXX"
                  className="w-full h-32 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                />
                
                <div className="flex space-x-4">
                  <button
                    onClick={handleProcess}
                    disabled={loading || !naturalLanguageInput.trim()}
                    className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                  >
                    {loading ? (
                      <Loader className="w-5 h-5 animate-spin" />
                    ) : (
                      <Wand2 className="w-5 h-5" />
                    )}
                    <span>{loading ? 'Processing...' : 'Process Data'}</span>
                  </button>
                  
                  <button
                    onClick={resetApp}
                    className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50"
                  >
                    Start Over
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Results */}
        {currentStep === 3 && processedResult && (
          <div className="space-y-6">
            {/* Processing Summary */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center space-x-3 mb-6">
                <CheckCircle className="w-8 h-8 text-green-600" />
                <h3 className="text-xl font-bold text-gray-900">Processing Complete!</h3>
              </div>
              <div className="text-sm text-gray-600">
                Columns processed: {processedResult.columns_processed.join(', ') || 'None'}
              </div>
            </div>

            {/* Processed Data Preview */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Updated Data</h3>
              
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-gray-50">
                      {Object.keys(processedResult.processed_data[0] || {}).map((col) => (
                        <th key={col} className="border border-gray-200 px-4 py-2 text-left font-medium text-gray-700">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {processedResult.processed_data.slice(0, 10).map((row, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        {Object.keys(row).map((col) => (
                          <td key={col} className="border border-gray-200 px-4 py-2 text-gray-600">
                            {String(row[col] || '')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Actions */}
            <div className="flex space-x-4">
              <button
                onClick={resetApp}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 flex items-center space-x-2"
              >
                <Upload className="w-5 h-5" />
                <span>Process Another File</span>
              </button>
              
              <button
                onClick={() => setCurrentStep(2)}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50"
              >
                Try Different Pattern
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RegexPatternApp;