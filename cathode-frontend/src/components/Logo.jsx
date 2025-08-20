import React from 'react';

const Logo = ({ small }) => (
  <div className={`flex items-center ${small ? 'space-x-2' : 'space-x-3'}`}>
    <div className={`rounded-full p-2 ${small ? 'w-8 h-8' : 'w-10 h-10'} bg-yellow-400/90 flex items-center justify-center`}>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L14 8L20 12L14 16L12 22L10 16L4 12L10 8L12 2Z" fill="#0ea5e9" />
      </svg>
    </div>
    <div className="font-semibold tracking-tight text-lg text-white">Cathode</div>
  </div>
);

export default Logo;