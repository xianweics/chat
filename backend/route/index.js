const authRoute = require('./auth');
const sessionsRoute = require('./sessions');
const chatRoute = require('./chat');

const initRoute = app => {
  authRoute(app);
  sessionsRoute(app);
  chatRoute(app);
}

module.exports = {initRoute}
