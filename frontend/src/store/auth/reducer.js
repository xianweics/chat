import * as statuses from './statuses.config';
import {MODULE_NAME, modules} from '@store/config';
import * as actionTypes from './actionTypes';
import {TOKEN, USER} from '@src/config';
import {parseToken} from '@src/utils';

const prefix = modules.auth;

const getInitialState = () => {
  const token = localStorage.getItem(TOKEN);
  const userStr = localStorage.getItem(USER);
  const user = userStr ? JSON.parse(userStr) : null;

  return {
    [MODULE_NAME]: prefix,
    user,
    token,
    login: {
      status: statuses.LOGIN_STATUS_IDLE,
      error: null,
    },
    register: {
      status: statuses.REGISTER_STATUS_IDLE,
      error: null,
    },
  };
};

const auth = (state = getInitialState(), action) => {
  const {type, payload} = action;
  switch (type) {
    case actionTypes.LOGIN_REQUEST:
      return {
        ...state,
        login: {
          error: null,
          status: statuses.LOGIN_STATUS_LOADING,
        },
      };
    case actionTypes.LOGIN_SUCCESS:
      const {userId, username} = parseToken(payload);
      const user = {id: userId, username};
      localStorage.setItem(TOKEN, payload);
      localStorage.setItem(USER, JSON.stringify(user));
      return {
        ...state,
        user,
        token: payload,
        login: {
          error: null,
          status: statuses.LOGIN_STATUS_SUCCEEDED,
        },
      };
    case actionTypes.LOGIN_FAILURE:
      return {
        ...state,
        login: {
          error: payload,
          status: statuses.LOGIN_STATUS_FAILED,
        },
      };
    case actionTypes.REGISTER_REQUEST:
      return {
        ...state, register: {
          error: null,
          status: statuses.REGISTER_STATUS_LOADING,
        },
      };
    case actionTypes.REGISTER_SUCCESS:
      return {
        ...state,
        register: {
          status: statuses.REGISTER_STATUS_SUCCEEDED,
          error: null,
        },
      };
    case actionTypes.REGISTER_FAILURE:
      return {
        ...state, register: {
          status: statuses.REGISTER_STATUS_FAILED,
          error: payload,
        },
      };
    case actionTypes.LOGOUT:
      localStorage.removeItem(TOKEN);
      localStorage.removeItem(USER);
      return {...getInitialState()};
    default:
      return state;
  }
};

export default auth;
