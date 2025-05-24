import './App.css'
import { useState, useEffect, useRef } from 'react'
import type { ChatMessage, UploadedFile } from './types'
import { ThemeProvider } from './context/ThemeContext'
import Sidebar from './components/Sidebar/Sidebar'
import ChatContainer from './components/Chat/ChatContainer'
import Toast from './components/common/Toast'

function App() {
  const [query, setQuery] = useState<string>('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isStreamingUpload, setIsStreamingUpload] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string>('');
  const [isToastVisible, setIsToastVisible] = useState<boolean>(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(true);

  const chatEndRef = useRef<HTMLDivElement>(null);

  const backendUrl = 'http://localhost:8000';

  // Load uploaded files from backend on component mount
  useEffect(() => {
    loadUploadedFiles();
  }, []);

  const loadUploadedFiles = async () => {
    try {
      const response = await fetch(`${backendUrl}/get_uploaded_files`);
      if (response.ok) {
        const data = await response.json();
        setUploadedFiles(data.files || []);
      } else {
        console.error('Failed to load uploaded files');
      }
    } catch (error) {
      console.error('Error loading uploaded files:', error);
    }
  };

  useEffect(() => {
    if (isToastVisible) {
      const timer = setTimeout(() => {
        setIsToastVisible(false);
        setToastMessage('');
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [isToastVisible]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleQueryChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuery(event.target.value);
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      
      const formData = new FormData();
      formData.append('file', file);

      setIsStreamingUpload(true);

      try {
        const res = await fetch(`${backendUrl}/upload_file`, {
          method: 'POST',
          body: formData,
        });

        if (res.ok) {
          const result = await res.json();
          setToastMessage("✅ File uploaded successfully!");
          setIsToastVisible(true);

          const newFile: UploadedFile = {
            id: result.file_id, // Use file_id from backend
            name: result.filename,
            isActive: true,
          };
          
          // Add the new file to the list
          setUploadedFiles(prevFiles => {
            // Check if file already exists (by name for user experience)
            const existingFile = prevFiles.find(f => f.name === newFile.name);
            if (existingFile) {
              // Replace existing file with new one
              return prevFiles.map(f => f.name === newFile.name ? newFile : f);
            } else {
              // Add new file
              return [...prevFiles, newFile];
            }
          });
        } else {
          const errorResult = await res.json();
          setToastMessage(`Upload failed: ${errorResult.detail || res.statusText}`);
          setIsToastVisible(true);
        }
      } catch (error) {
        console.error('File upload error:', error);
        setToastMessage('Upload failed. See console for details.');
        setIsToastVisible(true);
      } finally {
        setIsStreamingUpload(false);
      }
    }
  };

  const toggleFileActiveStatus = async (fileId: string) => {
    // Find the current file to get its current status
    const file = uploadedFiles.find(f => f.id === fileId);
    if (!file) return;
    
    const newStatus = !file.isActive;
    
    try {
      const response = await fetch(`${backendUrl}/toggle_file_status`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_id: fileId,
          is_active: newStatus
        }),
      });

      if (response.ok) {
        // Update frontend state only after successful backend update
        setUploadedFiles(prevFiles =>
          prevFiles.map(file =>
            file.id === fileId ? { ...file, isActive: newStatus } : file
          )
        );
        
        const statusText = newStatus ? 'activated' : 'deactivated';
        setToastMessage(`📄 File ${statusText} successfully!`);
        setIsToastVisible(true);
      } else if (response.status === 404) {
        // File not found in vector store - remove from frontend
        const errorResult = await response.json();
        setUploadedFiles(prevFiles => prevFiles.filter(f => f.id !== fileId));
        setToastMessage(`⚠️ File not found in database and was removed from list: ${errorResult.detail}`);
        setIsToastVisible(true);
      } else {
        const errorResult = await response.json();
        setToastMessage(`Failed to update file status: ${errorResult.detail}`);
        setIsToastVisible(true);
      }
    } catch (error) {
      console.error('Error toggling file status:', error);
      setToastMessage('Error updating file status. See console for details.');
      setIsToastVisible(true);
    }
  };

  const handleNewChat = async () => {
    try {
      // Clear frontend chat messages
      setChatMessages([]);
      
      // Clear backend memory
      const response = await fetch(`${backendUrl}/clear_memory`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        setToastMessage('⚠️ Chat and memory cleared.');
      } else {
        console.error('Failed to clear memory on backend');
        setToastMessage('⚠️ Chat cleared (frontend only).');
      }
    } catch (error) {
      console.error('Error clearing memory:', error);
      setToastMessage('⚠️ Chat cleared (frontend only).');
    }
    
    setIsToastVisible(true);
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const handleDeleteFile = async (fileId: string) => {
    try {
      const response = await fetch(`${backendUrl}/delete_file/${fileId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        // Remove file from frontend state only after successful backend deletion
        setUploadedFiles(prevFiles => prevFiles.filter(file => file.id !== fileId));
        setToastMessage("🗑️ File deleted successfully!");
        setIsToastVisible(true);
      } else {
        const errorResult = await response.json();
        setToastMessage(`Failed to delete file: ${errorResult.detail}`);
        setIsToastVisible(true);
      }
    } catch (error) {
      console.error('Error deleting file:', error);
      setToastMessage('Error deleting file. See console for details.');
      setIsToastVisible(true);
    }
  };

  const isAnyFileActive = uploadedFiles.some(file => file.isActive);

  const handleQuerySubmit = () => {
    if (!query.trim()) return;

    const userMessage: ChatMessage = {
      id: 'user-' + Date.now(),
      type: 'user',
      content: query,
    };
    setChatMessages(prevMessages => [...prevMessages, userMessage]);

    if (!isAnyFileActive) {
      const aiResponse: ChatMessage = {
        id: 'ai-' + Date.now(),
        type: 'ai',
        content: "Please upload a file so I can answer.",
      };
      setChatMessages(prevMessages => [...prevMessages, aiResponse]);
      setQuery('');
      setIsStreaming(false); // Ensure streaming is off
      return;
    }

    const websocket = new WebSocket(`${backendUrl}/ws/stream`);
    setIsStreaming(true);

    let aiMessageId = 'ai-' + Date.now();
    let currentAiContent = '';

    const initialAiMessage: ChatMessage = {
      id: aiMessageId,
      type: 'ai',
      content: '', 
    };
    setChatMessages(prevMessages => [...prevMessages, initialAiMessage]);

    websocket.onopen = () => {
      websocket.send(JSON.stringify({ query }));
      setQuery('');
    };

    websocket.onmessage = (event) => {
      const data = event.data;
      if (data === '<<END>>') {
        setIsStreaming(false);
        websocket.close();
        return;
      }
      if (data === '<<E:NO_QUERY>>') {
        currentAiContent = 'Error: No query provided.';
        setChatMessages(prevMessages =>
          prevMessages.map(msg =>
            msg.id === aiMessageId ? { ...msg, content: currentAiContent } : msg
          )
        );
        setIsStreaming(false);
        websocket.close();
        return;
      }
      
      currentAiContent += data;
      setChatMessages(prevMessages =>
        prevMessages.map(msg =>
          msg.id === aiMessageId ? { ...msg, content: currentAiContent } : msg
        )
      );
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      currentAiContent = 'Error connecting to the server. Please try again.';
      setChatMessages(prevMessages =>
        prevMessages.map(msg =>
          msg.id === aiMessageId ? { ...msg, content: currentAiContent } : msg
        )
      );
      setIsStreaming(false);
    };

    websocket.onclose = () => {
      setIsStreaming(false);
    };
  };

  return (
    <ThemeProvider>
      <div className={`app-container ${isSidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
        <Sidebar
          uploadedFiles={uploadedFiles}
          onToggleActive={toggleFileActiveStatus}
          onNewChat={handleNewChat}
          isOpen={isSidebarOpen}
          onDeleteFile={handleDeleteFile}
        />
        
        <ChatContainer
          messages={chatMessages}
          query={query}
          isStreaming={isStreaming}
          onQueryChange={handleQueryChange}
          onSubmit={handleQuerySubmit}
          onFileChange={handleFileChange}
          isUploadingFile={isStreamingUpload}
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={toggleSidebar}
          isAnyFileActive={isAnyFileActive}
        />

        <Toast message={toastMessage} isVisible={isToastVisible} />
      </div>
    </ThemeProvider>
  );
}

export default App
