const {authenticateJWT} = require('./auth-middleware');
const {CHAT_URL} = require('./path');

const chatRoute = (app) => {
  app.post(CHAT_URL, authenticateJWT, async (req, res) => {
    try {
      const {sessionId, content} = req.body;

      const targetUrl = `${process.env.RAG_SERVER_PROTOCAL}://${process.env.RAG_SERVER_HOST}:${process.env.RAG_SERVER_PORT}/chat`;

      const response = await fetch(targetUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          content,
        }),
      });

      const data = await response.json();
      const {code, data: d, success} = data;
      if (!success) {
        res.status(code).json({data: 'Chat processing failed'});
      } else {
        res.status(code).json({data: d});
      }
    } catch (err) {
      res.status(500).json({data: 'Chat processing failed'});
    }
  });
};

module.exports = chatRoute;