import React, { useState } from 'react';
import ChatSidebar from './components/ChatSidebar';
import PlotCanvas from './components/PlotCanvas';
import GalleryBrowser from './components/GalleryBrowser';
import DataAnalysisPanel from './components/DataAnalysisPanel';
import DataEditor from './components/DataEditor';
import './App.css';

const API_URL = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your intelligent plotting assistant. Upload data or browse the gallery to get started.' }
  ]);
  const [currentPlot, setCurrentPlot] = useState(null);
  const [currentMetadata, setCurrentMetadata] = useState([]);
  const [currentCode, setCurrentCode] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [dataAnalysis, setDataAnalysis] = useState(null);

  // Settings state
  const [provider, setProvider] = useState('ollama');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('');

  const handleFileUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      setMessages(prev => [...prev, { role: 'user', content: `Uploaded: ${file.name}` }]);
      setIsProcessing(true);

      const response = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      setUploadedFile(data.path);
      setDataAnalysis(data.analysis);

      const suggestedText = data.analysis.suggested_plots.length > 0
        ? `\n\nSuggested plots: ${data.analysis.suggested_plots.map(p => p.type).join(', ')}`
        : '';

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `✅ File uploaded! Found ${data.preview.length} rows.${suggestedText} What would you like to visualize?`
      }]);
    } catch (error) {
      console.error('Error uploading file:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: '❌ Error uploading file.' }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSendMessage = async (text) => {
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setIsProcessing(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: text,
          context: uploadedFile,
          current_code: currentCode,
          provider: provider,
          api_key: apiKey,
          model: model
        }),
      });

      const data = await response.json();

      if (data.plot) {
        setCurrentPlot(data.plot);
        setCurrentMetadata(data.metadata || []);
        setCurrentCode(data.code);
      }

      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: '❌ Sorry, something went wrong.' }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleGallerySelect = async (example) => {
    // Send the example request to the backend
    await handleSendMessage(`Create a plot based on this example: ${example.title}. Adapt it to my data.`);
  };

  const [showDataEditor, setShowDataEditor] = useState(false);
  const [editorSchema, setEditorSchema] = useState(null);

  const handleDataSave = async (dataText, format) => {
    setShowDataEditor(false);
    setEditorSchema(null);
    setIsProcessing(true);

    try {
      const response = await fetch(`${API_URL}/paste_data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data: dataText,
          format: format
        }),
      });

      const data = await response.json();
      setUploadedFile(data.path);
      setDataAnalysis(data.analysis);

      // Show parsing validation info if available
      let validationMessage = '';
      if (data.parsing_info) {
        const info = data.parsing_info;
        validationMessage = `\n\n📊 Data Parsing Details:
- Detected delimiter: ${info.detected_delimiter === ',' ? 'comma' : info.detected_delimiter === '\t' ? 'tab' : info.detected_delimiter === ' ' ? 'space' : info.detected_delimiter}
- Rows parsed: ${info.rows_parsed}
- Columns parsed: ${info.columns_parsed}
- Column names: ${info.column_names.join(', ')}

Sample data (first row):
${JSON.stringify(info.sample_data[0] || {}, null, 2)}`;
      }

      const suggestedText = data.analysis.suggested_plots.length > 0
        ? `\n\nSuggested plots: ${data.analysis.suggested_plots.map(p => p.type).join(', ')}`
        : '';

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `✅ Data pasted! Found ${data.preview.length} rows.${validationMessage}${suggestedText}\n\nWhat would you like to visualize?`
      }]);
    } catch (error) {
      console.error('Error pasting data:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '❌ Error processing data. Please check the format.'
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="app-layout">
      {showDataEditor && (
        <DataEditor
          onSave={handleDataSave}
          onClose={() => {
            setShowDataEditor(false);
            setEditorSchema(null);
          }}
          schemaSuggestion={editorSchema}
        />
      )}
      {/* Left Sidebar - Chat */}
      <ChatSidebar
        messages={messages}
        isProcessing={isProcessing}
        onSendMessage={handleSendMessage}
        onFileUpload={handleFileUpload}
        provider={provider}
        setProvider={setProvider}
        apiKey={apiKey}
        setApiKey={setApiKey}
        model={model}
        setModel={setModel}
        onPasteData={() => setShowDataEditor(true)}
      />

      {/* Center - Plot Canvas (Maximum Visibility) */}
      <div className="main-content">
        {dataAnalysis && !currentPlot && (
          <DataAnalysisPanel
            analysis={dataAnalysis}
            onSuggestionClick={(suggestion) => {
              handleSendMessage(`Create a ${suggestion.type}. ${suggestion.reason}`);
            }}
          />
        )}
        <PlotCanvas
          plotData={currentPlot}
          metadata={currentMetadata}
          code={currentCode}
          context={uploadedFile}
          onCodeEdit={setCurrentCode}
          onSendToChat={handleSendMessage}
        />
      </div>

      {/* Right Sidebar - Gallery Browser (Always Visible) */}
      <GalleryBrowser
        onSelectExample={handleGallerySelect}
      />
    </div>
  );
}

export default App;
