export const parseToken = token => {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch (error) {
    throw error;
  }
}

export const formatSessionDescription = messages => messages.length === 0
  ? 'No messages yet'
  : messages[0]?.content.trim() || '';