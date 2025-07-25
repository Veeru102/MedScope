import React, { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import type { PDFDocumentProxy } from 'pdfjs-dist';

// Configure react-pdf worker.
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.js';

interface PDFViewerProps {
  filename: string;
  backendUrl: string;
  onTextSelect?: (text: string, context: string) => void;
  highlightedSection?: { page: number; text: string };
}

interface DocumentSection {
  name: string;
  page: number;
}

const PDFViewer: React.FC<PDFViewerProps> = ({ filename, backendUrl }) => {
  const [sections, setSections] = useState<DocumentSection[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState<number>(0);
  const [scale, setScale] = useState(1.0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [documentLoaded, setDocumentLoaded] = useState(false);

  // Construct PDF URLs w fallback options
  const primaryPdfUrl = `${backendUrl}/uploads/${filename}`;
  const fallbackPdfUrl = `${backendUrl}/files/${filename}`;
  const [currentPdfUrl, setCurrentPdfUrl] = useState(primaryPdfUrl);

  // PDF loading options.
  const pdfOptions = {
    cMapUrl: '/cmaps/',
    cMapPacked: true,
    standardFontDataUrl: '/standard_fonts/',
    httpHeaders: {
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache',
      'Expires': '0',
    },
  };

  // Validates PDF URL and handles fallbacks.
  useEffect(() => {
    const validatePdf = async (url: string, isFallback: boolean = false) => {
      try {
        setLoading(true);
        setError(null);
        
        console.log(`Attempting to load PDF from: ${url}`);
        const response = await fetch(url);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const contentType = response.headers.get('content-type');
        console.log(`Response content-type: ${contentType}`);
        
        const blob = await response.blob();
        if (!blob.type.includes('pdf') && !contentType?.includes('pdf')) {
          throw new Error(`Invalid content type: ${blob.type || contentType}`);
        }
        
        console.log(`PDF successfully validated from: ${url}`);
        setCurrentPdfUrl(url);
        setDocumentLoaded(true);
        
      } catch (err) {
        console.error(`PDF validation error for ${url}:`, err);
        
        if (!isFallback) {
          console.log('Trying fallback URL...');
          return validatePdf(fallbackPdfUrl, true);
        }
        
        setError(err instanceof Error ? 
          `Failed to load PDF: ${err.message}. Tried both /uploads and /files endpoints.` : 
          'Failed to load PDF from both endpoints'
        );
        setLoading(false);
      }
    };

    validatePdf(primaryPdfUrl);
  }, [filename, backendUrl, primaryPdfUrl, fallbackPdfUrl]);

  // Fetches document sections and page count.
  useEffect(() => {
    const fetchDocumentInfo = async () => {
      try {
        const response = await fetch(`${backendUrl}/document-info/${filename}`);
        if (response.ok) {
          const data = await response.json();
          setTotalPages(data.metadata.page_count || 1);
          
          // Map sections to approximate page numbers
          const sectionList = data.sections.map((section: string, index: number) => ({
            name: section,
            page: Math.floor((index / data.sections.length) * (data.metadata.page_count || 1)) + 1
          }));
          setSections(sectionList);
        }
      } catch (err) {
        console.error('Error fetching document info:', err);
        // Continue anyways
      }
    };

    fetchDocumentInfo();
  }, [filename, backendUrl]);

  const onDocumentLoadSuccess = (pdf: PDFDocumentProxy) => {
    setTotalPages(pdf.numPages);
    setLoading(false);
    setError(null);
  };

  const onDocumentLoadError = (err: Error) => {
    console.error('Error loading PDF:', err);
    setError(`Failed to load PDF: ${err.message}`);
    setLoading(false);
  };

  const onPageLoadSuccess = () => {
    setLoading(false);
  };

  const onPageLoadError = (err: Error) => {
    console.error(`Error loading page ${currentPage}:`, err);
    setError(`Failed to load page ${currentPage}: ${err.message}`);
  };

  // Navigation controls.
  const navigateToSection = (sectionPage: number) => setCurrentPage(sectionPage);
  const goToPrevPage = () => setCurrentPage(prev => Math.max(1, prev - 1));
  const goToNextPage = () => setCurrentPage(prev => Math.min(totalPages, prev + 1));
  const zoomIn = () => setScale(prev => Math.min(2.0, prev + 0.2));
  const zoomOut = () => setScale(prev => Math.max(0.5, prev - 0.2));
  const resetZoom = () => setScale(1.0);

  return (
    <div className="flex h-full bg-gray-100">
      {/* Section navigation sidebar */}
      <div className="w-64 bg-white p-4 overflow-y-auto border-r border-gray-300 shadow-sm">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Sections</h3>
        <ul className="space-y-2">
          {sections.map((section, index) => (
            <li key={index}>
              <button
                onClick={() => navigateToSection(section.page)}
                className={`w-full text-left px-3 py-2 rounded-md transition-colors duration-200 text-sm ${
                  currentPage === section.page
                    ? 'bg-blue-500 text-white'
                    : 'hover:bg-gray-100 text-gray-700'
                }`}
              >
                <div className="font-medium truncate">{section.name}</div>
                <div className="text-xs opacity-75">Page {section.page}</div>
              </button>
            </li>
          ))}
        </ul>
        
        {/* Document info display */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Document Info</h4>
          <p className="text-xs text-gray-600">Total Pages: {totalPages}</p>
          <p className="text-xs text-gray-600">Current Page: {currentPage}</p>
          <p className="text-xs text-gray-600">Zoom: {Math.round(scale * 100)}%</p>
        </div>
      </div>

      {/* PDF Viewer */}
      <div className="flex-1 flex flex-col bg-gray-50">
        {/* Toolbar */}
        <div className="flex items-center justify-between p-4 bg-white border-b border-gray-200 shadow-sm">
          <div className="flex items-center space-x-4">
            <span className="text-gray-700 font-medium text-sm">
              {filename.replace(/^\d{8}_\d{6}_/, '')}
            </span>
            <div className="flex items-center space-x-2">
              <button
                onClick={goToPrevPage}
                disabled={currentPage <= 1}
                className="px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={goToNextPage}
                disabled={currentPage >= totalPages}
                className="px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={zoomOut}
              className="px-2 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              -
            </button>
            <button
              onClick={resetZoom}
              className="px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm"
            >
              {Math.round(scale * 100)}%
            </button>
            <button
              onClick={zoomIn}
              className="px-2 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              +
            </button>
            <a
              href={currentPdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
            >
              Open in New Tab
            </a>
          </div>
        </div>

        {/* PDF Display */}
        <div className="flex-1 overflow-auto flex justify-center py-4">
          {loading && !error && (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
              <div className="text-gray-500 text-lg font-medium">Loading PDF...</div>
              <div className="text-gray-400 text-sm mt-2">Please wait while we prepare your document</div>
            </div>
          )}
          
          {error && (
            <div className="flex items-center justify-center h-full">
              <div className="text-red-500 text-center p-4 bg-red-50 rounded-lg border border-red-200 max-w-md">
                <div className="text-xl mb-2">⚠️</div>
                <div className="font-medium mb-2">Error loading PDF</div>
                <div className="text-sm mb-2 text-gray-700">
                  <strong>File:</strong> {filename}
                </div>
                <div className="text-sm mb-2 text-gray-700">
                  <strong>Current URL:</strong> {currentPdfUrl}
                </div>
                <div className="text-sm mb-4 text-red-600">{error}</div>
                <div className="flex flex-col space-y-2">
                  <div className="flex space-x-2 justify-center">
                    <button 
                      onClick={() => window.location.reload()} 
                      className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
                    >
                      Reload Page
                    </button>
                    <a
                      href={currentPdfUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm"
                    >
                      Open in Browser
                    </a>
                  </div>
                  <div className="text-xs text-gray-600 mt-2">
                    <div>Primary URL: {primaryPdfUrl}</div>
                    <div>Fallback URL: {fallbackPdfUrl}</div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {documentLoaded && !error && (
            <Document
              file={currentPdfUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={
                <div className="flex flex-col items-center justify-center p-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mb-2"></div>
                  <div className="text-gray-500">Loading document...</div>
                </div>
              }
              error={
                <div className="text-red-500 p-4 bg-red-50 rounded-lg border border-red-200">
                  <div className="font-medium mb-2">Failed to load PDF</div>
                  <div className="text-sm text-red-600">Please try refreshing the page or check your connection.</div>
                </div>
              }
              options={pdfOptions}
              className="w-full h-full"
            >
              <Page
                key={`page_${currentPage}`}
                pageNumber={currentPage}
                scale={scale}
                loading={
                  <div className="flex flex-col items-center justify-center p-8">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mb-2"></div>
                    <div className="text-gray-500 text-sm">Loading page {currentPage}...</div>
                  </div>
                }
                error={
                  <div className="text-red-500 p-4">
                    <div>Failed to load page {currentPage}</div>
                    <button 
                      onClick={() => setCurrentPage(currentPage)} 
                      className="text-sm text-blue-500 hover:text-blue-600 mt-2"
                    >
                      Retry
                    </button>
                  </div>
                }
                onLoadSuccess={onPageLoadSuccess}
                onLoadError={onPageLoadError}
                className="shadow-lg"
                renderTextLayer={true}
                renderAnnotationLayer={false}
              />
            </Document>
          )}
        </div>
      </div>
    </div>
  );
};

export default PDFViewer; 