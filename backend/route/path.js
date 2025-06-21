const prefix = 'api';
const getRoute = url => `/${prefix}/${url}`;
const REGISTER_URL = getRoute('register');
const LOGIN_URL = getRoute('login');
const LOGOUT_URL = getRoute('logout');
const SESSIONS_URL = getRoute('sessions');
const CHAT_URL = getRoute('chat');
const MESSAGES_BY_ID_URL = `${SESSIONS_URL}/:id/messages`;

module.exports = {
  REGISTER_URL,
  LOGIN_URL,
  LOGOUT_URL,
  SESSIONS_URL,
  MESSAGES_BY_ID_URL,
  CHAT_URL,
};