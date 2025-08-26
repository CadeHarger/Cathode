import React from 'react';
import StepHeader from '../components/StepHeader';
import CustomBr from '../components/CustomBr';
import BottomBar from '../components/BottomBar';

import './styles/home.css'; // Reusing home styles for simplicity

function About({ onBack }) {
  return (
    <div className="container">
      <StepHeader 
        stepNumber="i" 
        title="About Cathode" 
        subtitle="Crafting playlists from experience" 
        onCancel={onBack} 
      />
      <div className="playlists-container" style={{ alignItems: 'flex-start' }}>
        <h3 className="bp6-heading">What is Cathode?</h3>
        <p className="bp6-text-large">
          Cathode is a smart playlist generator that uses natural language to understand the mood, 
          vibe, or experience you're looking for, and curates a unique playlist to match.
        </p>
        <CustomBr />
        <h3 className="bp6-heading">How does it work?</h3>
        <p>
          We use a combination of language models and music metadata analysis to find the perfect tracks 
          for your custom prompt. Just describe what you want, and let us handle the rest.
        </p>
        <CustomBr />
        <h3 className="bp6-heading">Credits</h3>
        <p>
          Built with React, Blueprint.js, and a lot of coffee.
        </p>
      </div>
      <BottomBar onHome={onBack} />
    </div>
  );
}

export default About;
