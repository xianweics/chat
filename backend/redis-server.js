require('dotenv').config();

const redis = require('redis');

const redisClient = redis.createClient({
    socket: {
        host: process.env.REDIS_URL,
        port: process.env.REDIS_PORT,
        reconnectStrategy: (retries) => {
            if (retries > process.env.REDIS_MAX_TIME) {
                return new Error(`Redis retry ${process.env.REDIS_MAX_TIME} times`);
            }
            return Math.min(retries * 1000, 5000);
        }
    },
    password: process.env.REDIS_PASSWORD
});

const start = async () => {
    try {
        await redisClient.connect()
        console.info('Success to connect redis')
    } catch (e) {
        console.error('Fail to connect redis', e)
    }
}
module.exports = {
    start,
    redisClient
};