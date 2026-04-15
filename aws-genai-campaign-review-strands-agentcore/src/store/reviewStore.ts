import { create } from 'zustand';
import { PersonaReview } from '../services/s3';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

type UploadStatus = 'idle' | 'uploading' | 'success' | 'error';
type ReviewFetchStatus = 'idle' | 'waiting' | 'fetching' | 'polling' | 'success' | 'error';
type AgentStatus = 'idle' | 'processing' | 'success' | 'error';

interface ReviewState {
  selectedFile: File | null;
  messages: Message[];
  isProcessing: boolean;
  error: string | null;
  
  // Campaign tracking
  currentCampaignId: string | null;
  
  // S3 Upload state
  uploadStatus: UploadStatus;
  uploadedFileKey: string | null;
  uploadedFileUrl: string | null;
  uploadError: string | null;
  
  // Agent processing state
  agentStatus: AgentStatus;
  agentError: string | null;
  agentResults: string | null;
  
  // Persona Reviews state
  personaReviews: PersonaReview[];
  reviewFetchStatus: ReviewFetchStatus;
  reviewFetchError: string | null;
  waitCountdown: number;
  
  setSelectedFile: (file: File | null) => void;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  setProcessing: (processing: boolean) => void;
  setError: (error: string | null) => void;
  clearMessages: () => void;
  
  // Campaign actions
  setCurrentCampaignId: (campaignId: string | null) => void;
  
  // S3 Upload actions
  setUploadStatus: (status: UploadStatus) => void;
  setUploadedFile: (key: string | null, url: string | null) => void;
  setUploadError: (error: string | null) => void;
  resetUpload: () => void;
  
  // Agent processing actions
  setAgentStatus: (status: AgentStatus) => void;
  setAgentError: (error: string | null) => void;
  setAgentResults: (results: string | null) => void;
  
  // Persona Reviews actions
  setPersonaReviews: (reviews: PersonaReview[]) => void;
  setReviewFetchStatus: (status: ReviewFetchStatus) => void;
  setReviewFetchError: (error: string | null) => void;
  setWaitCountdown: (seconds: number) => void;
  clearReviews: () => void;
  clearCampaign: () => void;
}

export const useReviewStore = create<ReviewState>((set) => ({
  selectedFile: null,
  messages: [],
  isProcessing: false,
  error: null,
  
  // Campaign initial state
  currentCampaignId: null,
  
  // S3 Upload initial state
  uploadStatus: 'idle',
  uploadedFileKey: null,
  uploadedFileUrl: null,
  uploadError: null,
  
  // Agent processing initial state
  agentStatus: 'idle',
  agentError: null,
  agentResults: null,
  
  // Persona Reviews initial state
  personaReviews: [],
  reviewFetchStatus: 'idle',
  reviewFetchError: null,
  waitCountdown: 0,
  
  setSelectedFile: (file) => set({ selectedFile: file }),
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, {
      ...message,
      id: Date.now().toString(),
      timestamp: new Date()
    }]
  })),
  setProcessing: (processing) => set({ isProcessing: processing }),
  setError: (error) => set({ error }),
  clearMessages: () => set({ messages: [] }),
  
  // Campaign actions
  setCurrentCampaignId: (campaignId) => set({ currentCampaignId: campaignId }),
  
  // S3 Upload actions
  setUploadStatus: (status) => set({ uploadStatus: status }),
  setUploadedFile: (key, url) => set({ 
    uploadedFileKey: key, 
    uploadedFileUrl: url,
    uploadStatus: key ? 'success' : 'idle'
  }),
  setUploadError: (error) => set({ 
    uploadError: error,
    uploadStatus: error ? 'error' : 'idle'
  }),
  resetUpload: () => set({
    uploadStatus: 'idle',
    uploadedFileKey: null,
    uploadedFileUrl: null,
    uploadError: null,
    selectedFile: null,
    currentCampaignId: null,
    agentStatus: 'idle',
    agentError: null,
    agentResults: null
  }),
  
  // Agent processing actions
  setAgentStatus: (status) => set({ agentStatus: status }),
  setAgentError: (error) => set({ 
    agentError: error,
    agentStatus: error ? 'error' : 'idle'
  }),
  setAgentResults: (results) => set({ 
    agentResults: results,
    agentStatus: results ? 'success' : 'idle'
  }),
  
  // Persona Reviews actions
  setPersonaReviews: (reviews) => set({ 
    personaReviews: reviews,
    reviewFetchStatus: 'success'
  }),
  setReviewFetchStatus: (status) => set({ reviewFetchStatus: status }),
  setReviewFetchError: (error) => set({ 
    reviewFetchError: error,
    reviewFetchStatus: error ? 'error' : 'idle'
  }),
  setWaitCountdown: (seconds) => set({ waitCountdown: seconds }),
  clearReviews: () => set({
    personaReviews: [],
    reviewFetchStatus: 'idle',
    reviewFetchError: null,
    waitCountdown: 0
  }),
  
  // Clear all campaign data (for starting fresh)
  clearCampaign: () => set({
    selectedFile: null,
    currentCampaignId: null,
    uploadStatus: 'idle',
    uploadedFileKey: null,
    uploadedFileUrl: null,
    uploadError: null,
    agentStatus: 'idle',
    agentError: null,
    agentResults: null,
    personaReviews: [],
    reviewFetchStatus: 'idle',
    reviewFetchError: null,
    waitCountdown: 0
  }),
}));
