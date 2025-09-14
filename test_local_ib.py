#!/usr/bin/env python3
"""
本地IBKR連接測試腳本
用於測試與IBKR Gateway的本地連接
"""

import socket
import sys

def test_port_connection(host, port):
    """測試端口連接"""
    print(f"🔍 測試連接 {host}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ 端口 {port} 可連接")
            return True
        else:
            print(f"❌ 端口 {port} 無法連接 (錯誤代碼: {result})")
            return False
    except Exception as e:
        print(f"❌ 連接測試失敗: {e}")
        return False

def main():
    print("🚀 IBKR Gateway 連接診斷工具")
    print("=" * 50)
    
    # 測試不同的主機地址
    hosts_to_test = [
        ("localhost", "本地主機"),
        ("127.0.0.1", "本地回環"),
        ("host.docker.internal", "Docker內部主機")
    ]
    
    port = 4002
    
    for host, description in hosts_to_test:
        print(f"\n📡 測試 {description} ({host}):")
        test_port_connection(host, port)
    
    print("\n" + "=" * 50)
    print("💡 如果所有測試都失敗，請檢查：")
    print("   1. IBKR Gateway是否正在運行")
    print("   2. 是否已登入實盤賬戶")
    print("   3. API設置是否正確")
    print("   4. 防火牆是否阻擋端口4002")

if __name__ == "__main__":
    main()
