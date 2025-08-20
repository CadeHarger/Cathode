import React from 'react';
import { Button } from '@blueprintjs/core';
import { Add } from '@blueprintjs/icons';

function NewButton({ onClick }) {
  return (
    <Button 
      onClick={onClick} 
      large
      intent="primary"
      text="+ New Playlist"
      icon={<Add />}
    />
  );
}

export default NewButton;