#!/usr/bin/env bash

root_path=$(pwd)
config_path=${1:-/etc/adpeeper/adpeeper.env}
source_path=${2:-$root_path/deploy/config/defaults.env}
ADP_SECRET_KEY=$(echo $RANDOM | sha256sum | head -c 64; echo;)

rm -fr venv
python3 -m venv venv
source venv/bin/activate

pip install -e .

sudo rm -fr "$config_path"
sudo mkdir -p "$(dirname "$config_path")"
sudo cp "$source_path" "$config_path"

export ADP_ENV_FILE=$config_path
export ADP_SECRET_KEY

ADP_SALT=$(adp gen_salt -r)

{
  echo ""
  echo "ADP_SALT=$ADP_SALT"
  echo "ADP_SECRET_KEY=$ADP_SECRET_KEY"
} | sudo tee -a "$ADP_ENV_FILE"
