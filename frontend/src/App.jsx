import React from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import Translator from './components/Translator';
import HowItWorks from './components/HowItWorks';
import SupportedLanguages from './components/SupportedLanguages';
import About from './components/About';
import Footer from './components/Footer';

function App() {
  return (
    <div className="app-layout">
      <div className="bg-glow-container" aria-hidden="true">
        <div className="bg-glow-1"></div>
        <div className="bg-glow-2"></div>
      </div>

      <Navbar />

      <main>
        <Hero />
        <Translator />
        <HowItWorks />
        <SupportedLanguages />
        <About />
      </main>

      <Footer />
    </div>
  );
}

export default App;
