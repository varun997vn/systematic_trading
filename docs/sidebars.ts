import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  systematicTradingSidebar: [
    'systematic-trading/trader',              // appears last
    'systematic-trading/data-manager',
    'systematic-trading/strategies',
    'systematic-trading/package-architecture', // appears first
    'systematic-trading/database',
  ],
};

export default sidebars;
