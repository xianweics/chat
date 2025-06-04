const prefix = 'api';
const getRoute = url => `/${prefix}/${url}`;
const REGISTER_URL = getRoute('register');
const LOGIN_URL = getRoute('login');
const SESSIONS_URL = getRoute('sessions');
const CHAT_URL = getRoute('chat');
const SESSIONS_URL_BASE_ID = `${SESSIONS_URL}/:id/messages`;

module.exports = {
  REGISTER_URL,
  LOGIN_URL,
  SESSIONS_URL,
  SESSIONS_URL_BASE_ID,
  CHAT_URL
}