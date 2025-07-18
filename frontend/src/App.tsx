import React, { useState, useCallback } from "react";
import PDFViewer from './components/PDFViewer';
import AudienceSelector from './components/AudienceSelector';
import type { AudienceType } from './components/AudienceSelector';
import HighlightableText from './components/HighlightableText';

// Placeholder component for the PDF viewer area - Keep for future use
// @ts-ignore
const PdfViewerPlaceholder: React.FC = () => (
    <div className="w-full h-96 bg-gray-100 flex items-center justify-center text-gray-500 italic rounded-md border border-dashed border-gray-300">
        PDF Preview Area (Implementation Needed)
        {/* TODO: Integrate a PDF rendering library like PDF.js here. */}
        {/* You would fetch the PDF content (or a URL) and render it in this div. */}
    </div>
);

// Helper component for the collapsible sidebar - Now displays interactive document cards
const Sidebar: React.FC<{ files: string[], onSummarize: (filename: string) => void, summaries: Record<string, string>, isCollapsed: boolean, onFileSelect: (filename: string) => void, selectedFiles: string[], onRemoveFile: (filename: string) => void, onToggleCollapse: () => void } > = ({ files, onSummarize, summaries, isCollapsed, onFileSelect, selectedFiles, onRemoveFile, onToggleCollapse }) => (
  <aside className={`flex-shrink-0 ${isCollapsed ? 'w-16' : 'w-80'} bg-gray-800 text-gray-200 h-full transition-width duration-300 overflow-y-auto flex flex-col border-r border-blue-900`}>
    <div className="p-4 border-b border-blue-900 flex items-center justify-between">
      {!isCollapsed && <h2 className="text-xl font-semibold text-blue-300">Documents</h2>}
      {/* Toggle Button */}
       <button 
          onClick={onToggleCollapse} 
          className="p-1 rounded hover:bg-gray-700 text-gray-400 hover:text-white"
          title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
       >
           {/* Simple text toggle, replace with icon later */}
           {isCollapsed ? '>' : '<'}
       </button>
    </div>
    {/* Search and Filter Placeholder */}
    {/* {!isCollapsed && <input type="text" placeholder="Search..." className="m-4 p-2 rounded bg-gray-700 text-gray-200 border border-gray-600 focus:outline-none focus:border-blue-500" />} */}

    <ul className="flex-1 overflow-y-auto space-y-3 p-4">
      {files.length === 0 ? (
        <li className={`text-gray-400 italic ${isCollapsed ? 'hidden' : ''}`}>No documents yet.</li>
      ) : (
        files.map((file, idx) => {
          const isSelected = selectedFiles.includes(file);
          // Determine summary status: Summarizing, Summarized, or Ready
          const summaryStatus = summaries[file] 
              ? (summaries[file] === "Summarizing..." ? "Summarizing..." : "Summarized") 
              : "Ready";

          // Extract original filename by removing timestamp prefix (YYYYMMDD_HHMMSS_)
          const originalFilename = file.replace(/^\d{8}_\d{6}_/, '');

          // Parse date from filename format YYYYMMDD_HHMMSS
          const filenameParts = file.split('_');
          let uploadDate = 'Unknown Date';
          if (filenameParts.length >= 2) {
              const datePart = filenameParts[0]; // YYYYMMDD
              const year = datePart.substring(0, 4);
              const month = datePart.substring(4, 6);
              const day = datePart.substring(6, 8);
              // Create a date string like YYYY-MM-DD to parse
              const dateString = `${year}-${month}-${day}`;
              const dateObj = new Date(dateString);
              if (!isNaN(dateObj.getTime())) {
                 uploadDate = dateObj.toLocaleDateString(); // Format as local date string
              }
          }

          return (
            <li key={idx} 
                className={`cursor-pointer p-3 rounded-lg shadow-md transition-colors duration-200 ${isSelected ? 'bg-blue-700 border border-blue-500' : 'bg-gray-700 hover:bg-gray-600 border border-transparent'}`}
                onClick={() => onFileSelect(file)} // Toggle selection for the file
            >
              <div className="flex justify-between items-center mb-2">
                {/* Suggestion: Add a document icon */} 
                <span className={`flex-1 truncate font-medium ${isSelected ? 'text-white' : 'text-blue-400'} ${isCollapsed ? 'hidden' : 'mr-2'}`}>{originalFilename}</span> {/* Use original filename here */}
                {!isCollapsed && (
                   <span className={`flex-shrink-0 text-xs font-semibold px-2 py-1 rounded-full
                     ${summaryStatus === "Summarized" ? 'bg-green-600 text-white'
                       : summaryStatus === "Summarizing..." ? 'bg-yellow-600 text-white'
                       : 'bg-gray-500 text-white'}`}>
                     {summaryStatus}
                   </span>
                )}
              </div>
               {!isCollapsed && (
                  <div className={`flex justify-between items-center text-xs ${isSelected ? 'text-blue-200' : 'text-gray-400'}`}>
                     <span>Uploaded: {uploadDate}</span>
                     {summaryStatus === "Ready" && (
                         <button onClick={(e) => { e.stopPropagation(); onSummarize(file); }} className="ml-2 text-blue-300 hover:text-blue-100">Summarize</button>
                     )}
                     {/* Ensure red text for remove and add hover effect */}
                     <button onClick={(e) => { e.stopPropagation(); onRemoveFile(file); }} className="ml-2 text-red-400 hover:text-red-600 font-medium">Remove</button>
                  </div>
               )}
              {/* Summary preview (optional, could add a small snippet here if not collapsed) */}
              {/* {summaries[file] && !isCollapsed && summaryStatus === "Summarized" && <p className="text-xs text-gray-400 mt-2 line-clamp-2">{summaries[file]}</p>} */}
            </li>
          );
        })
      )}
    </ul>
    {/* + Upload Floating Button (adjust positioning as needed) */}
    {/* This could trigger a modal or scroll to the upload section */}
    {/* {!isCollapsed && (
        <div className="p-4">
            <button className="w-full bg-blue-600 text-white py-2 rounded-full flex items-center justify-center shadow-lg hover:bg-blue-700 transition-colors duration-200">
                 + Upload
            </button>
        </div>
    )} */}
     {/* Sizing Adjust: Adding a draggable sizing handle is a complex feature and is not implemented in this step. */}
  </aside>
);

// Helper component for PDF upload area with drag-and-drop
const PDFUpload: React.FC<{ onUpload: (file: File) => void, uploading: boolean }> = ({ onUpload, uploading }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFileName(file.name);
      onUpload(file);
      e.target.value = ''; // Clear the input after selection
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        const file = e.dataTransfer.files[0];
        if (file.type === 'application/pdf') {
            setSelectedFileName(file.name);
            onUpload(file);
        } else {
            alert("Only PDF files are supported."); // Suggestion: Use a better notification
        }
    }
  }, [onUpload]);

  return (
    // Card container
    <div className="bg-white rounded-lg shadow-lg p-6 mb-8 border border-blue-200">
      <h3 className="text-xl font-semibold mb-4 text-blue-800">Upload Document</h3>
      
      <div 
        className={`border-2 rounded-lg p-8 text-center transition-all duration-200 
          ${isDragOver 
            ? 'border-blue-500 bg-blue-50 border-solid' 
            : 'border-gray-300 bg-gray-50 border-solid hover:border-blue-400 hover:bg-gray-100'}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <label className="block text-sm text-gray-600 cursor-pointer">
          {selectedFileName ? (
            <div className="flex items-center justify-center">
               {uploading ? (
                 <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                 <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                 <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l2-2.647z"></path>
                 </svg>
               ) : (
                 <svg className="w-6 h-6 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
               )}
              <span>{selectedFileName}</span>
            </div>
          ) : (
            <>Drag and drop your PDF here, or <span className="text-blue-600 underline">browse files</span></>
          )}
          <input type="file" accept="application/pdf" onChange={handleFileChange} disabled={uploading} className="hidden" />
        </label>
      </div>
    </div>
  );
};

// Helper component for AI Summary display
const SummaryDisplay: React.FC<{ summary: string | null, filename: string }> = ({ summary, filename }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [selectedSentence, setSelectedSentence] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<any>(null);
  const [sourceEvidence, setSourceEvidence] = useState<any>(null);
  const [loadingExplanation, setLoadingExplanation] = useState(false);
  const [loadingSourceEvidence, setLoadingSourceEvidence] = useState(false);
  const [showExplanationResult, setShowExplanationResult] = useState(false);
  const [showSourceEvidenceResult, setShowSourceEvidenceResult] = useState(false);

  // Handle question-based highlighting (improved functionality)
  const handleTextHighlight = async (selectedText: string, context: string, question: string) => {
    setSelectedSentence(selectedText);
    setLoadingExplanation(true);
    setShowExplanationResult(true);
    setShowSourceEvidenceResult(false); // Hide source evidence when showing explanation
    
    try {
      const response = await fetch(`${BACKEND_URL}/explain-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          filename, 
          selected_text: selectedText,
          context,
          question,
          audience_type: 'patient' // Default to patient for explanations
        })
      });
      
      if (!response.ok) throw new Error('Failed to fetch explanation');
      const data = await response.json();
      setExplanation({ ...data, userQuestion: question }); // Store the user's question
    } catch (error) {
      console.error('Error fetching explanation:', error);
      setExplanation({ 
        explanation: 'Failed to get explanation. Please try again.',
        userQuestion: question 
      });
    } finally {
      setLoadingExplanation(false);
    }
  };

  // Handle source evidence highlighting (new functionality)
  const handleSourceEvidence = async (selectedText: string) => {
    setSelectedSentence(selectedText);
    setLoadingSourceEvidence(true);
    setShowSourceEvidenceResult(true);
    setShowExplanationResult(false); // Hide explanation when showing source evidence
    
    try {
      const response = await fetch(`${BACKEND_URL}/explanation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          filename, 
          sentence: selectedText
        })
      });
      
      if (!response.ok) throw new Error('Failed to fetch source evidence');
      const data = await response.json();
      setSourceEvidence(data);
    } catch (error) {
      console.error('Error fetching source evidence:', error);
      setSourceEvidence({ 
        source_chunks: [], 
        confidence: 0,
        error: 'Failed to get source evidence. Please try again.' 
      });
    } finally {
      setLoadingSourceEvidence(false);
    }
  };







  // Show a loading indicator if summary is in progress
  if (summary === "Summarizing...") {
      return (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-8 border border-blue-200 flex items-center justify-center">
               <svg className="animate-spin h-8 w-8 text-blue-600 mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                 <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                 <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l2-2.647z"></path>
               </svg>
               <span className="text-lg text-blue-800">Generating Summary...</span>
          </div>
      );
  }

  if (!summary) {
    return null; // Don't display card if no summary
  }
  
  const handleCopyToClipboard = () => {
      navigator.clipboard.writeText(summary).then(() => {
          alert('Summary copied to clipboard!'); // Suggestion: Use a better toast/notification
      }).catch(err => {
          console.error('Failed to copy summary: ', err);
      });
  };

  return (
     // Card container
    <div className="bg-white rounded-lg shadow-lg p-6 mb-8 border border-blue-200">
       <div className="flex justify-between items-center mb-4 cursor-pointer" onClick={() => setIsCollapsed(!isCollapsed)}>
         <h3 className="text-xl font-semibold text-blue-800">AI Summary</h3>
         {/* Suggestion: Add collapse/expand icon */}
          <button className="text-gray-500 hover:text-gray-700">
              {isCollapsed ? '+' : '-'}
          </button>
       </div>
      
       {!isCollapsed && (
           <div className="text-gray-700">
             <HighlightableText 
               text={summary} 
               onHighlight={handleTextHighlight}
               onSourceEvidence={handleSourceEvidence}
               className="leading-relaxed"
             />
           </div>
       )}

      {/* Source Evidence Result */}
      {showSourceEvidenceResult && (
        <div className="mt-4 p-4 bg-green-50 rounded-lg border border-green-200">
          <div className="flex justify-between items-start mb-3">
            <h4 className="text-sm font-semibold text-green-800">Source Evidence</h4>
            <button
              onClick={() => {
                setShowSourceEvidenceResult(false);
                setSourceEvidence(null);
              }}
              className="text-green-600 hover:text-green-800 text-sm"
            >
              Close
            </button>
          </div>
          {loadingSourceEvidence ? (
            <div className="text-sm text-green-700">Finding source evidence...</div>
          ) : sourceEvidence?.error ? (
            <div className="text-sm text-red-600">{sourceEvidence.error}</div>
          ) : (
            <>
              {/* Selected Text Display */}
              <div className="mb-3 p-2 bg-white rounded border border-green-200">
                <div className="text-xs font-medium text-green-600 mb-1">Highlighted Text:</div>
                <div className="text-sm text-gray-700 italic">
                  "{selectedSentence && selectedSentence.length > 200 
                    ? `${selectedSentence.substring(0, 200)}...` 
                    : selectedSentence}"
                </div>
              </div>
              
              {/* Confidence Score with Tooltip */}
              <div className="mb-3 flex items-center gap-2">
                <span className="text-sm font-medium text-green-800">
                  Overall Confidence: {((sourceEvidence?.confidence || 0) * 100).toFixed(2)}%
                </span>
                <div className="group relative">
                  <span className="text-xs text-gray-400 cursor-help">ⓘ</span>
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none w-64 z-10">
                    Confidence based on average cosine similarity between highlighted text and top 3 most relevant PDF chunks
                  </div>
                </div>
              </div>
              
              {/* Source Chunks */}
              <div className="space-y-3">
                {sourceEvidence?.source_chunks?.map((chunk: any, idx: number) => (
                  <div key={idx} className="p-3 bg-white rounded border border-green-200">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-green-600">
                          Source {idx + 1} (Similarity: {(chunk.similarity * 100).toFixed(2)}%)
                        </span>
                        <div className="group relative">
                          <span className="text-xs text-gray-400 cursor-help">ⓘ</span>
                          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none w-48 z-10">
                            Vector similarity between highlighted text and this PDF chunk
                          </div>
                        </div>
                      </div>
                      {chunk.metadata?.page && (
                        <span className="text-xs text-gray-500">
                          Page {chunk.metadata.page}
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-800 leading-relaxed">
                      {chunk.content.length > 350 
                        ? `${chunk.content.substring(0, 350)}...` 
                        : chunk.content
                      }
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Explanation Result */}
      {showExplanationResult && explanation && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex justify-between items-start mb-3">
            <h4 className="text-sm font-semibold text-blue-800">AI Explanation</h4>
            <button
              onClick={() => {
                setShowExplanationResult(false);
                setExplanation(null);
              }}
              className="text-blue-600 hover:text-blue-800 text-sm"
            >
              Close
            </button>
          </div>
          {loadingExplanation ? (
            <div className="text-sm text-blue-700">Loading explanation...</div>
          ) : (
            <>
              {/* User's Question */}
              {explanation.userQuestion && (
                <div className="mb-3 p-2 bg-white rounded border border-blue-200">
                  <div className="text-xs font-medium text-blue-600 mb-1">Your Question:</div>
                  <div className="text-sm text-gray-800 italic">"{explanation.userQuestion}"</div>
                </div>
              )}
              
              {/* Selected Text */}
              <div className="mb-3 p-2 bg-white rounded border border-blue-200">
                <div className="text-xs font-medium text-blue-600 mb-1">Selected Text:</div>
                <div className="text-sm text-gray-700 italic">
                  "{selectedSentence && selectedSentence.length > 200 
                    ? `${selectedSentence.substring(0, 200)}...` 
                    : selectedSentence}"
                </div>
              </div>
              
              {/* AI Response */}
              <div className="p-3 bg-white rounded border border-blue-200">
                <div className="text-xs font-medium text-blue-600 mb-2">AI Response:</div>
                <div className="text-sm text-gray-800 leading-relaxed">
                  {explanation.explanation}
                </div>
              </div>
            </>
          )}
        </div>
      )}
      
       {/* Action buttons */}
       <div className="mt-4 flex justify-end">
           <button 
           onClick={handleCopyToClipboard} 
           className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors duration-200 text-sm"
        >
           Copy Summary
        </button>
       </div>
    </div>
  );
};

// Helper component for the Chat interface - Now in a card
const Chat: React.FC<{ files: string[] }> = ({ files }) => {
  const [messages, setMessages] = useState<{ sender: "user" | "bot", text: string, sources?: any[] }[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Format chat messages with proper text handling
  const formatChatMessage = (text: string): React.ReactNode => {
    if (!text) return '';
    
    // Split by paragraphs and format each
    const paragraphs = text.split('\n').filter(p => p.trim() !== '');
    
    return paragraphs.map((paragraph, idx) => {
      // Handle bold text
      const formattedText = paragraph.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      
      return (
        <p key={idx} className={`${idx > 0 ? 'mt-2' : ''} leading-relaxed`}>
          <span dangerouslySetInnerHTML={{ __html: formattedText }} />
        </p>
      );
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || files.length === 0) return;

    const userMessage = { sender: "user" as const, text: question };
    setMessages(prev => [...prev, userMessage]);
    setQuestion("");
    setLoading(true);

    try {
      // Use query-doc for single document or query for multiple
      const endpoint = files.length === 1 ? '/query-doc' : '/query';
      const body = files.length === 1 
        ? { question, document_id: files[0] }
        : { query: question, filenames: files };

      const res = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      
      const botMessage = { 
        sender: "bot" as const, 
        text: data.answer || data.message, 
        sources: data.citations || data.sources 
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      console.error("Chat error:", err);
      const errorMessage = { sender: "bot" as const, text: `Error: ${err}. Please try again.` };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any); // Cast needed for form submission type
    }
  };

  // More suggested questions for placeholder
  const suggestedQuestions = [
      "What are the key objectives of this paper?",
      "Summarize the methodology used.",
      "What were the major findings?",
      "Discuss the limitations mentioned.",
      "What is the field of study?",
      "Can you suggest related papers?"
  ];
  const placeholderText = `Ask: ${suggestedQuestions[Math.floor(Math.random() * suggestedQuestions.length)]}`;

  return (
     // Card container
    <div className="bg-white rounded-lg shadow-lg overflow-hidden border border-blue-200 flex flex-col h-full">
       <div className="flex justify-between items-center p-6 border-b border-gray-200 cursor-pointer" onClick={() => setIsCollapsed(!isCollapsed)}>
          <h3 className="text-xl font-semibold text-blue-800">Chat Assistant</h3>
           {/* Style the collapse (-) button to be visually minimal and aligned top-right */}
          <button className="text-gray-500 hover:text-gray-800 float-right">
              {isCollapsed ? '+' : '-'}
          </button>
       </div>
      
       {!isCollapsed && (
         <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50">
           {messages.length === 0 ? (
             <div className="text-gray-600 text-center italic mt-10">Ask a research question about your uploaded papers.</div>
           ) : (
             messages.map((msg, idx) => (
               <div key={idx} className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}>
                 {/* Suggestion: Use avatar/icon for sender */}
                 <div className={`inline-block p-4 rounded-xl max-w-sm break-words ${msg.sender === "user" ? "bg-blue-600 text-white rounded-br-none" : "bg-gray-200 text-gray-800 rounded-bl-none"}`}>
                   <div className="text-sm leading-relaxed">
                     {formatChatMessage(msg.text)}
                   </div>
                   {msg.sender === "bot" && msg.sources && msg.sources.length > 0 && (
                     <div className="mt-3 pt-3 border-t border-gray-300">
                       <div className="text-xs font-medium mb-2">Sources:</div>
                       {msg.sources.map((source: any, idx: number) => (
                         <div key={idx} className="text-xs bg-white/10 rounded p-2 mb-1">
                           <span className="font-medium">[{source.index || idx + 1}]</span>
                           {source.chunk ? (
                             <>
                               <span className="text-gray-300"> Section: {source.chunk.metadata?.section || 'Unknown'}</span>
                               <div className="mt-1 text-gray-400">{source.chunk.content.substring(0, 100)}...</div>
                             </>
                           ) : (
                             <span className="text-gray-300"> {source.metadata?.filename || source.content?.substring(0, 100) || 'Unknown source'}</span>
                           )}
                         </div>
                       ))}
                     </div>
                   )}
                 </div>
               </div>
             ))
           )}
           {loading && (
              <div className="flex justify-start">
                  <div className="inline-block p-4 rounded-xl bg-gray-200 text-gray-800 rounded-bl-none">
                      {/* Simple loading indicator */}
                      Loading...
                  </div>
              </div>
           )}
         </div>
       )}

       {!isCollapsed && (
         <form onSubmit={handleSubmit} className="flex gap-4 p-4 border-t border-gray-200 bg-white">
           {/* Use textarea for multiline input */}
           <textarea
             value={question}
             onChange={(e) => setQuestion(e.target.value)}
             onKeyDown={handleKeyDown} // Handle Shift+Enter
             placeholder={placeholderText} // Use dynamic placeholder
             className="flex-1 border border-gray-300 rounded-lg px-4 py-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow duration-200 resize-none placeholder-gray-500 bg-white" // Improved text/background contrast and explicit background
             disabled={loading || files.length === 0}
             rows={1} // Start with one row, will expand with content
           />
           <button type="submit" className="flex-shrink-0 bg-blue-700 text-white px-8 py-3 rounded-lg hover:bg-blue-800 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed" disabled={loading || files.length === 0}>
             Send
           </button>
         </form>
       )}
    </div>
  );
};

const BACKEND_URL = "https://medscope.onrender.com";

const App: React.FC = () => {
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [summaries, setSummaries] = useState<Record<string, string>>({});
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false); // State for sidebar collapse
  const [selectedAudience, setSelectedAudience] = useState<AudienceType>('clinician');
  const [showPdfViewer, setShowPdfViewer] = useState(false);
  const [relatedDocuments, setRelatedDocuments] = useState<any[]>([]);


  const handleUpload = async (file: File) => {
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`${BACKEND_URL}/upload`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      setUploadedFiles((prev) => [...prev, data.filename]);
      // Clear summary if file is re-uploaded or new file is uploaded
      setSummaries(prev => { delete prev[data.filename]; return { ...prev }; });
      setSelectedFiles([data.filename]); // Select the newly uploaded file
      
      // Fetch related documents
      fetchRelatedDocuments(data.filename);
    } catch (err) {
      console.error("Upload error:", err);
      alert(`Failed to upload PDF: ${err}`); // Suggestion: Use a better notification system
    } finally {
      setUploading(false);
    }
  };

  const fetchRelatedDocuments = async (filename: string) => {
    try {
      const response = await fetch(`${BACKEND_URL}/related-documents/${filename}`);
      if (response.ok) {
        const data = await response.json();
        setRelatedDocuments(data.related || []);
      }
    } catch (error) {
      console.error('Error fetching related documents:', error);
    }
  };

  const handleSummarize = async (filename: string) => {
     // Prevent summarizing if already summarizing or summary exists
     if (summaries[filename] && summaries[filename] !== "Summarizing...") return;

     setSummaries(prev => ({ ...prev, [filename]: "Summarizing..." }));

    try {
      const res = await fetch(`${BACKEND_URL}/summarize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          filename,
          audience_type: selectedAudience 
        }),
      });
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      setSummaries((prev) => ({ ...prev, [filename]: data.message }));
      

    } catch (err) {
      console.error("Summarization error:", err);
      setSummaries(prev => ({ ...prev, [filename]: `Summarization failed: ${err}` })); // Keep error message in state
    }
  };

   // Placeholder for file removal - needs backend implementation
  // @ts-ignore
  const handleRemoveFile = async (filename: string) => {
     // TODO: Implement backend endpoint for file deletion
     // For now, just remove from frontend state
     try {
         const res = await fetch(`${BACKEND_URL}/delete_file`, {
             method: "POST",
             headers: { "Content-Type": "application/json" },
             body: JSON.stringify({ filename }),
         });
         if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

         // Remove from frontend state only after successful backend deletion
         setUploadedFiles(prev => prev.filter(file => file !== filename));
         setSummaries(prev => { delete prev[filename]; return { ...prev }; });
         if (selectedFiles.includes(filename)) {
             setSelectedFiles(prev => prev.filter(file => file !== filename));
         }
         // Also clear the selected file name in the upload box if the deleted file was selected there
         // This might require passing down a state setter or ref from PDFUpload, 
         // but for now, we assume setSelectedFiles([]) is sufficient if the file was selected in the list.
         // If the file was only selected in the upload box via drag/drop without being in the uploadedFiles list, 
         // we'd need a different mechanism to clear the PDFUpload's internal state.
         // Let's assume for now that files in the upload box are also added to the uploadedFiles list upon successful upload.

         alert(`File deleted successfully: ${filename}`); // Suggestion: Use a better notification system
     } catch (err) {
         console.error("File deletion error:", err);
         alert(`Failed to delete file: ${err}`); // Suggestion: Use a better notification system
     }
   };

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const handleFileSelect = (filename: string) => {
      // Toggle selection: if already selected, unselect. Otherwise, select just this one.
      if (selectedFiles.includes(filename)) {
          setSelectedFiles([]); // Clear selection
      } else {
          setSelectedFiles([filename]); // Select this file
      }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <Sidebar 
        files={uploadedFiles} 
        onSummarize={handleSummarize} 
        summaries={summaries}
        isCollapsed={isSidebarCollapsed}
        onFileSelect={handleFileSelect}
        selectedFiles={selectedFiles}
        onRemoveFile={handleRemoveFile}
        onToggleCollapse={toggleSidebar} // Pass the toggle function
      />

      {/* Main Content Area */}
      {/* Added some padding here to the main content container */}
      <main className="flex-1 flex flex-col p-8 overflow-hidden bg-white">
         {/* Header with Title and Tagline */}
        <header className="mb-8">
          <h1 className="text-5xl font-extrabold text-blue-900 mb-2">MedPub</h1>
          <p className="text-xl text-gray-600">Your AI-powered assistant for summarizing and exploring medical publications</p>
        </header>

        {/* Content area: Upload, Summary, and Chat in a single column */}
        {/* This outer div manages the vertical stacking and gap */}
        <div className="flex-1 flex flex-col gap-8 overflow-y-auto">
           {/* Upload component always visible */}
           <PDFUpload onUpload={handleUpload} uploading={uploading} />
              
           {/* Audience Selector */}
           {selectedFiles.length > 0 && (
             <AudienceSelector
               selectedAudience={selectedAudience}
               onAudienceChange={setSelectedAudience}
               disabled={Object.values(summaries).some(s => s === "Summarizing...")}
             />
           )}
           
           {/* Container for Summary and Chat, or the Welcome Message */}
           {/* This container needs to take up the remaining space */} 
           {selectedFiles.length > 0 ? (
             <div className="flex-1 flex flex-col gap-8">
                {/* Add PDF Viewer Toggle */}
                {selectedFiles.length === 1 && (
                  <div className="flex justify-between items-center">
                    <button
                      onClick={() => setShowPdfViewer(!showPdfViewer)}
                      className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-md transition-colors"
                    >
                      {showPdfViewer ? 'Hide PDF Viewer' : 'Show PDF Viewer'}
                    </button>
                    
                    {/* Related Documents */}
                    {relatedDocuments.length > 0 && (
                      <div className="bg-gray-50 rounded-lg p-4 border">
                        <h4 className="text-sm font-semibold text-gray-700 mb-3">Related Documents</h4>
                        <div className="space-y-2">
                          {relatedDocuments.slice(0, 3).map((doc, idx) => (
                            <div key={idx} className="flex items-start gap-3 p-2 bg-white rounded border border-gray-200">
                              <div className="flex-1">
                                <div className="text-sm font-medium text-blue-600 truncate">
                                  {doc.title || doc.filename.replace(/^\d{8}_\d{6}_/, '')}
                                </div>
                                <div className="text-xs text-gray-500 mt-1">
                                  Similarity: {(doc.similarity_score * 100).toFixed(1)}% • 
                                  Common topics: {doc.common_topics?.join(', ') || 'None'}
                                </div>
                              </div>
                              <div className="text-xs text-gray-400">
                                #{idx + 1}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* PDF Viewer */}
                {showPdfViewer && selectedFiles.length === 1 && (
                  <div className="h-96 border border-gray-300 rounded-lg overflow-hidden">
                    <PDFViewer
                      filename={selectedFiles[0]}
                      backendUrl={BACKEND_URL}
                    />
                  </div>
                )}

                {/* Display summary only if ONE file is selected and summarized */}
                {selectedFiles.length === 1 && summaries[selectedFiles[0]] && summaries[selectedFiles[0]] !== "Summarizing..." && (
                   <SummaryDisplay 
                     summary={summaries[selectedFiles[0]]} 
                     filename={selectedFiles[0]}
                   />
                )}
                 {/* Chat takes remaining vertical space below summary if visible */}
                {/* Ensure chat container grows */} 
                <div className="flex-1 h-full min-h-[400px]">
                   <Chat files={selectedFiles} />{/* Pass selected files to chat */} 
                </div>
             </div>
             ) : (
                // Welcome/Instructional Message when no file is selected
                // This div should also take up remaining space
                <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-600 italic p-8 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50 bg-white">
                    <svg className="w-16 h-16 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18m-6 4h6m-6 4h6"></path></svg>
                    <p className="text-lg font-semibold mb-2">Welcome to MedPub!</p>
                    <p>Upload a medical paper to get started. You can drag and drop a PDF above or click to browse your files.</p>
                    <p className="mt-4 text-sm">Once uploaded and summarized, you can chat with the document and get AI-powered insights.</p>
                </div>
            )}
        </div>
      </main>
       {/* Suggestion: Add a button here or in the header to toggle the sidebar collapse state */}
    </div>
  );
};

export default App;
