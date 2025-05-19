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
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isStreamingUpload, setIsStreamingUpload] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string>('');
  const [isToastVisible, setIsToastVisible] = useState<boolean>(false);

  const chatEndRef = useRef<HTMLDivElement>(null);

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

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) {
      setToastMessage('Please select a file first.');
      setIsToastVisible(true);
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    setIsStreamingUpload(true);

    try {
      const res = await fetch('http://localhost:8000/upload_file', {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        await res.json();
        setToastMessage("File uploaded successfully!");
        setIsToastVisible(true);

        if (selectedFile) {
          const newFile: UploadedFile = {
            id: selectedFile.name,
            name: selectedFile.name,
            isActive: true,
          };
          if (!uploadedFiles.find(f => f.name === newFile.name)) {
            setUploadedFiles(prevFiles => [...prevFiles, newFile]);
          }
        }
        setSelectedFile(null);
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
  };

  const toggleFileActiveStatus = (fileId: string) => {
    setUploadedFiles(prevFiles =>
      prevFiles.map(file =>
        file.id === fileId ? { ...file, isActive: !file.isActive } : file
      )
    );
  };

  const handleNewChat = () => {
    setChatMessages([]);
  };

  const handleQuerySubmit = () => {
    if (!query.trim()) return;

    const userMessage: ChatMessage = {
      id: 'user-' + Date.now(),
      type: 'user',
      content: query,
    };
    setChatMessages(prevMessages => [...prevMessages, userMessage]);

    const websocket = new WebSocket('ws://localhost:8000/ws/stream');
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
      <div className="app-container">
        <Sidebar
          selectedFile={selectedFile}
          isStreaming={isStreamingUpload}
          uploadedFiles={uploadedFiles}
          onFileChange={handleFileChange}
          onUpload={handleFileUpload}
          onToggleActive={toggleFileActiveStatus}
          onNewChat={handleNewChat}
        />
        
        <ChatContainer
          messages={chatMessages}
          query={query}
          isStreaming={isStreaming}
          onQueryChange={handleQueryChange}
          onSubmit={handleQuerySubmit}
        />

        <Toast message={toastMessage} isVisible={isToastVisible} />
      </div>
    </ThemeProvider>
  );
}

export default App
