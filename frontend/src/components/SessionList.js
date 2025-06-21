import {Button, Card, List, Skeleton, Typography} from 'antd';
import {PlusOutlined} from '@ant-design/icons';
import {useDispatch, useSelector} from 'react-redux';

import {
  createSession,
  loadMessages,
  loadSessions,
  resetLoadMessage,
  setActiveSession,
} from '@store/chat/actions';
import {
  SESSION_STATUS_IDLE,
  SESSION_STATUS_LOADING,
} from '@store/chat/statuses.config';
import {modules} from '@store/config';
import {useCallback, useEffect, useMemo} from 'react';
import {formatSessionDescription} from '@src/utils';

const {Title} = Typography;

const SessionList = () => {
  const dispatch = useDispatch();
  const {sessions, activeSessionId} = useSelector(state => state[modules.chat]);
  const [sessionsList, sessionsStatus] = useMemo(
      () => [
        Object.values(sessions.data),
        sessions.status], [sessions]);
  const isLoading = useMemo(
      () => [SESSION_STATUS_LOADING, SESSION_STATUS_IDLE].includes(
          sessionsStatus), [sessionsStatus]);
  const handleCreateSession = useCallback(async () => {
    const {success, sessionId} = await dispatch(createSession());
    if (success) {
      dispatch(setActiveSession(sessionId));
      dispatch(resetLoadMessage());
    }
  }, [dispatch]);

  const handleSelectSession = useCallback(sessionId => {
    dispatch(setActiveSession(sessionId));
    dispatch(loadMessages(sessionId));
  }, [dispatch]);

  useEffect(() => {
    dispatch(loadSessions());
    console.info(11);
  }, [dispatch]);

  return (
      <Card style={{border: 'none'}}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: 16,
        }}>
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
                          backgroundColor: id === activeSessionId ?
                              '#e6f7ff' :
                              '',
                          padding: '10px 16px',
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