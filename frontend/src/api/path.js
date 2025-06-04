export const HOST = 'http://localhost:5000';
const createPath = url => `${HOST}/api/${url}`;

export const REGISTER_URL = createPath('register');
export const LOGIN_URL = createPath('login');
export const LOGOUT_URL = createPath('logout');
export const SESSIONS_URL = createPath('sessions');
export const CHAT_URL = createPath('chat');

export const getSessionsMessages = sessionId => `${SESSIONS_URL}/${sessionId}/messages`

