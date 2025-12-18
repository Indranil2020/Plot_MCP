import React from 'react';
import './JoinAssistantPanel.css';

const JoinAssistantPanel = ({ suggestions }) => {
  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div className="join-assistant-panel">
      <div className="join-header">
        <h3>Join Assistant</h3>
        <span className="join-subtitle">Suggested keys for merging files</span>
      </div>
      <div className="join-list">
        {suggestions.map((suggestion, idx) => (
          <div key={`${suggestion.left}-${suggestion.right}-${suggestion.key}-${idx}`} className="join-card">
            <div className="join-title">
              {suggestion.left} ⟷ {suggestion.right}
            </div>
            <div className="join-key">Key: {suggestion.key}</div>
            <div className="join-example">{suggestion.example}</div>
            {suggestion.warnings && suggestion.warnings.length > 0 && (
              <div className="join-warnings">
                {suggestion.warnings.map((warning) => (
                  <div key={warning} className="join-warning">
                    {warning}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default JoinAssistantPanel;
