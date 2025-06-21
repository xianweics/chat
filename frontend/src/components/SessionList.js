import {Button, Card, Flex, List, message, Skeleton, Typography} from 'antd';
import {LogoutOutlined, PlusOutlined} from '@ant-design/icons';
import {useDispatch, useSelector} from 'react-redux';

import {
  createSession,
  loadMessages,
  loadSessions,
  setActiveSession,
} from '@store/chat/actions';
import {logoutUser} from '@store/auth/actions';
import {
  SESSION_STATUS_IDLE,
  SESSION_STATUS_LOADING,
} from '@store/chat/statuses.config';
import {modules} from '@store/config';
import {useCallback, useEffect, useMemo} from 'react';
import {formatSessionDescription} from '@src/utils';
import {useNavigate} from 'react-router-dom';

const {Title} = Typography;

const SessionList = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
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
    }
  }, [dispatch]);
  const handleLogout = useCallback(async () => {
    const {success} = await dispatch(logoutUser());
    if (success) {
      navigate('/');
      message.success('Logout successfully');
    } else {
      message.success('Logout failed');
    }
  }, [dispatch, navigate]);

  const handleSelectSession = useCallback(sessionId => {
    dispatch(setActiveSession(sessionId));
    dispatch(loadMessages(sessionId));
  }, [dispatch]);

  useEffect(() => {
    dispatch(loadSessions());
  }, [dispatch]);

  return (
      <Card style={{border: 'none'}}>
        <Title level={4} style={{margin: 0}}>Chat Sessions</Title>
        <div>
          <Flex gap="small" justify="flex-end" style={{margin: '12px 0'}}>
            <Button
                size="small"
                type="primary"
                icon={<PlusOutlined/>}
                onClick={handleCreateSession}
                loading={isLoading}
            >
              New
            </Button>
            <Button
                size="small"
                icon={<LogoutOutlined/>}
                onClick={handleLogout}
            >
              Logout
            </Button>
          </Flex>
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