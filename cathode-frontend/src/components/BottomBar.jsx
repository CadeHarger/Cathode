import Logo from './Logo';
import { ButtonGroup, Button } from '@blueprintjs/core';

import './BottomBar.css';


const BottomBar = ({ onHome, onAbout, onHomeWarning }) => {
    const handleHomeClick = () => {
        if (onHomeWarning) {
            onHomeWarning();
        } else {
            onHome();
        }
    };

    return (
        <div className="bottom-bar">
                <Button text="Home" icon="home" minimal onClick={handleHomeClick} />
                <Button text="About" icon="info-sign" minimal onClick={onAbout} />
        </div>
    )
}

export default BottomBar;