const getEnvVars = () => {
  // Get the environment from the process.env
  const ENV = process.env.APP_ENV || 'development';

  if (__DEV__) {
    if (__DEV__) {
      console.log(`Building app with ${ENV} environment`);
    }
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
