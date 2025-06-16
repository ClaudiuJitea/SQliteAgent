// Utility Functions Module
class Utils {
    // Date and time utilities
    static formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
        if (!date) return '';
        
        const d = new Date(date);
        if (isNaN(d.getTime())) return 'Invalid Date';
        
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        const seconds = String(d.getSeconds()).padStart(2, '0');
        
        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    }
    
    static formatRelativeTime(date) {
        if (!date) return '';
        
        const now = new Date();
        const target = new Date(date);
        const diffMs = now - target;
        const diffSecs = Math.floor(diffMs / 1000);
        const diffMins = Math.floor(diffSecs / 60);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffSecs < 60) {
            return 'just now';
        } else if (diffMins < 60) {
            return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
        } else if (diffHours < 24) {
            return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
        } else if (diffDays < 7) {
            return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
        } else {
            return this.formatDate(date, 'MM/DD/YYYY');
        }
    }
    
    // String utilities
    static truncateString(str, maxLength = 50, suffix = '...') {
        if (!str || str.length <= maxLength) return str;
        return str.substring(0, maxLength - suffix.length) + suffix;
    }
    
    static capitalizeFirst(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    }
    
    static camelToSnake(str) {
        return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
    }
    
    static snakeToCamel(str) {
        return str.replace(/_([a-z])/g, (match, letter) => letter.toUpperCase());
    }
    
    static slugify(str) {
        return str
            .toLowerCase()
            .trim()
            .replace(/[^\w\s-]/g, '')
            .replace(/[\s_-]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }
    
    // Number utilities
    static formatNumber(num, decimals = 0) {
        if (num === null || num === undefined || isNaN(num)) return '0';
        return Number(num).toLocaleString(undefined, {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    }
    
    static formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
    
    static formatPercentage(value, total, decimals = 1) {
        if (!total || total === 0) return '0%';
        const percentage = (value / total) * 100;
        return `${percentage.toFixed(decimals)}%`;
    }
    
    // Array utilities
    static groupBy(array, key) {
        return array.reduce((groups, item) => {
            const group = item[key];
            groups[group] = groups[group] || [];
            groups[group].push(item);
            return groups;
        }, {});
    }
    
    static sortBy(array, key, direction = 'asc') {
        return [...array].sort((a, b) => {
            const aVal = a[key];
            const bVal = b[key];
            
            if (aVal < bVal) return direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return direction === 'asc' ? 1 : -1;
            return 0;
        });
    }
    
    static unique(array, key = null) {
        if (key) {
            const seen = new Set();
            return array.filter(item => {
                const value = item[key];
                if (seen.has(value)) {
                    return false;
                }
                seen.add(value);
                return true;
            });
        }
        return [...new Set(array)];
    }
    
    static chunk(array, size) {
        const chunks = [];
        for (let i = 0; i < array.length; i += size) {
            chunks.push(array.slice(i, i + size));
        }
        return chunks;
    }
    
    // Object utilities
    static deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (typeof obj === 'object') {
            const cloned = {};
            Object.keys(obj).forEach(key => {
                cloned[key] = this.deepClone(obj[key]);
            });
            return cloned;
        }
    }
    
    static deepMerge(target, source) {
        const result = { ...target };
        
        Object.keys(source).forEach(key => {
            if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                result[key] = this.deepMerge(result[key] || {}, source[key]);
            } else {
                result[key] = source[key];
            }
        });
        
        return result;
    }
    
    static getNestedValue(obj, path, defaultValue = null) {
        const keys = path.split('.');
        let current = obj;
        
        for (const key of keys) {
            if (current === null || current === undefined || !(key in current)) {
                return defaultValue;
            }
            current = current[key];
        }
        
        return current;
    }
    
    static setNestedValue(obj, path, value) {
        const keys = path.split('.');
        let current = obj;
        
        for (let i = 0; i < keys.length - 1; i++) {
            const key = keys[i];
            if (!(key in current) || typeof current[key] !== 'object') {
                current[key] = {};
            }
            current = current[key];
        }
        
        current[keys[keys.length - 1]] = value;
        return obj;
    }
    
    // DOM utilities
    static createElement(tag, attributes = {}, children = []) {
        const element = document.createElement(tag);
        
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'innerHTML') {
                element.innerHTML = value;
            } else if (key === 'textContent') {
                element.textContent = value;
            } else if (key.startsWith('data-')) {
                element.setAttribute(key, value);
            } else {
                element[key] = value;
            }
        });
        
        children.forEach(child => {
            if (typeof child === 'string') {
                element.appendChild(document.createTextNode(child));
            } else if (child instanceof Node) {
                element.appendChild(child);
            }
        });
        
        return element;
    }
    
    static removeElement(element) {
        if (element && element.parentNode) {
            element.parentNode.removeChild(element);
        }
    }
    
    static toggleClass(element, className, force = null) {
        if (!element) return;
        
        if (force !== null) {
            element.classList.toggle(className, force);
        } else {
            element.classList.toggle(className);
        }
    }
    
    static hasClass(element, className) {
        return element && element.classList.contains(className);
    }
    
    // Event utilities
    static debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    }
    
    static throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    // Validation utilities
    static isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    static isValidURL(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }
    
    static isValidJSON(str) {
        try {
            JSON.parse(str);
            return true;
        } catch {
            return false;
        }
    }
    
    static isValidSQL(sql) {
        // Basic SQL validation
        const sqlKeywords = /\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TRUNCATE)\b/i;
        return sqlKeywords.test(sql.trim());
    }
    
    // Storage utilities
    static setLocalStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Error setting localStorage:', error);
            return false;
        }
    }
    
    static getLocalStorage(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Error getting localStorage:', error);
            return defaultValue;
        }
    }
    
    static removeLocalStorage(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Error removing localStorage:', error);
            return false;
        }
    }
    
    static clearLocalStorage() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('Error clearing localStorage:', error);
            return false;
        }
    }
    
    // File utilities
    static downloadFile(content, filename, contentType = 'text/plain') {
        const blob = new Blob([content], { type: contentType });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    }
    
    static readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = e => resolve(e.target.result);
            reader.onerror = e => reject(e);
            reader.readAsText(file);
        });
    }
    
    static readFileAsDataURL(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = e => resolve(e.target.result);
            reader.onerror = e => reject(e);
            reader.readAsDataURL(file);
        });
    }
    
    // URL utilities
    static getQueryParams() {
        const params = new URLSearchParams(window.location.search);
        const result = {};
        for (const [key, value] of params) {
            result[key] = value;
        }
        return result;
    }
    
    static setQueryParam(key, value) {
        const url = new URL(window.location);
        url.searchParams.set(key, value);
        window.history.replaceState({}, '', url);
    }
    
    static removeQueryParam(key) {
        const url = new URL(window.location);
        url.searchParams.delete(key);
        window.history.replaceState({}, '', url);
    }
    
    // Color utilities
    static hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }
    
    static rgbToHex(r, g, b) {
        return '#' + [r, g, b].map(x => {
            const hex = x.toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        }).join('');
    }
    
    static getContrastColor(hexColor) {
        const rgb = this.hexToRgb(hexColor);
        if (!rgb) return '#000000';
        
        const brightness = (rgb.r * 299 + rgb.g * 587 + rgb.b * 114) / 1000;
        return brightness > 128 ? '#000000' : '#ffffff';
    }
    
    // Random utilities
    static generateId(length = 8) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    }
    
    static generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    static randomChoice(array) {
        return array[Math.floor(Math.random() * array.length)];
    }
    
    static randomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }
    
    // Performance utilities
    static measureTime(func, label = 'Operation') {
        const start = performance.now();
        const result = func();
        const end = performance.now();
        console.log(`${label} took ${(end - start).toFixed(2)} milliseconds`);
        return result;
    }
    
    static async measureAsyncTime(asyncFunc, label = 'Async Operation') {
        const start = performance.now();
        const result = await asyncFunc();
        const end = performance.now();
        console.log(`${label} took ${(end - start).toFixed(2)} milliseconds`);
        return result;
    }
    
    // Error handling utilities
    static safeExecute(func, defaultValue = null, errorHandler = null) {
        try {
            return func();
        } catch (error) {
            if (errorHandler) {
                errorHandler(error);
            } else {
                console.error('Safe execute error:', error);
            }
            return defaultValue;
        }
    }
    
    static async safeExecuteAsync(asyncFunc, defaultValue = null, errorHandler = null) {
        try {
            return await asyncFunc();
        } catch (error) {
            if (errorHandler) {
                errorHandler(error);
            } else {
                console.error('Safe execute async error:', error);
            }
            return defaultValue;
        }
    }
    
    // Type checking utilities
    static isObject(value) {
        return value !== null && typeof value === 'object' && !Array.isArray(value);
    }
    
    static isArray(value) {
        return Array.isArray(value);
    }
    
    static isString(value) {
        return typeof value === 'string';
    }
    
    static isNumber(value) {
        return typeof value === 'number' && !isNaN(value);
    }
    
    static isBoolean(value) {
        return typeof value === 'boolean';
    }
    
    static isFunction(value) {
        return typeof value === 'function';
    }
    
    static isEmpty(value) {
        if (value === null || value === undefined) return true;
        if (typeof value === 'string') return value.trim().length === 0;
        if (Array.isArray(value)) return value.length === 0;
        if (this.isObject(value)) return Object.keys(value).length === 0;
        return false;
    }
    
    // Browser utilities
    static getBrowserInfo() {
        const ua = navigator.userAgent;
        const browsers = {
            chrome: /Chrome/.test(ua) && /Google Inc/.test(navigator.vendor),
            firefox: /Firefox/.test(ua),
            safari: /Safari/.test(ua) && /Apple Computer/.test(navigator.vendor),
            edge: /Edg/.test(ua),
            ie: /Trident/.test(ua)
        };
        
        const browser = Object.keys(browsers).find(key => browsers[key]) || 'unknown';
        
        return {
            name: browser,
            userAgent: ua,
            language: navigator.language,
            platform: navigator.platform,
            cookieEnabled: navigator.cookieEnabled,
            onLine: navigator.onLine
        };
    }
    
    static isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }
    
    static isTablet() {
        return /iPad|Android(?!.*Mobile)/i.test(navigator.userAgent);
    }
    
    static isDesktop() {
        return !this.isMobile() && !this.isTablet();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Utils;
} else {
    window.Utils = Utils;
}