#!/usr/bin/env python3
"""
IBKR連接詳細診斷腳本
"""

import os
import sys
from ib_insync import *

def diagnose_ibkr_connection():
    """詳細診斷IBKR連接"""
    print("🔍 IBKR連接詳細診斷")
    print("=" * 60)
    
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
        
        # 檢查連接狀態
        print(f"\n📊 連接狀態:")
        print(f"   連接狀態: {ib.isConnected()}")
        print(f"   客戶端ID: {ib.client.clientId}")
        
        # 獲取賬戶信息
        print(f"\n💰 獲取賬戶信息...")
        try:
            accounts = ib.managedAccounts()
            print(f"   賬戶列表: {accounts}")
            print(f"   賬戶數量: {len(accounts)}")
            
            if accounts:
                account = accounts[0]
                print(f"   使用賬戶: {account}")
                
                # 獲取賬戶摘要
                print(f"\n📈 獲取賬戶摘要...")
                try:
                    summary = ib.accountSummary()
                    print(f"   摘要項目數量: {len(summary)}")
                    for item in summary[:5]:  # 只顯示前5項
                        print(f"   {item.tag}: {item.value}")
                except Exception as e:
                    print(f"   ❌ 獲取摘要失敗: {e}")
                
                # 獲取持倉
                print(f"\n📊 獲取持倉信息...")
                try:
                    positions = ib.positions()
                    print(f"   持倉數量: {len(positions)}")
                    
                    for pos in positions[:3]:  # 只顯示前3個持倉
                        print(f"   {pos.contract.symbol}: {pos.position} 股")
                except Exception as e:
                    print(f"   ❌ 獲取持倉失敗: {e}")
            else:
                print("   ⚠️ 沒有找到賬戶")
                
        except Exception as e:
            print(f"   ❌ 獲取賬戶信息失敗: {e}")
        
        # 斷開連接
        ib.disconnect()
        print(f"\n✅ 診斷完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 連接失敗: {e}")
        print(f"\n🔧 請檢查:")
        print(f"   1. IBKR Gateway是否正在運行")
        print(f"   2. 是否已登入實盤賬戶")
        print(f"   3. API連接是否已啟用")
        print(f"   4. 端口{port}是否開放")
        print(f"   5. 防火牆設置")
        return False

if __name__ == "__main__":
    success = diagnose_ibkr_connection()
    sys.exit(0 if success else 1)
