'use client';

import {useState} from 'react';
import {usePathname, useRouter} from 'next/navigation';
import {
    Box,
    Drawer,
    AppBar,
    Toolbar,
    List,
    Typography,
    Divider,
    IconButton,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
} from '@mui/material';
import {
    Menu as MenuIcon,
    Dashboard as DashboardIcon,
    ShowChart as ChartIcon,
    AccountBalance as PositionsIcon,
    SwapHoriz as TradesIcon,
    Psychology as StrategyIcon,
    Notifications as SignalsIcon,
    Storage as DataIcon,
    Settings as SettingsIcon,
} from '@mui/icons-material';

const drawerWidth = 240;

interface NavItem {
    text: string;
    icon: React.ReactElement;
    path: string;
}

const navItems: NavItem[] = [
    {text: 'Dashboard', icon: <DashboardIcon/>, path: '/dashboard'},
    {text: 'Charts', icon: <ChartIcon/>, path: '/charts'},
    {text: 'Positions', icon: <PositionsIcon/>, path: '/positions'},
    {text: 'Trades', icon: <TradesIcon/>, path: '/trades'},
    {text: 'Strategies', icon: <StrategyIcon/>, path: '/strategies'},
    {text: 'Signals', icon: <SignalsIcon/>, path: '/signals'},
    {text: 'Data', icon: <DataIcon/>, path: '/data'},
    {text: 'Settings', icon: <SettingsIcon/>, path: '/settings'},
];

export default function AppDashboardLayout({
                                               children,
                                           }: {
    children: React.ReactNode;
}) {
    const [mobileOpen, setMobileOpen] = useState(false);
    const pathname = usePathname();
    const router = useRouter();

    const handleDrawerToggle = () => {
        setMobileOpen(!mobileOpen);
    };

    const handleNavigation = (path: string) => {
        router.push(path);
        setMobileOpen(false);
    };

    const drawer = (
        <Box>
            <Toolbar>
                <Typography variant="h6" noWrap component="div" fontWeight={700}>
                    Trading System
                </Typography>
            </Toolbar>
            <Divider/>
            <List>
                {navItems.map((item) => (
                    <ListItem key={item.text} disablePadding>
                        <ListItemButton
                            selected={pathname === item.path}
                            onClick={() => handleNavigation(item.path)}
                        >
                            <ListItemIcon>{item.icon}</ListItemIcon>
                            <ListItemText primary={item.text}/>
                        </ListItemButton>
                    </ListItem>
                ))}
            </List>
        </Box>
    );

    return (
        <html lang="en">
        <body>
        <Box sx={{display: 'flex'}}>
            <AppBar
                position="fixed"
                sx={{
                    width: {sm: `calc(100% - ${drawerWidth}px)`},
                    ml: {sm: `${drawerWidth}px`},
                }}
            >
                <Toolbar>
                    <IconButton
                        color="inherit"
                        aria-label="open drawer"
                        edge="start"
                        onClick={handleDrawerToggle}
                        sx={{mr: 2, display: {sm: 'none'}}}
                    >
                        <MenuIcon/>
                    </IconButton>
                    <Typography variant="h6" noWrap component="div">
                        {navItems.find((item) => item.path === pathname)?.text || 'Trading System'}
                    </Typography>
                </Toolbar>
            </AppBar>

            <Box
                component="nav"
                sx={{width: {sm: drawerWidth}, flexShrink: {sm: 0}}}
            >
                {/* Mobile drawer */}
                <Drawer
                    variant="temporary"
                    open={mobileOpen}
                    onClose={handleDrawerToggle}
                    ModalProps={{
                        keepMounted: true,
                    }}
                    sx={{
                        display: {xs: 'block', sm: 'none'},
                        '& .MuiDrawer-paper': {
                            boxSizing: 'border-box',
                            width: drawerWidth,
                        },
                    }}
                >
                    {drawer}
                </Drawer>

                {/* Desktop drawer */}
                <Drawer
                    variant="permanent"
                    sx={{
                        display: {xs: 'none', sm: 'block'},
                        '& .MuiDrawer-paper': {
                            boxSizing: 'border-box',
                            width: drawerWidth,
                        },
                    }}
                    open
                >
                    {drawer}
                </Drawer>
            </Box>

            <Box
                component="main"
                sx={{
                    flexGrow: 1,
                    p: 3,
                    width: {sm: `calc(100% - ${drawerWidth}px)`},
                    minHeight: '100vh',
                    bgcolor: 'background.default',
                }}
            >
                <Toolbar/>
                {children}
            </Box>
        </Box>
        </body>
        </html>
    );
}