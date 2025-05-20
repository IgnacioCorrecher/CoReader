import type { UploadedFile } from '../../types';

interface FileListProps {
  files: UploadedFile[];
  onToggleActive: (fileId: string) => void;
  onDeleteFile: (fileId: string) => void;
}

const FileList: React.FC<FileListProps> = ({ files, onToggleActive, onDeleteFile }) => {
  return (
    <div className="sidebar-section uploaded-files-display-section">
      <h3 className="uploaded-files-header">Uploaded Files</h3>
      {files.length === 0 ? (
        <p className="empty-file-list-message">Empty</p>
      ) : (
        <ul className="file-list">
          {files.map((file) => (
            <li key={file.id} className="file-list-item">
              <div style={{ display: 'flex', alignItems: 'center', overflow: 'hidden'}}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteFile(file.id);
                  }}
                  className="delete-file-button"
                  style={{ background: 'transparent'}}
                  title={`Delete ${file.name}`}
                >
                  <span role="img" aria-label="delete">🗑️</span>
                </button>
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