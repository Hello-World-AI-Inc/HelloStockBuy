from ib_insync import IB
import os

# Get connection parameters from environment or use defaults
host = os.getenv('IBKR_HOST', 'ibkr-gateway')
port = int(os.getenv('IBKR_PORT', '4001'))
client_id = 123

ib = IB()

try:
    print(f"Connecting to IBKR Gateway at {host}:{port}...")
    ib.connect(host, port, clientId=client_id, timeout=20)
    if ib.isConnected():
        print("✅ Successfully connected to IBKR Gateway!")
    else:
        print("❌ Failed to connect to IBKR Gateway.")
finally:
    ib.disconnect()
    print("Disconnected.") 