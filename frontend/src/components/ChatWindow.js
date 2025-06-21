import {useCallback, useEffect, useMemo, useState} from 'react';
import {Button, Card, Input, Skeleton, Typography} from 'antd';
import {SendOutlined} from '@ant-design/icons';
import {useDispatch, useSelector} from 'react-redux';

import MessageBubble from './MessageBubble';
import {sendMessage} from '@store/chat/actions';
import {modules} from '@store/config';
import {
  CREATE_SESSION_STATUS_LOADING,
  LOAD_MESSAGES_STATUS_LOADING,
  LOAD_MESSAGES_STATUS_SUCCEEDED,
  SEND_MESSAGE_STATUS_LOADING,
} from '@store/chat/statuses.config';

const {Title} = Typography;

const ChatWindow = () => {
  const [message, setMessage] = useState('');
  const dispatch = useDispatch();

  const {activeSessionId, sessions, messages, send, create} = useSelector(
      state => state[modules.chat]);
  const list = useMemo(() => {
    const {status, data} = messages;
    return status === LOAD_MESSAGES_STATUS_SUCCEEDED ? data : [];
  }, [messages]);
  const currentSession = useMemo(() => sessions.data[activeSessionId],
      [activeSessionId, sessions]);
  const isLoadingSend = useMemo(
      () => send.status === SEND_MESSAGE_STATUS_LOADING,
      [send]);
  const isLoadingMessages = useMemo(
      () => messages.status === LOAD_MESSAGES_STATUS_LOADING ||
          create.status === CREATE_SESSION_STATUS_LOADING,
      [messages, create]);

  const handleSendMessage = useCallback(() => {
    if (!message.trim()) return;

    dispatch(sendMessage(activeSessionId, message));
    setMessage('');
  }, [message, activeSessionId, dispatch]);

  const handleKeyPress = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);

  useEffect(() => {
    setMessage('');
  }, [activeSessionId]);

  useEffect(() => {
    console.info('ss', list);
  }, [list]);

  return activeSessionId ?
      <Card
          title={currentSession?.title || 'Chat Session'}
          style={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            border: 'none',
          }}
      >
        {isLoadingMessages ? <Skeleton active paragraph={{rows: 6}}/> : <>
          <div style={{overflowY: 'auto', padding: 16, height: '100%'}}>
            {list.length === 0 && !isLoadingSend ?
                <div style={{
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'rgba(0,0,0,0.45)',
                }}>
                  No chat history
                </div>
                : list.map(item => <MessageBubble key={item.id} {...item} />)
            }
          </div>
          <div style={{padding: 16, borderTop: '1px solid #f0f0f0'}}>
            <Input.TextArea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onPressEnter={handleKeyPress}
                placeholder="Type a message..."
                autoSize={{minRows: 1, maxRows: 6}}
                disabled={isLoadingSend}
            />
            <div style={{textAlign: 'right', marginTop: 12}}>
              <Button
                  type="primary"
                  icon={<SendOutlined/>}
                  onClick={handleSendMessage}
                  loading={isLoadingSend}
                  disabled={!message.trim()}
              >
                Send
              </Button>
            </div>
          </div>
        </>}

      </Card> :
      <Card style={{
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: 'none',
      }}>
        <Title level={4} type="secondary" style={{
          display: 'flex',
          alignItems: 'center',
          height: '100%',
        }}>Please select or create a chat session</Title>
      </Card>;
};

export default ChatWindow;