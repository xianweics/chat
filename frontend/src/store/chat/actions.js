import api from '@api';
import * as actionTypes from './actionTypes';
import * as apiPath from '@api/path';
import {modules} from '@store/config';
import {extractResponseData} from '@src/utils';

const {auth} = modules;
export const loadSessions = () => async (dispatch, getState) => {
  dispatch({type: actionTypes.LOAD_SESSIONS_REQUEST});
  try {
    const token = getState()[auth].token;
    const response = await api.get(apiPath.SESSIONS_URL, {
      headers: {Authorization: `Bearer ${token}`},
    });
    dispatch({
      type: actionTypes.LOAD_SESSIONS_SUCCESS,
      payload: extractResponseData(response, false),
    });
    return {success: true};
  } catch (error) {
    const errorMessage = extractResponseData(error) ||
        'Failed to load sessions';
    dispatch({type: actionTypes.LOAD_SESSIONS_FAILURE, payload: errorMessage});
    return {success: false, error: errorMessage};
  }
};

export const createSession = () => async (dispatch, getState) => {
  dispatch({type: actionTypes.CREATE_SESSIONS_REQUEST});
  try {
    const token = getState()[auth].token;
    const response = await api.post(apiPath.SESSIONS_URL, {}, {
      headers: {Authorization: `Bearer ${token}`},
    });
    const data = extractResponseData(response, false);
    dispatch(
        {type: actionTypes.CREATE_SESSIONS_SUCCESS, payload: data});
    return {success: true, sessionId: data.id};
  } catch (error) {
    const errorMessage = extractResponseData(error) ||
        'Failed to create session';
    dispatch(
        {type: actionTypes.CREATE_SESSIONS_FAILURE, payload: errorMessage});
    return {success: false, error: errorMessage};
  }
};

export const loadMessages = sessionId => async (dispatch, getState) => {
  dispatch({type: actionTypes.LOAD_MESSAGES_REQUEST});
  try {
    const token = getState()[auth].token;
    const response = await api.get(apiPath.getSessionsMessages(sessionId), {
      headers: {Authorization: `Bearer ${token}`},
    });
    dispatch({
      type: actionTypes.LOAD_MESSAGES_SUCCESS,
      payload: {sessionId, data: extractResponseData(response, false)},
    });
    return {success: true};
  } catch (error) {
    const errorMessage = extractResponseData(error) ||
        'Failed to load messages';
    dispatch({type: actionTypes.LOAD_MESSAGES_FAILURE, payload: errorMessage});
    return {success: false, error: errorMessage};
  }
};

export const sendMessage = (sessionId, content) => async (
    dispatch, getState) => {
  dispatch({type: actionTypes.SEND_MESSAGE_REQUEST});
  try {
    dispatch({
      type: actionTypes.UPDATE_TEMP_MESSAGES, payload: {
        data: [
          {
            content,
            id: '$temp0',
            session_id: sessionId,
            role: 'user',
            ai_model: '',
            created_at: new Date().toISOString(),
          }, {
            content: '',
            isLoading: true,
            id: '$temp1',
            session_id: sessionId,
            role: 'ai',
            ai_model: '',
            created_at: new Date().toISOString(),
          },
        ],
        type: 'add',
      },
    });
    const token = getState()[auth].token;
    const response = await api.post(apiPath.CHAT_URL, {
      sessionId, content,
    }, {
      headers: {Authorization: `Bearer ${token}`},
    });

    const data = extractResponseData(response, false);

    dispatch({
      type: actionTypes.SEND_MESSAGE_SUCCESS,
      payload: {sessionId, data, removeData: ['$temp1']},
    });

    return {success: true};
  } catch (error) {
    const errorMessage = extractResponseData(error) || 'Failed to send message';
    dispatch({type: actionTypes.SEND_MESSAGES_FAILURE, payload: errorMessage});
    dispatch({
      type: actionTypes.UPDATE_TEMP_MESSAGES, payload: {
        data: ['$temp0', '$temp1'],
        type: 'remove',
      },
    });
    return {success: false, error: errorMessage};
  }
};

export const setActiveSession = sessionId => (dispatch) => {
  dispatch({type: actionTypes.SET_ACTIVE_SESSION, payload: sessionId});
};