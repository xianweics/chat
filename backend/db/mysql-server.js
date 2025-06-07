const {Sequelize} = require("sequelize");
const initModels = require('./models');

const sequelize = new Sequelize(process.env.MYSQL_DB_NAME, process.env.MYSQL_DB_USER, process.env.DB_PASSWORD, {
  host: process.env.MYSQL_DB_HOST,
  dialect: 'mysql',
  logging: true,
  port: process.env.MYSQL_DB_PORT
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
