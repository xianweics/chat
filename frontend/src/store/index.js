import { configureStore } from '@reduxjs/toolkit';

import auth from './auth/reducer';
import chat from './chat/reducer';

export default configureStore({
    reducer: {
        auth, chat
    }
});