const baseConfig = require("../../../karma.conf.js");

module.exports = function (config) {
  baseConfig(config);

  config.set({
    coverageReporter: {
      dir: require("path").join(__dirname, "./coverage/my-app"),
    },
  });
};
