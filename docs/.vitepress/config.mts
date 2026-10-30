import { defineConfig } from 'vitepress'

export default defineConfig({
  // GitHub Pages 项目站点走子路径；本地预览不带
  base: process.env.DOCS_BASE || '/',
  lang: 'zh-CN',
  title: '不完全减肥指南',
  description: '给普通人的减重方法：热量缺口、怎么吃、怎么练、卡住了怎么办。每条结论标证据等级，来源可核。',
  cleanUrls: true,
  lastUpdated: true,
  head: [
    ['meta', { name: 'viewport', content: 'width=device-width,initial-scale=1' }],
  ],
  themeConfig: {
    nav: [
      { text: '开始读', link: '/ch00-my-account' },
      { text: '附录', link: '/appendix/a-food-table' },
    ],
    outline: { level: [2, 3], label: '本页目录' },
    search: { provider: 'local', options: { translations: {
      button: { buttonText: '搜索', buttonAriaLabel: '搜索' },
      modal: { noResultsText: '没有找到结果', resetButtonTitle: '清空', footer: { selectText: '选择', navigateText: '切换', closeText: '关闭' } },
    } } },
    docFooter: { prev: '上一节', next: '下一节' },
    darkModeSwitchLabel: '深色',
    sidebarMenuLabel: '目录',
    returnToTopLabel: '回到顶部',
    lastUpdatedText: '最后更新',
    editLink: { pattern: 'https://github.com/simonlin000/incomplete-weight-loss-guide/edit/main/docs/:path', text: '发现错误，去改一行' },
    sidebar: [
      { text: '第零部分　我的账', link: '/ch00-my-account' },
      {
        text: '第一部分　先把糊涂账拆掉',
        collapsed: false,
        items: [{ text: '十一种说法，一条条拆', link: '/ch01-myths' }],
      },
      { text: '第二部分　一条铁律', link: '/ch02-one-rule' },
      { text: '第三部分　怎么吃', link: '/ch03-eating' },
      { text: '第四部分　怎么练', link: '/ch04-training' },
      { text: '第五部分　从今天开始：30 天', link: '/ch05-first-30-days' },
      { text: '第六部分　卡住了怎么办', link: '/ch06-plateau' },
      { text: '第七部分　瘦下来之后', link: '/ch07-after' },
      { text: '第八部分　安全边界', link: '/ch08-safety' },
      { text: '第九部分　怎么判断真假', link: '/ch09-fact-check' },
      { text: '尾声　你一定要瘦', link: '/epilogue' },
      {
        text: '附录',
        collapsed: false,
        items: [
          { text: '附 A　食物交换表', link: '/appendix/a-food-table' },
          { text: '附 B　常见问题', link: '/appendix/b-faq' },
          { text: '附 C　术语表', link: '/appendix/c-glossary' },
          { text: '附 D　跟着谁看', link: '/appendix/d-who-to-follow' },
          { text: '附 E　来源全表', link: '/appendix/e-sources' },
        ],
      },
    ],
  },
})
