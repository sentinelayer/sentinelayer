#!/bin/bash
# Database backup script

BACKUP_DIR="/backups/sentinelayer"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="sentinelayer"
DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5432"

mkdir -p $BACKUP_DIR

echo "🔹 Creating backup of $DB_NAME..."
PGPASSWORD="postgres" pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -Fc $DB_NAME > $BACKUP_DIR/${DB_NAME}_${DATE}.dump

if [ $? -eq 0 ]; then
    echo "✅ Backup successful: ${DB_NAME}_${DATE}.dump"
    
    # Keep only last 7 days
    find $BACKUP_DIR -name "*.dump" -mtime +7 -delete
else
    echo "❌ Backup failed!"
    exit 1
fi
