import {modules} from '@store/config';

const createActionType = type => `${modules.chat}/${type}`;

export const LOAD_SESSIONS_REQUEST = createActionType('loadSessionsRequest');
export const LOAD_SESSIONS_SUCCESS = createActionType('loadSessionsSuccess');
export const LOAD_SESSIONS_FAILURE = createActionType('loadSessionsFailure');
export const CREATE_SESSIONS_REQUEST = createActionType('createSessionRequest');
export const CREATE_SESSIONS_FAILURE = createActionType('createSessionFailure');
export const CREATE_SESSIONS_SUCCESS = createActionType('createSessionSuccess');
export const LOAD_MESSAGES_REQUEST = createActionType('loadMessagesRequest');
export const LOAD_MESSAGES_SUCCESS = createActionType('loadMessagesSuccess');
export const LOAD_MESSAGES_FAILURE = createActionType('loadMessagesFailure');
export const SEND_MESSAGE_REQUEST = createActionType('sendMessageRequest');
export const SEND_MESSAGE_SUCCESS = createActionType('sendMessageSuccess');
export const SEND_MESSAGES_FAILURE = createActionType('sendMessageFailure');
export const SET_ACTIVE_SESSION = createActionType('setActiveSession');
export const UPDATE_TEMP_MESSAGES = createActionType('updateTempMessages');
