require('dotenv').config();

const express = require('express');
const cors = require('cors');
const redisServer = require('./redis-server');
const mysqlServer = require('./mysql-server');
const {initRoute} = require('./route');
const app = express();
app.use(cors());
app.use(express.json());
initRoute(app);

(async () => {
    try {
        await redisServer.start();
        await mysqlServer.start();

        console.info('All dbs connected');
        const PORT = process.env.SERVER_PORT;
        app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
    } catch (err) {
        console.error('Fail to launch server', err);
    }
})();