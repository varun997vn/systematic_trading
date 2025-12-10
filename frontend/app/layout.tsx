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
    Badge,
    Avatar,
    Tooltip,
    useMediaQuery,
    useTheme,
    alpha,
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
    TrendingUp as TrendingUpIcon,
    Close as CloseIcon,
} from '@mui/icons-material';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {ReactQueryDevtools} from '@tanstack/react-query-devtools';
import {ThemeProvider} from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from '@/theme';

const drawerWidth = 280;

interface NavItem {
    text: string;
    icon: React.ReactElement;
    path: string;
    badge?: number;
}

const navItems: NavItem[] = [
    {text: 'Dashboard', icon: <DashboardIcon/>, path: '/dashboard'},
    {text: 'Charts', icon: <ChartIcon/>, path: '/charts'},
    {text: 'Positions', icon: <PositionsIcon/>, path: '/positions', badge: 5},
    {text: 'Trades', icon: <TradesIcon/>, path: '/trades'},
    {text: 'Strategies', icon: <StrategyIcon/>, path: '/strategies'},
    {text: 'Signals', icon: <SignalsIcon/>, path: '/signals', badge: 3},
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
    const muiTheme = useTheme();
    const isMobile = useMediaQuery(muiTheme.breakpoints.down('sm'));

    // Create QueryClient with useState to ensure it's only created once
    const [queryClient] = useState(
        () =>
            new QueryClient({
                defaultOptions: {
                    queries: {
                        staleTime: 1000 * 60, // 1 minute
                        refetchOnWindowFocus: false,
                        retry: 1,
                    },
                    mutations: {
                        retry: 1,
                    },
                },
            })
    );

    const handleDrawerToggle = () => {
        setMobileOpen(!mobileOpen);
    };

    const handleNavigation = (path: string) => {
        router.push(path);
        setMobileOpen(false);
    };

    const drawer = (
        <Box sx={{height: '100%', display: 'flex', flexDirection: 'column'}}>
            {/* Logo Section */}
            <Box
                sx={{
                    p: 3,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2,
                    borderBottom: '1px solid',
                    borderColor: 'divider',
                }}
            >
                <Box
                    sx={{
                        width: 40,
                        height: 40,
                        borderRadius: 2,
                        background: 'linear-gradient(135deg, #3BCEAC 0%, #10B981 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        boxShadow: '0 4px 12px rgba(59, 206, 172, 0.3)',
                    }}
                >
                    <TrendingUpIcon sx={{color: 'white', fontSize: 24}}/>
                </Box>
                <Box>
                    <Typography variant="h6" fontWeight={700} sx={{lineHeight: 1.2}}>
                        Systematic Trading
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                        Professional Trading
                    </Typography>
                </Box>
            </Box>

            {/* Navigation Items */}
            <Box sx={{flexGrow: 1, overflowY: 'auto', py: 2}}>
                <List>
                    {navItems.map((item) => (
                        <ListItem key={item.text} disablePadding sx={{px: 1}}>
                            <ListItemButton
                                selected={pathname === item.path}
                                onClick={() => handleNavigation(item.path)}
                                sx={{
                                    minHeight: 48,
                                    px: 2.5,
                                    '&.Mui-selected': {
                                        backgroundColor: alpha(muiTheme.palette.secondary.main, 0.12),
                                        borderLeft: `3px solid ${muiTheme.palette.secondary.main}`,
                                        '& .MuiListItemIcon-root': {
                                            color: muiTheme.palette.secondary.main,
                                        },
                                        '& .MuiListItemText-primary': {
                                            color: muiTheme.palette.secondary.main,
                                            fontWeight: 600,
                                        },
                                    },
                                }}
                            >
                                <ListItemIcon sx={{minWidth: 40}}>
                                    {item.badge ? (
                                        <Badge badgeContent={item.badge} color="error" variant="dot">
                                            {item.icon}
                                        </Badge>
                                    ) : (
                                        item.icon
                                    )}
                                </ListItemIcon>
                                <ListItemText
                                    primary={item.text}
                                    primaryTypographyProps={{
                                        fontSize: '0.9375rem',
                                        fontWeight: pathname === item.path ? 600 : 500,
                                    }}
                                />
                            </ListItemButton>
                        </ListItem>
                    ))}
                </List>
            </Box>

            {/* User Profile Section */}
            <Box
                sx={{
                    p: 2,
                    borderTop: '1px solid',
                    borderColor: 'divider',
                    backgroundColor: alpha(muiTheme.palette.primary.main, 0.02),
                }}
            >
                <Box sx={{display: 'flex', alignItems: 'center', gap: 1.5}}>
                    <Avatar
                        sx={{
                            width: 36,
                            height: 36,
                            bgcolor: 'secondary.main',
                            fontWeight: 600,
                            fontSize: '0.875rem',
                        }}
                    >
                        TU
                    </Avatar>
                    <Box sx={{flexGrow: 1, minWidth: 0}}>
                        <Typography variant="body2" fontWeight={600} noWrap>
                            Trading User
                        </Typography>
                        <Typography variant="caption" color="text.secondary" noWrap>
                            Premium Account
                        </Typography>
                    </Box>
                </Box>
            </Box>
        </Box>
    );

    return (
        <QueryClientProvider client={queryClient}>
            <ThemeProvider theme={theme}>
                <html lang="en">
                <head>
                    <link rel="preconnect" href="https://fonts.googleapis.com"/>
                    <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous"/>
                </head>
                <body>
                <CssBaseline/>
                <Box sx={{display: 'flex', minHeight: '100vh'}}>
                    {/* App Bar */}
                    <AppBar
                        position="fixed"
                        elevation={0}
                        sx={{
                            width: {sm: `calc(100% - ${drawerWidth}px)`},
                            ml: {sm: `${drawerWidth}px`},
                            zIndex: (theme) => theme.zIndex.drawer + 1,
                        }}
                    >
                        <Toolbar sx={{justifyContent: 'space-between'}}>
                            <Box sx={{display: 'flex', alignItems: 'center', gap: 2}}>
                                <IconButton
                                    color="inherit"
                                    aria-label="toggle drawer"
                                    edge="start"
                                    onClick={handleDrawerToggle}
                                    sx={{
                                        display: {sm: 'none'},
                                        '&:hover': {
                                            backgroundColor: 'rgba(255, 255, 255, 0.1)',
                                        },
                                    }}
                                >
                                    {mobileOpen ? <CloseIcon/> : <MenuIcon/>}
                                </IconButton>
                                <Typography
                                    variant="h6"
                                    noWrap
                                    component="div"
                                    sx={{
                                        fontWeight: 600,
                                        letterSpacing: '-0.01em',
                                    }}
                                >
                                    {navItems.find((item) => item.path === pathname)?.text || 'Trading System'}
                                </Typography>
                            </Box>

                            {/* App Bar Actions */}
                            <Box sx={{display: 'flex', gap: 1}}>
                                <Tooltip title="Notifications" arrow>
                                    <IconButton
                                        color="inherit"
                                        sx={{
                                            '&:hover': {
                                                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                                            },
                                        }}
                                    >
                                        <Badge badgeContent={7} color="error">
                                            <SignalsIcon/>
                                        </Badge>
                                    </IconButton>
                                </Tooltip>
                            </Box>
                        </Toolbar>
                    </AppBar>

                    {/* Sidebar Navigation */}
                    <Box
                        component="nav"
                        sx={{
                            width: {sm: drawerWidth},
                            flexShrink: {sm: 0},
                        }}
                    >
                        {/* Mobile drawer */}
                        <Drawer
                            variant="temporary"
                            open={mobileOpen}
                            onClose={handleDrawerToggle}
                            ModalProps={{
                                keepMounted: true, // Better mobile performance
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

                    {/* Main Content Area */}
                    <Box
                        component="main"
                        sx={{
                            flexGrow: 1,
                            width: {sm: `calc(100% - ${drawerWidth}px)`},
                            minHeight: '100vh',
                            backgroundColor: 'background.default',
                            position: 'relative',
                        }}
                    >
                        <Toolbar/> {/* Spacer for fixed AppBar */}
                        <Box
                            sx={{
                                p: {xs: 2, sm: 3, md: 4},
                                maxWidth: '1600px',
                                mx: 'auto',
                            }}
                        >
                            {children}
                        </Box>
                    </Box>
                </Box>
                {/* React Query Dev Tools - only in development */}
                {process.env.NODE_ENV === 'development' && (
                    <ReactQueryDevtools initialIsOpen={false}/>
                )}
                </body>
                </html>
            </ThemeProvider>
        </QueryClientProvider>
    );
}