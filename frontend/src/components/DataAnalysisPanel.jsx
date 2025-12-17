import React from 'react';
import './DataAnalysisPanel.css';

const DataAnalysisPanel = ({ analysis, onSuggestionClick }) => {
    if (!analysis) return null;

    return (
        <div className="data-analysis-panel">
            <div className="analysis-header">
                <h3>Data Analysis</h3>
                <span className="data-shape">{analysis.shape[0]} rows × {analysis.shape[1]} columns</span>
            </div>

            <div className="analysis-content">
                <div className="column-types">
                    <div className="type-group">
                        <span className="type-label">Numeric:</span>
                        <span className="type-count">{analysis.numeric_cols.length}</span>
                    </div>
                    <div className="type-group">
                        <span className="type-label">Categorical:</span>
                        <span className="type-count">{analysis.categorical_cols.length}</span>
                    </div>
                    <div className="type-group">
                        <span className="type-label">Date/Time:</span>
                        <span className="type-count">{analysis.datetime_cols.length}</span>
                    </div>
                </div>

                {analysis.warnings && analysis.warnings.length > 0 && (
                    <div className="analysis-warnings">
                        <h4>⚠️ Data Issues</h4>
                        <ul>
                            {analysis.warnings.map((warning, idx) => (
                                <li key={idx}>{warning}</li>
                            ))}
                        </ul>
                    </div>
                )}

                <div className="smart-suggestions">
                    <h4>Recommended Visualizations</h4>
                    <div className="suggestion-cards">
                        {analysis.suggested_plots.map((suggestion, idx) => (
                            <div
                                key={idx}
                                className="suggestion-card"
                                onClick={() => onSuggestionClick(suggestion)}
                            >
                                <div className="suggestion-header">
                                    <span className="suggestion-type">{suggestion.type}</span>
                                    <span className="confidence-badge" style={{
                                        backgroundColor: suggestion.confidence > 0.8 ? '#4caf50' : '#ff9800'
                                    }}>
                                        {Math.round(suggestion.confidence * 100)}% Match
                                    </span>
                                </div>
                                <p className="suggestion-reason">{suggestion.reason}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DataAnalysisPanel;
