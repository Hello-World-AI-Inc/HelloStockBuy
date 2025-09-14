#!/usr/bin/env python3
"""
IBKR連接測試腳本
用於測試與IBKR Gateway的連接
"""

import os
import sys
from ib_insync import *

def test_ibkr_connection():
    """測試IBKR連接"""
    print("🔍 測試IBKR Gateway連接...")
    
    # 從環境變量獲取配置
    host = os.getenv('IBKR_HOST', 'host.docker.internal')
    port = int(os.getenv('IBKR_PORT', '4002'))
    client_id = int(os.getenv('IBKR_CLIENT_ID', '12345'))
    
    print(f"📡 連接參數:")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Client ID: {client_id}")
    
    try:
        # 創建IB連接
        ib = IB()
        
        print(f"\n🔄 嘗試連接到 {host}:{port}...")
        ib.connect(host, port, clientId=client_id, timeout=10)
        
        print("✅ 連接成功！")
        
        # 獲取賬戶信息
        print("\n📊 獲取賬戶信息...")
        accounts = ib.managedAccounts()
        print(f"   賬戶列表: {accounts}")
        
        if accounts:
            account = accounts[0]
            print(f"   使用賬戶: {account}")
            
            # 獲取賬戶摘要
            print("\n💰 獲取賬戶摘要...")
            summary = ib.accountSummary()
            for item in summary[:5]:  # 只顯示前5項
                print(f"   {item.tag}: {item.value}")
            
            # 獲取持倉
            print("\n📈 獲取持倉信息...")
            positions = ib.positions()
            print(f"   持倉數量: {len(positions)}")
            
            for pos in positions[:3]:  # 只顯示前3個持倉
                print(f"   {pos.contract.symbol}: {pos.position} 股")
        
        # 斷開連接
        ib.disconnect()
        print("\n✅ 測試完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 連接失敗: {e}")
        print("\n🔧 請檢查:")
        print("   1. IBKR Gateway是否正在運行")
        print("   2. API連接是否已啟用")
        print("   3. 端口4002是否開放")
        print("   4. 防火牆設置")
        return False

if __name__ == "__main__":
    success = test_ibkr_connection()
    sys.exit(0 if success else 1)
