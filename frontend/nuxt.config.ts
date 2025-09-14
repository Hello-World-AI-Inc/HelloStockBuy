// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-05-15',
  devtools: { enabled: true },
  devServer: {
    host: '0.0.0.0',
    port: 3000
  },

  modules: [
    '@nuxt/eslint',
    '@nuxt/fonts',
    '@nuxt/icon',
    '@nuxt/image',
    '@nuxt/scripts',
    '@nuxt/test-utils',
    '@nuxt/ui',
    '@nuxtjs/tailwindcss'
    // '@nuxtjs/i18n' // 暫時禁用
  ],

  runtimeConfig: {
    public: {
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
    }
  },

  // i18n: {
  //   locales: [
  //     {
  //       code: 'en',
  //       name: 'English',
  //       file: 'en.json'
  //     },
  //     {
  //       code: 'zh_tw',
  //       name: '繁體中文',
  //       file: 'zh_tw.json'
  //     }
  //   ],
  //   lazy: true,
  //   langDir: 'locales/',
  //   defaultLocale: process.env.DEFAULT_LOCALE || 'en',
  //   fallbackLocale: process.env.FALLBACK_LOCALE || 'en',
  //   strategy: 'prefix_except_default',
  //   detectBrowserLanguage: {
  //     useCookie: true,
  //     cookieKey: 'i18n_redirected',
  //     redirectOn: 'root'
  //   }
  // }
})