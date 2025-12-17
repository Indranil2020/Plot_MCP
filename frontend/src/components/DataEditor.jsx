import React, { useState } from 'react';
import './DataEditor.css';

const DataEditor = ({ initialData, onSave, onClose, schemaSuggestion }) => {
    const [dataText, setDataText] = useState(initialData || '');
    const [format, setFormat] = useState('csv'); // csv or json

    const handleSave = () => {
        // Basic validation
        if (!dataText.trim()) {
            alert('Please enter some data');
            return;
        }
        onSave(dataText, format);
    };

    return (
        <div className="data-editor-overlay">
            <div className="data-editor-modal">
                <div className="editor-header">
                    <h3>Data Editor</h3>
                    <button onClick={onClose} className="close-btn">×</button>
                </div>

                {schemaSuggestion && (
                    <div className="schema-suggestion">
                        <h4>Required Format for {schemaSuggestion.plotType}:</h4>
                        <pre>{schemaSuggestion.template}</pre>
                        <p className="suggestion-note">{schemaSuggestion.description}</p>
                    </div>
                )}

                <div className="editor-toolbar">
                    <div className="format-selector">
                        <label>
                            <input
                                type="radio"
                                value="csv"
                                checked={format === 'csv'}
                                onChange={(e) => setFormat(e.target.value)}
                            /> CSV
                        </label>
                        <label>
                            <input
                                type="radio"
                                value="json"
                                checked={format === 'json'}
                                onChange={(e) => setFormat(e.target.value)}
                            /> JSON
                        </label>
                    </div>
                    <button
                        className="clear-btn"
                        onClick={() => setDataText('')}
                    >
                        Clear
                    </button>
                </div>

                <textarea
                    className="data-input"
                    value={dataText}
                    onChange={(e) => setDataText(e.target.value)}
                    placeholder={format === 'csv' ? "col1,col2,col3\n1,2,3\n4,5,6" : "[\n  {\"col1\": 1, \"col2\": 2},\n  {\"col1\": 4, \"col2\": 5}\n]"}
                    spellCheck="false"
                />

                <div className="editor-footer">
                    <button onClick={onClose} className="cancel-btn">Cancel</button>
                    <button onClick={handleSave} className="save-btn">Use This Data</button>
                </div>
            </div>
        </div>
    );
};

export default DataEditor;
