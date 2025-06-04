const {authenticateJWT} = require("./auth-middleware");
const {CHAT_URL} = require("./path");
const {Message} = require("../db/mysql-server");

const chatRoute = (app) => {
  app.post(CHAT_URL, authenticateJWT, async (req, res) => {
    try {
      const {sessionId, content} = req.body;

      // Save user message
      const userMsg = await Message.create({
        sessionId,
        content,
        is_from_ai: false
      });

      // Call Python service to process chat logic
      // This will be implemented in the next iteration
      // todo
      const aiResponse = `AI Response: ${content} (This is a simulated response)`;

      // Save AI response
      const aiMsg = await Message.create({
        sessionId,
        content: aiResponse,
        is_from_ai: true
      });

      res.json({userMsg, aiMsg});
    } catch (err) {
      console.error('Chat processing error:', err);
      res.status(500).json({error: 'Chat processing failed'});
    }
  });
}

module.exports = chatRoute;