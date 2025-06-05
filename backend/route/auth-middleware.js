const jwt = require("jsonwebtoken");
const {readFileSync} = require("fs");
const {resolve} = require("path");

const publicKey = readFileSync(resolve(__dirname, "../../public.pem"));

const authenticateJWT = (req, res, next) => {
  const authHeader = req.headers.authorization;
  if (authHeader) {
    const token = authHeader.split(' ')[1];
    jwt.verify(token, publicKey, {algorithms: ["RS256"]}, (err, user) => {
      if (err) {
        return res.sendStatus(403);
      }

      req.user = user;
      next();
    });
  } else {
    res.sendStatus(401);
  }
};

module.exports = {authenticateJWT}