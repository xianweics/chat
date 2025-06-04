import {useState, useEffect, useRef, useMemo, useCallback} from 'react';
import {Button, Input, Typography, Card} from 'antd';
import {SendOutlined} from '@ant-design/icons';
import {useDispatch, useSelector} from 'react-redux';

import MessageBubble from './MessageBubble';
import {sendMessage} from '@store/chat/actions';
import {AUTH_STATUS_LOADING} from "@src/config";
import {modules} from "@store/config";

const {Title} = Typography;

const ChatWindow = () => {
  const [message, setMessage] = useState('');
  const messagesEndRef = useRef(null);
  const dispatch = useDispatch();

  const {activeSessionId, sessions, status} = useSelector(state => state[modules.chat]);

  const currentSession = useMemo(() => activeSessionId ? sessions[activeSessionId] : null, [activeSessionId, sessions]);
  const messages = useMemo(() => currentSession?.messages || [], [currentSession]);

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
    messagesEndRef.current?.scrollIntoView({behavior: 'smooth'});
  }, []);

  return activeSessionId ? <Card
    title={currentSession?.title || 'Chat Session'}
    style={{height: '100%', display: 'flex', flexDirection: 'column'}}
  >
    <div style={{flex: 1, overflowY: 'auto', padding: 16}}>
      {messages.length === 0 ?
        <div style={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'rgba(0,0,0,0.45)'
        }}>
          No chat history
        </div>
        : messages.map((msg) => <MessageBubble
            key={msg.id}
            isFromAi={msg.is_from_ai}
            content={msg.content}
          />
        )}
      <div ref={messagesEndRef}/>
    </div>

    <div style={{padding: 16, borderTop: '1px solid #f0f0f0'}}>
      <Input.TextArea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onPressEnter={handleKeyPress}
        placeholder="Type a message..."
        autoSize={{minRows: 1, maxRows: 6}}
        disabled={status === AUTH_STATUS_LOADING}
      />
      <div style={{textAlign: 'right', marginTop: 12}}>
        <Button
          type="primary"
          icon={<SendOutlined/>}
          onClick={handleSendMessage}
          loading={status === AUTH_STATUS_LOADING}
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