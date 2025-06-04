require('dotenv').config();

const express = require('express');
const cors = require('cors');
const redisServer = require('./db/redis-server');
const mysqlServer = require('./db/mysql-server');
const {initRoute} = require('./route');
const app = express();
app.use(cors());
app.use(express.json());
initRoute(app);

const start = async () => {
  await redisServer.start();
  await mysqlServer.start();
  const server = app.listen(process.env.SERVER_PORT, process.env.SERVER_HOST, () => {
    console.log(`Server running on http://${server.address().address}:${server.address().port}`)
  });
}

start().catch(err => {
  console.error('Failed to launch server', err);
})