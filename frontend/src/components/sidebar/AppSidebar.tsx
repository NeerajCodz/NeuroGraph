import {
  MessageSquare,
  History,
  Network,
  LogOut,
  Bell,
  Brain,
  User,
  Plus,
  FolderOpen,
  ChevronRight,
  Loader2
} from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
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
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger
} from '@/components/ui/collapsible';
import { ShinyText } from '@/components/reactbits/ShinyText';
import { useAuth } from '@/contexts/AuthContext';
import { workspaceApi, conversationsApi } from '@/services/api';

interface Workspace {
  id: string;
  name: string;
  is_owner?: boolean;
}

interface Conversation {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  workspace_id?: string;
}

const memoryItems = [
  { title: 'Memory Store', subtitle: 'knowledge base', url: '/memory', icon: Brain },
  { title: 'Knowledge Graph', subtitle: 'entity mapping', url: '/graph', icon: Network },
];

const profileItems = [
  { title: 'Profile', subtitle: 'account settings', url: '/profile', icon: User },
];

export function AppSidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  // Safe default destructured from context hook
  const { isMobile = false, state = 'expanded' } = useSidebar() || {};
  const collapsed = state === 'collapsed';

  // State for workspaces and conversations
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [expandedWorkspace, setExpandedWorkspace] = useState<string | null>(null);
  const [isLoadingWorkspaces, setIsLoadingWorkspaces] = useState(true);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);

  // Load workspaces on mount
  useEffect(() => {
    const loadWorkspaces = async () => {
      try {
        setIsLoadingWorkspaces(true);
        const result = await workspaceApi.list() as Workspace[];
        setWorkspaces(Array.isArray(result) ? result : []);
      } catch (err) {
        console.error('Failed to load workspaces:', err);
        setWorkspaces([]);
      } finally {
        setIsLoadingWorkspaces(false);
      }
    };
    loadWorkspaces();
  }, []);

  // Load conversations (personal)
  useEffect(() => {
    const loadConversations = async () => {
      try {
        setIsLoadingConversations(true);
        const result = await conversationsApi.list() as Conversation[];
        setConversations(Array.isArray(result) ? result : []);
      } catch (err) {
        console.error('Failed to load conversations:', err);
        setConversations([]);
      } finally {
        setIsLoadingConversations(false);
      }
    };
    loadConversations();
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const formatTimeAgo = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return 'now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  const handleNewChat = () => {
    navigate('/chat');
    // Force a reload by using state
    window.dispatchEvent(new CustomEvent('new-chat'));
  };
  
  const userInitials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : user?.email?.slice(0, 2).toUpperCase() || 'U';

  // Get recent personal conversations (not in workspaces)
  const personalConversations = conversations.filter(c => !c.workspace_id).slice(0, 10);

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

      <SidebarContent className="flex flex-col gap-5 px-3 py-5">
        {/* New Chat Button */}
        <SidebarGroup className="p-0">
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton
                  tooltip="New Chat"
                  onClick={handleNewChat}
                  className="group/menu h-11 rounded-2xl px-2 transition-all duration-300 gradient-primary text-primary-foreground shadow-[0_16px_30px_-16px_rgba(172,106,255,0.95)]"
                >
                  <span className="flex w-full items-center gap-3">
                    <span className="grid h-7 w-7 shrink-0 place-content-center rounded-xl bg-black/20">
                      <Plus className="h-4 w-4" />
                    </span>
                    <span className="text-[13px] font-medium group-data-[collapsible=icon]:hidden">New Chat</span>
                  </span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Workspaces */}
        <SidebarGroup className="p-0">
          <SidebarGroupLabel className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.24em] text-white/45">Workspaces</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-1">
              {isLoadingWorkspaces ? (
                <div className="flex items-center justify-center py-3 text-white/30">
                  <Loader2 className="w-4 h-4 animate-spin" />
                </div>
              ) : workspaces.length === 0 ? (
                <div className="px-3 py-2 text-xs text-white/30">No workspaces yet</div>
              ) : (
                workspaces.map((workspace) => (
                  <Collapsible
                    key={workspace.id}
                    open={expandedWorkspace === workspace.id}
                    onOpenChange={(open) => setExpandedWorkspace(open ? workspace.id : null)}
                  >
                    <SidebarMenuItem>
                      <CollapsibleTrigger asChild>
                        <SidebarMenuButton
                          tooltip={workspace.name}
                          className="group/menu h-10 rounded-xl px-2 transition-all duration-300 text-white/70 hover:bg-white/7 hover:text-white"
                        >
                          <span className="flex w-full items-center gap-3">
                            <span className="grid h-7 w-7 shrink-0 place-content-center rounded-lg bg-white/5 group-hover/menu:bg-white/10">
                              <FolderOpen className="h-4 w-4" />
                            </span>
                            <span className="flex-1 truncate text-[12.5px] font-medium group-data-[collapsible=icon]:hidden">{workspace.name}</span>
                            <ChevronRight className={`h-3 w-3 text-white/30 transition-transform group-data-[collapsible=icon]:hidden ${expandedWorkspace === workspace.id ? 'rotate-90' : ''}`} />
                          </span>
                        </SidebarMenuButton>
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        <div className="ml-6 border-l border-white/10 pl-3 mt-1 space-y-1">
                          <button
                            onClick={() => navigate(`/chat?workspace=${workspace.id}`)}
                            className="w-full text-left px-2 py-1.5 text-[11px] text-white/50 hover:text-white/80 rounded-lg hover:bg-white/5 transition-colors"
                          >
                            + New in workspace
                          </button>
                        </div>
                      </CollapsibleContent>
                    </SidebarMenuItem>
                  </Collapsible>
                ))
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Recent Chats */}
        <SidebarGroup className="p-0">
          <SidebarGroupLabel className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.24em] text-white/45">Recent Chats</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-1">
              {isLoadingConversations ? (
                <div className="flex items-center justify-center py-3 text-white/30">
                  <Loader2 className="w-4 h-4 animate-spin" />
                </div>
              ) : personalConversations.length === 0 ? (
                <div className="px-3 py-2 text-xs text-white/30">No conversations yet</div>
              ) : (
                personalConversations.map((conv) => {
                  const isActive = location.pathname === '/chat' && location.search.includes(conv.id);
                  return (
                    <SidebarMenuItem key={conv.id}>
                      <SidebarMenuButton
                        isActive={isActive}
                        tooltip={conv.title}
                        onClick={() => navigate(`/chat?conversation=${conv.id}`)}
                        className={
                          'group/menu h-10 rounded-xl px-2 transition-all duration-300 ' +
                          (isActive
                            ? 'gradient-secondary text-white'
                            : 'text-white/65 hover:bg-white/7 hover:text-white')
                        }
                      >
                        <span className="flex w-full items-center gap-3">
                          <span className={"grid h-7 w-7 shrink-0 place-content-center rounded-lg transition " + (isActive ? 'bg-black/20' : 'bg-white/5 group-hover/menu:bg-white/10')}>
                            <History className="h-4 w-4" />
                          </span>
                          <span className="flex min-w-0 flex-col text-left group-data-[collapsible=icon]:hidden">
                            <span className="truncate text-[12px] font-medium">{conv.title || 'Untitled'}</span>
                            <span className={"truncate text-[10px] " + (isActive ? 'text-white/80' : 'text-white/35')}>
                              {formatTimeAgo(conv.created_at)}
                            </span>
                          </span>
                        </span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  );
                })
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Memory Section */}
        <SidebarGroup className="p-0">
          <SidebarGroupLabel className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.24em] text-white/45">Memory</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-1.5">
              {memoryItems.map((item) => {
                const isActive = location.pathname === item.url;
                return (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    isActive={isActive}
                    tooltip={item.title}
                    onClick={() => navigate(item.url)}
                    className={
                      "group/menu h-11 rounded-2xl px-2 transition-all duration-300 " +
                      (isActive
                        ? "gradient-secondary text-white"
                        : "text-white/70 hover:bg-white/7 hover:text-white")
                    }
                  >
                    <span className="flex w-full items-center gap-3">
                      <span className={"grid h-8 w-8 shrink-0 place-content-center rounded-xl transition " + (isActive ? "bg-black/20" : "bg-white/5 group-hover/menu:bg-white/10")}>
                        <item.icon className={"h-[17px] w-[17px] transition-transform duration-300 " + (isActive ? "scale-105" : "group-hover/menu:scale-110")} />
                      </span>
                      <span className="flex min-w-0 flex-col text-left group-data-[collapsible=icon]:hidden">
                        <span className="truncate text-[13px] font-medium">{item.title}</span>
                        <span className={"truncate text-[10px] uppercase tracking-[0.15em] " + (isActive ? "text-white/80" : "text-white/35")}>{item.subtitle}</span>
                      </span>
                    </span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              )})}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Profile Section */}
        <SidebarGroup className="mt-auto p-0">
          <SidebarGroupContent>
            <SidebarMenu className="gap-1.5">
              {profileItems.map((item) => {
                const isActive = location.pathname === item.url || location.pathname.startsWith('/profile');
                return (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    isActive={isActive}
                    tooltip={item.title}
                    onClick={() => navigate(item.url)}
                    className={
                      "group/menu h-11 rounded-2xl px-2 transition-all duration-300 " +
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
                        <span className="truncate text-[13px] font-medium">{item.title}</span>
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
                  <AvatarFallback className="gradient-primary text-[11px] font-semibold text-primary-foreground">{userInitials}</AvatarFallback>
                </Avatar>
                {!collapsed && (
                  <div className="flex min-w-0 flex-col text-sm">
                    <span className="truncate font-semibold text-white">{user?.full_name || 'User'}</span>
                    <span className="truncate text-[10px] uppercase tracking-[0.2em] text-white/45">{user?.email || ''}</span>
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
                      <AvatarFallback className="gradient-primary text-xs text-primary-foreground">{userInitials}</AvatarFallback>
                    </Avatar>
                    <div className="grid flex-1 text-left text-sm leading-tight">
                      <span className="truncate font-bold text-white">{user?.full_name || 'User'}</span>
                      <span className="truncate text-xs text-white/50">{user?.email || ''}</span>
                    </div>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator className="my-2 bg-white/5" />
                <DropdownMenuItem 
                  className="cursor-pointer rounded-xl py-3 transition-all hover:bg-white/10 focus:bg-white/10 focus:text-white"
                  onClick={() => navigate('/profile')}
                >
                  <User className="mr-3 h-4 w-4" />
                  <span className="font-medium">Profile & Settings</span>
                </DropdownMenuItem>
                <DropdownMenuItem className="cursor-pointer rounded-xl py-3 transition-all hover:bg-white/10 focus:bg-white/10 focus:text-white">
                  <Bell className="mr-3 h-4 w-4" />
                  <span className="font-medium">Notifications</span>
                  <span className="ml-auto flex h-5 w-5 items-center justify-center rounded-full bg-purple-400/20 text-[10px] font-bold text-purple-100 ring-1 ring-purple-200/40">
                    0
                  </span>
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
