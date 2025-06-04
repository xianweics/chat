import {configureStore} from '@reduxjs/toolkit';

import auth from './auth/reducer';
import chat from './chat/reducer';
import {modules} from "@store/config";

export default configureStore({
  reducer: {
    [modules.auth]: auth,
    [modules.chat]: chat
  }
});