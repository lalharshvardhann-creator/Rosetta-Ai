import React from 'react';

function Hero() {
  return (
    <header id="hero" className="hero-section">
      <div className="container">
        <div className="hero-badge">
          <span className="badge-dot"></span>
          <span>Hackathon Project In Development</span>
        </div>

        <h1 className="hero-title">
          Translate Code <span className="gradient-text">Across Languages</span>
        </h1>

        <p className="hero-description">
          An intelligent developer platform in development. We are designing an AST-assisted pipeline 
          to translate source code across programming languages while helping preserve structure and logic.
        </p>

        <div className="hero-actions">
          <a href="#translator" className="btn-primary">
            <span>🚀 Open Translator</span>
          </a>
          <a href="#how-it-works" className="btn-secondary">
            <span>Learn How It Works</span>
          </a>
        </div>

        <div className="hero-highlights">
          <div className="highlight-item">
            <span className="highlight-icon">✓</span>
            <span>AST-Driven Architecture (In Development)</span>
          </div>
          <div className="highlight-item">
            <span className="highlight-icon">✓</span>
            <span>Structure & Logic Preservation Goal</span>
          </div>
          <div className="highlight-item">
            <span className="highlight-icon">✓</span>
            <span>Multi-Language Roadmap</span>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Hero;
