#!/bin/bash

# Start Backend
cd Backend/ && python3 main.py &

cd .. &

# Start Frontend
cd Frontend/ && ng serve --open