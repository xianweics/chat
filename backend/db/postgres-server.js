const { Sequelize } = require("sequelize");
const initModels = require('./models');

const sequelize = new Sequelize(process.env.POSTGRES_DB_NAME, process.env.POSTGRES_DB_USER, process.env.POSTGRES_DB_PASSWORD, {
  host: process.env.POSTGRES_DB_HOST,
  dialect: 'postgres',
  logging: true,
  port: process.env.POSTGRES_DB_PORT,
  pool: {
    max: 5,
    min: 0,
    idle: 10000
  }
});

const models = initModels(sequelize);

const start = async () => {
  try {
    await sequelize.authenticate();
    if (process.env.NODE_ENV === 'development') {
      await sequelize.sync({ alter: true });
      console.info('Database structure synchronized');
    }
    console.info('Successfully connected to PostgreSQL');
  } catch (e) {
    console.error('Failed to connect to PostgreSQL', e);
  }
};

module.exports = {
  start,
  sequelize,
  ...models
}; 