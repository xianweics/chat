import api from '@api';
import * as apiPath from '@api/path';
import * as actionTypes from './actionTypes';
import {extractResponseData} from '@src/utils';

export const registerUser = (username, password) => async dispatch => {
  dispatch({type: actionTypes.REGISTER_REQUEST});
  try {
    await api.post(apiPath.REGISTER_URL, {username, password});
    dispatch({type: actionTypes.REGISTER_SUCCESS});
    return {success: true};
  } catch (error) {
    const errorMessage = extractResponseData(error) || 'Registration failed';
    dispatch({type: actionTypes.REGISTER_FAILURE, payload: errorMessage});
    return {success: false, error: errorMessage};
  }
};

export const loginUser = (username, password) => async dispatch => {
  dispatch({type: actionTypes.LOGIN_REQUEST});
  try {
    const response = await api.post(apiPath.LOGIN_URL,
        {username, password});
    dispatch({
      type: actionTypes.LOGIN_SUCCESS,
      payload: extractResponseData(response, false),
    });
    return {success: true};
  } catch (error) {
    const errorMessage = extractResponseData(error) || 'Login failed';
    dispatch({type: actionTypes.LOGIN_FAILURE, payload: errorMessage});
    return {success: false, error: errorMessage};
  }
};

export const logoutUser = () => async dispatch => {
  dispatch({type: actionTypes.LOGOUT});
  dispatch({type: actionTypes.SET_ACTIVE_SESSION, payload: null});
  try {
    await api.post(apiPath.LOGOUT_URL);
    return {success: true};
  } catch (error) {
    return {success: false};
  }
};