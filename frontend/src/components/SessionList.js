import {List, Button, Typography, Skeleton, Card} from 'antd';
import {PlusOutlined} from '@ant-design/icons';
import {useDispatch, useSelector} from 'react-redux';

import {
  createSession,
  setActiveSession,
  loadMessages
} from '@store/chat/actions';
import {AUTH_STATUS_LOADING} from "@src/config";
import {modules} from "@store/config";
import {useCallback, useMemo} from "react";

const {Title} = Typography;

const SessionList = () => {
  const dispatch = useDispatch();
  const {sessions, activeSessionId, status} = useSelector(state => state[modules.chat]);
  const sessionsList = useMemo(() => Object.values(sessions), [sessions]);

  const handleCreateSession = useCallback(async () => {
    const {success, sessionId} = await dispatch(createSession());
    if (success) {
      dispatch(setActiveSession(sessionId));
    }
  },[dispatch]);

  const handleSelectSession = useCallback(sessionId => {
    dispatch(setActiveSession(sessionId));
    dispatch(loadMessages(sessionId));
  },[dispatch]);

  return (
    <Card style={{height: '100%'}}>
      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: 16}}>
        <Title level={4} style={{margin: 0}}>Chat Sessions</Title>
        <Button
          type="primary"
          icon={<PlusOutlined/>}
          onClick={handleCreateSession}
          loading={status === AUTH_STATUS_LOADING}
        >
          New
        </Button>
      </div>

      {status === AUTH_STATUS_LOADING ?
        <Skeleton active paragraph={{rows: 4}}/> :
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
                  ? session.messages[session.messages.length - 1]?.content.substring(0, 50) + '...'
                  : 'No messages yet'}
              />
            </List.Item>
          )}
        />
      }
    </Card>
  );
};

export default SessionList;