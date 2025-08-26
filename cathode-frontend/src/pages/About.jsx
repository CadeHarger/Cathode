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
        subtitle="Cathode (Catharsis-Ode): A cathode is the electrode of a polarized electrical device from which current is released" 
        onCancel={onBack} 
      />
      <div className="playlists-container" style={{ alignItems: 'flex-start' }}>
        <h3 className="bp6-heading">What is Cathode?</h3>
        <p className="bp6-text-large">
          Cathode seeks to find music that is relatable and achieves catharsis for the experience and feeling of the user by using a combination of heuristics and language models.
        </p>
        <CustomBr />
        <h3 className="bp6-heading">How does it work?</h3>
        <p className="bp6-text-large">
          Cathode first generates a list of queries to search for playlists on Spotify from the user's query. 
          It then matches all the songs from the playlists to an <a href="https://www.kaggle.com/datasets/carlosgdcj/genius-song-lyrics-with-language-information/data" target="_blank" rel="noopener noreferrer">open-source database of song lyrics</a>. 
          These songs are filtered by the genre filters.
          Cathode then uses vector search on embeddings of the matched lyrics to create a song score. 
          The top 100 scoring songs are ranked using weighted LLM-prompted scores and popularity weights. 
          The final playlist is made by selecting the top 25 songs from the final results!
        </p>
        <CustomBr />
        <h3 className="bp6-heading">Credits</h3>
        <p className="bp6-text-large">
          Built by Cade Harger with React, Blueprint.js, Python, GCP, and a lot of Cursor tokens. Reach out to me on my <a href="https://www.linkedin.com/in/cadeharger/">LinkedIn</a> if you found this interesting! 
        </p>
        <p className="bp6-text-large">
            <a href="https://github.com/cadeharger/cathode">Project Github</a>
        </p>
      </div>
      <BottomBar onHome={onBack} />
    </div>
  );
}

export default About;
