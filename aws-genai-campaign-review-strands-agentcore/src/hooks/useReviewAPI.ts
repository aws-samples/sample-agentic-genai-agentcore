import { submitCampaignReview } from '../services/api';
import { useReviewStore } from '../store/reviewStore';

export const useReviewAPI = () => {
  const { addMessage, setProcessing, setError } = useReviewStore();

  const sendMessage = async (message: string, file?: File) => {
    setProcessing(true);
    setError(null);
    
    // Add user message
    addMessage({ content: message, sender: 'user' });
    
    try {
      let campaignData = message;
      
      // If file is provided, include its content
      if (file) {
        const fileContent = await file.text();
        campaignData = `Document: ${file.name}\n\nContent:\n${fileContent}\n\nUser Query: ${message}`;
      }
      
      const results = await submitCampaignReview(campaignData);
      
      // Format the response for display
      let responseContent = '';
      if (results.persona_review) {
        responseContent += `**Persona Review:**\nScore: ${results.persona_review.content_resonance_score || 'N/A'}/10\n\n`;
      }
      if (results.compliance_validation) {
        responseContent += `**Compliance Status:** ${results.compliance_validation.compliance_status || 'N/A'}\n`;
        responseContent += `**Compliance Score:** ${results.compliance_validation.overall_compliance_score || 0}/100\n\n`;
      }
      if (results.summary) {
        responseContent += `**Summary:**\n${results.summary}`;
      }
      
      addMessage({ content: responseContent || 'Review completed successfully.', sender: 'assistant' });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      addMessage({ content: `Error: ${errorMessage}`, sender: 'assistant' });
      setError(errorMessage);
    } finally {
      setProcessing(false);
    }
  };

  return { sendMessage };
};
