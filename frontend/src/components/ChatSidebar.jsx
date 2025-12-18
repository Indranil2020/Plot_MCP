import React, { useEffect, useRef, useState } from 'react';
import ProjectExplorer from './ProjectExplorer';
import SessionList from './SessionList';
import './ChatSidebar.css';

const ChatSidebar = ({
  messages,
  isProcessing,
  onSendMessage,
  provider,
  setProvider,
  apiKey,
  setApiKey,
  model,
  setModel,
  onPasteData,
  projects,
  currentProject,
  projectFiles,
  selectedFiles,
  onCreateProject,
  onSelectProject,
  onUploadFiles,
  onToggleFile,
  sessions,
  currentSessionId,
  onSelectSession,
  onCreateSession
}) => {
  const [input, setInput] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (event) => {
    event.preventDefault();
    if (input.trim() && !isProcessing) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const selectedLabels = selectedFiles.map((path) => {
    const parts = path.split(/[/\\]/);
    return { path, label: parts[parts.length - 1] };
  });

  return (
    <div className="chat-sidebar">
      <div className="chat-header">
        <h2>Plot Assistant</h2>
        <div className="header-actions">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="icon-btn"
            title="Settings"
          >
            Settings
          </button>
        </div>
      </div>

      {showSettings && (
        <div className="settings-panel">
          <div className="setting-group">
            <label>Provider:</label>
            <select value={provider} onChange={(event) => setProvider(event.target.value)}>
              <option value="ollama">Ollama (Local)</option>
              <option value="gemini">Google Gemini</option>
              <option value="openai">OpenAI</option>
            </select>
          </div>
          {(provider === 'gemini' || provider === 'openai') && (
            <div className="setting-group">
              <label>API Key:</label>
              <input
                type="password"
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
                placeholder="Enter API Key"
              />
            </div>
          )}
          <div className="setting-group">
            <label>Model (Optional):</label>
            <input
              type="text"
              value={model}
              onChange={(event) => setModel(event.target.value)}
              placeholder={provider === 'ollama' ? 'llama3' : 'Default'}
            />
          </div>
        </div>
      )}

      <div className="sidebar-tools">
        <ProjectExplorer
          projects={projects}
          currentProject={currentProject}
          projectFiles={projectFiles}
          selectedFiles={selectedFiles}
          onSelectProject={onSelectProject}
          onCreateProject={onCreateProject}
          onUploadFiles={onUploadFiles}
          onToggleFile={onToggleFile}
          onPasteData={onPasteData}
          isProcessing={isProcessing}
        />
        <SessionList
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSelectSession={onSelectSession}
          onCreateSession={onCreateSession}
          isProcessing={isProcessing}
        />
      </div>

      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-content">{msg.content}</div>
          </div>
        ))}
        {isProcessing && (
          <div className="message assistant">
            <div className="message-content typing">Thinking...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {selectedLabels.length > 0 && (
        <div className="selected-files-bar">
          <span className="selected-label">Selected files:</span>
          <div className="selected-files-list">
            {selectedLabels.map((item) => (
              <span key={item.path} className="selected-file-chip">
                {item.label}
              </span>
            ))}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Describe your plot or ask for changes..."
          disabled={isProcessing}
          className="chat-input"
        />
        <button type="submit" disabled={isProcessing || !input.trim()} className="send-btn">
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatSidebar;
