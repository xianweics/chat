import {Button, Card, List, Skeleton, Typography} from 'antd';
import {PlusOutlined} from '@ant-design/icons';
import {useDispatch, useSelector} from 'react-redux';

import {
  createSession,
  loadMessages, resetLoadMessage,
  setActiveSession,
} from '@store/chat/actions';
import {SESSION_STATUS_LOADING} from '@store/chat/statuses.config';
import {modules} from '@store/config';
import {useCallback, useMemo} from 'react';
import {formatSessionDescription} from '@src/utils';

const {Title} = Typography;

const SessionList = () => {
  const dispatch = useDispatch();
  const {sessions, activeSessionId} = useSelector(state => state[modules.chat]);
  const [sessionsList, status] = useMemo(() => [Object.values(sessions.sessions), sessions.status], [sessions]);
  
  const isLoading = useMemo(() => status === SESSION_STATUS_LOADING, [status]);
  const handleCreateSession = useCallback(async () => {
    const {success, sessionId} = await dispatch(createSession());
    if (success) {
      dispatch(setActiveSession(sessionId));
      dispatch(resetLoadMessage());
    }
  },[dispatch]);

  const handleSelectSession = useCallback(sessionId => {
    dispatch(setActiveSession(sessionId));
    dispatch(loadMessages(sessionId));
  },[dispatch]);

  return (
    <Card>
      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: 16}}>
        <Title level={4} style={{margin: 0}}>Chat Sessions</Title>
        <Button
          type="primary"
          icon={<PlusOutlined/>}
          onClick={handleCreateSession}
          loading={isLoading}
        >
          New
        </Button>
      </div>

      {isLoading ?
        <Skeleton active paragraph={{rows: 4}}/> :
        <List
          itemLayout="horizontal"
          dataSource={sessionsList}
          renderItem={({id, title, messages}) => (
            <List.Item
              style={{
                cursor: 'pointer',
                backgroundColor: id === activeSessionId ? '#e6f7ff' : '',
                padding: '10px 16px'
              }}
              onClick={() => handleSelectSession(id)}
            >
              <List.Item.Meta
                title={title}
                description={<div style={{
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}>
                  {formatSessionDescription(messages)}
                </div>}
              />
            </List.Item>
          )}
        />
      }
    </Card>
  );
};

export default SessionList;