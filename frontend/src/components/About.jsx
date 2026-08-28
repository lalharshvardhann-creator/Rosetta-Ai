import React from 'react';

function About() {
  return (
    <section id="about" className="about-section">
      <div className="container">
        <div className="about-card">
          <div className="about-grid">
            <div className="about-text">
              <span className="section-tag">About the Project</span>
              <h3>Bridging the Gap in Software Modernization</h3>
              <p>
                <strong>Rosetta AI</strong> is a hackathon project exploring how to help developers migrate source code across programming languages with higher reliability and structure preservation.
              </p>
              <p>
                We are developing an approach that combines <strong>Abstract Syntax Tree (AST) analysis</strong> with AI code translation to help ensure syntactic and structural consistency as the project progresses.
              </p>
            </div>

            <div className="about-stats-box">
              <div className="stat-item">
                <span className="stat-value">4</span>
                <span className="stat-label">Target Languages</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">AST</span>
                <span className="stat-label">Architectural Core</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">3-Step</span>
                <span className="stat-label">Planned Pipeline</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">Open</span>
                <span className="stat-label">Hackathon Concept</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default About;
