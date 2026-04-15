import { useState, useRef, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { useReviewStore } from '../store/reviewStore';
import { useReviewAPI } from '../hooks/useReviewAPI';
import { uploadFileToS3, fetchReviews, callAgentAPI } from '../services/s3';

export function ChatInterface() {
  const [inputMessage, setInputMessage] = useState('');
  const { 
    selectedFile, 
    messages, 
    isProcessing, 
    currentCampaignId,
    setSelectedFile,
    setCurrentCampaignId,
    uploadStatus,
    uploadedFileKey,
    uploadError,
    setUploadStatus,
    setUploadedFile,
    setUploadError,
    // Agent processing state
    agentStatus,
    agentError,
    setAgentStatus,
    setAgentError,
    setAgentResults,
    // Review fetch state
    reviewFetchStatus,
    waitCountdown,
    setReviewFetchStatus,
    setPersonaReviews,
    setWaitCountdown,
    clearCampaign
  } = useReviewStore();
  const { sendMessage } = useReviewAPI();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Handle agent API call after successful upload
  useEffect(() => {
    if (uploadStatus === 'success' && currentCampaignId && uploadedFileKey && agentStatus === 'idle') {
      handleAgentProcessing();
    }
  }, [uploadStatus, currentCampaignId, uploadedFileKey, agentStatus]);

  const handleAgentProcessing = async () => {
    if (!currentCampaignId || !uploadedFileKey) return;
    
    setAgentStatus('processing');
    const result = await callAgentAPI(currentCampaignId, uploadedFileKey);
    
    if (result.success) {
      setAgentResults(result.results || 'Processing completed');
      // Start the review fetch countdown after agent completes
      setReviewFetchStatus('waiting');
      setWaitCountdown(10);
    } else {
      setAgentError(result.error || 'Agent processing failed');
    }
  };

  // Countdown timer and polling for reviews
  useEffect(() => {
    if (reviewFetchStatus === 'waiting' && waitCountdown > 0) {
      const timer = setTimeout(() => {
        setWaitCountdown(waitCountdown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (reviewFetchStatus === 'waiting' && waitCountdown === 0) {
      // Countdown finished, start polling for reviews
      handleFetchReviews();
    }
  }, [reviewFetchStatus, waitCountdown, setWaitCountdown]);

  // Poll for reviews until we get results
  useEffect(() => {
    let pollInterval: ReturnType<typeof setInterval> | null = null;
    
    if (reviewFetchStatus === 'polling' && currentCampaignId) {
      pollInterval = setInterval(async () => {
        const result = await fetchReviews(currentCampaignId);
        if (result.success && result.reviews && result.reviews.length > 0) {
          setPersonaReviews(result.reviews);
          console.log(`Fetched ${result.reviews.length} persona reviews for campaign ${currentCampaignId}`);
        }
      }, 5000); // Poll every 5 seconds
    }
    
    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [reviewFetchStatus, currentCampaignId, setPersonaReviews]);

  const handleFetchReviews = async () => {
    setReviewFetchStatus('fetching');
    const result = await fetchReviews(currentCampaignId || undefined);
    
    if (result.success && result.reviews && result.reviews.length > 0) {
      setPersonaReviews(result.reviews);
      console.log(`Fetched ${result.reviews.length} persona reviews for campaign ${currentCampaignId}`);
    } else {
      // No reviews yet, start polling
      setReviewFetchStatus('polling');
    }
  };

  const onDrop = async (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setSelectedFile(file);
      
      // Clear previous campaign data
      clearCampaign();
      
      // Upload to S3 automatically
      setUploadStatus('uploading');
      setUploadError(null);
      
      const result = await uploadFileToS3(file);
      
      if (result.success && result.key && result.url && result.campaignId) {
        setUploadedFile(result.key, result.url);
        setCurrentCampaignId(result.campaignId);
        console.log('File uploaded to S3:', result.url, 'Campaign ID:', result.campaignId);
      } else {
        setUploadError(result.error || 'Upload failed');
        setUploadStatus('error');
      }
    }
  };

  const handleRemoveFile = () => {
    clearCampaign(); // Clear all campaign data instead of just upload data
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt']
    },
    maxSize: 10 * 1024 * 1024,
    multiple: false,
    disabled: uploadStatus === 'uploading'
  });

  const handleSendMessage = async () => {
    if (!inputMessage.trim() && !selectedFile) return;
    
    const message = inputMessage.trim() || 'Please review this document';
    await sendMessage(message, selectedFile || undefined);
    setInputMessage('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getUploadStatusDisplay = () => {
    switch (uploadStatus) {
      case 'uploading':
        return (
          <div className="flex items-center space-x-2 text-blue-600">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <span>Uploading to S3...</span>
          </div>
        );
      case 'success':
        return (
          <div className="text-green-600">
            <p className="font-medium">✓ Uploaded to S3</p>
            <p className="text-xs truncate max-w-xs" title={uploadedFileKey || ''}>
              {uploadedFileKey}
            </p>
            {agentStatus === 'processing' && (
              <p className="text-xs text-blue-600 mt-1">
                Processing with AI agents...
              </p>
            )}
            {agentStatus === 'success' && reviewFetchStatus === 'waiting' && (
              <p className="text-xs text-blue-600 mt-1">
                Fetching reviews in {waitCountdown}s...
              </p>
            )}
            {agentStatus === 'success' && reviewFetchStatus === 'fetching' && (
              <p className="text-xs text-blue-600 mt-1">
                Fetching persona reviews...
              </p>
            )}
            {agentStatus === 'success' && reviewFetchStatus === 'polling' && (
              <p className="text-xs text-blue-600 mt-1">
                <span className="animate-pulse">⏳</span> AI processing... checking for reviews
              </p>
            )}
            {agentStatus === 'success' && reviewFetchStatus === 'success' && (
              <p className="text-xs text-green-600 mt-1">
                ✓ Reviews loaded
              </p>
            )}
            {agentStatus === 'error' && (
              <p className="text-xs text-red-600 mt-1">
                ✗ Agent processing failed: {agentError}
              </p>
            )}
          </div>
        );
      case 'error':
        return (
          <div className="text-red-600">
            <p className="font-medium">✗ Upload failed</p>
            <p className="text-xs">{uploadError}</p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold text-gray-900">Campaign Review Chat</h2>
      </div>

      {/* File Upload Area */}
      <div className="p-4 border-b">
        <div {...getRootProps()} className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-primary bg-blue-50' : 
          uploadStatus === 'uploading' ? 'border-blue-400 bg-blue-50' :
          uploadStatus === 'success' ? 'border-green-400 bg-green-50' :
          uploadStatus === 'error' ? 'border-red-400 bg-red-50' :
          'border-gray-300 hover:border-primary'
        }`}>
          <input {...getInputProps()} />
          {selectedFile ? (
            <div className="text-sm">
              <p className="font-medium text-gray-900">{selectedFile.name}</p>
              <p className="text-xs text-gray-500 mt-1">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </p>
              <div className="mt-2">
                {getUploadStatusDisplay()}
              </div>
            </div>
          ) : (
            <div className="text-sm text-gray-600">
              <p>Drop a document here or click to select</p>
              <p className="text-xs mt-1">Supports PDF, DOCX, TXT (max 10MB)</p>
              <p className="text-xs mt-1 text-blue-600">Files are automatically uploaded to S3</p>
            </div>
          )}
        </div>
        {selectedFile && uploadStatus !== 'uploading' && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleRemoveFile();
            }}
            className="mt-2 text-sm text-red-600 hover:text-red-800"
          >
            Remove file
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <p>Upload a document and ask questions about it</p>
            <p className="text-sm mt-2">Or just type a message to start the conversation</p>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.sender === 'user' 
                  ? 'bg-primary text-white' 
                  : 'bg-gray-100 text-gray-900'
              }`}>
                <div className="whitespace-pre-wrap text-sm">{message.content}</div>
                <div className="text-xs mt-1 opacity-70">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
        {isProcessing && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                <span className="text-sm">Processing...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t">
        <div className="flex space-x-2">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about the document or request a review..."
            className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            rows={2}
            disabled={isProcessing}
          />
          <button
            onClick={handleSendMessage}
            disabled={isProcessing || (!inputMessage.trim() && !selectedFile)}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
