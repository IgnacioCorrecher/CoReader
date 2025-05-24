import { useState } from 'react';
import type { Citation } from '../../types';

interface CitationsProps {
  citations: Citation[];
}

const Citations: React.FC<CitationsProps> = ({ citations }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <div className="citations-container">
      <button 
        className="citations-toggle-button"
        onClick={() => setIsOpen(!isOpen)}
      >
        📄 {isOpen ? 'Hide' : 'Show'} Citations ({citations.length})
      </button>
      
      {isOpen && (
        <div className="citations-list">
          {citations.map((citation, index) => (
            <div key={index} className="citation-item">
              <div className="citation-header">
                <span className="citation-filename">📄 {citation.filename}</span>
              </div>
              <div className="citation-content">
                {citation.content}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Citations; 