const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const {readFileSync} = require('fs');
const {resolve} = require('path');

const {User} = require('../db/postgres-server');
const {REGISTER_URL, LOGIN_URL, LOGOUT_URL} = require('./path');
const privateKey = readFileSync(resolve(__dirname, '../private.pem'));

const authRoute = app => {
  app.post(REGISTER_URL, async (req, res) => {
    const {username, password} = req.body;
    if (!username || !password) {
      res.status(400).json({data: 'Registration failed'});
      return;
    }
    const formatUserName = username.trim();
    const hasSameUser = await User.findOne({where: {username: formatUserName}});
    if (hasSameUser) {
      res.status(409).json({data: 'User already exists'});
      return;
    }
    try {
      const hashedPassword = await bcrypt.hash(password, 10);
      await User.create({username, password: hashedPassword});
      res.status(201).json({data: `User ${username} created`});
    } catch (err) {
      res.status(400).json({data: 'Registration failed'});
    }
  });

  app.post(LOGIN_URL, async (req, res) => {
    try {
      const {username, password} = req.body;
      if (!username || !password) {
        res.status(400).json({data: 'Login failed'});
        return;
      }
      const formatUserName = username.trim();
      const user = await User.findOne({where: {username: formatUserName}});
      if (!user) {
        return res.status(401).json({data: 'Invalid credentials'});
      }

      const isValid = await bcrypt.compare(password, user.password);

      if (!isValid) {
        return res.status(401).json({data: 'Invalid credentials'});
      }

      const token = jwt.sign({userId: user.id, username: user.username},
          privateKey, {
            expiresIn: process.env.JWT_EXPIRE_TIME,
            algorithm: process.env.JWT_ALGORITHM,
          });

      res.json({data: token});
    } catch (err) {
      res.status(500).json({data: 'Login failed'});
    }
  });

  app.post(LOGOUT_URL, (req, res) => {
    try {
      res.json({data: 'Logout successful'});
    } catch (err) {
      res.status(500).json({data: 'Logout failed'});
    }
  });
};

module.exports = authRoute;
