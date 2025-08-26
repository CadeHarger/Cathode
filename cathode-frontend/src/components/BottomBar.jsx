import Logo from './Logo';
import { ButtonGroup, Button } from '@blueprintjs/core';

import './BottomBar.css';


const BottomBar = ({ onHome, onAbout }) => {
    return (
        <div className="bottom-bar">
                <Button text="Home" icon="home" minimal onClick={onHome} />
                <Button text="About" icon="info-sign" minimal onClick={onAbout} />
        </div>
    )
}

export default BottomBar;