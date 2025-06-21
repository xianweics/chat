const {authenticateJWT} = require('./auth-middleware');
const {AISession, AIMessage} = require('../db/postgres-server');
const {SESSIONS_URL, MESSAGES_BY_ID_URL} = require('./path');

const sessionRoute = app => {
  app.get(SESSIONS_URL, authenticateJWT, async (req, res) => {
    try {
      const sessions = await AISession.findAll({
        where: {user_id: req.user.userId},
        order: [['created_at', 'DESC']],
        include: [
          {
            model: AIMessage,
            as: 'messages',
            limit: 1,
            order: [['created_at', 'ASC']],
          }],
      });

      res.json({data: sessions});
    } catch (err) {
      res.status(500).json({data: {error: 'Failed to retrieve sessions'}});
    }
  });
  app.post(SESSIONS_URL, authenticateJWT, async (req, res) => {
    try {
      const session = await AISession.create({
        user_id: req.user.userId,
        title: `Chat-${new Date().toLocaleString()}`,
      });
      res.status(201).json({data: session});
    } catch (err) {
      res.status(500).json({data: 'Failed to create session'});
    }
  });
  app.get(MESSAGES_BY_ID_URL, authenticateJWT, async (req, res) => {
    try {
      const data = await AIMessage.findAll({
        where: {session_id: req.params.id},
        order: [['created_at', 'ASC']],
      });

      res.json({data});
    } catch (err) {
      res.status(500).json({data: 'Failed to retrieve messages'});
    }
  });
};

module.exports = sessionRoute;