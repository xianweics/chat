import {modules} from "@store/config";

const createActionType = type => `${modules.auth}/${type}`;

export const REGISTER_SUCCESS = createActionType('registerSuccess');
export const REGISTER_REQUEST = createActionType('registerRequest');
export const REGISTER_FAILURE = createActionType('registerFailure');
export const LOGIN_REQUEST = createActionType('loginRequest');
export const LOGIN_SUCCESS = createActionType('loginSuccess');
export const LOGIN_FAILURE = createActionType('loginFailure');
export const LOGOUT = createActionType('logout');
export const RESET = createActionType('reset');
export const SET_ACTIVE_SESSION = createActionType('setActiveSession');
