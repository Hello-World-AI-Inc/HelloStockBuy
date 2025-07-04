<template>
  <div class="min-h-screen bg-gray-900 text-white">
    <!-- Header -->
    <header class="bg-gray-800 border-b border-gray-700 shadow-lg">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-4">
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span class="text-white font-bold text-sm">HS</span>
            </div>
            <h1 class="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              HelloStockBuy
            </h1>
          </div>
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-2">
              <div :class="connectionStatus ? 'bg-green-400 animate-pulse' : 'bg-red-400'" class="w-3 h-3 rounded-full"></div>
              <span class="text-sm text-gray-300">{{ connectionStatus ? 'Connected' : 'Disconnected' }}</span>
            </div>
            <!-- Data Source Selector -->
            <div class="flex items-center space-x-2 bg-gray-700 px-3 py-1 rounded-lg">
              <span class="text-xs text-gray-400">Data Source:</span>
              <select v-model="currentDataSource" @change="changeDataSource" class="bg-gray-700 text-white text-xs rounded px-2 py-1 focus:outline-none">
                <option value="yahoo">Yahoo</option>
                <option value="ibkr">IBKR</option>
              </select>
              <span class="text-xs text-gray-400 ml-2">Interval:</span>
              <select v-model="selectedInterval" @change="onIntervalChange" class="bg-gray-700 text-white text-xs rounded px-2 py-1 focus:outline-none w-20">
                <option v-for="interval in refreshIntervals" :key="interval" :value="interval">
                  {{ interval === 60 ? '1 min' : interval === 180 ? '3 mins' : interval === 300 ? '5 mins' : interval + 's' }}
                </option>
              </select>
            </div>
            <button @click="connectIBKR" class="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-2 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg">
              Connect IBKR
            </button>
          </div>
        </div>
      </div>
    </header>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Account Summary Section -->
      <div class="bg-gray-800 rounded-xl shadow-xl border border-gray-700 p-6 mb-8">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-xl font-semibold text-white flex items-center">
            <svg class="w-5 h-5 mr-2 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
            </svg>
            Account Summary
          </h2>
          <button @click="fetchAccountSummary" :disabled="isLoadingAccountSummary" class="bg-gradient-to-r from-yellow-600 to-orange-600 text-white px-4 py-2 rounded-lg hover:from-yellow-700 hover:to-orange-700 disabled:from-gray-600 disabled:to-gray-600 disabled:cursor-not-allowed transition-all duration-200 shadow-lg">
            {{ isLoadingAccountSummary ? 'Loading...' : 'Refresh' }}
          </button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-4">
          <div class="bg-gray-700 rounded-lg p-4 flex flex-col items-center">
            <div class="text-sm text-gray-400 mb-1">Net Liquidation Value</div>
            <div class="text-2xl font-bold text-green-300">${{ accountSummary.netLiquidationValue?.toLocaleString() ?? '--' }}</div>
          </div>
          <div class="bg-gray-700 rounded-lg p-4 flex flex-col items-center">
            <div class="text-sm text-gray-400 mb-1">Total Cash Value</div>
            <div class="text-2xl font-bold text-yellow-300">${{ accountSummary.totalCashValue?.toLocaleString() ?? '--' }}</div>
          </div>
          <div class="bg-gray-700 rounded-lg p-4 flex flex-col items-center">
            <div class="text-sm text-gray-400 mb-1">Available Funds</div>
            <div class="text-2xl font-bold text-blue-300">${{ accountSummary.availableFunds?.toLocaleString() ?? '--' }}</div>
          </div>
          <div class="bg-gray-700 rounded-lg p-4 flex flex-col items-center">
            <div class="text-sm text-gray-400 mb-1">Buying Power</div>
            <div class="text-2xl font-bold text-purple-300">${{ accountSummary.buyingPower?.toLocaleString() ?? '--' }}</div>
          </div>
        </div>
        
        <!-- Additional Account Metrics -->
        <div class="grid grid-cols-1 md:grid-cols-6 gap-4 mb-6">
          <div class="bg-gray-700 rounded-lg p-3 flex flex-col items-center">
            <div class="text-xs text-gray-400 mb-1">Account</div>
            <div class="text-sm font-semibold text-white">{{ accountSummary.account ?? '--' }}</div>
          </div>
          <div class="bg-gray-700 rounded-lg p-3 flex flex-col items-center">
            <div class="text-xs text-gray-400 mb-1">Gross Position Value</div>
            <div class="text-sm font-semibold text-cyan-300">${{ accountSummary.grossPositionValue?.toLocaleString() ?? '--' }}</div>
          </div>
          <div class="bg-gray-700 rounded-lg p-3 flex flex-col items-center">
            <div class="text-xs text-gray-400 mb-1">Realized P&L</div>
            <div class="text-sm font-semibold" :class="accountSummary.realizedPnl >= 0 ? 'text-green-400' : 'text-red-400'">${{ accountSummary.realizedPnl?.toLocaleString() ?? '--' }}</div>
          </div>
          <div class="bg-gray-700 rounded-lg p-3 flex flex-col items-center">
            <div class="text-xs text-gray-400 mb-1">Unrealized P&L</div>
            <div class="text-sm font-semibold" :class="accountSummary.unrealizedPnl >= 0 ? 'text-green-400' : 'text-red-400'">${{ accountSummary.unrealizedPnl?.toLocaleString() ?? '--' }}</div>
          </div>
          <div class="bg-gray-700 rounded-lg p-3 flex flex-col items-center">
            <div class="text-xs text-gray-400 mb-1">Excess Liquidity</div>
            <div class="text-sm font-semibold text-emerald-300">${{ accountSummary.excessLiquidity?.toLocaleString() ?? '--' }}</div>
          </div>
          <div class="bg-gray-700 rounded-lg p-3 flex flex-col items-center">
            <div class="text-xs text-gray-400 mb-1">Margin Req</div>
            <div class="text-sm font-semibold text-orange-300">${{ accountSummary.maintMarginReq?.toLocaleString() ?? '--' }}</div>
          </div>
        </div>
        <!-- Stock List -->
        <div v-if="portfolio.length > 0" class="mt-4">
          <h3 class="text-lg font-semibold text-white mb-2">Stocks on Hand</h3>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-700">
              <thead class="bg-gray-700">
                <tr>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Symbol</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Quantity</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Avg Price</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Current Price</th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">P&L</th>
                </tr>
              </thead>
              <tbody class="bg-gray-800 divide-y divide-gray-700">
                <tr v-for="position in portfolio" :key="position.symbol" class="hover:bg-gray-700 transition-colors duration-150">
                  <td class="px-4 py-2 whitespace-nowrap text-sm font-medium text-white">{{ position.symbol }}</td>
                  <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-300">{{ position.quantity }}</td>
                  <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-300">${{ position.avg_cost?.toFixed(2) }}</td>
                  <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-300">${{ position.current_price?.toFixed(2) ?? '--' }}</td>
                  <td class="px-4 py-2 whitespace-nowrap text-sm font-semibold" :class="getPnLColor(position)">{{ getPnL(position) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Market Data Section -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div class="lg:col-span-2">
          <div class="bg-gray-800 rounded-xl shadow-xl border border-gray-700 p-6">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-xl font-semibold text-white flex items-center">
                <svg class="w-5 h-5 mr-2 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
                Market Data
                <span class="ml-3 px-2 py-0.5 rounded bg-blue-700 text-xs font-semibold text-blue-100 uppercase tracking-wide">{{ currentDataSource.toUpperCase() }}</span>
              </h2>
            </div>
            <div class="flex space-x-4 mb-6">
              <input
                v-model="customSymbol"
                @keyup.enter="onCustomSymbolInput"
                placeholder="Enter symbol (e.g., AAPL)"
                class="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button @click="fetchMarketData" class="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg">
                Get Data
              </button>
            </div>
            
            <div v-if="marketData" class="bg-gray-700 rounded-xl p-6 border border-gray-600">
              <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div class="text-center">
                  <div class="text-sm text-gray-400 mb-1">Symbol</div>
                  <div class="text-lg font-bold text-white">{{ marketData.symbol }}</div>
                </div>
                <div class="text-center">
                  <div class="text-sm text-gray-400 mb-1">Price</div>
                  <div class="text-xl font-bold text-green-400 flex items-center justify-center">
                    ${{ marketData.price?.toFixed(2) }}
                  </div>
                  <div v-if="getPriceChange() !== null" :class="'mt-1 text-xs font-semibold ' + getPriceChangeColor()">
                    ({{ getPriceChangeString() }})
                  </div>
                </div>
                <div class="text-center">
                  <div class="text-sm text-gray-400 mb-1">Bid</div>
                  <div class="text-lg text-blue-400">${{ marketData.bid?.toFixed(2) }}</div>
                </div>
                <div class="text-center">
                  <div class="text-sm text-gray-400 mb-1">Ask</div>
                  <div class="text-lg text-purple-400">${{ marketData.ask?.toFixed(2) }}</div>
                </div>
                <div class="text-center">
                  <div class="text-sm text-gray-400 mb-1">High</div>
                  <div class="text-lg text-green-400">${{ marketData.high?.toFixed(2) }}</div>
                </div>
                <div class="text-center">
                  <div class="text-sm text-gray-400 mb-1">Low</div>
                  <div class="text-lg text-red-400">${{ marketData.low?.toFixed(2) }}</div>
                </div>
                <div class="text-center">
                  <div class="text-sm text-gray-400 mb-1">Volume</div>
                  <div class="text-lg text-white">{{ marketData.volume?.toLocaleString() }}</div>
                </div>
                <div class="text-center">
                  <div class="text-sm text-gray-400 mb-1">Time</div>
                  <div class="text-sm text-gray-300">{{ formatTime(marketData.timestamp) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Trading Panel -->
        <div class="bg-gray-800 rounded-xl shadow-xl border border-gray-700 p-6">
          <h2 class="text-xl font-semibold text-white mb-6 flex items-center">
            <svg class="w-5 h-5 mr-2 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
            </svg>
            Trading
          </h2>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">Symbol</label>
              <input 
                v-model="tradeSymbol" 
                placeholder="AAPL" 
                class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">Action</label>
              <select 
                v-model="tradeAction" 
                class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              >
                <option value="BUY" class="bg-gray-700">Buy</option>
                <option value="SELL" class="bg-gray-700">Sell</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-2">Quantity</label>
              <input 
                v-model.number="tradeQuantity" 
                type="number" 
                min="1"
                placeholder="100" 
                class="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
            <button 
              @click="placeOrder" 
              :disabled="!tradeSymbol || !tradeQuantity"
              class="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white py-3 rounded-lg hover:from-green-700 hover:to-emerald-700 disabled:from-gray-600 disabled:to-gray-600 disabled:cursor-not-allowed transition-all duration-200 shadow-lg font-semibold"
            >
              Place Order
            </button>
          </div>
        </div>
      </div>

      <!-- Portfolio Section -->
      <div class="bg-gray-800 rounded-xl shadow-xl border border-gray-700 p-6">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-xl font-semibold text-white flex items-center">
            <svg class="w-5 h-5 mr-2 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
            </svg>
            Portfolio
          </h2>
          <button @click="fetchPortfolio" class="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all duration-200 shadow-lg">
            Refresh
          </button>
        </div>
        
        <div v-if="portfolio.length > 0" class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-700">
            <thead class="bg-gray-700">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Symbol</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Quantity</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Avg Cost</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Market Value</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">P&L</th>
              </tr>
            </thead>
            <tbody class="bg-gray-800 divide-y divide-gray-700">
              <tr v-for="position in portfolio" :key="position.symbol" class="hover:bg-gray-700 transition-colors duration-150">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{{ position.symbol }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">{{ position.quantity }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">${{ position.avg_cost?.toFixed(2) }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">${{ position.market_value?.toFixed(2) }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold" :class="getPnLColor(position)">
                  {{ getPnL(position) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="text-center py-12 text-gray-400">
          <svg class="w-16 h-16 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
          </svg>
          <p class="text-lg">No positions in portfolio</p>
          <p class="text-sm text-gray-500 mt-2">Your account has ${{ accountSummary.totalCashValue?.toLocaleString() ?? '0' }} in cash available for trading</p>
          <p class="text-xs text-gray-600 mt-1">Use the trading panel to place your first order</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const config = useRuntimeConfig()
const apiBaseUrl = config.public.apiBaseUrl

// Reactive data
const connectionStatus = ref(false)
const searchSymbol = ref('')
const marketData = ref(null)
const portfolio = ref([])
const tradeSymbol = ref('')
const tradeAction = ref('BUY')
const tradeQuantity = ref(100)
const accountSummary = ref({ cash: null, portfolioValue: null })
const isLoadingAccountSummary = ref(false)
const currentDataSource = ref('yahoo')
const symbolList = ref(['AAPL', 'MSFT', 'TSLA', 'AMZN', 'GOOG'])
const selectedSymbol = ref('AAPL')
const customSymbol = ref('AAPL')
const refreshIntervals = [60, 180, 300]
const selectedInterval = ref(60)
let marketDataInterval = null

// Methods
const connectIBKR = async () => {
  try {
    const response = await $fetch(`${apiBaseUrl}/connect`)
    connectionStatus.value = true
    if (response.message === 'Connected to IBKR') {
      await fetchAccountSummary()
      await fetchPortfolio()
    }
  } catch (error) {
    console.error('Failed to connect to IBKR:', error)
    connectionStatus.value = false
  }
}

const fetchMarketData = async () => {
  const symbol = customSymbol.value.trim()
  if (!symbol) return
  try {
    marketData.value = await $fetch(`${apiBaseUrl}/market-data/${symbol}`)
  } catch (error) {
    console.error('Failed to fetch market data:', error)
  }
}

const fetchPortfolio = async () => {
  try {
    const response = await $fetch(`${apiBaseUrl}/account/positions`)
    portfolio.value = response.positions || []
  } catch (error) {
    console.error('Failed to fetch portfolio:', error)
    portfolio.value = []
  }
}

const placeOrder = async () => {
  if (!tradeSymbol.value || !tradeQuantity.value) return
  
  try {
    const response = await $fetch(`${apiBaseUrl}/order`, {
      method: 'POST',
      body: {
        symbol: tradeSymbol.value,
        action: tradeAction.value,
        quantity: tradeQuantity.value
      }
    })
    
    if (response.order_id) {
      alert(`Order placed successfully! Order ID: ${response.order_id}`)
      // Refresh portfolio after order
      await fetchPortfolio()
    }
  } catch (error) {
    console.error('Failed to place order:', error)
    alert('Failed to place order')
  }
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleTimeString()
}

const getPnL = (position) => {
  if (!position.avg_cost || !position.market_value || !position.quantity) return '$0.00'
  const pnl = (position.market_value - (position.avg_cost * position.quantity))
  return `$${pnl.toFixed(2)}`
}

const getPnLColor = (position) => {
  if (!position.avg_cost || !position.market_value || !position.quantity) return 'text-gray-400'
  const pnl = (position.market_value - (position.avg_cost * position.quantity))
  return pnl >= 0 ? 'text-green-400' : 'text-red-400'
}

const fetchAccountSummary = async () => {
  isLoadingAccountSummary.value = true
  try {
    const response = await $fetch(`${apiBaseUrl}/account/summary`)
    accountSummary.value = {
      netLiquidationValue: response.net_liquidation_value,
      totalCashValue: response.total_cash_value,
      availableFunds: response.available_funds,
      buyingPower: response.buying_power,
      grossPositionValue: response.gross_position_value,
      realizedPnl: response.realized_pnl,
      unrealizedPnl: response.unrealized_pnl,
      maintMarginReq: response.maint_margin_req,
      initMarginReq: response.init_margin_req,
      excessLiquidity: response.excess_liquidity,
      account: response.account
    }
  } catch (error) {
    console.error('Failed to fetch account summary:', error)
    accountSummary.value = {
      netLiquidationValue: null,
      totalCashValue: null,
      availableFunds: null,
      buyingPower: null,
      grossPositionValue: null,
      realizedPnl: null,
      unrealizedPnl: null,
      maintMarginReq: null,
      initMarginReq: null,
      excessLiquidity: null,
      account: null
    }
  } finally {
    isLoadingAccountSummary.value = false
  }
}

const fetchCurrentDataSource = async () => {
  try {
    const res = await $fetch(`${apiBaseUrl}/market-data-source`)
    currentDataSource.value = res.source
  } catch (e) {
    currentDataSource.value = 'yahoo'
  }
}

const changeDataSource = async () => {
  try {
    await $fetch(`${apiBaseUrl}/market-data-source`, {
      method: 'POST',
      body: { source: currentDataSource.value }
    })
    // Optionally refresh market data after switching
    if (selectedSymbol.value) {
      await fetchMarketData()
    }
  } catch (e) {
    alert('Failed to change data source')
  }
}

const startMarketDataInterval = () => {
  if (marketDataInterval) clearInterval(marketDataInterval)
  marketDataInterval = setInterval(fetchMarketData, selectedInterval.value * 1000)
}

const stopMarketDataInterval = () => {
  if (marketDataInterval) clearInterval(marketDataInterval)
  marketDataInterval = null
}

const onCustomSymbolInput = () => {
  fetchMarketData()
  startMarketDataInterval()
}

const onIntervalChange = () => {
  startMarketDataInterval()
}

onMounted(async () => {
  await fetchCurrentDataSource()
  await connectIBKR()
  await fetchAccountSummary()
  fetchMarketData()
  startMarketDataInterval()
})

onUnmounted(() => {
  stopMarketDataInterval()
})

const getPriceChange = () => {
  if (!marketData.value || marketData.value.price == null || marketData.value.open == null) return null
  const diff = marketData.value.price - marketData.value.open
  return diff
}

const getPriceChangeString = () => {
  const diff = getPriceChange()
  if (diff == null) return ''
  if (diff > 0) return `+$${diff.toFixed(2)}`
  if (diff < 0) return `-$${Math.abs(diff).toFixed(2)}`
  return '$0.00'
}

const getPriceChangeColor = () => {
  const diff = getPriceChange()
  if (diff == null) return 'text-gray-400'
  if (diff > 0) return 'text-green-400'
  if (diff < 0) return 'text-red-400'
  return 'text-gray-400'
}
</script> 