# Database Migration Guide

Migrate from SQLite to PostgreSQL (Neon) on your server.

## 🚀 Quick Start

1. **Setup environment variables:**
   ```bash
   # Add to your .env file
   POSTGRES_URL=postgresql://username:password@ep-hostname.region.neon.tech/database
   ```

2. **Run migration:**
   ```bash
   chmod +x server_migrate.sh
   ./server_migrate.sh full
   ```

## 📋 Available Commands

### `server_migrate.sh` (Main Script)
```bash
./server_migrate.sh test      # Test PostgreSQL connection
./server_migrate.sh init      # Initialize database tables
./server_migrate.sh migrate   # Migrate data from SQLite
./server_migrate.sh full      # Full migration (default)
./server_migrate.sh info      # Show database statistics
```

### Individual Python Scripts
```bash
# Initialize PostgreSQL tables
python3 init_postgres.py

# Test connection only
python3 init_postgres.py --test-only

# Get database info
python3 init_postgres.py --info-only

# Migrate from custom SQLite file
python3 migrate_db.py --sqlite /path/to/database.db
```

## 📊 What Gets Migrated

The migration script handles these tables:

- **📋 Tasks** - Video processing tasks with clips, transcripts
- **🚀 Upscale Tasks** - Video upscaling tasks 
- **🎥 Downloaded Videos** - Registry of downloaded videos
- **🎬 Clips** - Generated clips with titles and descriptions (NEW)
- **🧩 Clip Fragments** - Individual transcript segments (NEW)

## 🔄 Migration Process

1. **Backup** - Creates automatic backup of SQLite database
2. **Initialize** - Creates PostgreSQL tables (including new clip tables)
3. **Migrate** - Transfers data with duplicate detection
4. **Verify** - Shows before/after statistics

## ⚠️ Important Notes

### Before Migration
- ✅ Set `POSTGRES_URL` in `.env` file
- ✅ Test connection with `./server_migrate.sh test`
- ✅ Backup your SQLite database manually (optional)
- ✅ Stop your application temporarily

### During Migration
- 🔒 Migration creates automatic backup of SQLite
- 🔍 Duplicate detection prevents data conflicts
- 📊 Progress is shown for each table
- ❌ Failed records are logged but don't stop migration

### After Migration
- 🔄 Restart your application
- 📊 Check `./server_migrate.sh info` for statistics
- 🗑️ Remove old SQLite file when confirmed working
- 📈 Monitor application logs

## 🛠️ Troubleshooting

### Connection Issues
```bash
# Test connection
./server_migrate.sh test

# Check environment variables
./check_env.sh
```

### Missing Dependencies
```bash
# Install required packages
pip install psycopg2-binary sqlalchemy sqlmodel
```

### Permission Errors
```bash
# Make scripts executable
chmod +x server_migrate.sh load_env.sh check_env.sh
```

### Migration Conflicts
```bash
# Show current database state
./server_migrate.sh info

# Manual migration with custom SQLite file
python3 migrate_db.py --sqlite /path/to/old/database.db
```

## 📝 Example Usage

### Full Migration (Recommended)
```bash
# Load environment
source load_env.sh

# Run full migration
./server_migrate.sh full
```

### Step-by-Step Migration
```bash
# 1. Test connection
./server_migrate.sh test

# 2. Initialize tables
./server_migrate.sh init  

# 3. Migrate data
./server_migrate.sh migrate

# 4. Check results
./server_migrate.sh info
```

### Check Status
```bash
# Environment variables
./check_env.sh

# Database statistics
./server_migrate.sh info

# Connection test
python3 init_postgres.py --test-only
```

## 🔒 Security Notes

- 🔐 Never commit database URLs to version control
- 🔑 Use environment variables for sensitive data
- 🛡️ Ensure PostgreSQL credentials are secure
- 📁 SQLite backups contain all data - protect them

## 📚 Files Created

- `migrate_db.py` - Main migration script
- `init_postgres.py` - Database initialization 
- `server_migrate.sh` - User-friendly wrapper script
- `DATABASE_MIGRATION.md` - This documentation

## 🎯 Next Steps After Migration

1. **Update Application** - Ensure `POSTGRES_URL` is set
2. **Test Features** - Verify all functionality works
3. **Monitor Performance** - Watch for any issues
4. **Clean Up** - Remove old SQLite files when confirmed
5. **Backup Strategy** - Set up PostgreSQL backups

## 🆘 Support

If you encounter issues:

1. Check the error messages carefully
2. Verify `POSTGRES_URL` format is correct
3. Test connection independently
4. Check PostgreSQL server status
5. Review application logs