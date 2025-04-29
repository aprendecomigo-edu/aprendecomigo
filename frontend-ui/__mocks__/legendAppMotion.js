// Mock for @legendapp/motion
module.exports = {
  Motion: {
    View: {
      displayName: 'Motion.View',
    },
  },
  AnimatePresence: ({ children }) => children,
  createMotionAnimatedComponent: component => component,
  // Add any other exports needed by your components
};
