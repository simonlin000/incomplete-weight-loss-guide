import DefaultTheme from 'vitepress/theme'
import { h } from 'vue'
import './custom.css'
import CalorieCalc from './components/CalorieCalc.vue'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('CalorieCalc', CalorieCalc)
  },
  Layout() {
    return h(DefaultTheme.Layout, null, {
      // 每页正文结束处固定署名
      'doc-footer-before': () =>
        h('div', { class: 'author-sign' }, [
          h('span', { class: 'author-sign-label' }, '作者'),
          h('strong', 'Simonlin'),
          h('span', { class: 'author-sign-sep' }, '｜'),
          h('span', { class: 'author-sign-label' }, '公众号'),
          h('strong', 'Simonlin的精神世界'),
        ]),
    })
  },
}
