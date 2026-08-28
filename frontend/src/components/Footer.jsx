import React from 'react';

function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-content">
        <div className="footer-left">
          <span className="brand-icon">🏛️⚡</span>
          <p>© {new Date().getFullYear()} Rosetta AI — College Hackathon Project.</p>
        </div>

        <div className="footer-links">
          <a href="#hero">Top</a>
          <a href="#translator">Translator</a>
          <a href="#how-it-works">Pipeline</a>
          <a href="#languages">Languages</a>
          <a href="#about">About</a>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
