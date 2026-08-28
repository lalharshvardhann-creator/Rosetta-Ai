import React, { useState } from 'react';

function PipelineVisualizer({ sourceLang = 'Python', targetLang, isTranslating }) {
  const [activeStage, setActiveStage] = useState(null);

  const sourceIcon =
    sourceLang === 'Java' ? '☕' : sourceLang === 'C++' ? '⚡' : sourceLang === 'JavaScript' ? '🌐' : '🐍';

  const stages = [
    {
      id: 'source',
      num: '01',
      title: `${sourceLang} Source`,
      tag: 'AST Input',
      icon: sourceIcon,
      desc: `Parses raw ${sourceLang} code into an Abstract Syntax Tree (AST) using standard grammar rules.`,
    },
    {
      id: 'ast',
      num: '02',
      title: 'AST Analysis',
      tag: 'Semantic Walk',
      icon: '🔍',
      desc: 'Traverses syntax nodes, resolves variable scopes, and performs static type inference (int, float, str, bool, list, dict).',
    },
    {
      id: 'ir',
      num: '03',
      title: 'IR Layer',
      tag: 'Language-Agnostic',
      icon: '⚙️',
      desc: 'Lowers AST into standardized Intermediate Representation (IR) nodes like IRFunction, IRBlock, and IRBinaryOp.',
    },
    {
      id: 'target',
      num: '04',
      title: `${targetLang} Generator`,
      tag: 'Idiomatic Emitter',
      icon: targetLang === 'Java' ? '☕' : targetLang === 'C++' ? '⚡' : targetLang === 'Python' ? '🐍' : '🌐',
      desc: `Emits clean, idiomatic ${targetLang} code with proper type declarations, OOP class wrappers, and I/O streams.`,
    },
  ];

  return (
    <div className="pipeline-visualizer-card">
      <div className="pipeline-header">
        <div className="pipeline-title-group">
          <span className="pipeline-badge">🏛️ Architecture Pipeline</span>
          <h3 className="pipeline-title">AST ➔ IR ➔ Target Compilation Flow</h3>
        </div>
        <span className="pipeline-subtitle-hint">
          {isTranslating ? (
            <span className="pipeline-active-badge">
              <span className="pulse-dot"></span> Compiling {sourceLang} ➔ {targetLang}...
            </span>
          ) : (
            'Click any stage to view architectural details'
          )}
        </span>
      </div>

      <div className="pipeline-stages-grid">
        {stages.map((stage, idx) => {
          const isSelected = activeStage === stage.id;
          return (
            <React.Fragment key={stage.id}>
              <div
                className={`pipeline-stage-node ${isSelected ? 'stage-selected' : ''} ${
                  isTranslating ? `stage-pulsing stage-pulse-${idx}` : ''
                }`}
                onClick={() => setActiveStage(isSelected ? null : stage.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    setActiveStage(isSelected ? null : stage.id);
                  }
                }}
              >
                <div className="stage-top">
                  <span className="stage-num">{stage.num}</span>
                  <span className="stage-icon">{stage.icon}</span>
                </div>
                <h4 className="stage-title">{stage.title}</h4>
                <span className="stage-tag">{stage.tag}</span>
              </div>
              {idx < stages.length - 1 && (
                <div className={`pipeline-arrow-connector ${isTranslating ? 'arrow-active' : ''}`}>
                  ➔
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {activeStage && (
        <div className="stage-detail-box" role="region" aria-live="polite">
          <div className="detail-header">
            <span className="detail-icon">💡</span>
            <strong>
              Stage {stages.find((s) => s.id === activeStage)?.num}:{' '}
              {stages.find((s) => s.id === activeStage)?.title}
            </strong>
          </div>
          <p className="detail-desc">{stages.find((s) => s.id === activeStage)?.desc}</p>
        </div>
      )}
    </div>
  );
}

export default PipelineVisualizer;
