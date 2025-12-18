import React, { useRef, useState } from 'react';
import './ProjectExplorer.css';

const formatSize = (bytes) => {
  if (!bytes && bytes !== 0) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const ProjectExplorer = ({
  projects,
  currentProject,
  projectFiles,
  selectedFiles,
  onSelectProject,
  onCreateProject,
  onUploadFiles,
  onToggleFile,
  onPasteData,
  isProcessing
}) => {
  const [newProjectName, setNewProjectName] = useState('');
  const fileInputRef = useRef(null);

  const handleCreateProject = () => {
    const trimmed = newProjectName.trim();
    if (!trimmed) return;
    onCreateProject(trimmed);
    setNewProjectName('');
  };

  const handleFileChange = (event) => {
    const files = Array.from(event.target.files || []);
    if (files.length === 0) return;
    onUploadFiles(files);
    event.target.value = '';
  };

  const fileEntries = projectFiles.filter((entry) => entry.type === 'file');

  return (
    <div className="project-explorer">
      <div className="section-header">
        <span>Project</span>
      </div>

      <div className="project-select-row">
        <select
          value={currentProject || ''}
          onChange={(event) => onSelectProject(event.target.value)}
          className="project-select"
        >
          <option value="" disabled>Select a project</option>
          {projects.map((project) => (
            <option key={project} value={project}>
              {project}
            </option>
          ))}
        </select>
      </div>

      <div className="project-create-row">
        <input
          type="text"
          value={newProjectName}
          onChange={(event) => setNewProjectName(event.target.value)}
          placeholder="New project name"
          className="project-input"
        />
        <button
          type="button"
          onClick={handleCreateProject}
          className="project-create-btn"
          disabled={isProcessing}
        >
          Create
        </button>
      </div>

      <div className="project-actions">
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="project-action-btn"
          disabled={!currentProject || isProcessing}
        >
          Upload files
        </button>
        <button
          type="button"
          onClick={onPasteData}
          className="project-action-btn secondary"
          disabled={!currentProject || isProcessing}
        >
          Paste data
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.json"
          multiple
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
      </div>

      <div className="file-list">
        {!currentProject && (
          <div className="file-empty">Select a project to view files.</div>
        )}
        {currentProject && fileEntries.length === 0 && (
          <div className="file-empty">No files yet.</div>
        )}
        {fileEntries.map((entry) => {
          const isSelected = selectedFiles.includes(entry.path);
          return (
            <label
              key={entry.path}
              className={`file-row ${isSelected ? 'selected' : ''}`}
            >
              <input
                type="checkbox"
                checked={isSelected}
                onChange={() => onToggleFile(entry.path)}
              />
              <span className="file-name">{entry.name}</span>
              <span className="file-size">{formatSize(entry.size)}</span>
            </label>
          );
        })}
      </div>
    </div>
  );
};

export default ProjectExplorer;
