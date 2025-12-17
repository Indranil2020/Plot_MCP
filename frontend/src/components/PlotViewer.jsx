import React, { useState } from 'react';

const PlotViewer = ({ plotData, code }) => {
    const [showCode, setShowCode] = useState(false);

    const downloadPlot = () => {
        const link = document.createElement('a');
        link.href = `data:image/png;base64,${plotData}`;
        link.download = `plot_${Date.now()}.png`;
        link.click();
    };

    const copyCode = () => {
        navigator.clipboard.writeText(code);
        alert('Code copied to clipboard!');
    };

    if (!plotData) {
        return (
            <div className="main-content">
                <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '3rem' }}>
                    <h1>🎨 Ready to Create Beautiful Plots</h1>
                    <p>Upload a dataset and ask me to visualize it.</p>
                    <p style={{ fontSize: '0.9rem', marginTop: '1rem', color: '#666' }}>
                        I can create publication-quality plots with full Matplotlib capabilities.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="main-content">
            <div className="plot-container">
                <div className="card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h3>📊 Generated Plot (300 DPI)</h3>
                        <button onClick={downloadPlot} className="download-btn">
                            ⬇️ Download PNG
                        </button>
                    </div>
                    <img
                        src={`data:image/png;base64,${plotData}`}
                        alt="Generated Plot"
                        className="plot-image"
                    />
                </div>

                <div className="card">
                    <div
                        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', cursor: 'pointer' }}
                        onClick={() => setShowCode(!showCode)}
                    >
                        <h3>💻 Generated Code</h3>
                        <div>
                            {showCode && (
                                <button onClick={(e) => { e.stopPropagation(); copyCode(); }} className="copy-btn" style={{ marginRight: '1rem' }}>
                                    📋 Copy
                                </button>
                            )}
                            <span>{showCode ? '▼' : '▶'}</span>
                        </div>
                    </div>

                    {showCode && (
                        <pre className="code-block">
                            <code>{code}</code>
                        </pre>
                    )}
                </div>
            </div>
        </div>
    );
};

export default PlotViewer;
