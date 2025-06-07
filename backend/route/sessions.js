const {authenticateJWT} = require("./auth-middleware");
const {Session, Message} = require("../db/postgres-server");
const {SESSIONS_URL, SESSIONS_URL_BASE_ID} = require("./path");

const sessionRoute = app => {
  app.get(SESSIONS_URL, authenticateJWT, async (req, res) => {
    try {
      const sessions = await Session.findAll({
        where: {userId: req.user.userId},
        order: [['updatedAt', 'DESC']],
        include: [{
          model: Message,
          as: 'messages',
          limit: 1,
          order: [['createdAt', 'ASC']]
        }]
      });

      res.json(sessions);
    } catch (err) {
      console.error('Get sessions error:', err);
      res.status(500).json({error: 'Failed to retrieve sessions'});
    }
  });
  app.post(SESSIONS_URL, authenticateJWT, async (req, res) => {
    try {
      const session = await Session.create({
        userId: req.user.userId,
        title: `Chat-${new Date().toLocaleDateString('en-US')}`
      });

      res.status(201).json(session);
    } catch (err) {
      console.error('Create session error:', err);
      res.status(500).json({error: 'Failed to create session'});
    }
  });
  app.get(SESSIONS_URL_BASE_ID, authenticateJWT, async (req, res) => {
    try {
      const session = await Session.findByPk(req.params.id);

      if (!session || session.userId !== req.user.userId) {
        return res.status(404).json({error: 'Session not found'});
      }

      const messages = await Message.findAll({
        where: {sessionId: req.params.id},
        order: [['createdAt', 'ASC']]
      });

      res.json(messages);
    } catch (err) {
      console.error('Get messages error:', err);
      res.status(500).json({error: 'Failed to retrieve messages'});
    }
  });
}

module.exports = sessionRoute;