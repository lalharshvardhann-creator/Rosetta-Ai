import React from 'react';

function SupportedLanguages() {
  const languages = [
    {
      name: 'Python',
      icon: '🐍',
      tag: 'Dynamic & Concise',
      description: 'Widely used in Data Science, AI, scripting, and backend development with clean, readable syntax.',
    },
    {
      name: 'Java',
      icon: '☕',
      tag: 'Object-Oriented & Robust',
      description: 'Enterprise standard with strong static typing, cross-platform JVM runtime, and extensive OOP design.',
    },
    {
      name: 'C++',
      icon: '⚡',
      tag: 'High Performance & Systems',
      description: 'Direct memory management, ultra-fast execution, and systems-level hardware control.',
    },
    {
      name: 'JavaScript',
      icon: '🌐',
      tag: 'Universal Web & Full-Stack',
      description: 'The ubiquitous language of modern web browsers, interactive interfaces, and Node.js servers.',
    },
  ];

  return (
    <section id="languages" className="languages-section">
      <div className="container">
        <div className="section-header">
          <span className="section-tag">Ecosystem</span>
          <h2 className="section-title">Supported Languages</h2>
          <p className="section-subtitle">
            Target language ecosystems planned for cross-language translation and AST mapping.
          </p>
        </div>

        <div className="languages-grid">
          {languages.map((lang) => (
            <div key={lang.name} className="lang-card">
              <span className="lang-icon">{lang.icon}</span>
              <h3>{lang.name}</h3>
              <p>{lang.description}</p>
              <span className="lang-badge">{lang.tag}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default SupportedLanguages;
