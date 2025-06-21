import React from 'react';
import SessionList from '@components/SessionList';
import ChatWindow from '@components/ChatWindow';
import {Layout} from 'antd';

const {Content, Sider} = Layout;

const Chat = () => {

  return (
      <Layout style={{height: '100vh'}}>
        <Sider
            width={300}
            style={{
              background: '#fff',
              borderRight: '1px solid #f0f0f0',
              overflow: 'auto',
            }}
        >
          <SessionList/>
        </Sider>
        <Content style={{height: '100%', overflow: 'auto'}}>
          <ChatWindow/>
        </Content>
      </Layout>
  );
};

export default Chat; 