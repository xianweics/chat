import api from '@api';
import * as apiPath from "@api/path";
import * as actionTypes from "./actionTypes";
import {TOKEN} from "@src/config";
import {parseToken} from "@src/utils";

export const registerUser = (username, password) => async dispatch => {
  dispatch({type: actionTypes.REGISTER_REQUEST});
  try {
    await api.post(apiPath.REGISTER_URL, {username, password});
    dispatch({type: actionTypes.REGISTER_SUCCESS});
    return {success: true};
  } catch (error) {
    const errorMessage = error.response?.data?.error || 'Registration failed';
    dispatch({type: actionTypes.REGISTER_FAILURE, payload: errorMessage});
    return {success: false, error: errorMessage};
  }
};

export const loginUser = (un, password) => async dispatch => {
  dispatch({type: actionTypes.LOGIN_REQUEST});
  try {
    const response = await api.post(apiPath.LOGIN_URL, {username: un, password});
    const {token} = response.data;
    localStorage.setItem(TOKEN, token);

    const {userId, username} = parseToken(token);
    const user = {id: userId, username};
    dispatch({type: actionTypes.LOGIN_SUCCESS, payload: {user, token}});
    return {success: true, user};
  } catch (error) {
    const errorMessage = error.response?.data?.error || 'Login failed';
    dispatch({type: actionTypes.LOGIN_FAILURE, payload: errorMessage});
    return {success: false, error: errorMessage};
  }
};

export const logoutUser = () => async dispatch => {
  localStorage.removeItem(TOKEN);
  dispatch({type: actionTypes.LOGOUT});
  dispatch({type: actionTypes.SET_ACTIVE_SESSION, payload: null});
  await api.post(apiPath.LOGOUT_URL);
};