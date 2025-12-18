import React from 'react';
import './DataPreviewPanel.css';

const DataPreviewPanel = ({ analysis, preview, fileName }) => {
  if (!analysis) return null;

  const columns = analysis.columns || [];
  const dtypes = (analysis.dtypes || analysis.schema?.dtypes) ?? {};

  return (
    <div className="data-preview-panel">
      <div className="preview-header">
        <div>
          <h3>Data Preview</h3>
          {fileName && <p className="preview-subtitle">{fileName}</p>}
        </div>
        {analysis.shape && (
          <span className="preview-shape">{analysis.shape[0]} rows × {analysis.shape[1]} cols</span>
        )}
      </div>

      <div className="preview-body">
        <div className="preview-table">
          <table>
            <thead>
              <tr>
                {columns.map((col) => (
                  <th key={col}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(preview || []).map((row, idx) => (
                <tr key={idx}>
                  {columns.map((col) => (
                    <td key={col}>{row[col]?.toString()}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="type-summary">
          <h4>Type Summary</h4>
          <div className="type-list">
            {columns.map((col) => (
              <div key={col} className="type-row">
                <span className="type-col">{col}</span>
                <span className="type-dtype">{dtypes[col] || 'unknown'}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataPreviewPanel;
