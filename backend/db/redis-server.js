require('dotenv').config();

const redis = require('redis');

const redisClient = redis.createClient({
  socket: {
    host: process.env.REDIS_URL,
    port: process.env.REDIS_PORT
  },
  password: process.env.REDIS_PASSWORD
});

const start = async () => {
  try {
    await redisClient.connect()
    console.info('Successfully connected to Redis')
  } catch (e) {
    console.error('Failed to connect to Redis', e)
  }
}
module.exports = {
  start,
  redisClient
};