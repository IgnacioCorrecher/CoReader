import './App.css'
import { useState } from 'react'

function App() {

  const [query, setQuery] = useState<string>('');
  const [response, setResponse] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState<boolean>(false);

  const handleQueryChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuery(event.target.value);
  };


  const handleQuerySubmit = () => {

    // Check if Empty, and if so do nothing
    if (!query.trim()) return;
  
    // Open Websocket Instance
    const websocket = new WebSocket('ws://localhost:8000/ws/stream');
    setIsStreaming(true);
    setResponse('');
  
    // Triggers when the websocket connection is successful
    websocket.onopen = () => {
      console.log('WebSocket connection opened.');
      websocket.send(JSON.stringify({ query }));
      console.log('Query sent to backend.');
    };
  
    // Triggers when backend sends any message (A token response from the LLM)
    websocket.onmessage = (event) => {
      const data = event.data;
      console.log('data: ', data);

      if (data === '<<END>>'){
        websocket.close();
        setIsStreaming(false);
        return;
      }
      if (data === '<<E:NO_QUERY>>'){
        console.log('ERROR: No Query, closing connection...');
        websocket.close();
        setIsStreaming(false);
        return;
      }

      setResponse((prevResponse) => prevResponse + data);

    };
  
    // Triggers when error ocurrs
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      websocket.close();
      setIsStreaming(false);
    };
  
    // Triggers when websocket closes
    websocket.onclose = () => {
      console.log('WebSocket connection closed');
      setIsStreaming(false);
    };
  };

  return (
    <div className='main-div'>

      <div className='header-container'>
        {/* Title */}
        <h1>RAG application</h1>

        {/* Query Input Bar */}
        <div className='query-input-bar'>
          <textarea
            className='query-textarea'
            value = {query}
            onChange={handleQueryChange}
            placeholder="AMA about your file..."
            rows={5}
            cols={100}
          ></textarea>
          <button
            className='sumbit-btn'
            onClick={handleQuerySubmit}
            disabled={isStreaming}
          >
            Sumbit
          </button>
        </div>
      </div>

      <div className='response-container'>
        {response}
      </div>
      
    </div>
  )
}

export default App
