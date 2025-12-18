import React from 'react';
import DataAnalysisPanel from './DataAnalysisPanel';
import DataPreviewPanel from './DataPreviewPanel';
import GalleryBrowser from './GalleryBrowser';
import JoinAssistantPanel from './JoinAssistantPanel';
import './InspectorDrawer.css';

const TAB_IDS = {
  PREVIEW: 'preview',
  JOIN: 'join',
  ANALYSIS: 'analysis',
  GALLERY: 'gallery'
};

const DEFAULT_EMPTY_TEXT = {
  [TAB_IDS.PREVIEW]: 'Select a file to preview its columns and sample rows.',
  [TAB_IDS.JOIN]: 'Select at least two files to see join suggestions.',
  [TAB_IDS.ANALYSIS]: 'Upload or select data to see automatic plot suggestions.',
  [TAB_IDS.GALLERY]: 'Browse official Matplotlib examples and apply one as a starting point.'
};

const InspectorDrawer = ({
  activeTab,
  onTabChange,
  onClose,
  previewAnalysis,
  previewData,
  previewFileName,
  joinSuggestions,
  dataAnalysis,
  onSuggestionClick,
  onSelectGalleryExample
}) => {
  const tabs = [
    { id: TAB_IDS.PREVIEW, label: 'Preview' },
    { id: TAB_IDS.JOIN, label: 'Join' },
    { id: TAB_IDS.ANALYSIS, label: 'Analysis' },
    { id: TAB_IDS.GALLERY, label: 'Gallery' }
  ];

  const renderContent = () => {
    if (activeTab === TAB_IDS.PREVIEW) {
      if (!previewAnalysis) {
        return <div className="inspector-empty">{DEFAULT_EMPTY_TEXT[TAB_IDS.PREVIEW]}</div>;
      }
      return (
        <DataPreviewPanel
          analysis={previewAnalysis}
          preview={previewData}
          fileName={previewFileName}
        />
      );
    }

    if (activeTab === TAB_IDS.JOIN) {
      if (!joinSuggestions || joinSuggestions.length === 0) {
        return <div className="inspector-empty">{DEFAULT_EMPTY_TEXT[TAB_IDS.JOIN]}</div>;
      }
      return <JoinAssistantPanel suggestions={joinSuggestions} />;
    }

    if (activeTab === TAB_IDS.ANALYSIS) {
      if (!dataAnalysis) {
        return <div className="inspector-empty">{DEFAULT_EMPTY_TEXT[TAB_IDS.ANALYSIS]}</div>;
      }
      return <DataAnalysisPanel analysis={dataAnalysis} onSuggestionClick={onSuggestionClick} />;
    }

    if (activeTab === TAB_IDS.GALLERY) {
      return (
        <GalleryBrowser
          onSelectExample={onSelectGalleryExample}
          onClose={onClose}
        />
      );
    }

    return <div className="inspector-empty">Select a tool.</div>;
  };

  return (
    <div className="inspector-drawer">
      <div className="inspector-header">
        <div className="inspector-tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`inspector-tab ${tab.id === activeTab ? 'active' : ''}`}
              onClick={() => onTabChange(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <button type="button" className="inspector-close" onClick={onClose}>
          Close
        </button>
      </div>
      <div className="inspector-body">{renderContent()}</div>
    </div>
  );
};

export default InspectorDrawer;
