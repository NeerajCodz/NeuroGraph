import {
  MessageSquare,
  History,
  Network,
  Settings,
  Shield,
  LogOut,
  Bell,
  Rocket
} from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
  SidebarRail,
  useSidebar
} from '@/components/ui/sidebar';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';   
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';
import { ShinyText } from '@/components/reactbits/ShinyText';

const items = [
  { title: 'Intelligence Chat', subtitle: 'live reasoning', url: '/chat', icon: MessageSquare },
];

const chatHistoryItems = [
  { id: 'risk-audit', title: 'Q4 Deployment Risk', subtitle: '2m ago' },
  { id: 'beta-cluster', title: 'Cluster Beta Deep Dive', subtitle: '18m ago' },
  { id: 'iam-policies', title: 'IAM Policy Conflicts', subtitle: '1h ago' },
];

const footerItems = [
  { title: 'Knowledge Graph', subtitle: 'entity mapping', url: '/graph', icon: Network },
  { title: 'System Settings', subtitle: 'preferences', url: '/settings', icon: Settings },
  { title: 'Administration', subtitle: 'monitoring', url: '/admin', icon: Shield },
];

export function AppSidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  // Safe default destructured from context hook
  const { isMobile = false, state = 'expanded' } = useSidebar() || {};
  const collapsed = state === 'collapsed';

  const handleLogout = () => {
    navigate('/login');
  };

  return (
    <Sidebar collapsible="icon" className="font-sans">
      <SidebarHeader className="h-24 justify-center border-b border-white/10 bg-gradient-to-b from-purple-900/35 via-purple-950/20 to-transparent px-4 transition-all duration-300 group-data-[collapsible=icon]:px-2">
        <div className="flex w-full items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-purple-200 via-purple-100 to-fuchsia-100 shadow-[0_12px_28px_-14px_rgba(212,166,255,0.95)]">
            <Network className="h-5 w-5 text-purple-950 stroke-[2.2]" />
          </div>
          {!collapsed && (
            <div className="flex min-w-0 flex-col">
              <span className="truncate text-base font-semibold tracking-tight text-white">NeuroGraph</span>
              <ShinyText text="Context Intelligence" speed={5} className="text-[10px] uppercase tracking-[0.2em] text-purple-200/80" />
            </div>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent className="flex flex-col gap-7 px-3 py-6">
        <SidebarGroup className="p-0">
          <SidebarGroupLabel className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.24em] text-white/45">Workspace</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-1.5">
              {items.map((item) => {
                const isActive = location.pathname === item.url;
                return (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    isActive={isActive}
                    tooltip={item.title}
                    onClick={() => navigate(item.url)}
                    className={
                      "group/menu h-12 rounded-2xl px-2 transition-all duration-300 " +
                      (isActive
                        ? "gradient-primary text-primary-foreground shadow-[0_16px_30px_-16px_rgba(172,106,255,0.95)]"
                        : "text-white/70 hover:bg-white/7 hover:text-white")
                    }
                  >
                    <span className="flex w-full items-center gap-3">
                      <span className={"grid h-8 w-8 shrink-0 place-content-center rounded-xl transition " + (isActive ? "bg-black/20" : "bg-white/5 group-hover/menu:bg-white/10")}>
                        <item.icon className={"h-[17px] w-[17px] transition-transform duration-300 " + (isActive ? "scale-105" : "group-hover/menu:scale-110")} />
                      </span>
                      <span className="flex min-w-0 flex-col text-left group-data-[collapsible=icon]:hidden">
                        <span className="truncate text-[13.5px] font-medium">{item.title}</span>
                        <span className={"truncate text-[10px] uppercase tracking-[0.15em] " + (isActive ? "text-white/80" : "text-white/35")}>{item.subtitle}</span>
                      </span>
                    </span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              )})}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup className="p-0">
          <SidebarGroupLabel className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.24em] text-white/45">Chat History</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-1.5">
              {chatHistoryItems.map((item) => {
                const isActive = location.pathname === '/chat' && location.search.includes(item.id);

                return (
                  <SidebarMenuItem key={item.id}>
                    <SidebarMenuButton
                      isActive={isActive}
                      tooltip={item.title}
                      onClick={() => navigate(`/chat?thread=${item.id}`)}
                      className={
                        'group/menu h-10 rounded-xl px-2 transition-all duration-300 ' +
                        (isActive
                          ? 'gradient-secondary text-white'
                          : 'text-white/65 hover:bg-white/7 hover:text-white')
                      }
                    >
                      <span className="flex w-full items-center gap-3">
                        <span className={"grid h-7 w-7 shrink-0 place-content-center rounded-lg transition " + (isActive ? 'bg-black/20' : 'bg-white/5 group-hover/menu:bg-white/10')}>
                          <History className={"h-4 w-4 transition-transform duration-300 " + (isActive ? 'scale-105' : 'group-hover/menu:scale-110')} />
                        </span>
                        <span className="flex min-w-0 flex-col text-left group-data-[collapsible=icon]:hidden">
                          <span className="truncate text-[12.5px] font-medium">{item.title}</span>
                          <span className={"truncate text-[10px] uppercase tracking-[0.15em] " + (isActive ? 'text-white/80' : 'text-white/35')}>{item.subtitle}</span>
                        </span>
                      </span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup className="mt-auto p-0">
          <SidebarGroupLabel className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.24em] text-white/45">Operations</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-1.5">
              {footerItems.map((item) => {
                const isActive = location.pathname === item.url;
                return (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    isActive={isActive}
                    tooltip={item.title}
                    onClick={() => navigate(item.url)}
                    className={
                      "group/menu h-12 rounded-2xl px-2 transition-all duration-300 " +
                      (isActive
                        ? "gradient-secondary text-white"
                        : "text-white/70 hover:bg-white/7 hover:text-white")
                    }
                  >
                    <span className="flex w-full items-center gap-3">
                      <span className={"grid h-8 w-8 shrink-0 place-content-center rounded-xl transition " + (isActive ? "bg-black/20" : "bg-white/5 group-hover/menu:bg-white/10")}>
                        <item.icon className={"h-[17px] w-[17px] transition-transform duration-300 " + (isActive ? "" : "group-hover/menu:-rotate-6")} />
                      </span>
                      <span className="flex min-w-0 flex-col text-left group-data-[collapsible=icon]:hidden">
                        <span className="truncate text-[13.5px] font-medium">{item.title}</span>
                        <span className={"truncate text-[10px] uppercase tracking-[0.15em] " + (isActive ? "text-white/80" : "text-white/35")}>{item.subtitle}</span>
                      </span>
                    </span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              )})}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t border-white/10 p-4">
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger className="group flex w-full cursor-pointer items-center gap-3 rounded-2xl bg-white/5 p-2.5 text-left transition hover:bg-white/10">
                <Avatar className="h-10 w-10 shrink-0 ring-1 ring-purple-200/30 transition-all group-hover:ring-purple-200/55">
                  <AvatarImage src="" alt="User" />
                  <AvatarFallback className="gradient-primary text-[11px] font-semibold text-primary-foreground">AD</AvatarFallback>
                </Avatar>
                {!collapsed && (
                  <div className="flex min-w-0 flex-col text-sm">
                    <span className="truncate font-semibold text-white">System Admin</span>
                    <span className="truncate text-[10px] uppercase tracking-[0.2em] text-white/45">admin@neurograph</span>
                  </div>
                )}
              </DropdownMenuTrigger>
              <DropdownMenuContent
                side={isMobile ? 'bottom' : 'right'}
                align="end"
                className="w-64 rounded-2xl border-white/15 bg-[#110a22]/95 p-3 text-white shadow-2xl backdrop-blur-xl"
              >
                <DropdownMenuLabel className="p-0 font-normal mb-3">
                  <div className="flex items-center gap-3 rounded-xl bg-white/5 px-2 py-2 text-left text-sm">
                    <Avatar className="h-10 w-10 border border-white/10 shadow-sm">
                      <AvatarFallback className="gradient-primary text-xs text-primary-foreground">AD</AvatarFallback>
                    </Avatar>
                    <div className="grid flex-1 text-left text-sm leading-tight">
                      <span className="truncate font-bold text-white">System Admin</span>
                      <span className="truncate text-xs text-white/50">admin@neurograph</span>
                    </div>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator className="my-2 bg-white/5" />
                <DropdownMenuItem className="cursor-pointer rounded-xl py-3 transition-all hover:bg-white/10 focus:bg-white/10 focus:text-white">
                  <Bell className="mr-3 h-4 w-4" />
                  <span className="font-medium">Notifications</span>
                  <span className="ml-auto flex h-5 w-5 items-center justify-center rounded-full bg-purple-400/20 text-[10px] font-bold text-purple-100 ring-1 ring-purple-200/40">
                    4
                  </span>
                </DropdownMenuItem>
                <DropdownMenuItem className="cursor-pointer rounded-xl py-3 transition-all hover:bg-white/10 focus:bg-white/10 focus:text-white">
                  <Rocket className="mr-3 h-4 w-4" />
                  <span className="font-medium">Launch Diagnostics</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator className="my-2 bg-white/5" />
                <DropdownMenuItem className="cursor-pointer rounded-xl py-3 text-red-300 transition-all hover:bg-red-500/12 focus:bg-red-500/12 focus:text-red-200" onClick={handleLogout}>
                  <LogOut className="mr-3 h-4 w-4" />
                  <span className="font-medium">Sign Out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
