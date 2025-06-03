import {List, Button, Typography, Skeleton, Card} from 'antd';
import {PlusOutlined} from '@ant-design/icons';
import {useDispatch, useSelector} from 'react-redux';

import {
    createSession,
    setActiveSession,
    loadMessages
} from '@store/chat/actions';

const {Title} = Typography;

const SessionList = () => {
    const dispatch = useDispatch();
    const {sessions, activeSessionId, status} = useSelector(state => state.chat);
    const sessionsList = Object.values(sessions);

    const handleCreateSession = async () => {
        const {payload} = await dispatch(createSession());
        if (payload.id) {
            dispatch(setActiveSession(payload.id));
        }
    };

    const handleSelectSession = (sessionId) => {
        dispatch(setActiveSession(sessionId));
        dispatch(loadMessages(sessionId));
    };

    return (
        <Card style={{height: '100%'}}>
            <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: 16}}>
                <Title level={4} style={{margin: 0}}>聊天会话</Title>
                <Button
                    type="primary"
                    icon={<PlusOutlined/>}
                    onClick={handleCreateSession}
                    loading={status === 'loading'}
                >
                    新建
                </Button>
            </div>

            {status === 'loading' ? (
                <Skeleton active paragraph={{rows: 4}}/>
            ) : (
                <List
                    itemLayout="horizontal"
                    dataSource={sessionsList}
                    renderItem={session => (
                        <List.Item
                            style={{
                                cursor: 'pointer',
                                backgroundColor: session.id === activeSessionId ? '#e6f7ff' : '',
                                padding: '10px 16px'
                            }}
                            onClick={() => handleSelectSession(session.id)}
                        >
                            <List.Item.Meta
                                title={session.title}
                                description={session.messages.length > 0
                                    ? session.messages[session.messages.length - 1].content.substring(0, 50) + '...'
                                    : '暂无消息'}
                            />
                        </List.Item>
                    )}
                />
            )}
        </Card>
    );
};

export default SessionList;