require('dotenv').config();

const {Sequelize} = require("sequelize");
const initModels = require('./models');

const sequelize = new Sequelize(process.env.DB_NAME, process.env.DB_USER, process.env.DB_PASSWORD, {
  host: process.env.DB_HOST,
  dialect: 'mysql',
  logging: true,
  port: process.env.DB_PORT
});

const models = initModels(sequelize);

const start = async () => {
  try {
    await sequelize.authenticate()
    if (process.env.NODE_ENV === 'development') {
      await sequelize.sync({alter: true})
      console.info('Database structure synchronized')
    }
    console.info('Successfully connected to MySQL')
  } catch (e) {
    console.error('Failed to connect to MySQL', e)
  }
}

module.exports = {
  start,
  sequelize,
  ...models
}
