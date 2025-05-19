import type { UploadedFile } from '../../types';
import ThemeToggle from './ThemeToggle';
import FileUpload from './FileUpload';
import FileList from './FileList';

interface SidebarProps {
  selectedFile: File | null;
  isStreaming: boolean;
  uploadedFiles: UploadedFile[];
  onFileChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onUpload: () => void;
  onToggleActive: (fileId: string) => void;
  onNewChat: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  selectedFile,
  isStreaming,
  uploadedFiles,
  onFileChange,
  onUpload,
  onToggleActive,
  onNewChat
}) => {
  return (
    <div className='sidebar'>
      <ThemeToggle />
      
      <button onClick={onNewChat} className="new-chat-button">
        + New Chat
      </button>
      
      <FileUpload
        selectedFile={selectedFile}
        isStreaming={isStreaming}
        onFileChange={onFileChange}
        onUpload={onUpload}
      />
      
      <FileList
        files={uploadedFiles}
        onToggleActive={onToggleActive}
      />
    </div>
  );
};

export default Sidebar; 