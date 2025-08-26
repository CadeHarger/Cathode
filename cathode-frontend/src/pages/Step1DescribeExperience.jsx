import React from 'react';
import { Button, TextArea } from '@blueprintjs/core';
import './styles/steps.css';
import Logo from '../components/Logo';
import { Home } from '@blueprintjs/icons';

function Step1DescribeExperience({ prompt, setPrompt, onCancel, onNext }) {
  return (
    <div className="container">
      <div className="top-section-1">
        <div className="logo-1">
          <Logo />
        </div>
        <div className="flex flex-col items-center justify-center">
          <h1 className="bp6-heading text-text-dark font-bold text-xl mb-2">Describe your experience.</h1>
          <p className="bp6-text-muted">Write a few lines about what happened and how you felt. Be detailed and honest- it helps us get the best results.</p>
        </div>
        <div className="home-1">
            <Home onClick={onCancel} size={30} className="home-icon" />
        </div>
      </div>
      <div className="middle-section-1">
        <TextArea 
          value={prompt} 
          onChange={(e) => setPrompt(e.target.value)} 
          rows={6} 
          className="w-full rounded-lg p-3 bg-slate-200 text-text-dark placeholder-slate-500" 
          placeholder="I finally got promoted at work and I'm so electrified because..." 
          size="large"
          fill
          style={{
            height: '100%'
          }}
        />
      </div>
      <div className="flex justify-between items-center mt-4">
        <Button onClick={onCancel} text="Cancel" variant="minimal" size="large"/>
        <Button onClick={onNext} intent="primary" text="Next" variant="outlined" size="large" disabled={prompt.trim().length < 1}/>
      </div>
    </div>
  );
}

export default Step1DescribeExperience;