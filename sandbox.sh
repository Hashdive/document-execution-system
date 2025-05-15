#!/bin/bash

SANDBOX_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/tools/sandbox"

if [ ! -d "$SANDBOX_DIR" ]; then
    echo "Sandbox directory not found at $SANDBOX_DIR"
    echo "Please clone the sandbox repository first:"
    echo "mkdir -p tools && cd tools && git clone https://github.com/algorand/sandbox.git"
    exit 1
fi

cd "$SANDBOX_DIR"

case "$1" in
    start)
        ./sandbox up dev
        ;;
    stop)
        ./sandbox down
        ;;
    status)
        ./sandbox status
        ;;
    accounts)
        ./sandbox goal account list
        ;;
    clean)
        ./sandbox clean
        ;;
    *)
        echo "Usage: $0 {start|stop|status|accounts|clean}"
        echo ""
        echo "start    - Start the Algorand Sandbox in development mode"
        echo "stop     - Stop the Algorand Sandbox"
        echo "status   - Check the status of Algorand Sandbox"
        echo "accounts - List the accounts available in the Sandbox"
        echo "clean    - Remove all Sandbox data and start fresh"
        exit 1
esac