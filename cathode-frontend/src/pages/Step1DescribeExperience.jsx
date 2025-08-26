import React from 'react';
import { Button, TextArea } from '@blueprintjs/core';
import './styles/steps.css';
import StepHeader from '../components/StepHeader';
import BottomBar from '../components/BottomBar';

function Step1DescribeExperience({ prompt, setPrompt, onCancel, onNext }) {
  return (
    <div className="container">
      <StepHeader 
        stepNumber={1}
        title="Describe your experience."
        subtitle="Write a few lines about what happened and how you felt. Be detailed and honest- it helps us get the best results."
        onCancel={onCancel}
      />
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
      <BottomBar />
    </div>
  );
}

export default Step1DescribeExperience;