import React from 'react';
import { Add } from '@blueprintjs/icons';

import './NewButton.css';

function NewButton({ onClick }) {
  return (
    <div className="new-button" onClick={onClick}>  
      <Add size='10vh' className="add-icon" />
      <div className="new-button-text">Generate Playlist</div>
    </div>
  );
}

export default NewButton;