-- 初始資料匯入腳本
-- 這個檔案會在資料庫 migration 完成後自動執行

-- 插入預設的目標股票代碼
INSERT INTO target_symbols (symbol, created_at) VALUES
('AAPL', NOW()),
('GOOGL', NOW()),
('MSFT', NOW()),
('TSLA', NOW()),
('AMZN', NOW()),
('NVDA', NOW()),
('META', NOW()),
('BRK.A', NOW()),
('UNH', NOW()),
('JNJ', NOW())
ON CONFLICT (symbol) DO NOTHING;

-- 插入預設的市場資料範例（可選）
-- INSERT INTO market_data (symbol, price, volume, high, low, open_price, timestamp) VALUES
-- ('AAPL', 150.00, 1000000, 152.00, 148.00, 149.00, NOW()),
-- ('GOOGL', 2800.00, 500000, 2820.00, 2780.00, 2790.00, NOW())
-- ON CONFLICT DO NOTHING;

-- 建立預設的測試使用者（密碼需要先 hash）
-- INSERT INTO users (username, email, hashed_password, created_at, is_active) VALUES
-- ('testuser', 'test@example.com', 'hashed_password_here', NOW(), true)
-- ON CONFLICT (username) DO NOTHING;

-- 顯示插入的資料
SELECT '已插入 ' || COUNT(*) || ' 個目標股票代碼' as result FROM target_symbols; 