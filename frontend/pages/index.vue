<template>
  <div class="min-h-screen bg-gray-900 text-white flex items-center justify-center">
    <div class="text-center">
      <div class="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mx-auto mb-6">
        <span class="text-white font-bold text-2xl">HS</span>
      </div>
      <h1 class="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-4">
        HelloStockBuy
      </h1>
      <p class="text-gray-400 mb-8">AI-Powered Investment Platform</p>
      <div class="space-y-4">
        <NuxtLink to="/chat" class="block bg-gradient-to-r from-green-600 to-emerald-600 text-white px-8 py-4 rounded-lg hover:from-green-700 hover:to-emerald-700 transition-all duration-200 shadow-lg text-lg font-semibold">
          Start AI Investment Advisor
        </NuxtLink>
        <NuxtLink to="/analysis" class="block bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg text-lg font-semibold">
          View Analysis Dashboard
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup>
// Simple redirect page - no complex functionality needed
</script>
