<template>
  <div class="relative">
    <button 
      @click="toggleDropdown"
      class="flex items-center space-x-2 px-3 py-2 text-sm text-gray-300 hover:text-white transition-colors"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
      </svg>
      <span>{{ currentLocaleName }}</span>
      <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>
    
    <div 
      v-if="showDropdown"
      class="absolute right-0 mt-2 w-48 bg-gray-700 rounded-lg shadow-lg z-50"
    >
      <div class="py-1">
        <button
          v-for="locale in availableLocales"
          :key="locale.code"
          @click="switchLanguage(locale.code)"
          :class="[
            'w-full text-left px-4 py-2 text-sm transition-colors',
            locale.code === $i18n.locale 
              ? 'bg-gray-600 text-white' 
              : 'text-gray-300 hover:bg-gray-600 hover:text-white'
          ]"
        >
          {{ locale.name }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
const { $i18n } = useNuxtApp()
const showDropdown = ref(false)

const availableLocales = computed(() => {
  return $i18n.locales.value || [
    { code: 'en', name: 'English' },
    { code: 'zh_tw', name: '繁體中文' }
  ]
})

const currentLocaleName = computed(() => {
  const current = availableLocales.value.find(locale => locale.code === $i18n.locale.value)
  return current?.name || 'Language'
})

const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value
}

const switchLanguage = (localeCode) => {
  $i18n.setLocale(localeCode)
  showDropdown.value = false
}

// Close dropdown when clicking outside
onMounted(() => {
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.relative')) {
      showDropdown.value = false
    }
  })
})
</script>
