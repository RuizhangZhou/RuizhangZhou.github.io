// nuxt.config.ts
export default defineNuxtConfig({
  modules: [
    '@nuxt/content',
    '@nuxt/ui'
  ],

  ui: {
  },

  content: {
  },

  app: {
    head: {
      title: 'Ruizhang Zhou - Personal Website',
      meta: [
        { name: 'description', content: 'Personal Website - Ruizhang Zhou Resume and Project Experience' }
      ]
    }
  },

  css: ['~/assets/css/main.css'],
  compatibilityDate: '2025-04-13'
})