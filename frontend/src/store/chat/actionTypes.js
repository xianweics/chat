import {modules} from "@store/config";

const createActionType = type => `${modules.chat}/${type}`;

export const LOAD_SESSION_REQUEST = createActionType('loadSessionsRequest');
export const LOAD_SESSION_SUCCESS = createActionType('loadSessionsSuccess');
export const LOAD_SESSION_FAILURE = createActionType('loadSessionsFailure');
export const CREATE_SESSION_REQUEST = createActionType('createSessionRequest');
export const CREATE_SESSION_FAILURE = createActionType('createSessionFailure');
export const CREATE_SESSION_SUCCESS = createActionType('createSessionSuccess');
export const LOAD_MESSAGE_REQUEST = createActionType('loadMessagesRequest');
export const LOAD_MESSAGE_SUCCESS = createActionType('loadMessagesSuccess');
export const LOAD_MESSAGE_FAILURE = createActionType('loadMessagesFailure');
export const SEND_MESSAGE_REQUEST = createActionType('sendMessageRequest');
export const SEND_MESSAGE_SUCCESS = createActionType('sendMessageSuccess');
export const SEND_MESSAGE_FAILURE = createActionType('sendMessageFailure');
export const SET_ACTIVE_SESSION = createActionType('setActiveSession');
