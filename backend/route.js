require('dotenv').config();
const bcrypt = require("bcrypt");
const jwt = require('jsonwebtoken');
const {authenticateJWT} = require("./auth");
const {User, Session, Message} = require('./mysql-server');

const initRoute = app => {
    app.post('/api/register', async (req, res) => {
        try {
            const {username, password} = req.body;
            const hashedPassword = await bcrypt.hash(password, 10);
            const user = await User.create({username, password: hashedPassword});
            res.status(201).json({message: 'User created'});
        } catch (err) {
            console.error('Registration error:', err);
            res.status(400).json({error: 'Registration failed'});
        }
    });

    app.post('/api/login', async (req, res) => {
        try {
            const {username, password} = req.body;
            const user = await User.findOne({where: {username}});
            console.info(user);
            if (!user) {
                return res.status(401).json({code: 401, error: "INVALID_CREDENTIALS"});
            }

            const isValid = await bcrypt.compare(password, user.password);

            if (!isValid) {
                return res.status(401).json({code: 401, error: "INVALID_CREDENTIALS"});
            }

            const token = jwt.sign({userId: user.id, username: user.username}, process.env.JWT_SECRET, {
                expiresIn: '2h'
            });

            res.json({token});
        } catch (err) {
            console.error('Login error:', err);
            res.status(500).json({error: 'Login failed'});
        }
    });

    app.get('/api/sessions', authenticateJWT, async (req, res) => {
        try {
            const sessions = await Session.findAll({
                where: {userId: req.user.userId},
                order: [['updatedAt', 'DESC']],
                include: [{
                    model: Message,
                    as: 'Messages',
                    limit: 1,
                    order: [['createdAt', 'DESC']]
                }]
            });

            res.json(sessions);
        } catch (err) {
            console.error('Get sessions error:', err);
            res.status(500).json({error: 'Failed to retrieve sessions'});
        }
    });

    app.post('/api/sessions', authenticateJWT, async (req, res) => {
        try {
            const session = await Session.create({
                userId: req.user.userId,
                title: `对话-${new Date().toLocaleDateString('zh-CN')}`
            });

            res.status(201).json(session);
        } catch (err) {
            console.error('Create session error:', err);
            res.status(500).json({error: 'Failed to create session'});
        }
    });

    app.get('/api/sessions/:id/messages', authenticateJWT, async (req, res) => {
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

    app.post('/api/chat', authenticateJWT, async (req, res) => {
        try {
            const {sessionId, content} = req.body;

            // 保存用户消息
            const userMsg = await Message.create({
                sessionId,
                content,
                is_from_ai: false
            });

            // 在这里调用Python服务处理聊天逻辑
            // 这将在下一轮实现
            const aiResponse = `AI响应: ${content} (这是模拟响应)1`;

            // 保存AI响应
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

module.exports = {initRoute}
