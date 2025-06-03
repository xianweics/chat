import {useState, useEffect, useRef, useMemo} from 'react';
import {Button, Input, Typography, Card} from 'antd';
import {SendOutlined} from '@ant-design/icons';
import {useDispatch, useSelector} from 'react-redux';

import MessageBubble from './MessageBubble';
import {sendMessage} from '@store/chat/actions';

const {Title} = Typography;

const ChatWindow = () => {
    const [message, setMessage] = useState('');
    const messagesEndRef = useRef(null);
    const dispatch = useDispatch();

    const {activeSessionId, sessions, status} = useSelector(state => state.chat);

    const currentSession = useMemo(() => {
        return activeSessionId ? sessions[activeSessionId] : null
    }, [activeSessionId, sessions]);
    const messages = useMemo(() => {
        return currentSession ? currentSession.messages : []
    }, [currentSession]);

    const handleSendMessage = async () => {
        if (!message.trim()) return;

        dispatch(sendMessage(activeSessionId, message));
        setMessage('');
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    // 自动滚动到底部
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({behavior: 'smooth'});
    }, [messages]);

    if (!activeSessionId) {
        return (
            <Card style={{height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                <Title level={4} type="secondary">请选择或创建一个聊天会话</Title>
            </Card>
        );
    }

    return (
        <Card
            title={currentSession?.title || '聊天会话'}
            style={{height: '100%', display: 'flex', flexDirection: 'column'}}
        >
            <div style={{flex: 1, overflowY: 'auto', padding: 16}}>
                {messages.length === 0 ? (
                    <div style={{
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'rgba(0,0,0,0.45)'
                    }}>
                        暂无聊天记录
                    </div>
                ) : (
                    messages.map((msg) => (
                        <MessageBubble
                            key={msg.id}
                            isFromAi={msg.is_from_ai}
                            content={msg.content}
                        />
                    ))
                )}
                <div ref={messagesEndRef}/>
            </div>

            <div style={{padding: 16, borderTop: '1px solid #f0f0f0'}}>
                <Input.TextArea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onPressEnter={handleKeyPress}
                    placeholder="输入消息..."
                    autoSize={{minRows: 1, maxRows: 6}}
                    disabled={status === 'loading'}
                />
                <div style={{textAlign: 'right', marginTop: 12}}>
                    <Button
                        type="primary"
                        icon={<SendOutlined/>}
                        onClick={handleSendMessage}
                        loading={status === 'loading'}
                        disabled={!message.trim()}
                    >
                        发送
                    </Button>
                </div>
            </div>
        </Card>
    );
};

export default ChatWindow;