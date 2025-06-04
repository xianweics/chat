import api from '@api';
import * as actionTypes from "./actionTypes";
import * as apiPath from "@api/path";
import {modules} from "@store/config";

const {auth } = modules;
export const loadSessions = () => async (dispatch, getState) => {
  dispatch({type: actionTypes.LOAD_SESSION_REQUEST});
  try {
    const token = getState()[auth].token;
    const response = await api.get(apiPath.SESSIONS_URL, {
      headers: {Authorization: `Bearer ${token}`}
    });
    dispatch({type: actionTypes.LOAD_SESSION_SUCCESS, payload: response.data});
    return {success: true};
  } catch (error) {
    const errorMessage = error.response?.data?.error || 'Failed to load sessions';
    dispatch({type: actionTypes.LOAD_SESSION_FAILURE, payload: errorMessage});
    return {success: false, error: errorMessage};
  }
};

export const createSession = () => async (dispatch, getState) => {
  dispatch({type: actionTypes.CREATE_SESSION_REQUEST});
  try {
    const token = getState()[auth].token;
    const response = await api.post(apiPath.SESSIONS_URL, {}, {
      headers: {Authorization: `Bearer ${token}`}
    });
    dispatch({type: actionTypes.CREATE_SESSION_SUCCESS, payload: response.data});
    return {success: true, sessionId: response.data.id};
  } catch (error) {
    const errorMessage = error.response?.data?.error || 'Failed to create session';
    dispatch({type: actionTypes.CREATE_SESSION_FAILURE, payload: errorMessage});
    return {success: false, error: errorMessage};
  }
};

export const loadMessages = sessionId => async (dispatch, getState) => {
  dispatch({type: actionTypes.LOAD_MESSAGE_REQUEST});
  try {
    const token = getState()[auth].token;
    const response = await api.get(apiPath.getSessionsMessages(sessionId), {
      headers: {Authorization: `Bearer ${token}`}
    });
    dispatch({
      type: actionTypes.LOAD_MESSAGE_SUCCESS,
      payload: {sessionId, messages: response.data}
    });
    return {success: true};
  } catch (error) {
    const errorMessage = error.response?.data?.error || 'Failed to load messages';
    dispatch({type: actionTypes.LOAD_MESSAGE_FAILURE, payload: errorMessage});
    return {success: false, error: errorMessage};
  }
};

export const sendMessage = (sessionId, content) => async (dispatch, getState) => {
  dispatch({type: actionTypes.SEND_MESSAGE_REQUEST});
  try {
    const token = getState()[auth].token;
    const response = await api.post(apiPath.CHAT_URL, {
      sessionId, content
    }, {
      headers: {Authorization: `Bearer ${token}`}
    });

    const {userMsg, aiMsg} = response.data;

    dispatch({
      type: actionTypes.SEND_MESSAGE_SUCCESS,
      payload: {sessionId, userMessage: userMsg, aiMessage: aiMsg}
    });

    return {success: true};
  } catch (error) {
    const errorMessage = error.response?.data?.error || 'Failed to send message';
    dispatch({type: actionTypes.SEND_MESSAGE_FAILURE, payload: errorMessage});
    return {success: false, error: errorMessage};
  }
};

export const setActiveSession = sessionId => (dispatch) => {
  dispatch({type: actionTypes.SET_ACTIVE_SESSION, payload: sessionId});
};