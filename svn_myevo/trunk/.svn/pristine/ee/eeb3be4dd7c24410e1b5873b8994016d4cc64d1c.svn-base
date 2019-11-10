#/bin/bash
set -x

TOKEN=$1
FILE=$2

if [ "x$TOKEN" = "x" ] || [ "x$FILE" = "x" ] || [ ! -f $FILE ];
then
  echo "$0 token_id filename"
  exit 1
fi

curl -vX POST http://localhost:5202/chicken/api/order/create \
        -d @$FILE \
        --header "Content-Type: application/json" \
        --header "authorization: $TOKEN"




