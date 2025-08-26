import Logo from './Logo';
import { ButtonGroup, Button } from '@blueprintjs/core';

import './BottomBar.css';


const BottomBar = () => {
    return (
        <div className="bottom-bar">
                <Button text="Home" icon="home" minimal />
                <Button text="Settings" icon="settings" minimal />
        </div>
    )
}

export default BottomBar;