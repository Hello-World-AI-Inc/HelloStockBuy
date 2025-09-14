<template>
  <div class="h-screen bg-gray-900 text-white flex">
    <!-- Left Sidebar - Portfolio Information -->
    <div class="w-80 bg-gray-800 border-r border-gray-700 flex flex-col">
      <!-- Header -->
      <div class="p-4 border-b border-gray-700">
        <div class="flex items-center justify-between">
          <h1 class="text-xl font-bold text-white">AI Investment Advisor</h1>
          <NuxtLink to="/" class="text-gray-400 hover:text-white transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </NuxtLink>
        </div>
      </div>

      <!-- Connection Status -->
      <div class="p-4 border-b border-gray-700">
        <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <div :class="connectionStatus ? 'bg-green-400 animate-pulse' : 'bg-red-400'" class="w-3 h-3 rounded-full"></div>
          <span class="text-sm text-gray-300">{{ connectionStatus ? 'Connected' : 'Disconnected' }}</span>
        </div>
        <div class="flex items-center space-x-2">
          <button 
            @click="connectIBKR" 
            class="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-3 py-1 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 text-sm"
          >
            Connect
          </button>
        </div>
        </div>
      </div>

      <!-- Account Summary -->
      <div class="p-3 border-b border-gray-700">
        <div class="flex items-center justify-between mb-2">
          <h2 class="text-sm font-semibold text-white">Account Summary</h2>
          <div class="flex items-center space-x-3">
            <span 
              @click="openAccountModal" 
              class="text-sm text-gray-300 cursor-pointer hover:text-white transition-colors"
              :class="{ 'hover:underline': accountSummary.account }"
            >
              {{ accountSummary.account || '--' }}
            </span>
            <span :class="getAccountTypeColor(accountSummary.account)" class="text-sm font-medium">
              {{ getAccountType(accountSummary.account) }}
            </span>
          </div>
        </div>
        
        <div class="grid grid-cols-2 gap-2">
          <div class="bg-gray-700 rounded-lg p-2">
            <h3 class="text-xs font-medium text-gray-300 mb-1">Total Assets</h3>
            <p class="text-sm font-bold text-white">${{ accountSummary.netLiquidationValue?.toLocaleString() ?? '--' }}</p>
          </div>
          <div class="bg-gray-700 rounded-lg p-2">
            <h3 class="text-xs font-medium text-gray-300 mb-1">Cash Balance</h3>
            <p class="text-sm font-bold text-white">${{ accountSummary.totalCashValue?.toLocaleString() ?? '--' }}</p>
          </div>
          <div class="bg-gray-700 rounded-lg p-2">
            <h3 class="text-xs font-medium text-gray-300 mb-1">Available Funds</h3>
            <p class="text-sm font-bold text-white">${{ accountSummary.availableFunds?.toLocaleString() ?? '--' }}</p>
          </div>
          <div class="bg-gray-700 rounded-lg p-2">
            <h3 class="text-xs font-medium text-gray-300 mb-1">Buying Power</h3>
            <p class="text-sm font-bold text-white">${{ accountSummary.buyingPower?.toLocaleString() ?? '--' }}</p>
          </div>
        </div>
      </div>

      <!-- Current Positions -->
      <div class="flex-1 overflow-y-auto p-4">
        <h3 class="text-lg font-semibold text-white mb-3">Current Positions</h3>
        <div v-if="portfolio.length > 0" class="space-y-3">
          <div v-for="position in portfolio" :key="position.symbol" 
               @click="openPositionModal(position)"
               class="bg-gray-700 rounded-lg p-3 cursor-pointer hover:bg-gray-600 transition-colors">
            <div class="flex justify-between items-start mb-2">
              <h4 class="text-sm font-bold text-white">{{ position.symbol }}</h4>
              <span class="text-xs font-semibold text-gray-300">{{ position.position }} shares</span>
            </div>
            <div class="space-y-1 text-xs text-gray-300">
              <div class="flex justify-between">
                <span>Avg Cost: {{ formatNumber(position.avg_cost) }}</span>
                <span>Last Price: {{ formatNumber(position.market_price) ?? '--' }}</span>
              </div>
              <div class="flex justify-between">
                <span>High/Low: {{ formatNumber(getMarketData(position.symbol)?.low) }}/{{ formatNumber(getMarketData(position.symbol)?.high) }}</span>
                <span :class="getPriceChangeColor(position.symbol)">
                  {{ getPriceChange(position.symbol).change >= 0 ? '+' : '' }}{{ formatNumber(getPriceChange(position.symbol).change) }}/{{ getPriceChange(position.symbol).change >= 0 ? '+' : '' }}{{ getPriceChange(position.symbol).changePercent.toFixed(2) }}%
                </span>
              </div>
              <div class="flex justify-between">
                <span>Market Value: ${{ formatNumber(position.market_value) }}</span>
                <span>Unrealized P&L: <span :class="getPnLColor(position)">{{ getUnrealizedPnL(position) }}</span></span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-8 text-gray-400">
          <p class="text-sm">No positions</p>
        </div>
      </div>
    </div>

    <!-- Right Side - Chat Interface -->
    <div class="flex-1 flex flex-col">
      <!-- Chat Header -->
      <div class="bg-gray-800 border-b border-gray-700 p-4">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold text-white">Investment Advisor Chat</h2>
          <div class="flex items-center space-x-2">
            <div :class="isTyping ? 'bg-yellow-400 animate-pulse' : 'bg-gray-400'" class="w-3 h-3 rounded-full"></div>
            <span class="text-sm text-gray-300">{{ isTyping ? 'AI is thinking...' : 'AI is ready' }}</span>
            <button 
              @click="clearChat" 
              class="text-gray-400 hover:text-white transition-colors p-2 rounded-lg hover:bg-gray-700"
              title="Clear Chat"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Chat Messages -->
      <div ref="chatContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
        <div v-for="message in messages" :key="message.id" class="flex" :class="message.role === 'user' ? 'justify-end' : 'justify-start'">
          <div class="max-w-3xl rounded-lg p-4" :class="message.role === 'user' ? 'bg-blue-600' : 'bg-gray-700'">
            <div class="flex items-start space-x-3">
              <div v-if="message.role === 'assistant'" class="w-8 h-8 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <span class="text-xs font-bold text-white">AI</span>
              </div>
              <div class="flex-1">
                <div class="text-sm text-gray-300 mb-2">
                  {{ message.role === 'user' ? 'You' : 'AI Investment Advisor' }}
                  <span class="text-xs text-gray-500 ml-2">{{ formatTime(message.timestamp) }}</span>
                </div>
                <div class="text-white whitespace-pre-wrap leading-relaxed">{{ message.content }}</div>
              </div>
              <div v-if="message.role === 'user'" class="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <span class="text-xs font-bold text-white">您</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Typing indicator -->
        <div v-if="isTyping" class="flex justify-start">
          <div class="bg-gray-700 rounded-lg p-4">
            <div class="flex items-center space-x-3">
              <div class="w-8 h-8 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center">
                <span class="text-xs font-bold text-white">AI</span>
              </div>
              <div class="flex space-x-1">
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="px-4 py-2 border-t border-gray-700">
        <h4 class="text-sm font-semibold text-gray-300 mb-2">Quick Questions</h4>
        <div class="flex flex-wrap gap-2">
          <button 
            v-for="quickQuestion in quickQuestions" 
            :key="quickQuestion"
            @click="sendQuickQuestion(quickQuestion)"
            class="px-3 py-1 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors text-sm"
          >
            {{ quickQuestion }}
          </button>
        </div>
      </div>

      <!-- Input Area -->
      <div class="p-4 border-t border-gray-700">
        <div class="flex space-x-4">
          <input
            v-model="currentMessage"
            @keyup.enter="sendMessage"
            placeholder="Enter your question..."
            class="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
            :disabled="isTyping"
          />
          <button 
            @click="sendMessage" 
            :disabled="!currentMessage.trim() || isTyping"
            class="bg-gradient-to-r from-green-600 to-blue-600 text-white px-6 py-3 rounded-lg hover:from-green-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-600 disabled:cursor-not-allowed transition-all duration-200 shadow-lg"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Account Detail Modal -->
    <div v-if="showAccountModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click="closeAccountModal">
      <div class="bg-gray-800 rounded-xl p-6 max-w-lg w-full mx-4" @click.stop>
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-2xl font-bold text-white">賬戶詳情</h2>
          <button @click="closeAccountModal" class="text-gray-400 hover:text-white transition-colors">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="space-y-4">
          <!-- Account Info -->
          <div class="bg-gray-700 rounded-lg p-4">
            <h3 class="text-sm font-medium text-gray-300 mb-3">Basic Information</h3>
            <div class="space-y-3">
              <div>
                <p class="text-xs text-gray-400 mb-1">Account ID</p>
                <p class="text-sm font-semibold text-white">{{ accountSummary.account || '--' }}</p>
              </div>
              <div v-if="accountSummary.accountDisplayName && accountSummary.accountDisplayName !== accountSummary.account">
                <p class="text-xs text-gray-400 mb-1">Full Account Name</p>
                <p class="text-sm font-semibold text-white">{{ accountSummary.accountDisplayName || '--' }}</p>
              </div>
              <div v-else-if="accountSummary.account">
                <p class="text-xs text-gray-400 mb-1">Account Information</p>
                <p class="text-sm text-gray-300">IBKR API only provides account ID, no full user name</p>
              </div>
              <div>
                <p class="text-xs text-gray-400 mb-1">Account Type</p>
                <p :class="getAccountTypeColor(accountSummary.account)" class="text-sm font-semibold">
                  {{ getAccountType(accountSummary.account) }}
                </p>
              </div>
            </div>
          </div>

          <!-- Financial Summary -->
          <div class="bg-gray-700 rounded-lg p-4">
            <h3 class="text-sm font-medium text-gray-300 mb-3">Financial Summary</h3>
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-sm text-gray-400">Total Assets</span>
                <span class="text-sm font-semibold text-white">${{ accountSummary.netLiquidationValue?.toLocaleString() ?? '--' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-400">Cash Balance</span>
                <span class="text-sm font-semibold text-white">${{ accountSummary.totalCashValue?.toLocaleString() ?? '--' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-400">Available Funds</span>
                <span class="text-sm font-semibold text-white">${{ accountSummary.availableFunds?.toLocaleString() ?? '--' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-400">Buying Power</span>
                <span class="text-sm font-semibold text-white">${{ accountSummary.buyingPower?.toLocaleString() ?? '--' }}</span>
              </div>
            </div>
          </div>

          <!-- Additional Info -->
          <div class="bg-gray-700 rounded-lg p-4">
            <h3 class="text-sm font-medium text-gray-300 mb-3">Additional Information</h3>
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-sm text-gray-400">Total Position Value</span>
                <span class="text-sm font-semibold text-white">${{ accountSummary.grossPositionValue?.toLocaleString() ?? '--' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-400">Realized P&L</span>
                <span :class="getPnLColor(accountSummary.realizedPnl)" class="text-sm font-semibold">
                  ${{ accountSummary.realizedPnl?.toLocaleString() ?? '--' }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-400">Unrealized P&L</span>
                <span :class="getPnLColor(accountSummary.unrealizedPnl)" class="text-sm font-semibold">
                  ${{ accountSummary.unrealizedPnl?.toLocaleString() ?? '--' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Position Detail Modal -->
    <div v-if="showPositionModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click="closePositionModal">
      <div class="bg-gray-800 rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto" @click.stop>
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-2xl font-bold text-white">{{ selectedPosition?.symbol }} 詳細資料</h2>
          <button @click="closePositionModal" class="text-gray-400 hover:text-white transition-colors">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div v-if="selectedPosition" class="space-y-6">
          <!-- Intraday Chart -->
          <div class="bg-gray-700 rounded-lg p-4">
            <h3 class="text-sm font-medium text-gray-300 mb-3">Intraday Price Chart</h3>
            <IntradayChart :data="intradayData" :is-loading="isLoadingChart" />
          </div>

          <!-- Basic Position Info -->
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-gray-700 rounded-lg p-4">
              <h3 class="text-sm font-medium text-gray-300 mb-2">Basic Information</h3>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-gray-400">Stock Code:</span>
                  <span class="text-white font-semibold">{{ selectedPosition.symbol }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Position:</span>
                  <span class="text-white">{{ selectedPosition.position }} shares</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Exchange:</span>
                  <span class="text-white">{{ selectedPosition.exchange || 'N/A' }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Currency:</span>
                  <span class="text-white">{{ selectedPosition.currency }}</span>
                </div>
              </div>
            </div>

            <div class="bg-gray-700 rounded-lg p-4">
              <h3 class="text-sm font-medium text-gray-300 mb-2">Price Information</h3>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-gray-400">Average Cost:</span>
                  <span class="text-white">{{ formatNumber(selectedPosition.avg_cost) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Last Price:</span>
                  <span class="text-white">{{ formatNumber(selectedPosition.market_price) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Open Price:</span>
                  <span class="text-white">{{ formatNumber(getMarketData(selectedPosition.symbol)?.open) || 'N/A' }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Daily High/Low:</span>
                  <span class="text-white">{{ formatNumber(getMarketData(selectedPosition.symbol)?.low) }}/{{ formatNumber(getMarketData(selectedPosition.symbol)?.high) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Market Data -->
          <div class="bg-gray-700 rounded-lg p-4">
            <h3 class="text-sm font-medium text-gray-300 mb-4">Market Data</h3>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div class="space-y-2">
                <div class="flex justify-between">
                  <span class="text-gray-400">Bid:</span>
                  <span class="text-white">{{ formatNumber(getMarketData(selectedPosition.symbol)?.bid) || 'N/A' }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Ask:</span>
                  <span class="text-white">{{ formatNumber(getMarketData(selectedPosition.symbol)?.ask) || 'N/A' }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Volume:</span>
                  <span class="text-white">{{ getMarketData(selectedPosition.symbol)?.volume?.toLocaleString() || 'N/A' }}</span>
                </div>
              </div>
              <div class="space-y-2">
                <div class="flex justify-between">
                  <span class="text-gray-400">Daily Change:</span>
                  <span :class="getPriceChangeColor(selectedPosition.symbol)">
                    {{ getPriceChange(selectedPosition.symbol).change >= 0 ? '+' : '' }}{{ formatNumber(getPriceChange(selectedPosition.symbol).change) }}
                  </span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Change %:</span>
                  <span :class="getPriceChangeColor(selectedPosition.symbol)">
                    {{ getPriceChange(selectedPosition.symbol).change >= 0 ? '+' : '' }}{{ getPriceChange(selectedPosition.symbol).changePercent.toFixed(2) }}%
                  </span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">更新時間:</span>
                  <span class="text-white text-xs">
                    {{ getMarketData(selectedPosition.symbol)?.timestamp ? new Date(getMarketData(selectedPosition.symbol).timestamp * 1000).toLocaleTimeString() : 'N/A' }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Financial Summary -->
          <div class="bg-gray-700 rounded-lg p-4">
            <h3 class="text-sm font-medium text-gray-300 mb-4">Financial Summary</h3>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div class="space-y-2">
                <div class="flex justify-between">
                  <span class="text-gray-400">Total Market Value:</span>
                  <span class="text-white font-semibold">${{ formatNumber(selectedPosition.market_value) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Total Cost:</span>
                  <span class="text-white">${{ formatNumber(selectedPosition.avg_cost * selectedPosition.position) }}</span>
                </div>
              </div>
              <div class="space-y-2">
                <div class="flex justify-between">
                  <span class="text-gray-400">Unrealized P&L:</span>
                  <span :class="getPnLColor(selectedPosition)" class="font-semibold">
                    ${{ formatNumber(selectedPosition.unrealized_pnl) }}
                  </span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-400">Realized P&L:</span>
                  <span class="text-white">${{ formatNumber(selectedPosition.realized_pnl) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Performance Analysis -->
          <div class="bg-gray-700 rounded-lg p-4">
            <h3 class="text-sm font-medium text-gray-300 mb-4">Performance Analysis</h3>
            <div class="space-y-3 text-sm">
              <div class="flex justify-between items-center">
                <span class="text-gray-400">Return on Investment:</span>
                <span :class="getPnLColor(selectedPosition)" class="font-semibold">
                  {{ ((selectedPosition.unrealized_pnl / (selectedPosition.avg_cost * selectedPosition.position)) * 100).toFixed(2) }}%
                </span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-gray-400">Current vs Average Price:</span>
                <span :class="selectedPosition.market_price >= selectedPosition.avg_cost ? 'text-green-400' : 'text-red-400'" class="font-semibold">
                  {{ ((selectedPosition.market_price - selectedPosition.avg_cost) / selectedPosition.avg_cost * 100).toFixed(2) }}%
                </span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-gray-400">Position Weight:</span>
                <span class="text-white font-semibold">
                  {{ ((selectedPosition.market_value / accountSummary.netLiquidationValue) * 100).toFixed(2) }}%
                </span>
              </div>
            </div>
          </div>
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
const portfolio = ref([])
const accountSummary = ref({})
const isLoadingAccountSummary = ref(false)
const messages = ref([])
const currentMessage = ref('')
const isTyping = ref(false)
const chatContainer = ref(null)
const marketData = ref({}) // Store market data for each position
const selectedPosition = ref(null)
const showPositionModal = ref(false)
const intradayData = ref(null)
const isLoadingChart = ref(false)
const showAccountModal = ref(false)

// Quick questions
const quickQuestions = computed(() => [
  'Analyze my portfolio',
  'Recommend investment opportunities',
  'Assess investment risk',
  'Suggest position adjustment',
  'Market trend analysis',
  'Cash allocation advice'
])

// Methods
const connectIBKR = async () => {
  try {
    const response = await $fetch(`${apiBaseUrl}/connect`)
    if (response.message === 'Connected to IBKR') {
      // Try to fetch data to verify connection
      await fetchAccountSummary()
      await fetchPortfolio()
      
      // Only show success message if we actually got data
      if (accountSummary.value.account || portfolio.value.length > 0) {
        connectionStatus.value = true
        addSystemMessage('Successfully connected to IBKR, AI has retrieved your position information')
      } else {
        connectionStatus.value = false
        addSystemMessage('Connected to IBKR but no account data available. Please check your IBKR Gateway is running and account is accessible.')
      }
    }
  } catch (error) {
    console.error('Failed to connect to IBKR:', error)
    connectionStatus.value = false
    addSystemMessage('Failed to connect to IBKR, please check connection settings')
  }
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
  } finally {
    isLoadingAccountSummary.value = false
  }
}

const fetchPortfolio = async () => {
  try {
    const response = await $fetch(`${apiBaseUrl}/account/positions`)
    portfolio.value = response.positions || []
    
    // Fetch market data for each position
    await fetchMarketDataForPositions()
  } catch (error) {
    console.error('Failed to fetch portfolio:', error)
    portfolio.value = []
  }
}

const fetchMarketDataForPositions = async () => {
  for (const position of portfolio.value) {
    try {
      const data = await $fetch(`${apiBaseUrl}/market-data/${position.symbol}`)
      marketData.value[position.symbol] = data
    } catch (error) {
      console.error(`Failed to fetch market data for ${position.symbol}:`, error)
    }
  }
}

const sendMessage = async () => {
  if (!currentMessage.value.trim() || isTyping.value) return
  
  const userMessage = currentMessage.value.trim()
  currentMessage.value = ''
  
  // Add user message
  addMessage('user', userMessage)
  
  // Show typing indicator
  isTyping.value = true
  
  try {
    // Prepare context data
    const contextData = {
      portfolio: portfolio.value,
      accountSummary: accountSummary.value,
      message: userMessage,
      locale: 'zh_tw'
    }
    
    // Send to AI analysis endpoint
    const response = await $fetch(`${apiBaseUrl}/ai/analyze-ibkr`, {
      method: 'POST',
      body: contextData
    })
    
    // Add AI response
    addMessage('assistant', response.analysis)
    
  } catch (error) {
    console.error('Failed to get AI analysis:', error)
    addMessage('assistant', 'Sorry, AI analysis is temporarily unavailable. Please try again later.')
  } finally {
    isTyping.value = false
  }
}

const sendQuickQuestion = (question) => {
  currentMessage.value = question
  sendMessage()
}

const clearChat = () => {
  messages.value = []
  addSystemMessage('Hello! I\'m your AI Investment Advisor. I can analyze your portfolio, provide investment recommendations, and answer your investment questions. Please connect to IBKR first to get your position information.')
}

const addMessage = (role, content) => {
  const message = {
    id: Date.now() + Math.random(),
    role,
    content,
    timestamp: new Date()
  }
  messages.value.push(message)
  scrollToBottom()
}

const addSystemMessage = (content) => {
  addMessage('assistant', content)
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('zh-TW', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const getPnL = (position) => {
  if (!position.avg_cost || !position.market_value || !position.position) return '$0.00'
  const pnl = (position.market_value - (position.avg_cost * position.position))
  return `$${pnl.toFixed(2)}`
}

const getUnrealizedPnL = (position) => {
  if (!position.unrealized_pnl) return '$0.00'
  return `$${position.unrealized_pnl.toFixed(2)}`
}

const getPnLColor = (position) => {
  const pnl = position.unrealized_pnl || 0
  return pnl >= 0 ? 'text-green-400' : 'text-red-400'
}

const formatNumber = (value) => {
  if (!value || value === '--') return '--'
  return Number(value).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const getMarketData = (symbol) => {
  return marketData.value[symbol] || null
}

const getPriceChange = (symbol) => {
  const data = getMarketData(symbol)
  if (!data || !data.open) return { change: 0, changePercent: 0 }
  
  const change = data.price - data.open
  const changePercent = (change / data.open) * 100
  
  return { change, changePercent }
}

const getPriceChangeColor = (symbol) => {
  const { change } = getPriceChange(symbol)
  return change >= 0 ? 'text-green-400' : 'text-red-400'
}

const getAccountType = (account) => {
  if (!account) return '--'
  // IBKR paper trading accounts typically start with 'DU' or contain 'PAPER'
  if (account.includes('DU') || account.includes('PAPER') || account.includes('DEMO')) {
    return 'Paper'
  }
  return 'Live'
}

const getAccountTypeColor = (account) => {
  const accountType = getAccountType(account)
  if (accountType === 'Paper') {
    return 'text-yellow-400'
  } else if (accountType === 'Live') {
    return 'text-red-400'
  }
  return 'text-gray-400'
}

const openPositionModal = async (position) => {
  selectedPosition.value = position
  showPositionModal.value = true
  await loadIntradayData(position.symbol)
}

const closePositionModal = () => {
  showPositionModal.value = false
  selectedPosition.value = null
  intradayData.value = null
}

const openAccountModal = () => {
  if (accountSummary.value.account) {
    showAccountModal.value = true
  }
}

const closeAccountModal = () => {
  showAccountModal.value = false
}

const loadIntradayData = async (symbol) => {
  isLoadingChart.value = true
  try {
    const response = await $fetch(`${apiBaseUrl}/market-data/${symbol}/intraday`)
    intradayData.value = response
  } catch (error) {
    console.error('Error loading intraday data:', error)
    intradayData.value = null
  } finally {
    isLoadingChart.value = false
  }
}

// Initialize
onMounted(async () => {
  // Add welcome message
  addSystemMessage('Hello! I\'m your AI Investment Advisor. I can analyze your portfolio, provide investment recommendations, and answer your investment questions. Please connect to IBKR first to get your position information.')
  
  // Try to connect and fetch data
  await connectIBKR()
})
</script>