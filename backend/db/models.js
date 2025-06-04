const {DataTypes} = require("sequelize");

module.exports = sequelize => {
  const User = sequelize.define('User', {
    id: {type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true},
    username: {type: DataTypes.STRING(50), unique: true, allowNull: false},
    password: {type: DataTypes.STRING(255), allowNull: false}
  }, {timestamps: true});

  const Session = sequelize.define('Session', {
    id: {type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true},
    title: {type: DataTypes.STRING(100), allowNull: false, defaultValue: 'New session'}
  }, {timestamps: true});

  const Message = sequelize.define('Message', {
    id: {type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true},
    content: {type: DataTypes.TEXT, allowNull: false},
    is_from_ai: {type: DataTypes.BOOLEAN, allowNull: false, defaultValue: false}
  }, {
    timestamps: true,
    indexes: [{fields: ['createdAt']}]
  });

  User.hasMany(Session, {foreignKey: 'userId'});
  Session.belongsTo(User, {foreignKey: 'userId'});
  Session.hasMany(Message, {foreignKey: 'sessionId'});
  Message.belongsTo(Session, {foreignKey: 'sessionId'});
  return {User, Session, Message};
};