import React, { useState, useRef, useEffect } from 'react';

const ChatInterface = ({ onSendMessage, messages, isProcessing, onFileUpload }) => {
    const [input, setInput] = useState('');
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!input.trim() || isProcessing) return;
        onSendMessage(input);
        setInput('');
    };

    const handleFileChange = (e) => {
        if (e.target.files[0]) {
            onFileUpload(e.target.files[0]);
        }
    };

    return (
        <div className="sidebar">
            <div className="upload-area" onClick={() => fileInputRef.current.click()}>
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                    accept=".csv,.json"
                />
                <p>Click to upload CSV/JSON</p>
            </div>

            <div className="chat-messages">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.role}`}>
                        {msg.content}
                    </div>
                ))}
                {isProcessing && (
                    <div className="message assistant">
                        Thinking...
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSubmit}>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Describe the plot you want..."
                    disabled={isProcessing}
                />
                <button type="submit" className="btn" style={{ width: '100%' }} disabled={isProcessing}>
                    Send
                </button>
            </form>
        </div>
    );
};

export default ChatInterface;
