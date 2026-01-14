export const handler = async (event) => {
  console.log('Health check event:', JSON.stringify(event, null, 2));

  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
    },
    body: JSON.stringify({
      status: 'ok',
      message: 'Server is running',
      timestamp: new Date().toISOString(),
    }),
  };
};
