import React, { useState } from 'react';
import './PlotCanvas.css';

const PlotCanvas = ({ plotData, metadata, code, context, onCodeEdit, onSendToChat }) => {
    const [showCode, setShowCode] = useState(false);
    const [editedCode, setEditedCode] = useState('');
    const [isEditingCode, setIsEditingCode] = useState(false);
    const [hoveredElement, setHoveredElement] = useState(null);

    const [showDownloadOptions, setShowDownloadOptions] = useState(false);
    const [downloadFormat, setDownloadFormat] = useState('png');
    const [downloadDpi, setDownloadDpi] = useState(300);
    const [isDownloading, setIsDownloading] = useState(false);

    const handleDownload = async () => {
        setIsDownloading(true);
        try {
            const response = await fetch('http://localhost:8000/download_plot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    code: code,
                    context: context,
                    format: downloadFormat,
                    dpi: parseInt(downloadDpi)
                }),
            });

            if (!response.ok) throw new Error('Download failed');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `plot_${Date.now()}.${downloadFormat}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            setShowDownloadOptions(false);
        } catch (error) {
            console.error('Download error:', error);
            alert('Failed to download plot');
        } finally {
            setIsDownloading(false);
        }
    };

    const copyCode = () => {
        navigator.clipboard.writeText(code);
        // Visual feedback
        const btn = document.querySelector('.copy-code-btn');
        if (btn) {
            const originalText = btn.textContent;
            btn.textContent = '✅ Copied!';
            setTimeout(() => btn.textContent = originalText, 2000);
        }
    };

    const handleCodeEdit = () => {
        setEditedCode(code);
        setIsEditingCode(true);
    };

    const applyCodeEdit = () => {
        onCodeEdit(editedCode);
        onSendToChat(`Execute this modified code: ${editedCode}`);
        setIsEditingCode(false);
    };

    const handleElementClick = (element) => {
        const promptMessages = {
            title: `Current title: "${element.text}"\n\nWhat would you like to change it to?`,
            xlabel: `Current X-axis label: "${element.text}"\n\nWhat would you like to change it to?`,
            ylabel: `Current Y-axis label: "${element.text}"\n\nWhat would you like to change it to?`,
            legend: `What would you like to do with the legend?\n(e.g., "move to upper left", "remove legend", "change font size to 12")`
        };

        const promptMessage = promptMessages[element.type] || `How would you like to modify the ${element.type}?`;
        const userInput = prompt(promptMessage);

        if (userInput && userInput.trim()) {
            // Create a more specific instruction for the LLM
            let instruction = '';
            switch (element.type) {
                case 'title':
                    instruction = `Change the plot title to: ${userInput.trim()}`;
                    break;
                case 'xlabel':
                    instruction = `Change the X-axis label to: ${userInput.trim()}`;
                    break;
                case 'ylabel':
                    instruction = `Change the Y-axis label to: ${userInput.trim()}`;
                    break;
                case 'legend':
                    instruction = `Modify the legend: ${userInput.trim()}`;
                    break;
                default:
                    instruction = userInput.trim();
            }
            onSendToChat(instruction);
        }
    };

    if (!plotData) {
        return (
            <div className="plot-canvas empty">
                <div className="empty-state">
                    <div className="empty-icon">[ ]</div>
                    <h1>Ready to Create Beautiful Plots</h1>
                    <p>Upload your data or browse the gallery to get started</p>
                    <div className="features">
                        <div className="feature">
                            <span className="feature-icon">[*]</span>
                            <span>Publication Quality (300 DPI)</span>
                        </div>
                        <div className="feature">
                            <span className="feature-icon">[↻]</span>
                            <span>Iterative Editing</span>
                        </div>
                        <div className="feature">
                            <span className="feature-icon">[☰]</span>
                            <span>509 Official Examples</span>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="plot-canvas">
            {/* Toolbar */}
            <div className="plot-toolbar">
                <div className="toolbar-left">
                    <h3>Generated Plot</h3>
                    <span className="quality-badge">{downloadDpi} DPI</span>
                </div>
                <div className="toolbar-right">
                    <button onClick={() => setShowCode(!showCode)} className="toolbar-btn">
                        {showCode ? '[IMG] Show Plot' : '[</>] View Code'}
                    </button>
                    <button onClick={copyCode} className="toolbar-btn copy-code-btn">
                        [COPY] Copy Code
                    </button>
                    <div className="download-wrapper" style={{ position: 'relative', display: 'inline-block' }}>
                        <button
                            onClick={() => setShowDownloadOptions(!showDownloadOptions)}
                            className="toolbar-btn download-btn"
                        >
                            [↓] Download
                        </button>
                        {showDownloadOptions && (
                            <div className="download-options-popover" style={{
                                position: 'absolute',
                                top: '100%',
                                right: 0,
                                backgroundColor: '#1e1e1e',
                                border: '1px solid #333',
                                borderRadius: '4px',
                                padding: '10px',
                                zIndex: 1000,
                                minWidth: '200px',
                                boxShadow: '0 4px 6px rgba(0,0,0,0.3)'
                            }}>
                                <div style={{ marginBottom: '10px' }}>
                                    <label style={{ display: 'block', marginBottom: '5px', color: '#aaa', fontSize: '12px' }}>Format</label>
                                    <select
                                        value={downloadFormat}
                                        onChange={(e) => setDownloadFormat(e.target.value)}
                                        style={{ width: '100%', padding: '5px', background: '#2d2d2d', color: '#fff', border: '1px solid #444' }}
                                    >
                                        <option value="png">PNG Image</option>
                                        <option value="pdf">PDF Document</option>
                                        <option value="svg">SVG Vector</option>
                                    </select>
                                </div>
                                <div style={{ marginBottom: '10px' }}>
                                    <label style={{ display: 'block', marginBottom: '5px', color: '#aaa', fontSize: '12px' }}>Quality (DPI)</label>
                                    <select
                                        value={downloadDpi}
                                        onChange={(e) => setDownloadDpi(e.target.value)}
                                        style={{ width: '100%', padding: '5px', background: '#2d2d2d', color: '#fff', border: '1px solid #444' }}
                                    >
                                        <option value="72">72 DPI (Screen)</option>
                                        <option value="150">150 DPI (Draft)</option>
                                        <option value="300">300 DPI (Print)</option>
                                        <option value="600">600 DPI (High Res)</option>
                                    </select>
                                </div>
                                <button
                                    onClick={handleDownload}
                                    disabled={isDownloading}
                                    style={{
                                        width: '100%',
                                        padding: '8px',
                                        background: '#007bff',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '4px',
                                        cursor: isDownloading ? 'wait' : 'pointer',
                                        opacity: isDownloading ? 0.7 : 1
                                    }}
                                >
                                    {isDownloading ? 'Downloading...' : 'Download File'}
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Plot or Code View */}
            <div className="plot-content">
                {!showCode ? (
                    <div className="plot-image-container">
                        <div className="interactive-plot-wrapper" style={{ position: 'relative', display: 'inline-block' }}>
                            <img
                                src={`data:image/png;base64,${plotData}`}
                                alt="Generated Plot"
                                className="plot-image"
                            />
                            {/* Interactive Overlays */}
                            {metadata && metadata.map((item, index) => (
                                <div
                                    key={index}
                                    className={`plot-overlay ${item.type}`}
                                    style={{
                                        position: 'absolute',
                                        left: `${item.bbox[0] * 100}%`,
                                        bottom: `${item.bbox[1] * 100}%`, // Matplotlib uses bottom-left origin
                                        width: `${item.bbox[2] * 100}%`,
                                        height: `${item.bbox[3] * 100}%`,
                                        cursor: 'pointer',
                                        border: hoveredElement === index ? '2px solid #007bff' : 'none',
                                        backgroundColor: hoveredElement === index ? 'rgba(0, 123, 255, 0.1)' : 'transparent',
                                        borderRadius: '4px',
                                        transition: 'all 0.2s ease'
                                    }}
                                    onMouseEnter={() => setHoveredElement(index)}
                                    onMouseLeave={() => setHoveredElement(null)}
                                    onClick={() => handleElementClick(item)}
                                    title={`Click to edit ${item.type}`}
                                />
                            ))}
                        </div>
                        <div className="plot-hint">
                            Tip: Click on plot elements (title, labels) to edit them
                        </div>
                    </div>
                ) : (
                    <div className="code-view">
                        {!isEditingCode ? (
                            <>
                                <div className="code-header">
                                    <h4>Generated Code</h4>
                                    <button onClick={handleCodeEdit} className="edit-code-btn">
                                        [EDIT] Edit Code
                                    </button>
                                </div>
                                <pre className="code-block">
                                    <code>{code}</code>
                                </pre>
                            </>
                        ) : (
                            <>
                                <div className="code-header">
                                    <h4>Edit Code</h4>
                                    <div>
                                        <button onClick={() => setIsEditingCode(false)} className="cancel-btn">
                                            [X] Cancel
                                        </button>
                                        <button onClick={applyCodeEdit} className="apply-btn">
                                            [✓] Apply Changes
                                        </button>
                                    </div>
                                </div>
                                <textarea
                                    value={editedCode}
                                    onChange={(e) => setEditedCode(e.target.value)}
                                    className="code-editor"
                                    rows={20}
                                />
                            </>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default PlotCanvas;
