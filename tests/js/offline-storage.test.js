/**
 * Tests for OfflineStorage Module
 * Tests IndexedDB-based offline data persistence
 * @module tests/offline-storage.test
 */

// ==================== IndexedDB Mock Implementation ====================

/**
 * Mock IDBRequest implementation
 */
class MockIDBRequest {
  constructor() {
    this.result = null;
    this.error = null;
    this.onsuccess = null;
    this.onerror = null;
    this.onupgradeneeded = null;
  }

  _succeed(result) {
    this.result = result;
    if (this.onsuccess) {
      this.onsuccess({ target: this });
    }
  }

  _fail(error) {
    this.error = error;
    if (this.onerror) {
      this.onerror({ target: this });
    }
  }
}

/**
 * Mock IDBCursor implementation
 */
class MockIDBCursor {
  constructor(data, index = 0) {
    this.data = data;
    this.index = index;
    this.value = data[index];
    this.key = data[index]?.id;
    this.primaryKey = data[index]?.id;
  }

  continue() {
    this.index++;
    return this.index < this.data.length ? new MockIDBCursor(this.data, this.index) : null;
  }

  delete() {
    this.data.splice(this.index, 1);
    return new MockIDBRequest();
  }
}

/**
 * Mock IDBObjectStore implementation
 */
class MockIDBObjectStore {
  constructor(name, keyPath = 'id', autoIncrement = false) {
    this.name = name;
    this.keyPath = keyPath;
    this.autoIncrement = autoIncrement;
    this.data = new Map();
    this.indexes = new Map();
    this._autoIncrementId = 1;
    this._shouldFail = false;
    this._failError = null;
  }

  createIndex(name, keyPath, options = {}) {
    const index = new MockIDBIndex(name, keyPath, this, options);
    this.indexes.set(name, index);
    return index;
  }

  index(name) {
    const idx = this.indexes.get(name);
    if (!idx) {
      throw new Error(`Index "${name}" not found`);
    }
    return idx;
  }

  put(value) {
    const request = new MockIDBRequest();

    setTimeout(() => {
      if (this._shouldFail) {
        request._fail(this._failError || new Error('Mock IndexedDB error'));
        return;
      }

      let key;
      if (this.autoIncrement && !value[this.keyPath]) {
        key = this._autoIncrementId++;
        value[this.keyPath] = key;
      } else {
        key = value[this.keyPath];
      }

      this.data.set(key, { ...value });
      request._succeed(key);
    }, 0);

    return request;
  }

  add(value) {
    const request = new MockIDBRequest();

    setTimeout(() => {
      if (this._shouldFail) {
        request._fail(this._failError || new Error('Mock IndexedDB error'));
        return;
      }

      let key;
      if (this.autoIncrement) {
        key = this._autoIncrementId++;
        value[this.keyPath] = key;
      } else {
        key = value[this.keyPath];
      }

      if (this.data.has(key)) {
        request._fail(new Error('Key already exists'));
        return;
      }

      this.data.set(key, { ...value });
      request._succeed(key);
    }, 0);

    return request;
  }

  get(key) {
    const request = new MockIDBRequest();

    setTimeout(() => {
      if (this._shouldFail) {
        request._fail(this._failError || new Error('Mock IndexedDB error'));
        return;
      }

      const result = this.data.get(key);
      request._succeed(result || undefined);
    }, 0);

    return request;
  }

  getAll(query) {
    const request = new MockIDBRequest();

    setTimeout(() => {
      if (this._shouldFail) {
        request._fail(this._failError || new Error('Mock IndexedDB error'));
        return;
      }

      let results = Array.from(this.data.values());

      if (query instanceof MockIDBKeyRange) {
        results = results.filter(item => item[this.keyPath] === query.value);
      }

      request._succeed(results);
    }, 0);

    return request;
  }

  delete(key) {
    const request = new MockIDBRequest();

    setTimeout(() => {
      if (this._shouldFail) {
        request._fail(this._failError || new Error('Mock IndexedDB error'));
        return;
      }

      this.data.delete(key);
      request._succeed(undefined);
    }, 0);

    return request;
  }

  clear() {
    const request = new MockIDBRequest();

    setTimeout(() => {
      if (this._shouldFail) {
        request._fail(this._failError || new Error('Mock IndexedDB error'));
        return;
      }

      this.data.clear();
      request._succeed(undefined);
    }, 0);

    return request;
  }

  count() {
    const request = new MockIDBRequest();

    setTimeout(() => {
      if (this._shouldFail) {
        request._fail(this._failError || new Error('Mock IndexedDB error'));
        return;
      }

      request._succeed(this.data.size);
    }, 0);

    return request;
  }

  openCursor(range) {
    const request = new MockIDBRequest();

    setTimeout(() => {
      if (this._shouldFail) {
        request._fail(this._failError || new Error('Mock IndexedDB error'));
        return;
      }

      let data = Array.from(this.data.values());

      if (range instanceof MockIDBKeyRange) {
        data = data.filter(item => {
          const keyValue = item[range.indexKeyPath || this.keyPath];
          return keyValue === range.value;
        });
      }

      if (data.length === 0) {
        request._succeed(null);
      } else {
        // Store reference to original data for deletion
        const cursor = new MockIDBCursor(data);
        cursor.delete = () => {
          const itemToDelete = data[cursor.index];
          if (itemToDelete) {
            this.data.delete(itemToDelete[this.keyPath]);
          }
          return new MockIDBRequest();
        };
        cursor.continue = () => {
          cursor.index++;
          if (cursor.index < data.length) {
            cursor.value = data[cursor.index];
            cursor.key = data[cursor.index]?.id;
            request._succeed(cursor);
          } else {
            request._succeed(null);
          }
        };
        request._succeed(cursor);
      }
    }, 0);

    return request;
  }
}

/**
 * Mock IDBIndex implementation
 */
class MockIDBIndex {
  constructor(name, keyPath, store, options = {}) {
    this.name = name;
    this.keyPath = keyPath;
    this.store = store;
    this.unique = options.unique || false;
  }

  getAll(query) {
    const request = new MockIDBRequest();

    setTimeout(() => {
      if (this.store._shouldFail) {
        request._fail(this.store._failError || new Error('Mock IndexedDB error'));
        return;
      }

      let results = Array.from(this.store.data.values());

      if (query instanceof MockIDBKeyRange) {
        results = results.filter(item => item[this.keyPath] === query.value);
      }

      request._succeed(results);
    }, 0);

    return request;
  }

  openCursor(range) {
    const request = new MockIDBRequest();

    setTimeout(() => {
      if (this.store._shouldFail) {
        request._fail(this.store._failError || new Error('Mock IndexedDB error'));
        return;
      }

      let data = Array.from(this.store.data.values());

      if (range instanceof MockIDBKeyRange) {
        data = data.filter(item => item[this.keyPath] === range.value);
      }

      if (data.length === 0) {
        request._succeed(null);
      } else {
        const cursor = new MockIDBCursor(data);
        cursor.delete = () => {
          const itemToDelete = data[cursor.index];
          if (itemToDelete) {
            this.store.data.delete(itemToDelete[this.store.keyPath]);
          }
          return new MockIDBRequest();
        };
        cursor.continue = () => {
          cursor.index++;
          if (cursor.index < data.length) {
            cursor.value = data[cursor.index];
            cursor.key = data[cursor.index]?.id;
            request._succeed(cursor);
          } else {
            request._succeed(null);
          }
        };
        request._succeed(cursor);
      }
    }, 0);

    return request;
  }
}

/**
 * Mock IDBKeyRange implementation
 */
class MockIDBKeyRange {
  constructor(value, indexKeyPath = null) {
    this.value = value;
    this.indexKeyPath = indexKeyPath;
  }

  static only(value) {
    return new MockIDBKeyRange(value);
  }

  static bound(lower, upper, lowerOpen = false, upperOpen = false) {
    return new MockIDBKeyRange({ lower, upper, lowerOpen, upperOpen });
  }
}

/**
 * Mock IDBTransaction implementation
 */
class MockIDBTransaction {
  constructor(db, storeNames, mode = 'readonly') {
    this.db = db;
    this.storeNames = Array.isArray(storeNames) ? storeNames : [storeNames];
    this.mode = mode;
    this.onerror = null;
    this.oncomplete = null;
  }

  objectStore(name) {
    if (!this.storeNames.includes(name)) {
      throw new Error(`Store "${name}" not part of transaction`);
    }
    return this.db._stores.get(name);
  }
}

/**
 * Mock IDBDatabase implementation
 */
class MockIDBDatabase {
  constructor(name, version = 1) {
    this.name = name;
    this.version = version;
    this._stores = new Map();
    this.objectStoreNames = {
      contains: (name) => this._stores.has(name),
      length: 0
    };
  }

  createObjectStore(name, options = {}) {
    const store = new MockIDBObjectStore(
      name,
      options.keyPath || 'id',
      options.autoIncrement || false
    );
    this._stores.set(name, store);
    this.objectStoreNames.length++;
    return store;
  }

  transaction(storeNames, mode = 'readonly') {
    return new MockIDBTransaction(this, storeNames, mode);
  }

  close() {
    // Mock close
  }
}

/**
 * Mock IndexedDB factory
 */
class MockIndexedDB {
  constructor() {
    this._databases = new Map();
    this._shouldFailOpen = false;
    this._openError = null;
  }

  open(name, version = 1) {
    const request = new MockIDBRequest();

    setTimeout(() => {
      if (this._shouldFailOpen) {
        request._fail(this._openError || new Error('Failed to open database'));
        return;
      }

      let db = this._databases.get(name);
      const needsUpgrade = !db || db.version < version;

      if (!db) {
        db = new MockIDBDatabase(name, version);
        this._databases.set(name, db);
      }

      if (needsUpgrade && request.onupgradeneeded) {
        db.version = version;
        request.onupgradeneeded({ target: { result: db }, oldVersion: 0, newVersion: version });
      }

      request._succeed(db);
    }, 0);

    return request;
  }

  deleteDatabase(name) {
    const request = new MockIDBRequest();

    setTimeout(() => {
      this._databases.delete(name);
      request._succeed(undefined);
    }, 0);

    return request;
  }
}

// ==================== Global Setup ====================

// Store original values
const originalIndexedDB = global.indexedDB;
const originalIDBKeyRange = global.IDBKeyRange;
const originalNavigatorOnline = Object.getOwnPropertyDescriptor(navigator, 'onLine');

// Setup mocks before tests
let mockIndexedDB;

beforeEach(() => {
  // Reset the mock IndexedDB
  mockIndexedDB = new MockIndexedDB();
  global.indexedDB = mockIndexedDB;
  global.IDBKeyRange = MockIDBKeyRange;

  // Mock navigator.onLine
  Object.defineProperty(navigator, 'onLine', {
    value: true,
    writable: true,
    configurable: true
  });

  // Mock window event listeners
  const listeners = {};
  jest.spyOn(window, 'addEventListener').mockImplementation((event, handler) => {
    if (!listeners[event]) listeners[event] = [];
    listeners[event].push(handler);
  });
  jest.spyOn(window, 'removeEventListener').mockImplementation((event, handler) => {
    if (listeners[event]) {
      listeners[event] = listeners[event].filter(h => h !== handler);
    }
  });
  jest.spyOn(window, 'dispatchEvent').mockImplementation((event) => {
    const handlers = listeners[event.type] || [];
    handlers.forEach(handler => handler(event));
    return true;
  });

  // Store listeners for triggering in tests
  global._testListeners = listeners;

  // Mock fetch
  global.fetch = jest.fn();

  // Reset console mocks
  jest.spyOn(console, 'log').mockImplementation(() => {});
  jest.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  jest.clearAllMocks();
  jest.resetModules();
});

afterAll(() => {
  // Restore originals
  global.indexedDB = originalIndexedDB;
  global.IDBKeyRange = originalIDBKeyRange;
  if (originalNavigatorOnline) {
    Object.defineProperty(navigator, 'onLine', originalNavigatorOnline);
  }
});

// ==================== Tests ====================

describe('OfflineStorage Module', () => {
  let OfflineStorage;

  beforeEach(async () => {
    // Dynamic import to get fresh instance
    jest.resetModules();
    const module = await import('../../static/js/modules/offline-storage.js');
    OfflineStorage = module.OfflineStorage;
  });

  // ==================== Test 1: Initialization ====================

  describe('Initialization', () => {
    test('should initialize IndexedDB database successfully', async () => {
      const storage = new OfflineStorage();

      const db = await storage.init();

      expect(db).toBeDefined();
      expect(db.name).toBe('YuKyuOfflineDB');
      expect(storage.db).toBe(db);
    });

    test('should create all required object stores on first init', async () => {
      const storage = new OfflineStorage();

      await storage.init();

      const expectedStores = ['employees', 'genzai', 'ukeoi', 'staff', 'leaveRequests', 'usageDetails', 'pendingSync', 'metadata'];

      expectedStores.forEach(storeName => {
        expect(storage.db.objectStoreNames.contains(storeName)).toBe(true);
      });
    });

    test('should reuse existing database connection on subsequent inits', async () => {
      const storage = new OfflineStorage();

      const db1 = await storage.init();
      const db2 = await storage.init();

      expect(db1).toBe(db2);
    });

    test('should handle IndexedDB open error gracefully', async () => {
      mockIndexedDB._shouldFailOpen = true;
      mockIndexedDB._openError = new Error('Database open failed');

      const storage = new OfflineStorage();

      await expect(storage.init()).rejects.toThrow('Database open failed');
    });
  });

  // ==================== Test 2: Save Data Offline ====================

  describe('Save Data Offline', () => {
    test('should save employees to IndexedDB', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      const employees = [
        { id: 'EMP001_2025', employeeNum: 'EMP001', name: 'Test Employee 1', year: 2025, balance: 10 },
        { id: 'EMP002_2025', employeeNum: 'EMP002', name: 'Test Employee 2', year: 2025, balance: 15 }
      ];

      await storage.saveEmployees(employees, 2025);

      const savedEmployees = await storage.getEmployees(2025);
      expect(savedEmployees).toHaveLength(2);
      expect(savedEmployees[0].name).toBe('Test Employee 1');
    });

    test('should clear old data before saving new employees for same year', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      const oldEmployees = [
        { id: 'OLD001_2025', employeeNum: 'OLD001', name: 'Old Employee', year: 2025, balance: 5 }
      ];

      const newEmployees = [
        { id: 'NEW001_2025', employeeNum: 'NEW001', name: 'New Employee', year: 2025, balance: 20 }
      ];

      await storage.saveEmployees(oldEmployees, 2025);
      await storage.saveEmployees(newEmployees, 2025);

      const savedEmployees = await storage.getEmployees(2025);
      expect(savedEmployees).toHaveLength(1);
      expect(savedEmployees[0].name).toBe('New Employee');
    });

    test('should save registry data (genzai, ukeoi, staff)', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      const genzaiRecords = [
        { id: 'G001', employee_num: 'G001', name: 'Genzai Worker', status: 'active' }
      ];

      await storage.saveRegistry('genzai', genzaiRecords);

      const saved = await storage.getRegistry('genzai');
      expect(saved).toHaveLength(1);
      expect(saved[0].name).toBe('Genzai Worker');
    });

    test('should reject invalid registry types', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      await expect(storage.saveRegistry('invalid', [])).rejects.toThrow('Invalid registry type');
    });

    test('should save leave requests', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      const requests = [
        { id: 'LR001', employee_num: 'EMP001', status: 'PENDING', days_requested: 2 }
      ];

      await storage.saveLeaveRequests(requests);

      const saved = await storage.getLeaveRequests();
      expect(saved).toHaveLength(1);
      expect(saved[0].status).toBe('PENDING');
    });
  });

  // ==================== Test 3: Retrieve Data Offline ====================

  describe('Retrieve Data Offline', () => {
    test('should retrieve employees filtered by year', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      const emp2024 = [{ id: 'E001_2024', employeeNum: 'E001', name: 'Employee 2024', year: 2024 }];
      const emp2025 = [{ id: 'E001_2025', employeeNum: 'E001', name: 'Employee 2025', year: 2025 }];

      await storage.saveEmployees(emp2024, 2024);
      await storage.saveEmployees(emp2025, 2025);

      const result2025 = await storage.getEmployees(2025);
      expect(result2025).toHaveLength(1);
      expect(result2025[0].year).toBe(2025);
    });

    test('should retrieve all employees when no year filter', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      await storage.saveEmployees(
        [{ id: 'E001_2025', employeeNum: 'E001', year: 2025 }],
        2025
      );

      const allEmployees = await storage.getEmployees();
      expect(allEmployees.length).toBeGreaterThanOrEqual(1);
    });

    test('should retrieve leave requests filtered by status', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      const requests = [
        { id: 'LR001', status: 'PENDING' },
        { id: 'LR002', status: 'APPROVED' },
        { id: 'LR003', status: 'PENDING' }
      ];

      await storage.saveLeaveRequests(requests);

      const pending = await storage.getLeaveRequests('PENDING');
      expect(pending).toHaveLength(2);
      expect(pending.every(r => r.status === 'PENDING')).toBe(true);
    });

    test('should retrieve usage details by employee number', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      const details = [
        { id: 'UD001', employee_num: 'EMP001', use_date: '2025-01-15' },
        { id: 'UD002', employee_num: 'EMP001', use_date: '2025-01-16' },
        { id: 'UD003', employee_num: 'EMP002', use_date: '2025-01-15' }
      ];

      await storage.saveUsageDetails(details);

      const emp001Details = await storage.getUsageDetails('EMP001');
      expect(emp001Details).toHaveLength(2);
    });

    test('should return empty array when no data exists', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      const employees = await storage.getEmployees(2030);
      expect(employees).toEqual([]);
    });
  });

  // ==================== Test 4: Sync When Connection Restored ====================

  describe('Sync When Connection Restored', () => {
    test('should add pending leave request when offline', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      const requestData = {
        employee_num: 'EMP001',
        start_date: '2025-02-10',
        end_date: '2025-02-12',
        days_requested: 3
      };

      const pendingId = await storage.addPendingLeaveRequest(requestData);

      expect(pendingId).toBeDefined();

      const pending = await storage.getPendingSync();
      expect(pending).toHaveLength(1);
      expect(pending[0].type).toBe('leaveRequest');
      expect(pending[0].action).toBe('create');
    });

    test('should sync pending items when back online', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      // Add pending request
      await storage.addPendingLeaveRequest({ employee_num: 'EMP001', days_requested: 1 });

      // Mock successful API response
      global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ success: true }) });

      const result = await storage.syncPending();

      expect(result.success).toBe(1);
      expect(result.failed).toBe(0);
      expect(global.fetch).toHaveBeenCalledWith('/api/leave-requests', expect.any(Object));
    });

    test('should not sync when offline', async () => {
      const storage = new OfflineStorage();
      storage._isOnline = false;
      await storage.init();

      await storage.addPendingLeaveRequest({ employee_num: 'EMP001' });

      const result = await storage.syncPending();

      expect(result.success).toBe(0);
      expect(result.failed).toBe(0);
      expect(global.fetch).not.toHaveBeenCalled();
    });

    test('should handle sync failure for individual items', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      await storage.addPendingLeaveRequest({ employee_num: 'EMP001' });
      await storage.addPendingLeaveRequest({ employee_num: 'EMP002' });

      // First succeeds, second fails
      global.fetch
        .mockResolvedValueOnce({ ok: true })
        .mockResolvedValueOnce({ ok: false, status: 400 });

      const result = await storage.syncPending();

      expect(result.success).toBe(1);
      expect(result.failed).toBe(1);
    });

    test('should dispatch sync complete event', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      await storage.addPendingLeaveRequest({ employee_num: 'EMP001' });

      global.fetch.mockResolvedValueOnce({ ok: true });

      await storage.syncPending();

      expect(window.dispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'yukyu-sync-complete'
        })
      );
    });

    test('should remove synced items from pending queue', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      await storage.addPendingLeaveRequest({ employee_num: 'EMP001' });

      global.fetch.mockResolvedValueOnce({ ok: true });

      await storage.syncPending();

      const remainingPending = await storage.getPendingSync();
      expect(remainingPending).toHaveLength(0);
    });
  });

  // ==================== Test 5: IndexedDB Error Handling ====================

  describe('IndexedDB Error Handling', () => {
    test('should handle store operation errors', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      // Make the store fail
      const employeesStore = storage.db._stores.get('employees');
      employeesStore._shouldFail = true;
      employeesStore._failError = new Error('Store operation failed');

      await expect(storage.getEmployees(2025)).rejects.toThrow('Store operation failed');
    });

    test('should handle transaction errors gracefully', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      const metadataStore = storage.db._stores.get('metadata');
      metadataStore._shouldFail = true;
      metadataStore._failError = new Error('Transaction failed');

      await expect(storage.getMetadata('testKey')).rejects.toThrow('Transaction failed');
    });

    test('should handle network errors during sync', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      await storage.addPendingLeaveRequest({ employee_num: 'EMP001' });

      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await storage.syncPending();

      expect(result.failed).toBe(1);
      expect(result.success).toBe(0);
    });

    test('should log errors to console', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      await storage.addPendingLeaveRequest({ employee_num: 'EMP001' });

      global.fetch.mockRejectedValueOnce(new Error('Test error'));

      await storage.syncPending();

      expect(console.error).toHaveBeenCalled();
    });
  });

  // ==================== Test 6: Storage Stats and Metadata ====================

  describe('Storage Statistics and Metadata', () => {
    test('should set and get metadata', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      await storage.setMetadata('testKey', 'testValue');

      const value = await storage.getMetadata('testKey');
      expect(value).toBe('testValue');
    });

    test('should return null for non-existent metadata', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      const value = await storage.getMetadata('nonExistentKey');
      expect(value).toBeNull();
    });

    test('should track last sync timestamp', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      const before = Date.now();

      await storage.saveEmployees([{ id: 'E001_2025', year: 2025 }], 2025);

      const lastSync = await storage.getLastSync();
      expect(lastSync).toBeInstanceOf(Date);
      expect(lastSync.getTime()).toBeGreaterThanOrEqual(before);
    });

    test('should get storage statistics', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      await storage.saveEmployees([{ id: 'E001_2025', year: 2025 }], 2025);
      await storage.saveLeaveRequests([{ id: 'LR001', status: 'PENDING' }]);

      const stats = await storage.getStats();

      expect(stats).toHaveProperty('lastSync');
      expect(stats).toHaveProperty('isOnline');
      expect(stats).toHaveProperty('stores');
      expect(stats.stores.employees).toBe(1);
      expect(stats.stores.leaveRequests).toBe(1);
    });

    test('should get pending sync count', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      await storage.addPendingLeaveRequest({ employee_num: 'EMP001' });
      await storage.addPendingLeaveRequest({ employee_num: 'EMP002' });

      const count = await storage.getPendingSyncCount();
      expect(count).toBe(2);
    });
  });

  // ==================== Test 7: Data Staleness Check ====================

  describe('Data Staleness', () => {
    test('should detect stale data when no sync has occurred', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      const isStale = await storage.isDataStale(30);
      expect(isStale).toBe(true);
    });

    test('should detect fresh data within threshold', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      await storage.setMetadata('lastSync', Date.now());

      const isStale = await storage.isDataStale(30);
      expect(isStale).toBe(false);
    });

    test('should detect stale data beyond threshold', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      // Set last sync to 1 hour ago
      const oneHourAgo = Date.now() - (60 * 60 * 1000);
      await storage.setMetadata('lastSync', oneHourAgo);

      const isStale = await storage.isDataStale(30);
      expect(isStale).toBe(true);
    });

    test('should use default threshold of 30 minutes', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      // Set last sync to 20 minutes ago
      const twentyMinutesAgo = Date.now() - (20 * 60 * 1000);
      await storage.setMetadata('lastSync', twentyMinutesAgo);

      const isStale = await storage.isDataStale();
      expect(isStale).toBe(false);
    });
  });

  // ==================== Test 8: Clear All Data ====================

  describe('Clear All Data', () => {
    test('should clear all offline data', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      // Add data to multiple stores
      await storage.saveEmployees([{ id: 'E001_2025', year: 2025 }], 2025);
      await storage.saveLeaveRequests([{ id: 'LR001', status: 'PENDING' }]);
      await storage.setMetadata('testKey', 'testValue');

      await storage.clearAll();

      const employees = await storage.getEmployees(2025);
      const requests = await storage.getLeaveRequests();
      const metadata = await storage.getMetadata('testKey');

      expect(employees).toHaveLength(0);
      expect(requests).toHaveLength(0);
      expect(metadata).toBeNull();
    });

    test('should complete clear operation without error', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      // Add some data first
      await storage.saveEmployees([{ id: 'E001_2025', year: 2025 }], 2025);

      // Clear should not throw
      await expect(storage.clearAll()).resolves.not.toThrow();

      // Verify data was cleared
      const employees = await storage.getEmployees(2025);
      expect(employees).toHaveLength(0);
    });
  });

  // ==================== Test 9: Online/Offline Status ====================

  describe('Online/Offline Status', () => {
    test('should correctly report online status', async () => {
      const storage = new OfflineStorage();

      expect(storage.isOnline()).toBe(true);
    });

    test('should update status on offline event', async () => {
      const storage = new OfflineStorage();

      // Simulate going offline
      storage._isOnline = false;

      expect(storage.isOnline()).toBe(false);
    });

    test('should setup network listeners on construction', async () => {
      const storage = new OfflineStorage();

      expect(window.addEventListener).toHaveBeenCalledWith('online', expect.any(Function));
      expect(window.addEventListener).toHaveBeenCalledWith('offline', expect.any(Function));
    });
  });

  // ==================== Test 10: Remove Pending Item ====================

  describe('Remove Pending Item', () => {
    test('should remove specific pending item by ID', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      const id1 = await storage.addPendingLeaveRequest({ employee_num: 'EMP001' });
      const id2 = await storage.addPendingLeaveRequest({ employee_num: 'EMP002' });

      await storage.removePendingItem(id1);

      const pending = await storage.getPendingSync();
      expect(pending).toHaveLength(1);
      expect(pending[0].data.employee_num).toBe('EMP002');
    });

    test('should complete removal without error', async () => {
      const storage = new OfflineStorage();
      await storage.init();

      const id = await storage.addPendingLeaveRequest({ employee_num: 'EMP001' });

      // Removal should not throw
      await expect(storage.removePendingItem(id)).resolves.not.toThrow();

      // Verify item was removed
      const pending = await storage.getPendingSync();
      expect(pending).toHaveLength(0);
    });
  });
});

describe('NetworkStatusManager', () => {
  let NetworkStatusManager;

  beforeEach(async () => {
    // Setup minimal DOM
    document.body.innerHTML = '';
    document.head.innerHTML = '';

    jest.resetModules();
    const module = await import('../../static/js/modules/offline-storage.js');
    NetworkStatusManager = module.NetworkStatusManager;
  });

  test('should create network status indicator', () => {
    const manager = new NetworkStatusManager();

    const indicator = document.getElementById('network-status-indicator');
    expect(indicator).toBeTruthy();
  });

  test('should create toast element', () => {
    const manager = new NetworkStatusManager();

    const toast = document.getElementById('network-toast');
    expect(toast).toBeTruthy();
  });

  test('should not create duplicate indicators', () => {
    new NetworkStatusManager();
    new NetworkStatusManager();

    const indicators = document.querySelectorAll('#network-status-indicator');
    expect(indicators.length).toBe(1);
  });

  test('should add styles to document head', () => {
    new NetworkStatusManager();

    const style = document.querySelector('style');
    expect(style).toBeTruthy();
    expect(style.textContent).toContain('network-status-indicator');
  });
});
