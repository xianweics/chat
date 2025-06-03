import {Avatar, Card, Typography} from 'antd';
import {UserOutlined, RobotOutlined} from '@ant-design/icons';

const {Paragraph} = Typography;

const MessageBubble = ({isFromAi, content}) => {
    return (
        <div style={{
            display: 'flex',
            flexDirection: isFromAi ? 'row' : 'row-reverse',
            marginBottom: 16
        }}>
            <Avatar
                icon={isFromAi ? <RobotOutlined/> : <UserOutlined/>}
                style={{background: isFromAi ? '#1890ff' : '#52c41a'}}
            />

            <div style={{
                maxWidth: '70%',
                marginLeft: isFromAi ? 12 : 0,
                marginRight: isFromAi ? 0 : 12
            }}>
                <Card
                    size="small"
                    style={{
                        backgroundColor: isFromAi ? '#f0f0f0' : '#d9e7ff',
                        border: 'none',
                        borderRadius: 8
                    }}
                >
                    <Paragraph style={{margin: 0}}>{content}</Paragraph>
                </Card>
            </div>
        </div>
    );
};

export default MessageBubble;