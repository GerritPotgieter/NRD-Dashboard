/**
 * Simple in-memory cache utility for API responses
 */

class Cache {
    constructor(defaultTTL = 60000) { // Default 60 seconds
        this.cache = new Map();
        this.defaultTTL = defaultTTL;
    }

    /**
     * Generate cache key from params
     */
    generateKey(prefix, params = {}) {
        const sortedParams = Object.keys(params)
            .sort()
            .map(key => `${key}=${JSON.stringify(params[key])}`)
            .join('&');
        return `${prefix}:${sortedParams}`;
    }

    /**
     * Set cache entry
     */
    set(key, value, ttl = this.defaultTTL) {
        const expiresAt = Date.now() + ttl;
        this.cache.set(key, {
            value,
            expiresAt
        });
    }

    /**
     * Get cache entry
     */
    get(key) {
        const entry = this.cache.get(key);

        if (!entry) {
            return null;
        }

        // Check if expired
        if (Date.now() > entry.expiresAt) {
            this.cache.delete(key);
            return null;
        }

        return entry.value;
    }

    /**
     * Clear specific cache entry
     */
    clear(key) {
        this.cache.delete(key);
    }

    /**
     * Clear all cache entries with prefix
     */
    clearPrefix(prefix) {
        const keysToDelete = [];
        for (const key of this.cache.keys()) {
            if (key.startsWith(prefix)) {
                keysToDelete.push(key);
            }
        }
        keysToDelete.forEach(key => this.cache.delete(key));
    }

    /**
     * Clear all cache
     */
    clearAll() {
        this.cache.clear();
    }

    /**
     * Clean expired entries
     */
    cleanup() {
        const now = Date.now();
        for (const [key, entry] of this.cache.entries()) {
            if (now > entry.expiresAt) {
                this.cache.delete(key);
            }
        }
    }
}

// Create singleton instance
const apiCache = new Cache(30000); // 30 second default TTL

// Cleanup expired entries every minute
setInterval(() => {
    apiCache.cleanup();
}, 60000);

export default apiCache;
