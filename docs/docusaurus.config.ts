import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Systematic Trading',
  tagline: 'Algorithmic Trading Infrastructure & Documentation',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://your-docusaurus-site.example.com',
  baseUrl: '/',

  organizationName: 'your-organization',
  projectName: 'systematic-trading',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  // ✅ Tailwind CSS v4 integration
  plugins: [
    async function tailwindPlugin() {
      return {
        name: 'docusaurus-tailwindcss',
        configurePostCss(postcssOptions) {
          postcssOptions.plugins.push(require('tailwindcss'));
          postcssOptions.plugins.push(require('autoprefixer'));
          return postcssOptions;
        },
      };
    },
  ],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: 'docs',
          editUrl: 'https://github.com/your-org/systematic-trading/tree/main/',
        },
        blog: {
          showReadingTime: true,
          blogTitle: 'Trading Insights',
          blogDescription: 'Analysis, strategies, and system updates',
          feedOptions: {
            type: ['rss', 'atom'],
            xslt: true,
          },
          editUrl: 'https://github.com/your-org/systematic-trading/tree/main/',
          onInlineTags: 'warn',
          onInlineAuthors: 'warn',
          onUntruncatedBlogPosts: 'warn',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/systematic-trading-social.jpg',

    colorMode: {
      defaultMode: 'dark',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },

    navbar: {
      title: 'Systematic Trading',
      logo: {
        alt: 'Systematic Trading Logo',
        src: 'img/logo_stock.svg',
        srcDark: 'img/logo_stock.svg',
      },
      hideOnScroll: true,
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'systematicTradingSidebar',
          position: 'left',
          label: 'Documentation',
        },
        {
          to: '/architecture',
          label: 'Architecture',
          position: 'left',
        },
        {
          href: 'https://github.com/varun997vn/systematic_trading',
          position: 'right',
          className: 'header-github-link',
          'aria-label': 'GitHub repository',
        },
      ],
    },

    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            { label: 'Getting Started', to: '/docs/intro' },
            { label: 'Backend Architecture', to: '/docs/backend' },
            { label: 'Strategy Development', to: '/docs/strategies' },
            { label: 'API Reference', to: '/docs/api' },
          ],
        },
        {
          title: 'Resources',
          items: [
            { label: 'Trading Insights', to: '/blog' },
            { label: 'Backtesting Guide', to: '/docs/backtesting' },
            { label: 'Performance Metrics', to: '/docs/metrics' },
          ],
        },
        {
          title: 'Community',
          items: [
            {
              label: 'GitHub Discussions',
              href: 'https://github.com/your-org/systematic-trading/discussions',
            },
            { label: 'Discord', href: 'https://discord.gg/your-invite' },
            {
              label: 'Stack Overflow',
              href: 'https://stackoverflow.com/questions/tagged/systematic-trading',
            },
          ],
        },
        {
          title: 'More',
          items: [
            { label: 'GitHub', href: 'https://github.com/your-org/systematic-trading' },
            { label: 'Changelog', to: '/changelog' },
            { label: 'License', to: '/license' },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Systematic Trading.`,
    },

    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.vsDark,
      additionalLanguages: ['python', 'java', 'bash', 'json', 'yaml'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
