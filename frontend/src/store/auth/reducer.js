import {AUTH_STATUS_LOADING, AUTH_STATUS_SUCCEEDED, AUTH_STATUS_FAILED, AUTH_STATUS_IDLE} from "@src/config";
import {modules, MODULE_NAME} from "@store/config";
import * as actionTypes from "./actionTypes";

const prefix = modules.auth;

const authInitialState = {
  user: null,
  token: null,
  status: AUTH_STATUS_IDLE,
  error: null,
  [MODULE_NAME]: prefix
};

const auth = (state = authInitialState, action) => {
  const {type, payload} = action;
  const {user, token} = payload || {};
  switch (type) {
    case actionTypes.LOGIN_REQUEST:
      return {...state, status: AUTH_STATUS_LOADING};
    case actionTypes.LOGIN_SUCCESS:
      return {
        ...state,
        user,
        token,
        error: null,
        status: AUTH_STATUS_SUCCEEDED
      };
    case actionTypes.LOGIN_FAILURE:
      return {...state, status: AUTH_STATUS_FAILED, error: payload};
    case actionTypes.REGISTER_REQUEST:
      return {...state, status: AUTH_STATUS_LOADING};
    case actionTypes.REGISTER_SUCCESS:
      return {...state, status: AUTH_STATUS_SUCCEEDED, error: null};
    case actionTypes.REGISTER_FAILURE:
      return {...state, status: AUTH_STATUS_FAILED, error: payload};
    case actionTypes.LOGOUT:
      return {...authInitialState};
    default:
      return state;
  }
}

export default auth;
