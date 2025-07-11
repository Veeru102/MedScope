import React from 'react';

interface RelatedPaper {
  title: string;
  authors: string;
  year: string | number;
  abstract_snippet: string;
  categories: string;
  similarity_score: number;
  arxiv_url: string;
}

interface RelatedPapersProps {
  papers: RelatedPaper[];
}

const RelatedPapers: React.FC<RelatedPapersProps> = ({ papers }) => {
  if (!papers || papers.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 border border-blue-200">
      <h3 className="text-xl font-semibold text-blue-800 mb-4">Suggested Related Papers (arXiv)</h3>
      <div className="space-y-4">
        {papers.map((paper, idx) => (
          <div key={idx} className="border-l-4 border-blue-400 pl-4 py-3 bg-gray-50 rounded-r-lg">
            <div className="flex justify-between items-start mb-2">
              <h4 className="text-md font-medium text-gray-900 flex-1 pr-4">
                {idx + 1}. {paper.title}
              </h4>
              <span className="text-sm text-blue-600 font-medium whitespace-nowrap">
                {(paper.similarity_score * 100).toFixed(1)}% match
              </span>
            </div>
            
            <div className="text-sm text-gray-600 mb-2">
              <span className="font-medium">Authors:</span> {paper.authors}
              {paper.year && (
                <>
                  <span className="mx-2">•</span>
                  <span className="font-medium">Year:</span> {paper.year}
                </>
              )}
            </div>
            
            {paper.categories && (
              <div className="text-xs text-gray-500 mb-2">
                <span className="font-medium">Categories:</span> {paper.categories}
              </div>
            )}
            
            <p className="text-sm text-gray-700 mb-3 leading-relaxed">
              {paper.abstract_snippet}
            </p>
            
            {paper.arxiv_url && (
              <a
                href={paper.arxiv_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 transition-colors"
              >
                View on arXiv
                <svg
                  className="w-4 h-4 ml-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
              </a>
            )}
          </div>
        ))}
      </div>
      
      <div className="mt-4 p-3 bg-blue-50 rounded-lg">
        <p className="text-xs text-blue-700">
          <strong>Note:</strong> These papers are selected from a curated arXiv dataset using semantic similarity search. 
          Similarity scores indicate how closely the paper's content matches your uploaded document.
        </p>
      </div>
    </div>
  );
};

export default RelatedPapers; 