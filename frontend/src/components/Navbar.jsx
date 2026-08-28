import React from 'react';

function Navbar() {
  return (
    <nav className="navbar">
      <div className="container navbar-container">
        <a href="#hero" className="nav-brand">
          <span className="brand-icon">🏛️⚡</span>
          <span className="brand-text">
            Rosetta <span>AI</span>
          </span>
        </a>

        <ul className="nav-links">
          <li><a href="#hero">Home</a></li>
          <li><a href="#translator">Translator</a></li>
          <li><a href="#how-it-works">How It Works</a></li>
          <li><a href="#languages">Languages</a></li>
          <li><a href="#about">About</a></li>
        </ul>

        <a href="#translator" className="nav-cta-btn">
          Try Translator
        </a>
      </div>
    </nav>
  );
}

export default Navbar;
