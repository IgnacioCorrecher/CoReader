import type { UploadedFile } from '../../types';
import ThemeToggle from './ThemeToggle';
import FileList from './FileList';
import { useTheme } from '../../context/ThemeContext';

interface SidebarProps {
  uploadedFiles: UploadedFile[];
  onToggleActive: (fileId: string) => void;
  onNewChat: () => void;
  isOpen: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({
  uploadedFiles,
  onToggleActive,
  onNewChat,
  isOpen
}) => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
      <div className="theme-toggle-container">
        <ThemeToggle />
        <button 
          onClick={onNewChat} 
          style={{
            backgroundColor: 'transparent',
            color: isDark ? '#E5E5E5' : '#2D2D2D',
            border: `1px solid ${isDark ? '#E5E5E580' : '#2D2D2D80'}`,
            borderRadius: '8px',
            padding: '8px 16px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '14px',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => {
            const bgColor = isDark ? '#E5E5E5' : '#2D2D2D';
            e.currentTarget.style.backgroundColor = `${bgColor}20`; // 12.5% opacity
            e.currentTarget.style.transform = 'scale(1.025)';
            e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.1)';
            e.currentTarget.style.borderColor = isDark ? '#E5E5E580' : '#2D2D2D80';
            
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent';
            e.currentTarget.style.transform = 'scale(1)';
            e.currentTarget.style.boxShadow = 'none';
            e.currentTarget.style.borderColor = isDark ? '#E5E5E580' : '#2D2D2D80';
          }}
        >
          🔄 Clear Chat
        </button>
      </div>
      
      <FileList
        files={uploadedFiles}
        onToggleActive={onToggleActive}
      />
    </div>
  );
};

export default Sidebar; 