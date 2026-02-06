#!/usr/bin/env bash
# Smoke test: index reference PDFs, create project with questionnaire, generate answers, add doc, verify OUTDATED.
# Requires: backend running on localhost:8000
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
API="${API:-http://localhost:8000}"
DATA_DIR="${DATA_DIR:-$PROJECT_ROOT/data}"
echo "API=$API DATA_DIR=$DATA_DIR"

if [ ! -d "$DATA_DIR" ]; then
  echo "ERROR: DATA_DIR not found: $DATA_DIR"
  exit 1
fi

# 1) Index one reference PDF
echo "1. Indexing reference document..."
R1=$(curl -s -X POST "$API/api/documents/index-async" -F "file=@$DATA_DIR/20260110_MiniMax_Accountants_Report.pdf")
REQ_ID1=$(echo "$R1" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || true)
if [ -z "$REQ_ID1" ]; then echo "Failed to get request id. Response: $R1"; exit 1; fi
echo "   Request ID: $REQ_ID1"
for i in $(seq 1 60); do
  PAYLOAD=$(curl -s "$API/api/requests/$REQ_ID1")
  ST=$(echo "$PAYLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)
  ERR=$(echo "$PAYLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin).get('error_message','') or '')" 2>/dev/null || true)
  echo "   Status: $ST"
  [ "$ST" = "COMPLETED" ] && break
  if [ "$ST" = "FAILED" ]; then echo "Index request failed: $ERR"; exit 1; fi
  sleep 3
done
[ "$ST" != "COMPLETED" ] && echo "Index did not complete in time" && exit 1

# 2) Create project with questionnaire
echo "2. Creating project with questionnaire..."
R2=$(curl -s -X POST "$API/api/projects/create-async" -F "name=SmokeTest" -F "file=@$DATA_DIR/ILPA_Due_Diligence_Questionnaire_v1.2.pdf")
REQ_ID2=$(echo "$R2" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || true)
if [ -z "$REQ_ID2" ]; then echo "Failed to get request id. Response: $R2"; exit 1; fi
echo "   Request ID: $REQ_ID2"
for i in $(seq 1 60); do
  PAYLOAD=$(curl -s "$API/api/requests/$REQ_ID2")
  ST=$(echo "$PAYLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)
  PROJECT_ID=$(echo "$PAYLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin).get('entity_id',''))" 2>/dev/null || true)
  ERR=$(echo "$PAYLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin).get('error_message','') or '')" 2>/dev/null || true)
  echo "   Status: $ST"
  if [ "$ST" = "COMPLETED" ] && [ -n "$PROJECT_ID" ]; then break; fi
  if [ "$ST" = "FAILED" ]; then echo "Create project failed: $ERR"; exit 1; fi
  sleep 3
done
PROJECT_ID=$(curl -s "$API/api/requests/$REQ_ID2" | python3 -c "import sys,json; print(json.load(sys.stdin).get('entity_id','1'))" 2>/dev/null || true)
echo "   Project ID: $PROJECT_ID"

# 3) Generate all answers
echo "3. Generating all answers..."
R3=$(curl -s -X POST "$API/api/answers/generate-all-async?project_id=$PROJECT_ID")
REQ_ID3=$(echo "$R3" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || true)
for i in $(seq 1 40); do
  PAYLOAD=$(curl -s "$API/api/requests/$REQ_ID3")
  ST=$(echo "$PAYLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)
  ERR=$(echo "$PAYLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin).get('error_message','') or '')" 2>/dev/null || true)
  echo "   Status: $ST"
  [ "$ST" = "COMPLETED" ] && break
  if [ "$ST" = "FAILED" ]; then echo "Generate answers failed: $ERR"; exit 1; fi
  sleep 5
done
[ "$ST" != "COMPLETED" ] && echo "Generate answers did not complete (may be slow)" && exit 1

# 4) Project status after generate
STATUS=$(curl -s "$API/api/projects/$PROJECT_ID/status" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)
echo "   Project status after generate: $STATUS"

# 5) Index another document -> should mark ALL_DOCS projects as OUTDATED
echo "5. Indexing another document..."
R5=$(curl -s -X POST "$API/api/documents/index-async" -F "file=@$DATA_DIR/20260110_MiniMax_Audited_Consolidated_Financial_Statements.pdf")
REQ_ID5=$(echo "$R5" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || true)
for i in $(seq 1 60); do
  ST=$(curl -s "$API/api/requests/$REQ_ID5" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)
  [ "$ST" = "COMPLETED" ] && break
  [ "$ST" = "FAILED" ] && echo "Second index failed" && exit 1
  sleep 3
done

# 6) Verify project is OUTDATED
STATUS2=$(curl -s "$API/api/projects/$PROJECT_ID/status" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)
echo "   Project status after new doc: $STATUS2"
if [ "$STATUS2" = "OUTDATED" ]; then
  echo "PASS: Project transitioned to OUTDATED as expected."
else
  echo "FAIL: Expected OUTDATED, got $STATUS2"
  exit 1
fi
