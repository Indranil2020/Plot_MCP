import React, { useState, useRef, useEffect } from 'react';
import './ChatSidebar.css';

const ChatSidebar = ({
    messages,
    isProcessing,
    onSendMessage,
    onFileUpload,
    provider,
    setProvider,
    apiKey,
    setApiKey,
    model,
    setModel,
    onPasteData
}) => {
    const [input, setInput] = useState('');
    const [showSettings, setShowSettings] = useState(false);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (input.trim() && !isProcessing) {
            onSendMessage(input);
            setInput('');
        }
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            onFileUpload(file);
        }
    };

    return (
        <div className="chat-sidebar">
            {/* Header */}
            <div className="chat-header">
                <h2>Plot Assistant</h2>
                <div className="header-actions">
                    <button
                        onClick={() => setShowSettings(!showSettings)}
                        className="icon-btn"
                        title="Settings"
                    >
                        ⚙
                    </button>
                </div>
            </div>

            {/* Settings Panel */}
            {showSettings && (
                <div className="settings-panel">
                    <div className="setting-group">
                        <label>Provider:</label>
                        <select value={provider} onChange={(e) => setProvider(e.target.value)}>
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
                                onChange={(e) => setApiKey(e.target.value)}
                                placeholder="Enter API Key"
                            />
                        </div>
                    )}
                    <div className="setting-group">
                        <label>Model (Optional):</label>
                        <input
                            type="text"
                            value={model}
                            onChange={(e) => setModel(e.target.value)}
                            placeholder={provider === 'ollama' ? 'llama3' : 'Default'}
                        />
                    </div>
                </div>
            )}

            {/* File Upload */}
            <div className="file-upload-section">
                <div className="upload-buttons">
                    <button
                        onClick={() => fileInputRef.current.click()}
                        className="upload-btn"
                        title="Upload File"
                    >
                        ⬆ Upload
                    </button>
                    <button
                        onClick={onPasteData}
                        className="upload-btn paste-btn"
                        title="Paste Data"
                    >
                        📋 Paste
                    </button>
                </div>
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,.json"
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                />
            </div>

            {/* Messages */}
            <div className="chat-messages">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.role} `}>
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

            {/* Input */}
            <form onSubmit={handleSubmit} className="chat-input-form">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Describe your plot or ask for changes..."
                    disabled={isProcessing}
                    className="chat-input"
                />
                <button
                    type="submit"
                    disabled={isProcessing || !input.trim()}
                    className="send-btn"
                >
                    →
                </button>
            </form>
        </div>
    );
};

export default ChatSidebar;
