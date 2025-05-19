import type { UploadedFile } from '../../types';

interface FileListProps {
  files: UploadedFile[];
  onToggleActive: (fileId: string) => void;
}

const FileList: React.FC<FileListProps> = ({ files, onToggleActive }) => {
  if (files.length === 0) return null;

  return (
    <div className="sidebar-section uploaded-files-display-section">
      <h3>Active Files</h3>
      <ul className="file-list">
        {files.map((file) => (
          <li key={file.id} className="file-list-item">
            <span className="file-name">{file.name}</span>
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
    </div>
  );
};

export default FileList; 