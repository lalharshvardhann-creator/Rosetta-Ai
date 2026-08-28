import React, { useState } from 'react';
import PipelineVisualizer from './PipelineVisualizer';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const SOURCE_LANGUAGES = [
  'Python',
  'Java',
  'JavaScript',
  'C++',
];

const TARGET_LANGUAGES = [
  'Python',
  'Java',
  'JavaScript',
  'C++',
];

const LANG_TO_API = {
  'Python': 'python',
  'JavaScript': 'javascript',
  'Java': 'java',
  'C++': 'cpp',
};

async function fetchApi(endpoint, payload) {
  let response;
  try {
    response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (response.status === 404) {
      response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    }
  } catch (proxyErr) {
    response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  }
  return response;
}

async function copyToClipboard(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    await navigator.clipboard.writeText(text);
  } else {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
  }
}

function Translator() {
  const [sourceLang, setSourceLang] = useState('');
  const [targetLang, setTargetLang] = useState('');

  const [sourceCode, setSourceCode] = useState('');
  const [translatedCode, setTranslatedCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [copied, setCopied] = useState(false);

  const [analysisData, setAnalysisData] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState('');
  const [activeAnalysisTab, setActiveAnalysisTab] = useState('pseudocode');
  const [pseudocodeCopied, setPseudocodeCopied] = useState(false);

  const handleTranslate = async () => {
    if (!sourceLang) {
      setErrorMessage('Please choose a source language.');
      return;
    }
    if (!targetLang) {
      setErrorMessage('Please choose a target language.');
      return;
    }
    const trimmedCode = sourceCode.trim();
    if (!trimmedCode) {
      setErrorMessage('Please enter some source code first.');
      return;
    }

    if (isLoading) return;

    setIsLoading(true);
    setErrorMessage('');

    try {
      const response = await fetchApi('/api/translate', {
        source: trimmedCode,
        source_language: LANG_TO_API[sourceLang] || sourceLang.toLowerCase(),
        target_language: LANG_TO_API[targetLang] || targetLang.toLowerCase(),
      });
      const data = await response.json();

      if (response.ok && data.success) {
        setTranslatedCode(data.code || '');
        setErrorMessage('');
      } else {
        setTranslatedCode('');
        setErrorMessage(data.error || 'Translation failed.');
      }
    } catch (err) {
      setTranslatedCode('');
      setErrorMessage(
        'Unable to connect to the translation server. Please ensure backend is running on http://127.0.0.1:8000.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setSourceCode('');
    setTranslatedCode('');
    setErrorMessage('');
    setCopied(false);
    setAnalysisData(null);
    setAnalysisError('');
    setPseudocodeCopied(false);
  };

  const handleCopy = async () => {
    if (!translatedCode) return;
    try {
      await copyToClipboard(translatedCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  const handleAnalyze = async () => {
    if (!sourceLang) {
      setAnalysisError('Please choose a source language first.');
      return;
    }
    const trimmedCode = sourceCode.trim();
    if (!trimmedCode) {
      setAnalysisError('Please enter some source code to analyze.');
      return;
    }

    if (isAnalyzing) return;

    setIsAnalyzing(true);
    setAnalysisError('');

    try {
      const response = await fetchApi('/api/analyze', {
        source: trimmedCode,
        source_language: LANG_TO_API[sourceLang] || sourceLang.toLowerCase(),
      });
      const data = await response.json();

      if (response.ok && data.success) {
        setAnalysisData({
          pseudocode: data.pseudocode || '',
          time_complexity: data.time_complexity || 'O(1)',
          time_explanation: data.time_explanation || '',
          space_complexity: data.space_complexity || 'O(1)',
          space_explanation: data.space_explanation || '',
        });
        setAnalysisError('');
      } else {
        setAnalysisData(null);
        setAnalysisError(data.error || 'Code analysis failed.');
      }
    } catch (err) {
      setAnalysisData(null);
      setAnalysisError(
        'Unable to connect to the translation server. Please ensure backend is running on http://127.0.0.1:8000.'
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCopyPseudocode = async () => {
    if (!analysisData || !analysisData.pseudocode) return;
    try {
      await copyToClipboard(analysisData.pseudocode);
      setPseudocodeCopied(true);
      setTimeout(() => setPseudocodeCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy pseudocode:', err);
    }
  };

  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleTranslate();
      return;
    }
    if (e.key === 'Tab') {
      e.preventDefault();
      const textarea = e.target;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const val = textarea.value;
      const updated = val.substring(0, start) + '    ' + val.substring(end);
      setSourceCode(updated);
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 4;
      }, 0);
    }
  };

  return (
    <section id="translator" className="translator-section">
      <div className="container">
        <div className="section-header">
          <span className="section-tag">Interactive Workspace</span>
          <h2 className="section-title">Code Translator</h2>
          <p className="section-subtitle">
            Translate Python source code into clean, idiomatic Java, C++, or JavaScript.
          </p>
        </div>

        <div className="translator-card">
          <div className="language-chooser">
            <h3 className="chooser-title">Choose Languages</h3>
            <div className="chooser-row">
              <div className="chooser-group">
                <label htmlFor="source-lang" className="chooser-label">From</label>
                <select
                  id="source-lang"
                  className="lang-select"
                  value={sourceLang}
                  onChange={(e) => {
                    setSourceLang(e.target.value);
                    setErrorMessage('');
                  }}
                  aria-label="Select source language"
                >
                  <option value="" disabled>Choose language</option>
                  {SOURCE_LANGUAGES.map((lang) => (
                    <option key={lang} value={lang}>
                      {lang}
                    </option>
                  ))}
                </select>
              </div>

              <div className="chooser-arrow" aria-hidden="true">➔</div>

              <div className="chooser-group">
                <label htmlFor="target-lang" className="chooser-label">To</label>
                <select
                  id="target-lang"
                  className="lang-select"
                  value={targetLang}
                  onChange={(e) => {
                    setTargetLang(e.target.value);
                    setErrorMessage('');
                  }}
                  aria-label="Select target language"
                >
                  <option value="" disabled>Choose language</option>
                  {TARGET_LANGUAGES.map((lang) => (
                    <option key={lang} value={lang}>
                      {lang}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {errorMessage && (
            <div className="error-banner" role="alert">
              <span className="error-icon">⚠️</span>
              <div>
                <strong>Translation Error:</strong> {errorMessage}
              </div>
            </div>
          )}

          <div className="translator-workspace">
            <div className="editor-pane">
              <div className="pane-header">
                <span className="pane-badge">📝 {sourceLang || 'Source'} Editor</span>
                <span className="pane-shortcut-hint">Press Ctrl+Enter to Translate</span>
              </div>
              <textarea
                id="source-code-editor"
                name="source-code-editor"
                className="code-textarea"
                placeholder="Write or paste your code here..."
                value={sourceCode}
                onChange={(e) => {
                  setSourceCode(e.target.value);
                  if (errorMessage) setErrorMessage('');
                }}
                onKeyDown={handleKeyDown}
                spellCheck={false}
                autoCapitalize="off"
                autoComplete="off"
                autoCorrect="off"

                aria-label={`${sourceLang || 'Source'} code editor`}
              />
            </div>

            <div className="editor-pane">
              <div className="pane-header">
                <div className="pane-header-left">
                  <span className="pane-badge">✨ {targetLang || 'Target'} Output</span>
                  {translatedCode && (
                    <span className="pane-review-hint" title="Always verify generated target code before using in production">
                      ⚠️ Generated code — review before use
                    </span>
                  )}
                </div>
                {translatedCode && (
                  <button
                    type="button"
                    className={`btn-copy ${copied ? 'copied' : ''}`}
                    onClick={handleCopy}
                    title={`Copy translated ${targetLang} code`}
                    aria-label="Copy generated target code"
                  >
                    {copied ? '✓ Copied' : '📋 Copy'}
                  </button>
                )}
              </div>
              <div className="output-display" aria-live="polite">
                {isLoading ? (
                  <span className="output-placeholder">
                    <span className="spinner"></span> Generating {targetLang || 'target'} code through AST ➔ IR pipeline...
                  </span>
                ) : translatedCode ? (
                  <pre className="output-content"><code>{translatedCode}</code></pre>
                ) : (
                  <span className="output-placeholder">
                    Translated code will appear here after clicking "⚡ Translate Code".
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="translator-footer">
            <div className="footer-stats">
              <span>Lines: {sourceCode ? sourceCode.split('\n').length : 0}</span>
              <span>Characters: {sourceCode.length}</span>
            </div>

            <div className="action-buttons">
              <button
                type="button"
                className="btn-clear"
                onClick={handleClear}
                disabled={isLoading || isAnalyzing}
                title="Clear all editor contents and analysis"
              >
                Clear
              </button>
              <button
                type="button"
                className="btn-analyze"
                onClick={handleAnalyze}
                disabled={isLoading || isAnalyzing}
                title="Generate pseudocode and estimate Big-O complexity"
              >
                {isAnalyzing ? (
                  <>
                    <span className="spinner"></span> Analyzing...
                  </>
                ) : (
                  '🔍 Analyze Code'
                )}
              </button>
              <button
                type="button"
                className="btn-translate"
                onClick={handleTranslate}
                disabled={isLoading || isAnalyzing}
                title="Translate Python into selected target language (Ctrl+Enter)"
              >
                {isLoading ? (
                  <>
                    <span className="spinner"></span> Translating...
                  </>
                ) : (
                  '⚡ Translate Code'
                )}
              </button>
            </div>
          </div>
        </div>

        <PipelineVisualizer sourceLang={sourceLang} targetLang={targetLang} isTranslating={isLoading} />

        <div className="analysis-card">
          <div className="analysis-header">
            <div className="analysis-title-group">
              <span className="analysis-badge">⚡ Static Analysis</span>
              <h3 className="analysis-title">Code Analysis &amp; Big-O Complexity</h3>
            </div>

            <div className="analysis-tabs" role="tablist" aria-label="Code analysis views">
              <button
                type="button"
                role="tab"
                aria-selected={activeAnalysisTab === 'pseudocode'}
                className={`tab-btn ${activeAnalysisTab === 'pseudocode' ? 'active' : ''}`}
                onClick={() => setActiveAnalysisTab('pseudocode')}
              >
                <span>📋</span> Pseudocode
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={activeAnalysisTab === 'time'}
                className={`tab-btn ${activeAnalysisTab === 'time' ? 'active' : ''}`}
                onClick={() => setActiveAnalysisTab('time')}
              >
                <span>⏱️</span> Time Complexity
                {analysisData && (
                  <span className="tab-pill time-pill">{analysisData.time_complexity}</span>
                )}
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={activeAnalysisTab === 'space'}
                className={`tab-btn ${activeAnalysisTab === 'space' ? 'active' : ''}`}
                onClick={() => setActiveAnalysisTab('space')}
              >
                <span>💾</span> Space Complexity
                {analysisData && (
                  <span className="tab-pill space-pill">{analysisData.space_complexity}</span>
                )}
              </button>
            </div>
          </div>

          {analysisError && (
            <div className="error-banner analysis-error" role="alert">
              <span className="error-icon">⚠️</span>
              <div>
                <strong>Analysis Error:</strong> {analysisError}
              </div>
            </div>
          )}

          <div className="analysis-body">
            {isAnalyzing ? (
              <div className="analysis-loading">
                <span className="spinner large-spinner"></span>
                <p className="loading-text">Analyzing algorithmic logic, generating pseudocode, and estimating Big-O bounds...</p>
              </div>
            ) : analysisData ? (
              <div className="analysis-tab-content">
                {activeAnalysisTab === 'pseudocode' && (
                  <div className="pseudocode-pane">
                    <div className="pane-header-inner">
                      <span className="pane-subtitle">Standardized Algorithmic Pseudocode</span>
                      <button
                        type="button"
                        className={`btn-copy ${pseudocodeCopied ? 'copied' : ''}`}
                        onClick={handleCopyPseudocode}
                        title="Copy pseudocode"
                        aria-label="Copy pseudocode"
                      >
                        {pseudocodeCopied ? '✓ Copied' : '📋 Copy Pseudocode'}
                      </button>
                    </div>
                    <pre className="pseudocode-content"><code>{analysisData.pseudocode}</code></pre>
                  </div>
                )}

                {activeAnalysisTab === 'time' && (
                  <div className="complexity-pane">
                    <div className="complexity-hero-card">
                      <div className="complexity-metric-label">Estimated Time Complexity</div>
                      <div className="complexity-badge time-badge">{analysisData.time_complexity}</div>
                    </div>
                    <div className="complexity-reason-card">
                      <div className="reason-header">
                        <span className="reason-icon">💡</span>
                        <strong>Reason &amp; Algorithmic Rationale:</strong>
                      </div>
                      <p className="reason-text">{analysisData.time_explanation}</p>
                    </div>
                  </div>
                )}

                {activeAnalysisTab === 'space' && (
                  <div className="complexity-pane">
                    <div className="complexity-hero-card">
                      <div className="complexity-metric-label">Estimated Auxiliary Space Complexity</div>
                      <div className="complexity-badge space-badge">{analysisData.space_complexity}</div>
                    </div>
                    <div className="complexity-reason-card">
                      <div className="reason-header">
                        <span className="reason-icon">💡</span>
                        <strong>Reason &amp; Memory Footprint Rationale:</strong>
                      </div>
                      <p className="reason-text">{analysisData.space_explanation}</p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="analysis-empty-state">
                <div className="empty-icon">📊</div>
                <h4>Ready for Code Analysis</h4>
                <p>
                  Click the <strong>"🔍 Analyze Code"</strong> button to generate language-independent pseudocode and estimate asymptotic Time &amp; Space complexities.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

export default Translator;
