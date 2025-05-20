import type { UploadedFile } from '../../types';
import { useTheme } from '../../context/ThemeContext';

const FileIcon = () => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <svg 
      width="16" 
      height="16" 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke={isDark ? 'white' : 'black'} 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round"
      style={{ marginRight: '10px', flexShrink: 0, width: '18px', height: '18px' }}
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  );
};

interface FileListProps {
  files: UploadedFile[];
  onToggleActive: (fileId: string) => void;
}

const FileList: React.FC<FileListProps> = ({ files, onToggleActive }) => {
  return (
    <div className="sidebar-section uploaded-files-display-section">
      <h3 className="uploaded-files-header">Uploaded Files</h3>
      {files.length === 0 ? (
        <p className="empty-file-list-message">Empty</p>
      ) : (
        <ul className="file-list">
          {files.map((file) => (
            <li key={file.id} className="file-list-item">
              <div style={{ display: 'flex', alignItems: 'center', overflow: 'hidden' }}>
                <FileIcon />
                <span className="file-name">{file.name}</span>
              </div>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={file.isActive}
                  onChange={() => onToggleActive(file.id)}
                />
                <span className="slider round"></span>
              </label>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default FileList; 