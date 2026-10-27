// IndexedDB storage. Everything (ROMs, saves, the Bank) stays in this browser.
const DB_NAME = 'gen3-unified';
const STORES = ['roms', 'saves', 'bank', 'meta', 'backups'];

let dbPromise;
function open() {
  dbPromise ??= new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      for (const s of STORES) if (!req.result.objectStoreNames.contains(s)) {
        req.result.createObjectStore(s, s === 'bank' || s === 'backups' ? { keyPath: 'id', autoIncrement: true } : undefined);
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  return dbPromise;
}

async function run(store, mode, fn) {
  const db = await open();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store, mode);
    const result = fn(tx.objectStore(store));
    tx.oncomplete = () => resolve(result instanceof IDBRequest ? result.result : result);
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error);
  });
}

export const get = (store, key) => run(store, 'readonly', s => s.get(key));
export const put = (store, value, key) => run(store, 'readwrite', s => s.put(value, key));
export const del = (store, key) => run(store, 'readwrite', s => s.delete(key));
export const all = (store) => run(store, 'readonly', s => s.getAll());
export const keys = (store) => run(store, 'readonly', s => s.getAllKeys());

// Applies several writes atomically across stores.
export async function transaction(storeNames, fn) {
  const db = await open();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeNames, 'readwrite');
    const stores = Object.fromEntries(storeNames.map(n => [n, tx.objectStore(n)]));
    fn(stores);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error ?? new Error('Transaction aborted'));
  });
}
