import {useCallback, useEffect, useMemo, useState} from 'react';
import {Button, Card, Input, Typography} from 'antd';
import {SendOutlined} from '@ant-design/icons';
import {useDispatch, useSelector} from 'react-redux';

import MessageBubble from './MessageBubble';
import {sendMessage} from '@store/chat/actions';
import {modules} from '@store/config';
import {
  MESSAGE_STATUS_SUCCEEDED,
  SEND_STATUS_LOADING,
} from '@store/chat/statuses.config';

const {Title} = Typography;

const ChatWindow = () => {
  const [message, setMessage] = useState('');
  const dispatch = useDispatch();
  
  const {activeSessionId, sessions, messages, send} = useSelector(
    state => state[modules.chat]);
  const list = useMemo(() => {
    const {status, messages: msg} = messages;
    return status === MESSAGE_STATUS_SUCCEEDED ? msg : [];
  }, [messages]);
  const currentSession = useMemo(() => sessions[activeSessionId],
    [activeSessionId, sessions]);
  const isLoading = useMemo(() => send.status === SEND_STATUS_LOADING,
    [send]);

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
  },[activeSessionId]);
  
  return activeSessionId ? <Card
    title={currentSession?.title || 'Chat Session'}
    style={{height: '100%', display: 'flex', flexDirection: 'column'}}
  >
    <div style={{flex: 1, overflowY: 'auto', padding: 16}}>
      {list.length === 0 ?
        <div style={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'rgba(0,0,0,0.45)'
        }}>
          No chat history
        </div>
        : list.map((msg) => <MessageBubble
            key={msg.id}
            isFromAi={msg.is_from_ai}
            content={msg.content}
          />
        )}
    </div>

    <div style={{padding: 16, borderTop: '1px solid #f0f0f0'}}>
      <Input.TextArea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onPressEnter={handleKeyPress}
        placeholder="Type a message..."
        autoSize={{minRows: 1, maxRows: 6}}
        disabled={isLoading}
      />
      <div style={{textAlign: 'right', marginTop: 12}}>
        <Button
          type="primary"
          icon={<SendOutlined/>}
          onClick={handleSendMessage}
          loading={isLoading}
          disabled={!message.trim()}
        >
          Send
        </Button>
      </div>
    </div>
  </Card> : <Card style={{height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
    <Title level={4} type="secondary">Please select or create a chat session</Title>
  </Card>;
};

export default ChatWindow;