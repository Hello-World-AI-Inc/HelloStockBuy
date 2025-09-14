<template>
  <div class="w-full h-64 bg-gray-700 rounded-lg p-4">
    <div v-if="isLoading" class="flex items-center justify-center h-full">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
      <span class="ml-2 text-gray-300">載入圖表中...</span>
    </div>
    <div v-else-if="!chartData || chartData.length === 0" class="flex items-center justify-center h-full text-gray-400">
      暫無圖表數據
    </div>
    <canvas v-else ref="chartCanvas" class="w-full h-full"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'

// Register Chart.js components
Chart.register(...registerables)

const props = defineProps({
  data: {
    type: Object,
    default: null
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

const chartCanvas = ref(null)
let chartInstance = null

const chartData = ref([])

const createChart = () => {
  if (!chartCanvas.value || !chartData.value.length) return

  // Destroy existing chart
  if (chartInstance) {
    chartInstance.destroy()
  }

  const ctx = chartCanvas.value.getContext('2d')
  
  // Prepare data for Chart.js
  const labels = chartData.value.map(item => {
    const date = new Date(item.timestamp)
    // Convert to local time and format for Hong Kong/Taiwan timezone
    return date.toLocaleTimeString('zh-TW', { 
      hour: '2-digit', 
      minute: '2-digit',
      timeZone: 'Asia/Hong_Kong'
    })
  })
  
  const prices = chartData.value.map(item => item.price)
  
  // Determine line color based on price trend
  const firstPrice = prices[0]
  const lastPrice = prices[prices.length - 1]
  const lineColor = lastPrice >= firstPrice ? '#10b981' : '#ef4444' // green or red
  
  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: '價格',
        data: prices,
        borderColor: lineColor,
        backgroundColor: lineColor + '20', // Add transparency
        borderWidth: 2,
        fill: true,
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 4,
        pointHoverBackgroundColor: lineColor,
        pointHoverBorderColor: '#ffffff',
        pointHoverBorderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#ffffff',
          bodyColor: '#ffffff',
          borderColor: lineColor,
          borderWidth: 1,
          callbacks: {
            label: function(context) {
              return `價格: $${context.parsed.y.toFixed(2)}`
            }
          }
        }
      },
      scales: {
        x: {
          display: true,
          grid: {
            color: 'rgba(255, 255, 255, 0.1)',
            drawBorder: false
          },
          ticks: {
            color: '#9ca3af',
            maxTicksLimit: 6
          }
        },
        y: {
          display: true,
          grid: {
            color: 'rgba(255, 255, 255, 0.1)',
            drawBorder: false
          },
          ticks: {
            color: '#9ca3af',
            callback: function(value) {
              return '$' + value.toFixed(2)
            }
          }
        }
      },
      interaction: {
        intersect: false,
        mode: 'index'
      }
    }
  })
}

// Watch for data changes
watch(() => props.data, (newData) => {
  if (newData && newData.data) {
    chartData.value = newData.data
    nextTick(() => {
      createChart()
    })
  }
}, { immediate: true })

onMounted(() => {
  if (props.data && props.data.data) {
    chartData.value = props.data.data
    nextTick(() => {
      createChart()
    })
  }
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})
</script>
