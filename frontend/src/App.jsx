import React, { useEffect, useRef, useState } from 'react';
import ChatSidebar from './components/ChatSidebar';
import PlotCanvas from './components/PlotCanvas';
import DataEditor from './components/DataEditor';
import InspectorDrawer from './components/InspectorDrawer';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const DEFAULT_MESSAGE = {
  role: 'assistant',
  content: 'Hello! Create or open a project, then upload data to get started.'
};

function App() {
  const [messages, setMessages] = useState([DEFAULT_MESSAGE]);
  const [currentPlot, setCurrentPlot] = useState(null);
  const [currentMetadata, setCurrentMetadata] = useState([]);
  const [currentCode, setCurrentCode] = useState(null);
  const [sessionArtifacts, setSessionArtifacts] = useState({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [dataAnalysis, setDataAnalysis] = useState(null);

  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState('');
  const [projectFiles, setProjectFiles] = useState([]);
  const [datasetRegistry, setDatasetRegistry] = useState([]);
  const [plotHistory, setPlotHistory] = useState([]);
  const [plotHistoryIndex, setPlotHistoryIndex] = useState(0);
  const [selectedFiles, setSelectedFiles] = useState([]);

  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);

  const [provider, setProvider] = useState('ollama');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('');

  const [showDataEditor, setShowDataEditor] = useState(false);
  const [editorSchema, setEditorSchema] = useState(null);

  const [previewData, setPreviewData] = useState([]);
  const [previewAnalysis, setPreviewAnalysis] = useState(null);
  const [previewFileName, setPreviewFileName] = useState('');
  const [joinSuggestions, setJoinSuggestions] = useState([]);

  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [inspectorTab, setInspectorTab] = useState('preview');

  const [sidebarWidth, setSidebarWidth] = useState(360);
  const [isResizingSidebar, setIsResizingSidebar] = useState(false);
  const sidebarResizeStartX = useRef(0);
  const sidebarResizeStartWidth = useRef(360);

  useEffect(() => {
    const initialize = async () => {
      await fetchProjects();
      const sessionList = await fetchSessions();
      if (sessionList.length > 0) {
        await handleSelectSession(sessionList[0].id);
        return;
      }
      const session = await createSession();
      if (session) {
        await handleSelectSession(session.id);
      }
    };

    initialize();
  }, []);

  useEffect(() => {
    if (!isResizingSidebar) return;

    const handleMove = (event) => {
      const delta = event.clientX - sidebarResizeStartX.current;
      const nextWidth = sidebarResizeStartWidth.current + delta;
      const clampedWidth = Math.min(520, Math.max(280, nextWidth));
      setSidebarWidth(clampedWidth);
    };

    const handleUp = () => {
      setIsResizingSidebar(false);
    };

    window.addEventListener('mousemove', handleMove);
    window.addEventListener('mouseup', handleUp);
    return () => {
      window.removeEventListener('mousemove', handleMove);
      window.removeEventListener('mouseup', handleUp);
    };
  }, [isResizingSidebar]);

  useEffect(() => {
    if (plotHistory.length === 0) {
      setPlotHistoryIndex(0);
      return;
    }
    setPlotHistoryIndex(plotHistory.length - 1);
  }, [plotHistory]);

  useEffect(() => {
    const loadPreview = async () => {
      if (selectedFiles.length === 0) {
        setPreviewData([]);
        setPreviewAnalysis(null);
        setPreviewFileName('');
        return;
      }

      const filePath = selectedFiles[0];
      const nameParts = filePath.split(/[/\\]/);
      setPreviewFileName(nameParts[nameParts.length - 1]);

      try {
        const response = await fetch(`${API_URL}/preview`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ file_path: filePath })
        });
        const data = await response.json();
        setPreviewData(data.preview || []);
        setPreviewAnalysis(data.analysis || null);
      } catch (error) {
        console.error('Error loading preview:', error);
        setPreviewData([]);
        setPreviewAnalysis(null);
      }
    };

    loadPreview();
  }, [selectedFiles]);

  useEffect(() => {
    if (!currentProject) return;
    const updateState = async () => {
      await updateProjectUiState({
        selected_files: selectedFiles,
        plot_history_index: plotHistoryIndex
      });
    };
    updateState();
  }, [currentProject, selectedFiles, plotHistoryIndex]);

  useEffect(() => {
    const loadJoinSuggestions = async () => {
      if (selectedFiles.length < 2) {
        setJoinSuggestions([]);
        return;
      }

      try {
        const response = await fetch(`${API_URL}/join_suggestions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ selected_files: selectedFiles })
        });
        const data = await response.json();
        setJoinSuggestions(data.suggestions || []);
      } catch (error) {
        console.error('Error loading join suggestions:', error);
        setJoinSuggestions([]);
      }
    };

    loadJoinSuggestions();
  }, [selectedFiles]);

  const fetchProjects = async () => {
    try {
      const response = await fetch(`${API_URL}/projects`);
      const data = await response.json();
      setProjects(data.projects || []);
      return data.projects || [];
    } catch (error) {
      console.error('Error loading projects:', error);
      return [];
    }
  };

  const fetchProjectFiles = async (projectName) => {
    if (!projectName) return;
    try {
      const response = await fetch(`${API_URL}/projects/${encodeURIComponent(projectName)}/files`);
      const data = await response.json();
      setProjectFiles(data.files || []);
      setDatasetRegistry(data.datasets || []);
      setPlotHistory(data.plots || []);
      if (data.ui_state && Array.isArray(data.ui_state.selected_files)) {
        setSelectedFiles(data.ui_state.selected_files);
      }
    } catch (error) {
      console.error('Error loading project files:', error);
    }
  };

  const updateProjectUiState = async (updates) => {
    if (!currentProject) return;
    const response = await fetch(`${API_URL}/projects/${encodeURIComponent(currentProject)}/ui_state`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
    return response.json();
  };

  const fetchSessions = async () => {
    try {
      const response = await fetch(`${API_URL}/sessions`);
      const data = await response.json();
      const sessionList = data.sessions || [];
      setSessions(sessionList);
      return sessionList;
    } catch (error) {
      console.error('Error loading sessions:', error);
      return [];
    }
  };

  const createSession = async (projectName) => {
    try {
      const response = await fetch(`${API_URL}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_name: projectName || null })
      });
      const data = await response.json();
      if (data.session) {
        setSessions((prev) => [data.session, ...prev]);
        return data.session;
      }
    } catch (error) {
      console.error('Error creating session:', error);
    }
    return null;
  };

  const handleSelectSession = async (sessionId) => {
    if (!sessionId) return;
    try {
      const response = await fetch(`${API_URL}/sessions/${sessionId}/messages`);
      const data = await response.json();
      const nextMessages = data.messages && data.messages.length > 0 ? data.messages : [DEFAULT_MESSAGE];
      setMessages(nextMessages);
      setCurrentSession(sessionId);
      setSelectedFiles(Array.isArray(data.selected_files) ? data.selected_files : []);

      if (data.project_name) {
        setCurrentProject(data.project_name);
        await fetchProjectFiles(data.project_name);
      }

      const artifacts = sessionArtifacts[sessionId] || {};
      setCurrentPlot(artifacts.plot || null);
      setCurrentMetadata(artifacts.metadata || []);
      setCurrentCode(artifacts.code || null);
      setDataAnalysis(null);

      if ((!artifacts.plot || !artifacts.code) && data.plots && data.plots.length > 0) {
        const lastPlot = data.plots[data.plots.length - 1];
        await handleSelectHistoryPlot(lastPlot, data.plots.length - 1, data.project_name);
      }
    } catch (error) {
      console.error('Error selecting session:', error);
    }
  };

  const handleCreateSession = async () => {
    const session = await createSession(currentProject || null);
    if (session) {
      await handleSelectSession(session.id);
    }
  };

  const handleCreateProject = async (name) => {
    try {
      const response = await fetch(`${API_URL}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      });
      if (!response.ok) {
        return;
      }
      await fetchProjects();
      setCurrentProject(name);
      setSelectedFiles([]);
      setProjectFiles([]);
      await fetchProjectFiles(name);
      setMessages((prev) => [...prev, { role: 'assistant', content: `Project created: ${name}` }]);
    } catch (error) {
      console.error('Error creating project:', error);
    }
  };

  const handleSelectProject = async (projectName) => {
    setCurrentProject(projectName);
    setSelectedFiles([]);
    setProjectFiles([]);
    setDataAnalysis(null);
    if (projectName) {
      await fetchProjectFiles(projectName);
    }
  };

  const handleUploadFiles = async (files) => {
    if (!currentProject) {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Select a project before uploading files.' }]);
      return;
    }

    setIsProcessing(true);
    const uploadedPaths = [];

    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_URL}/projects/${encodeURIComponent(currentProject)}/upload`, {
          method: 'POST',
          body: formData
        });
        const data = await response.json();
        if (data.path) {
          uploadedPaths.push(data.path);
        }
        if (data.analysis) {
          setDataAnalysis(data.analysis);
        }
      }

      if (uploadedPaths.length > 0) {
        setSelectedFiles((prev) => {
          const merged = [...prev, ...uploadedPaths];
          return Array.from(new Set(merged));
        });
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `Uploaded ${uploadedPaths.length} file(s) to ${currentProject}.` }
        ]);
      }

      await fetchProjectFiles(currentProject);
    } catch (error) {
      console.error('Error uploading files:', error);
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Error uploading files.' }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleToggleFile = (filePath) => {
    setSelectedFiles((prev) => {
      if (prev.includes(filePath)) {
        return prev.filter((path) => path !== filePath);
      }
      return [...prev, filePath];
    });
  };

  const handleDataSave = async (dataText, format) => {
    if (!currentProject) {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Select a project before pasting data.' }]);
      return;
    }

    setShowDataEditor(false);
    setEditorSchema(null);
    setIsProcessing(true);

    try {
      const response = await fetch(`${API_URL}/paste_data`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data: dataText,
          format: format,
          project_name: currentProject
        })
      });

      const data = await response.json();
      if (data.path) {
        setSelectedFiles((prev) => Array.from(new Set([...prev, data.path])));
      }
      setDataAnalysis(data.analysis);

      const suggestedText = data.analysis && data.analysis.suggested_plots.length > 0
        ? ` Suggested plots: ${data.analysis.suggested_plots.map((p) => p.type).join(', ')}.`
        : '';

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Data saved to ${currentProject}.${suggestedText}`
        }
      ]);
      await fetchProjectFiles(currentProject);
    } catch (error) {
      console.error('Error pasting data:', error);
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Error processing data.' }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSendMessage = async (text) => {
    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setIsProcessing(true);

    try {
      let sessionId = currentSession;
      if (!sessionId) {
        const session = await createSession(currentProject || null);
        sessionId = session?.id;
        if (sessionId) {
          setCurrentSession(sessionId);
        }
      }

      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          context: selectedFiles.length === 1 ? selectedFiles[0] : null,
          selected_files: selectedFiles,
          current_code: currentCode,
          provider: provider,
          api_key: apiKey,
          model: model,
          project_name: currentProject,
          session_id: sessionId
        })
      });

      const data = await response.json();

      if (data.plot) {
        setCurrentPlot(data.plot);
        setCurrentMetadata(data.metadata || []);
        setCurrentCode(data.code);
        if (sessionId) {
          setSessionArtifacts((prev) => ({
            ...prev,
            [sessionId]: {
              plot: data.plot,
              metadata: data.metadata || [],
              code: data.code
            }
          }));
        }
      }

      if (data.plot_entry && currentProject) {
        await fetchProjectFiles(currentProject);
      }

      const warningText = data.warnings && data.warnings.length > 0
        ? `\n\nWarnings:\n- ${data.warnings.join('\n- ')}`
        : '';
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `${data.response || ''}${warningText}` }
      ]);
      await fetchSessions();
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, something went wrong.' }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleExecuteCode = async (codeText) => {
    if (!codeText || !codeText.trim()) {
      return false;
    }

    setIsProcessing(true);

    try {
      const response = await fetch(`${API_URL}/execute_plot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: codeText,
          context: selectedFiles.length === 1 ? selectedFiles[0] : null,
          selected_files: selectedFiles,
          project_name: currentProject || null,
          session_id: currentSession,
          description: 'Edited plot code'
        })
      });

      const data = await response.json();

      if (!response.ok || data.error) {
        const message = data.error_message || data.detail || 'Plot execution failed.';
        setMessages((prev) => [...prev, { role: 'assistant', content: message }]);
        return false;
      }

      if (data.plot) {
        setCurrentPlot(data.plot);
        setCurrentMetadata(data.metadata || []);
        setCurrentCode(data.code || codeText);

        if (currentSession) {
          setSessionArtifacts((prev) => ({
            ...prev,
            [currentSession]: {
              plot: data.plot,
              metadata: data.metadata || [],
              code: data.code || codeText
            }
          }));
        }
      }

      if (data.plot_entry && currentProject) {
        await fetchProjectFiles(currentProject);
      }
      return true;
    } catch (error) {
      console.error('Error executing code:', error);
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Error executing plot code.' }]);
      return false;
    } finally {
      setIsProcessing(false);
    }
  };

  const blobToBase64 = (blob) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const result = reader.result || '';
      const base64 = result.toString().split(',')[1] || '';
      resolve(base64);
    };
    reader.onerror = () => reject(new Error('Failed to read image'));
    reader.readAsDataURL(blob);
  });

  const handleSelectHistoryPlot = async (plotEntry, index, projectOverride) => {
    const projectName = projectOverride || currentProject;
    if (!plotEntry || !projectName) return;
    const response = await fetch(
      `${API_URL}/projects/${encodeURIComponent(projectName)}/plots/${plotEntry.id}/image`
    );
    const blob = await response.blob();
    const base64 = await blobToBase64(blob);
    setCurrentPlot(base64);
    setCurrentMetadata([]);
    setCurrentCode(plotEntry.code || null);
    setPlotHistoryIndex(index);

    if (currentSession) {
      setSessionArtifacts((prev) => ({
        ...prev,
        [currentSession]: {
          plot: base64,
          metadata: [],
          code: plotEntry.code || null
        }
      }));
    }
  };

  const handleGallerySelect = async (example) => {
    await handleSendMessage(`Create a plot based on this example: ${example.title}. Adapt it to my data.`);
  };

  const openInspectorTab = (tabId) => {
    setInspectorTab(tabId);
    setInspectorOpen(true);
  };

  const toggleInspector = () => {
    if (!inspectorOpen) {
      if (selectedFiles.length >= 2) {
        openInspectorTab('join');
        return;
      }
      if (selectedFiles.length >= 1) {
        openInspectorTab('preview');
        return;
      }
      openInspectorTab('gallery');
      return;
    }
    setInspectorOpen(false);
  };

  const handleSidebarResizeStart = (event) => {
    setIsResizingSidebar(true);
    sidebarResizeStartX.current = event.clientX;
    sidebarResizeStartWidth.current = sidebarWidth;
    event.preventDefault();
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

      <div className="sidebar-container" style={{ width: `${sidebarWidth}px` }}>
        <ChatSidebar
          messages={messages}
          isProcessing={isProcessing}
          onSendMessage={handleSendMessage}
          provider={provider}
          setProvider={setProvider}
          apiKey={apiKey}
          setApiKey={setApiKey}
          model={model}
          setModel={setModel}
          onPasteData={() => setShowDataEditor(true)}
          projects={projects}
          currentProject={currentProject}
          projectFiles={projectFiles}
          selectedFiles={selectedFiles}
          onCreateProject={handleCreateProject}
          onSelectProject={handleSelectProject}
          onUploadFiles={handleUploadFiles}
          onToggleFile={handleToggleFile}
          sessions={sessions}
          currentSessionId={currentSession}
          onSelectSession={handleSelectSession}
          onCreateSession={handleCreateSession}
        />
      </div>
      <div
        className={`sidebar-resizer ${isResizingSidebar ? 'active' : ''}`}
        onMouseDown={handleSidebarResizeStart}
        role="separator"
        aria-orientation="vertical"
      />

      <div className="main-content">
        <div className="plot-area">
          <PlotCanvas
            apiUrl={API_URL}
            plotData={currentPlot}
            metadata={currentMetadata}
            code={currentCode}
            context={selectedFiles.length === 1 ? selectedFiles[0] : null}
            selectedFiles={selectedFiles}
            currentProject={currentProject}
            onCodeEdit={setCurrentCode}
            onSendToChat={handleSendMessage}
            onExecuteCode={handleExecuteCode}
            plotHistory={plotHistory}
            plotHistoryIndex={plotHistoryIndex}
            onSelectHistoryPlot={handleSelectHistoryPlot}
            inspectorOpen={inspectorOpen}
            onToggleInspector={toggleInspector}
            onOpenInspectorTab={openInspectorTab}
          />
        </div>

        {inspectorOpen && (
          <InspectorDrawer
            activeTab={inspectorTab}
            onTabChange={setInspectorTab}
            onClose={() => setInspectorOpen(false)}
            previewAnalysis={previewAnalysis}
            previewData={previewData}
            previewFileName={previewFileName}
            joinSuggestions={joinSuggestions}
            dataAnalysis={previewAnalysis || dataAnalysis}
            onSuggestionClick={(suggestion) => {
              handleSendMessage(`Create a ${suggestion.type}. ${suggestion.reason}`);
            }}
            onSelectGalleryExample={handleGallerySelect}
          />
        )}
      </div>
    </div>
  );
}

export default App;
