winston = require('winston');
var convict = require('convict');


var conf = convict({
  debug: {
    doc: 'Turn on debugging messages (flag only)',
    format: Boolean,
    default: false,
    arg: 'debug',
    env: 'CRAWL_DEBUG'
  },
  initQueueSize: {
    doc: 'How many items to put in initial queue',
    default: 100,
    arg: 'queue',
    env: 'CRAWL_QUEUE'
  },
  maxItems: {
    doc: 'Stop the job after this many fetches',
    format: 'int',
    default: 0,
    arg: 'max',
    env: 'CRAWL_MAX'
  },
  timeToRun: {
    doc: 'Stop the job after this time',
    format: 'int',
    default: 240,
    arg: 'time',
    env: 'CRAWL_TIME'
  },
  fetchIncrement: {
    doc: 'Wait this many days before refetching the items',
    format: 'int',
    default: 7,
    arg: 'fetchwait',
    env: 'CRAWL_FETCHWAIT'
  },
  concurrency: {
    doc: 'How much concurrenct should the crawler implement',
    format: 'int',
    default: 4,
    arg: 'conc',
    env: 'CRAWL_CONC'
  },
  interval: {
    doc: 'Millisecond interval between requests',
    format: 'int',
    default: 2000,
    arg: 'interval',
    env: 'CRAWL_INTERVAL'
  },
  logFile: {
    doc: 'logfile location - full path. Note: _std.log or _err.log will be automatically appended.',
    //TODO: Path validation
    format: function check(val) {
      return true;
    },
    default: './logs/crawl',
    arg: 'logfile',
    env: 'CRAWL_LOGFILE'
  },
  //TODO - Ensure folder is there, otherwise no file logging.
  dbHost: {
    doc: 'Database Host',
    format: String,
    default: 'localhost',
    arg: 'dbHost',
    env: 'CRAWL_DBHOST'
  },
  dbPort: {
    doc: 'Database Port',
    format: 'int',
    default: 5432,
    arg: 'dbPort',
    env: 'CRAWL_DBPORT'
  },
  //TODO: Create new DB user account.
  dbUser: {
    doc: 'Database Username',
    format: String,
    default: 'webContent',
    arg: 'dbUser',
    env: 'CRAWL_DBUSER'
  },
  //TODO: Create new DB user account.
  dbPass: {
    doc: 'Database Password',
    format: String,
    default: 'developmentPassword',
    arg: 'dbPass',
    env: 'CRAWL_DBPASS'
  },
  dbName: {
    doc: 'The Database to use',
    format: String,
    default: 'webContent',
    arg: 'dbName',
    env: 'CRAWL_DBNAME'

  },
  flipOrder: {
    doc: 'Only select record ids which are odd',
    format: Boolean,
    default: false,
    arg: 'fliporder',
    env: 'CRAWL_FLIPORDER'
  },
  apiKey: {
    doc: 'Data.gov.au apiKey',
    format: String,
    default: '',
    arg: 'apikey',
    env: 'HOSTLOAD_APIKEY'
  },
  outputId: {
    doc: 'Data.gov.au output datastore ID',
    format: String,
    default: '377bc789-63ec-4cc0-9d2a-987f26d7a521',
    arg: 'outputid',
    env: 'HOSTLOAD_OUTPUT_ID'
  },
  whitelistId: {
    doc: 'Data.gov.au whitelist datastore ID',
    format: String,
    default: '8aea9d2f-fd21-42ef-8cc5-bf9db3533bf8',
    arg: 'whitelistid',
    env: 'HOSTLOAD_WHITELIST_ID'
  },
  blacklistId: {
    doc: 'Data.gov.au blacklist datastore ID',
    format: String,
    default: '6239de78-b28c-45a8-add2-413ed6a6f88a',
    arg: 'blacklistid',
    env: 'HOSTLOAD_BLACKLIST_ID'
  }
});
conf.validate();

module.exports = conf;

//console.log(JSON.stringify(conf));
