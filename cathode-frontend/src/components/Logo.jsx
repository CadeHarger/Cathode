import React from 'react';
import IconLogo from '../assets/Icon-Logo.png';
import TextLogo from '../assets/Text-Logo.jpeg';

const Logo = ({ small, text }) => (
  <div className={`flex items-center ${small ? 'space-x-2' : 'space-x-3'}`}>
    {text ? (
      <img 
        src={TextLogo} 
        alt="Cathode" 
        className={`${small ? '!h-8' : '!h-12'} !w-auto object-contain !max-w-40`}
        style={{
          height: small ? '7vh' : '16vh',
          width: 'auto',
          objectFit: 'contain'
        }}
      />
      ) : (
    <img 
      src={IconLogo} 
      alt="Cathode Icon" 
      className={`${small ? '!w-10 !h-10' : '!w-16 !h-16'} object-contain`}
      style={{
        width: small ? '40px' : '64px',
        height: small ? '40px' : '64px',
        objectFit: 'contain'
      }}
    />
    )}
  </div>
);

export default Logo;