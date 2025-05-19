interface FileUploadProps {
  selectedFile: File | null;
  isStreaming: boolean;
  onFileChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onUpload: () => void;
}

const FileUpload: React.FC<FileUploadProps> = ({
  selectedFile,
  isStreaming,
  onFileChange,
  onUpload
}) => {
  return (
    <div className="sidebar-section file-upload-section">
      <h2>Upload File</h2>
      <input type="file" onChange={onFileChange} />
      <button 
        onClick={onUpload} 
        disabled={!selectedFile || isStreaming} 
        className="upload-button"
      >
        {isStreaming ? 'Uploading...' : 'Upload'}
      </button>
    </div>
  );
};

export default FileUpload; 