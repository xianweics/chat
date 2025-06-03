import React, {useEffect} from 'react';
import {Layout, Spin} from 'antd';
import {useDispatch, useSelector} from 'react-redux';

import AuthForm from './components/AuthForm';
import SessionList from './components/SessionList';
import ChatWindow from './components/ChatWindow';
import {loadSessions} from '@store/chat/actions';

const {Content, Sider} = Layout;

function App() {
    const dispatch = useDispatch();
    const {user, token, status: authStatus} = useSelector(state => state.auth);
    const {status: chatStatus} = useSelector(state => state.chat);
    console.info(chatStatus)
    useEffect(() => {
        // 检查本地是否有token
        const storedToken = localStorage.getItem('token');
        if (storedToken) {
            try {
                // 解析JWT获取用户信息
                const payload = JSON.parse(atob(storedToken.split('.')[1]));
                const user = {id: payload.userId, username: payload.username};
                dispatch({type: 'auth/loginSuccess', payload: {user, token: storedToken}});

                // 加载会话
                dispatch(loadSessions());
            } catch (e) {
                localStorage.removeItem('token');
                console.error('Token解析失败', e);
            }
        }
    }, [dispatch]);

    useEffect(() => {
        if (user && token) {
            // 加载会话
            dispatch(loadSessions());
        }
    }, [user, token, dispatch]);

    if (authStatus === 'loading') {
        return (
            <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh'}}>
                <Spin size="large"/>
            </div>
        );
    }

    if (!user || !token) {
        return <AuthForm/>;
    }

    return (
        <Layout style={{height: '100vh'}}>
            <Sider
                width={300}
                style={{
                    background: '#fff',
                    borderRight: '1px solid #f0f0f0',
                    overflow: 'auto'
                }}
            >
                <SessionList/>
            </Sider>
            <Content style={{padding: 0, background: '#f0f2f5'}}>
                <ChatWindow/>
            </Content>
        </Layout>
    );
}

export default App;