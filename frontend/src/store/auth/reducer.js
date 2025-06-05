import * as statuses from './statuses.config';
import {MODULE_NAME, modules} from '@store/config';
import * as actionTypes from './actionTypes';

const prefix = modules.auth;

const authInitialState = {
  user: null,
  token: null,
  status: statuses.AUTH_STATUS_IDLE,
  error: null,
  [MODULE_NAME]: prefix
};

const auth = (state = authInitialState, action) => {
  const {type, payload} = action;
  const {user, token} = payload || {};
  switch (type) {
    case actionTypes.LOGIN_REQUEST:
      return {...state, status:  statuses.AUTH_STATUS_LOADING};
    case actionTypes.LOGIN_SUCCESS:
      return {
        ...state,
        user,
        token,
        error: null,
        status:  statuses.AUTH_STATUS_SUCCEEDED
      };
    case actionTypes.LOGIN_FAILURE:
      return {...state, status:  statuses.AUTH_STATUS_FAILED, error: payload};
    case actionTypes.REGISTER_REQUEST:
      return {...state, status:  statuses.AUTH_STATUS_LOADING};
    case actionTypes.REGISTER_SUCCESS:
      return {...state, status:  statuses.AUTH_STATUS_SUCCEEDED, error: null};
    case actionTypes.REGISTER_FAILURE:
      return {...state, status:  statuses.AUTH_STATUS_FAILED, error: payload};
    case actionTypes.LOGOUT:
    case actionTypes.RESET:
      return {...authInitialState};
    default:
      return state;
  }
}

export default auth;
