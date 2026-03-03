import { useDropzone } from 'react-dropzone';
import { useReviewStore } from '../store/reviewStore';
import { uploadFileToS3, callAgentAPI, fetchReviews } from '../services/s3';
import { useEffect, useRef } from 'react';

export function FileUpload() {
  const { 
    selectedFile, 
    setSelectedFile,
    setCurrentCampaignId,
    currentCampaignId,
    uploadStatus,
    uploadError,
    setUploadStatus,
    setUploadedFile,
    setUploadError,
    agentStatus,
    agentError,
    setAgentStatus,
    setAgentError,
    setAgentResults,
    setPersonaReviews,
    reviewFetchStatus,
    setReviewFetchStatus,
    clearCampaign
  } = useReviewStore();
  
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Poll for reviews when in polling state
  useEffect(() => {
    if (reviewFetchStatus === 'polling' && currentCampaignId) {
      pollIntervalRef.current = setInterval(async () => {
        const result = await fetchReviews(currentCampaignId);
        console.log('Polling for reviews:', result);
        if (result.success && result.reviews && result.reviews.length > 0) {
          console.log(`Found ${result.reviews.length} reviews, stopping poll`);
          setPersonaReviews(result.reviews);
          setReviewFetchStatus('success');
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        } else {
          console.log('No reviews yet, continuing to poll...');
        }
      }, 5000);
    }
    
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [reviewFetchStatus, currentCampaignId, setPersonaReviews, setReviewFetchStatus]);

  const handleFileUpload = async (files: File[]) => {
    if (files.length === 0) return;
    
    const file = files[0];
    setSelectedFile(file);
    
    try {
      setUploadStatus('uploading');
      setUploadError(null);
      
      // Generate campaign ID
      const campaignId = `campaign-${Date.now()}`;
      setCurrentCampaignId(campaignId);
      
      // Upload to S3
      const uploadResult = await uploadFileToS3(file, campaignId);
      
      if (!uploadResult.success || !uploadResult.key) {
        throw new Error(uploadResult.error || 'Upload failed');
      }
      
      setUploadedFile(uploadResult.key, null);
      setUploadStatus('success');
      
      // Start agent processing
      setAgentStatus('processing');
      setAgentError(null);
      
      const agentResponse = await callAgentAPI(campaignId, uploadResult.key);
      
      if (!agentResponse.success) {
        throw new Error(agentResponse.error || 'Agent processing failed');
      }
      
      setAgentResults(JSON.stringify(agentResponse));
      setAgentStatus('success');
      
      // Fetch the generated reviews - start polling since async processing
      setReviewFetchStatus('fetching');
      const reviewsResult = await fetchReviews(campaignId);
      console.log('Initial review fetch result:', reviewsResult);
      
      if (reviewsResult.success && reviewsResult.reviews && reviewsResult.reviews.length > 0) {
        console.log(`Found ${reviewsResult.reviews.length} reviews immediately`);
        setPersonaReviews(reviewsResult.reviews);
        setReviewFetchStatus('success');
      } else {
        console.log('No reviews yet, starting polling...');
        // No reviews yet, start polling
        setReviewFetchStatus('polling');
      }
      
    } catch (error) {
      console.error('Upload/processing error:', error);
      setUploadError(error instanceof Error ? error.message : 'Upload failed');
      setUploadStatus('error');
      setAgentError(error instanceof Error ? error.message : 'Processing failed');
      setAgentStatus('error');
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleFileUpload,
    accept: {
      'text/markdown': ['.md'],
      'text/plain': ['.txt']
    },
    multiple: false
  });

  const handleRemoveFile = () => {
    clearCampaign();
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border h-full flex flex-col">
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold text-gray-900">Upload Campaign Document</h2>
      </div>
      
      <div className="flex-1 p-4">
        {!selectedFile ? (
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors h-full flex flex-col justify-center ${
              isDragActive 
                ? 'border-blue-400 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input {...getInputProps()} />
            <div className="space-y-4">
              <div className="text-4xl text-gray-400">📄</div>
              <div>
                <p className="text-lg font-medium text-gray-900">
                  {isDragActive ? 'Drop your file here' : 'Drag & drop your campaign document'}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  or click to browse (Markdown or Text files)
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">{selectedFile.name}</p>
                  <p className="text-sm text-gray-500">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <button
                  onClick={handleRemoveFile}
                  className="text-red-600 hover:text-red-800 text-sm font-medium"
                >
                  Remove
                </button>
              </div>
            </div>

            {/* Status Display */}
            <div className="space-y-2">
              {uploadStatus === 'uploading' && (
                <div className="flex items-center space-x-2 text-blue-600">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span>Uploading...</span>
                </div>
              )}
              
              {uploadStatus === 'success' && (
                <div className="flex items-center space-x-2 text-green-600">
                  <span>✓</span>
                  <span>Upload completed</span>
                </div>
              )}
              
              {agentStatus === 'processing' && (
                <div className="flex items-center space-x-2 text-blue-600">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span>Processing with AI agents...</span>
                </div>
              )}
              
              {agentStatus === 'success' && reviewFetchStatus !== 'success' && (
                <div className="flex items-center space-x-2 text-blue-600">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span>AI processing... waiting for reviews</span>
                </div>
              )}
              
              {agentStatus === 'success' && reviewFetchStatus === 'success' && (
                <div className="flex items-center space-x-2 text-green-600">
                  <span>✓</span>
                  <span>AI processing completed</span>
                </div>
              )}
              
              {(uploadError || agentError) && (
                <div className="text-red-600 text-sm">
                  Error: {uploadError || agentError}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
