const getEnvVars = () => {
  // Get the environment from the process.env
  const ENV = process.env.APP_ENV || 'development';
  const isDev = process.env.NODE_ENV !== 'production';

  if (isDev) {
    console.log(`Building app with ${ENV} environment`);
  }

  return {
    // Common config
    name: 'Aprende Conmigo',
    slug: 'aprendecomigo',
    version: '1.0.0',
    orientation: 'portrait',
    // Environment specific configuration
    extra: {
      env: ENV,
    },
  };
};

export default getEnvVars();
