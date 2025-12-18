import React from 'react';
import './SessionList.css';

const SessionList = ({
  sessions,
  currentSessionId,
  onSelectSession,
  onCreateSession,
  isProcessing
}) => {
  return (
    <div className="session-list">
      <div className="section-header">
        <span>Chats</span>
        <button
          type="button"
          onClick={onCreateSession}
          className="session-create-btn"
          disabled={isProcessing}
        >
          New
        </button>
      </div>

      {sessions.length === 0 && (
        <div className="session-empty">No chats yet.</div>
      )}

      {sessions.map((session) => (
        <button
          key={session.id}
          type="button"
          className={`session-item ${session.id === currentSessionId ? 'active' : ''}`}
          onClick={() => onSelectSession(session.id)}
          disabled={isProcessing}
        >
          <div className="session-title">{session.title || 'Untitled chat'}</div>
          {session.project_name && (
            <div className="session-meta">Project: {session.project_name}</div>
          )}
          {session.last_message && (
            <div className="session-preview">{session.last_message}</div>
          )}
        </button>
      ))}
    </div>
  );
};

export default SessionList;
