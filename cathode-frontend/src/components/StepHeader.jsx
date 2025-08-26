import React, { useState, useEffect } from 'react';
import Logo from './Logo';
import { Home } from '@blueprintjs/icons';
import { isMobile } from '../utils/helpers';
import '../pages/styles/steps.css';

function StepHeader({ stepNumber, title, subtitle, onCancel }) {
  const [isMobileDevice, setIsMobileDevice] = useState(false);

  useEffect(() => {
    setIsMobileDevice(isMobile());
  }, []);

  return (
    <div className="top-section-1">
      <div className="logo-1">
        <Logo animated={false} />
      </div>
      <div className="flex flex-col items-center justify-center height-100">
        <h1 className="bp6-heading text-text-dark font-bold text-xl mb-2">
          <div className="flex flex-row items-center justify-center gap-20">
            <div className="step-number-container">
              <div className="step-number-trail"></div>
              <span className="step-number">{stepNumber}.</span>
            </div>
            {title}
          </div>
        </h1>
        {subtitle && <p className="bp6-text-muted">{subtitle}</p>}
      </div>
      {!isMobileDevice && (
        <div className="home-1">
          <Home onClick={onCancel} size={30} className="home-icon" />
        </div>
      )}
    </div>
  );
}

export default StepHeader;
