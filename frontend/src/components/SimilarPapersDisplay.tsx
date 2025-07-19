import React, { useState } from 'react';

interface SimilarPaper {
  id: string;
  title: string;
  abstract: string;
  similarity_score: number;
  rank: number;
  arxiv_url: string;
}

interface SimilarPapersResponse {
  papers: SimilarPaper[];
  total_found: number;
  search_time_ms: number;
  query: string;
}

interface SimilarPapersDisplayProps {
  summary: string;
  filename: string; 
  backendUrl: string;
}

// Custom hook for managing similar papers search
const useSimilarPapers = (backendUrl: string) => {
  const [papers, setPapers] = useState<SimilarPaper[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchPerformed, setSearchPerformed] = useState(false);

  const searchSimilarPapers = async (query: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${backendUrl}/arxiv/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, limit: 5 })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: SimilarPapersResponse = await response.json();
      setPapers(data.papers);
      setSearchPerformed(true);
      
      console.log(`Found ${data.total_found} similar papers in ${data.search_time_ms}ms`);
      
    } catch (err) {
      console.error('Error searching similar papers:', err);
      setError(err instanceof Error ? err.message : 'Failed to search similar papers');
      setPapers([]);
    } finally {
      setLoading(false);
    }
  };

  return { papers, loading, error, searchPerformed, searchSimilarPapers };
};

const SimilarPapersDisplay: React.FC<SimilarPapersDisplayProps> = ({ 
  summary, 
  filename: _, 
  backendUrl 
}) => {
  const { papers, loading, error, searchPerformed, searchSimilarPapers } = useSimilarPapers(backendUrl);
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Extract query from summary - use first 200 characters for search
  const getSearchQuery = () => {
    if (!summary) return '';
    // Remove HTML tags and get meaningful text
    const cleanText = summary.replace(/<[^>]*>/g, '').trim();
    return cleanText.length > 200 ? cleanText.substring(0, 200) : cleanText;
  };

  const handleSearchSimilarPapers = () => {
    const query = getSearchQuery();
    if (query) {
      searchSimilarPapers(query);
    }
  };

  // Get similarity color based on score
  const getSimilarityColor = (score: number) => {
    if (score >= 0.7) return 'bg-green-600';
    if (score >= 0.5) return 'bg-yellow-600';
    return 'bg-gray-600';
  };

  const formatSimilarityScore = (score: number) => {
    return `${(score * 100).toFixed(1)}%`;
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-8 border border-blue-200">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-semibold text-blue-800">Similar Research Papers</h3>
        {searchPerformed && (
          <button 
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="text-gray-500 hover:text-gray-700"
          >
            {isCollapsed ? '+' : '-'}
          </button>
        )}
      </div>

      {/* Search button */}
      {!searchPerformed && (
        <div className="text-center">
          <button
            onClick={handleSearchSimilarPapers}
            disabled={loading || !summary}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center mx-auto"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l2-2.647z"></path>
                </svg>
                Searching arXiv...
              </>
            ) : (
              <>
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
                Find Similar Research Papers
              </>
            )}
          </button>
          <p className="text-sm text-gray-500 mt-2">
            Search arXiv for papers similar to this document
          </p>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="p-4 bg-red-50 rounded-lg border border-red-200 mb-4">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z"></path>
            </svg>
            <span className="text-red-800 text-sm">Error: {error}</span>
          </div>
          <button
            onClick={handleSearchSimilarPapers}
            className="mt-2 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Results display */}
      {searchPerformed && !isCollapsed && (
        <div className="space-y-4">
          {papers.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <svg className="w-12 h-12 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
              No similar papers found. Try refining your search.
            </div>
          ) : (
            <>
              <div className="flex justify-between items-center mb-4">
                <p className="text-sm text-gray-600">
                  Found {papers.length} similar papers
                </p>
                <button
                  onClick={handleSearchSimilarPapers}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  Search Again
                </button>
              </div>
              
              {papers.map((paper, _index) => ( // index renamed to _index as it's currently unused
                <div 
                  key={paper.id} 
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow duration-200"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900 leading-tight mb-2">
                        {paper.title}
                      </h4>
                      <p className="text-sm text-gray-600 leading-relaxed">
                        {paper.abstract.length > 300 
                          ? `${paper.abstract.substring(0, 300)}...` 
                          : paper.abstract}
                      </p>
                    </div>
                    <div className="flex flex-col items-end ml-4">
                      <span className={`text-xs font-semibold px-2 py-1 rounded-full text-white ${getSimilarityColor(paper.similarity_score)}`}>
                        {formatSimilarityScore(paper.similarity_score)}
                      </span>
                      <span className="text-xs text-gray-500 mt-1">
                        Rank #{paper.rank}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-100">
                    <div className="flex items-center text-sm text-gray-500">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                      </svg>
                      arXiv:{paper.id}
                    </div>
                    <a
                      href={paper.arxiv_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center px-3 py-1 border border-blue-300 text-blue-600 text-sm rounded-md hover:bg-blue-50 transition-colors duration-200"
                    >
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                      </svg>
                      View Paper
                    </a>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default SimilarPapersDisplay; 