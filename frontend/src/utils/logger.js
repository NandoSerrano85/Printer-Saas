// utils/logger.js
class Logger {
  constructor() {
    this.logs = [];
    this.maxLogs = 1000;
  }

  log(level, message, data = {}) {
    const logEntry = {
      level,
      message,
      data,
      timestamp: new Date().toISOString(),
      tenant: this.getCurrentTenant(),
      url: window.location.href,
    };

    this.logs.push(logEntry);
    
    // Keep only the last N logs
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    // Console output for development
    if (process.env.NODE_ENV === 'development') {
      console[level](message, data);
    }

    // Send critical errors to server
    if (level === 'error') {
      this.sendToServer(logEntry);
    }
  }

  getCurrentTenant() {
    const hostname = window.location.hostname;
    return hostname.split('.')[0];
  }

  async sendToServer(logEntry) {
    try {
      await fetch('/api/logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(logEntry),
      });
    } catch (error) {
      console.error('Failed to send log to server:', error);
    }
  }

  info(message, data) {
    this.log('info', message, data);
  }

  warn(message, data) {
    this.log('warn', message, data);
  }

  error(message, data) {
    this.log('error', message, data);
  }

  debug(message, data) {
    this.log('debug', message, data);
  }

  getLogs() {
    return this.logs;
  }

  clearLogs() {
    this.logs = [];
  }
}

export const logger = new Logger();