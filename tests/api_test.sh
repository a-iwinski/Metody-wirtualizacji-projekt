#!/usr/bin/env bash
# AI: skrypt przygotowany z pomocą Claude (Anthropic) – test API backendu (pokaz KM2)
# Użycie: ./tests/api_test.sh [adres]   (domyślnie http://localhost:8000)
API=${1:-http://localhost:8000}
PASS=0; FAIL=0

check() {  # check "opis" oczekiwany_kod metoda ścieżka [body]
  local desc=$1 expected=$2 method=$3 path=$4 body=$5
  local code
  if [ -n "$body" ]; then
    code=$(curl -s -o /tmp/api_body -w '%{http_code}' -X "$method" "$API$path" -H 'Content-Type: application/json' -d "$body")
  else
    code=$(curl -s -o /tmp/api_body -w '%{http_code}' -X "$method" "$API$path")
  fi
  if [ "$code" = "$expected" ]; then echo "OK    $code  $method $path  – $desc"; PASS=$((PASS+1))
  else echo "FAIL  $code (oczekiwano $expected)  $method $path  – $desc"; cat /tmp/api_body; echo; FAIL=$((FAIL+1)); fi
}

SN="TEST-$RANDOM$RANDOM"
NEW='{"name":"Lenovo ThinkPad T14","serial_number":"'$SN'","category_id":1,"location_id":2,"status":"w_magazynie"}'

check "health"                         200 GET    /health
check "lista urządzeń"                 200 GET    /api/devices
check "pojedyncze urządzenie"          200 GET    /api/devices/1
check "nieistniejące urządzenie"       404 GET    /api/devices/99999
check "id nie jest liczbą"             400 GET    /api/devices/abc
check "dodanie urządzenia"             201 POST   /api/devices "$NEW"
ID=$(python3 -c 'import json;print(json.load(open("/tmp/api_body"))["id"])' 2>/dev/null)
check "duplikat nr seryjnego"          409 POST   /api/devices "$NEW"
check "brak wymaganych pól"            400 POST   /api/devices '{"name":"X"}'
check "pusta nazwa"                    400 POST   /api/devices '{"name":"","serial_number":"A1","category_id":1,"location_id":1}'
check "zły status"                     400 POST   /api/devices '{"name":"X","serial_number":"A2","category_id":1,"location_id":1,"status":"zgubiony"}'
check "nieistniejąca kategoria"        400 POST   /api/devices '{"name":"X","serial_number":"A3","category_id":999,"location_id":1}'
check "edycja urządzenia"              200 PUT    /api/devices/$ID '{"name":"Lenovo ThinkPad T14 Gen 5","serial_number":"'$SN'","category_id":1,"location_id":1,"status":"w_uzyciu"}'
check "edycja nieistniejącego"         404 PUT    /api/devices/99999 "$NEW"
check "usunięcie urządzenia"           204 DELETE /api/devices/$ID
check "ponowne usunięcie"              404 DELETE /api/devices/$ID

echo; echo "Wynik: $PASS OK, $FAIL FAIL"
[ "$FAIL" -eq 0 ]
