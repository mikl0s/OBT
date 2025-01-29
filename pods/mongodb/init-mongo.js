db.createUser({
  user: 'obt_user',
  pwd: 'obt_password',  // Will be overridden by environment variable
  roles: [
    {
      role: 'readWrite',
      db: 'obt_db'
    }
  ]
});

db = db.getSiblingDB('obt_db');

// Create collections with indexes
db.createCollection('hardware_configs');
db.hardware_configs.createIndex({ "cpu.model": 1 });
db.hardware_configs.createIndex({ "gpu.model": 1 });
db.hardware_configs.createIndex({ "created_at": 1 });

db.createCollection('models');
db.models.createIndex({ "name": 1 });
db.models.createIndex({ "tags": 1 });

db.createCollection('test_sessions');
db.test_sessions.createIndex({ "hardware_config_id": 1 });
db.test_sessions.createIndex({ "start_time": 1 });
db.test_sessions.createIndex({ "status": 1 });
db.test_sessions.createIndex({ "tags": 1 });

db.createCollection('test_results');
db.test_results.createIndex({ "session_id": 1 });
db.test_results.createIndex({ "model_id": 1 });
db.test_results.createIndex({ "test_type": 1 });
db.test_results.createIndex({ "created_at": 1 });
