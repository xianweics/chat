const {DataTypes, Sequelize} = require('sequelize');

const AIMessageRole = {
  USER: 'USER',
  AI: 'AI',
};

module.exports = sequelize => {
  const User = sequelize.define('users', {
    id: {
      type: DataTypes.UUID,
      primaryKey: true,
      unique: true,
      defaultValue: Sequelize.UUIDV4
    },
    username: {
      type: DataTypes.STRING(100),
      unique: true,
      allowNull: false,
    },
    password: {
      type: DataTypes.STRING(300),
      allowNull: false,
    },
    created_at: {
      type: DataTypes.DATE,
      defaultValue: Sequelize.fn('NOW'),
      allowNull: true,
    },
  }, {timestamps: false});

  const AISession = sequelize.define('ai_sessions', {
    id: {
      type: DataTypes.UUID,
      primaryKey: true,
      unique: true,
      defaultValue: Sequelize.UUIDV4,
    },
    user_id: {
      type: DataTypes.UUID,
      allowNull: false,
      references: {
        model: 'users',
        key: 'id',
      },
    },
    title: {
      type: DataTypes.STRING(100),
      defaultValue: 'New session',
    },
    created_at: {
      type: DataTypes.DATE,
      defaultValue: Sequelize.fn('NOW'),
      allowNull: true,
    },
  }, {timestamps: false});

  const AIMessage = sequelize.define('ai_messages', {
    id: {
      type: DataTypes.UUID,
      primaryKey: true,
      unique: true,
      defaultValue: Sequelize.UUIDV4,
    },
    session_id: {
      type: DataTypes.UUID,
      allowNull: false,
      references: {
        model: 'ai_sessions',
        key: 'id',
      },
    },
    role: {
      type: DataTypes.STRING(20),
      allowNull: false,
    },
    content: {
      type: DataTypes.TEXT,
      allowNull: false,
    },
    ai_model: {
      type: DataTypes.STRING(50),
      defaultValue: '',
    },
    created_at: {
      type: DataTypes.DATE,
      defaultValue: Sequelize.fn('NOW'),
      allowNull: false,
    },
  }, {
    timestamps: false,
  });

  User.hasMany(AISession, {
    foreignKey: 'user_id',
    as: 'sessions',
    onDelete: 'CASCADE',
  });

  AISession.belongsTo(User, {
    foreignKey: 'user_id',
    as: 'user',
  });

  AISession.hasMany(AIMessage, {
    foreignKey: 'session_id',
    as: 'messages',
    onDelete: 'CASCADE',
  });

  AIMessage.belongsTo(AISession, {
    foreignKey: 'session_id',
    as: 'session',
  });

  return {User, AISession, AIMessage};
};