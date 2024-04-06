#!/usr/bin/env bash

echo
echo "#######################################################"
echo "# Shell Environment..."
echo "#######################################################"
env

############################
# Step 1: Setup virtualenv
############################
echo
echo "#######################################################"
echo "# Setup virtualenv..."
echo "#######################################################"
if [ -n "${WORKSPACE:+1}" ]; then
  PATH=$WORKSPACE/venv/bin:/usr/local/bin:$PATH
  if [ ! -d "venv" ]; then
    virtualenv venv
  fi
  . venv/bin/activate
fi

echo
echo "#######################################################"
echo "# Python Environment..."
echo "#######################################################"
python3 --version

echo
echo "#######################################################"
echo "# Upgrading pip"
echo "#######################################################"
pip install --upgrade pip

echo
echo "#######################################################"
echo "# Installing requirements from requirements.txt..."
echo "#######################################################"
pip install -r requirements.txt
pip install -r requirements-csts.txt

########################
# Step 2: Execute Test
########################
echo
echo "#######################################################"
echo "# Executing: $@"
echo "#######################################################"
exec python -u $@