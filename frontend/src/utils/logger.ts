import { LogEntry, LogLevel } from '@/types';

type LogLevelType = 'debug' | 'info' | 'warn' | 'error';

interface ExtendedLogEntry extends LogEntry {
  tenant: string | null;
  url: string;
}

class Logger {
  private logs: ExtendedLogEntry[] = [];
  private readonly maxLogs: number = 1000;
  private readonly isDevelopment: boolean;

  constructor() {
    this.isDevelopment = process.env.NODE_ENV === 'development';
  }

  log(level: LogLevelType, message: string, metadata: Record<string, any> = {}): void {
    const logEntry: ExtendedLogEntry = {
      level,
      message,
      timestamp: Date.now(),
      metadata,
      tenant: this.getCurrentTenant(),
      url: typeof window !== 'undefined' ? window.location.href : '',
    };

    this.logs.push(logEntry);
    
    // Keep only the last N logs
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    // Console output for development
    if (this.isDevelopment && typeof console !== 'undefined') {
      const consoleMethod = console[level] || console.log;
      consoleMethod(`[${level.toUpperCase()}] ${message}`, metadata);
    }

    // Send critical errors to server
    if (level === 'error') {
      this.sendToServer(logEntry).catch((error) => {
        // Silently handle server logging errors to avoid infinite loops
        if (this.isDevelopment) {
          console.warn('Failed to send log to server:', error);
        }
      });
    }
  }

  private getCurrentTenant(): string | null {
    if (typeof window === 'undefined') {
      return null;
    }

    try {
      const hostname = window.location.hostname;
      const subdomain = hostname.split('.')[0];
      
      // Don't treat localhost, IPs, or common domains as subdomains
      if (['localhost', '127', '0', 'www'].includes(subdomain) || 
          /^\d+$/.test(subdomain)) {
        return 'demo'; // Default tenant for development
      }
      
      return subdomain;
    } catch (error) {
      return null;
    }
  }

  private async sendToServer(logEntry: ExtendedLogEntry): Promise<void> {
    if (typeof fetch === 'undefined') {
      return; // Not in browser environment
    }

    try {
      const response = await fetch('/api/logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(logEntry),
        // Don't wait too long for logging requests
        signal: AbortSignal.timeout(5000),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      // In development, we want to know about logging failures
      if (this.isDevelopment && typeof console !== 'undefined') {
        console.warn('Failed to send log to server:', error);
      }
      // In production, fail silently to avoid disrupting user experience
    }
  }

  // Convenience methods
  info(message: string, metadata?: Record<string, any>): void {
    this.log('info', message, metadata);
  }

  warn(message: string, metadata?: Record<string, any>): void {
    this.log('warn', message, metadata);
  }

  error(message: string, metadata?: Record<string, any>): void {
    this.log('error', message, metadata);
  }

  debug(message: string, metadata?: Record<string, any>): void {
    this.log('debug', message, metadata);
  }

  // Log management methods
  getLogs(): ExtendedLogEntry[] {
    return [...this.logs]; // Return a copy to prevent external mutation
  }

  getLogsByLevel(level: LogLevelType): ExtendedLogEntry[] {
    return this.logs.filter(log => log.level === level);
  }

  getLogsAfter(timestamp: number): ExtendedLogEntry[] {
    return this.logs.filter(log => log.timestamp > timestamp);
  }

  clearLogs(): void {
    this.logs = [];
  }

  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  // Performance logging
  time(label: string): void {
    if (this.isDevelopment && typeof console !== 'undefined' && console.time) {
      console.time(label);
    }
    
    this.debug(`Timer started: ${label}`);
  }

  timeEnd(label: string): void {
    if (this.isDevelopment && typeof console !== 'undefined' && console.timeEnd) {
      console.timeEnd(label);
    }
    
    this.debug(`Timer ended: ${label}`);
  }

  // Group logging (useful for debugging complex operations)
  group(label: string): void {
    if (this.isDevelopment && typeof console !== 'undefined' && console.group) {
      console.group(label);
    }
    
    this.debug(`Group started: ${label}`);
  }

  groupEnd(): void {
    if (this.isDevelopment && typeof console !== 'undefined' && console.groupEnd) {
      console.groupEnd();
    }
    
    this.debug('Group ended');
  }
}

export const logger = new Logger();
export default logger;