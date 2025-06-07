const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const {readFileSync} = require('fs');
const {resolve} = require('path');

const {User} = require('../db/postgres-server');
const {REGISTER_URL, LOGIN_URL} = require('./path');
const privateKey = readFileSync(resolve(__dirname, '../../private.pem'));

const authRoute = app => {
  app.post(REGISTER_URL, async (req, res) => {
    const {username, password} = req.body;
    const formatUserName = username.trim();
    const hasSameUser = await User.findOne({where: {username: formatUserName}});
    if (hasSameUser) {
      res.status(409).send({error: 'User already exists'});
      return;
    }
    try {
      const hashedPassword = await bcrypt.hash(password, 10);
      await User.create({username, password: hashedPassword});
      res.status(201).json({message: `User ${username} created`});
    } catch (err) {
      res.status(400).json({error: 'Registration failed'});
    }
  });

  app.post(LOGIN_URL, async (req, res) => {
    try {
      const {username, password} = req.body;
      const formatUserName = username.trim();
      const user = await User.findOne({where: {username: formatUserName}});
      if (!user) {
        return res.status(401).json({code: 401, error: 'INVALID_CREDENTIALS'});
      }

      const isValid = await bcrypt.compare(password, user.password);

      if (!isValid) {
        return res.status(401).json({code: 401, error: 'INVALID_CREDENTIALS'});
      }

      const token = jwt.sign({userId: user.id, username: user.username},
          privateKey, {
            expiresIn: process.env.JWT_EXPIRE_TIME,
            algorithm: process.env.JWT_ALGORITHM,
          });

      res.json({token});
    } catch (err) {
      console.error('Login error:', err);
      res.status(500).json({error: 'Login failed'});
    }
  });
};

module.exports = authRoute;
