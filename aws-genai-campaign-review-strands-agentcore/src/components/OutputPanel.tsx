import { useState } from 'react';
import { useReviewStore } from '../store/reviewStore';

export function OutputPanel() {
  const { 
    selectedFile, 
    personaReviews, 
    reviewFetchStatus, 
    reviewFetchError,
    waitCountdown 
  } = useReviewStore();
  
  const [activeTab, setActiveTab] = useState(0);

  // Render markdown content (simple renderer)
  const renderMarkdown = (content: string) => {
    // Simple markdown to HTML conversion
    const lines = content.split('\n');
    const elements: JSX.Element[] = [];
    
    lines.forEach((line, index) => {
      // Headers
      if (line.startsWith('### ')) {
        elements.push(
          <h3 key={index} className="text-lg font-semibold text-gray-800 mt-4 mb-2">
            {line.replace('### ', '')}
          </h3>
        );
      } else if (line.startsWith('## ')) {
        elements.push(
          <h2 key={index} className="text-xl font-bold text-gray-900 mt-6 mb-3">
            {line.replace('## ', '')}
          </h2>
        );
      } else if (line.startsWith('# ')) {
        elements.push(
          <h1 key={index} className="text-2xl font-bold text-gray-900 mt-6 mb-4">
            {line.replace('# ', '')}
          </h1>
        );
      }
      // Bold text
      else if (line.includes('**')) {
        const parts = line.split(/\*\*(.*?)\*\*/g);
        elements.push(
          <p key={index} className="text-gray-700 mb-2">
            {parts.map((part, i) => 
              i % 2 === 1 ? <strong key={i}>{part}</strong> : part
            )}
          </p>
        );
      }
      // List items
      else if (line.startsWith('- ') || line.startsWith('* ')) {
        elements.push(
          <li key={index} className="text-gray-700 ml-4 mb-1">
            {line.replace(/^[-*] /, '')}
          </li>
        );
      }
      // Numbered list
      else if (/^\d+\. /.test(line)) {
        elements.push(
          <li key={index} className="text-gray-700 ml-4 mb-1 list-decimal">
            {line.replace(/^\d+\. /, '')}
          </li>
        );
      }
      // Empty line
      else if (line.trim() === '') {
        elements.push(<div key={index} className="h-2" />);
      }
      // Regular paragraph
      else {
        elements.push(
          <p key={index} className="text-gray-700 mb-2">
            {line}
          </p>
        );
      }
    });
    
    return elements;
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold text-gray-900">Review Output</h2>
        {selectedFile && (
          <p className="text-sm text-gray-600 mt-1">Document: {selectedFile.name}</p>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Loading / Waiting States */}
        {reviewFetchStatus === 'waiting' && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-pulse text-6xl mb-4">⏳</div>
              <p className="text-gray-600 text-lg">Processing document...</p>
              <p className="text-blue-600 font-semibold mt-2">
                Fetching reviews in {waitCountdown} seconds
              </p>
            </div>
          </div>
        )}

        {reviewFetchStatus === 'fetching' && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-gray-600">Fetching persona reviews from S3...</p>
            </div>
          </div>
        )}

        {reviewFetchStatus === 'error' && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-red-600">
              <div className="text-4xl mb-4">❌</div>
              <p className="font-medium">Failed to fetch reviews</p>
              <p className="text-sm mt-2">{reviewFetchError}</p>
            </div>
          </div>
        )}

        {/* Reviews Display */}
        {reviewFetchStatus === 'success' && personaReviews.length > 0 && (
          <>
            {/* Tabs */}
            <div className="border-b">
              <div className="flex overflow-x-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
                {personaReviews.map((review, index) => (
                  <button
                    key={review.key}
                    onClick={() => setActiveTab(index)}
                    className={`px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors flex-shrink-0 ${
                      activeTab === index
                        ? 'border-blue-500 text-blue-600 bg-blue-50'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    {review.persona}
                  </button>
                ))}
              </div>
            </div>

            {/* Tab Content */}
            <div className="overflow-y-auto p-4 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100" style={{height: 'calc(100vh - 300px)'}}>
              {personaReviews[activeTab] && (
                <div className="prose max-w-none">
                  <div className="mb-4 pb-4 border-b">
                    <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                      {personaReviews[activeTab].fileName}
                    </span>
                  </div>
                  {renderMarkdown(personaReviews[activeTab].content)}
                </div>
              )}
            </div>
          </>
        )}

        {/* No Reviews Yet */}
        {(reviewFetchStatus === 'idle' || (reviewFetchStatus === 'success' && personaReviews.length === 0)) && (
          <div className="flex items-center justify-center h-full text-center">
            <div>
              <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Review Yet</h3>
              <p className="text-gray-600">
                Upload a document to see the AI review results here.
              </p>
              <p className="text-sm text-gray-500 mt-2">
                Reviews will automatically load after upload.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
