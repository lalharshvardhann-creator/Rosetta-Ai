import React from 'react';

function HowItWorks() {
  const steps = [
    {
      step: '01',
      icon: '🐍',
      title: 'Python AST Parsing',
      description:
        'Parses Python source code into an Abstract Syntax Tree (AST), validating syntax structure and program token hierarchies.',
    },
    {
      step: '02',
      icon: '🔍',
      title: 'Type & Scope Analysis',
      description:
        'Analyzes variable scopes, loop boundaries, and infers static data types (int, float, str, bool, collections) without runtime overhead.',
    },
    {
      step: '03',
      icon: '⚙️',
      title: 'Intermediate Representation (IR)',
      description:
        'Lowers AST nodes into language-agnostic IR trees (IRFunction, IRBlock, IRBinaryOp) isolating source syntax from target quirks.',
    },
    {
      step: '04',
      icon: '🚀',
      title: 'Target Code Generation',
      description:
        'Emits clean, idiomatic target code for JavaScript (ES6+), Java (typed classes & imports), or C++ (headers & std streams).',
    },
  ];

  return (
    <section id="how-it-works" className="how-it-works-section">
      <div className="container">
        <div className="section-header">
          <span className="section-tag">Core Architecture</span>
          <h2 className="section-title">How Rosetta AI Works</h2>
          <p className="section-subtitle">
            A multi-stage compiler pipeline combining Python AST parsing, Intermediate Representation (IR), and target code generation.
          </p>
        </div>

        <div className="steps-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))' }}>
          {steps.map((item) => (
            <div key={item.step} className="step-card">
              <span className="step-number">{item.step}</span>
              <div className="step-icon-wrapper">{item.icon}</div>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default HowItWorks;
