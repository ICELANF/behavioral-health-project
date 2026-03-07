#!/bin/bash
COLLECTION="bhp_knowledge"
BACKUP_DIR="/data/qdrant_backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
RESP=$(curl -s -X POST "http://localhost:6333/collections/${COLLECTION}/snapshots")
SNAPSHOT_NAME=$(echo $RESP | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['name'])")
curl -s -o "${BACKUP_DIR}/${COLLECTION}_${DATE}.snapshot" \
  "http://localhost:6333/collections/${COLLECTION}/snapshots/${SNAPSHOT_NAME}"
ls -t ${BACKUP_DIR}/*.snapshot | tail -n +6 | xargs rm -f 2>/dev/null
echo "备份完成: ${BACKUP_DIR}/${COLLECTION}_${DATE}.snapshot"
