import {
  History,
  LogOut,
  
  Brain,
  User,
  Plus,
  Bot,
  Cpu,
  Settings2,
  Plug,
  Shield,
  LayoutDashboard,
  Home,
  GitBranch,
  PanelLeftClose,
  PanelLeftOpen,
  Trash2,
  MoreVertical
} from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useState, useEffect, useMemo } from 'react';
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
  useSidebar
} from '@/components/ui/sidebar';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ShinyText } from '@/components/reactbits/ShinyText';
import { useAuth } from '@/contexts/AuthContext';
import { workspaceApi, conversationsApi } from '@/services/api';
import { useTheme } from '@/contexts/ThemeContext';

interface Workspace {
  id: string;
  name: string;
}
interface Conversation {
  id: string;
  title: string;
  workspace_id?: string;
}

export function AppSidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { state = 'expanded' } = useSidebar();
  const collapsed = state === 'collapsed';
  const { sidebarCollapsed, setSidebarCollapsed } = useTheme();

  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [workspaceSelection, setWorkspaceSelection] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const wsResult = await workspaceApi.list();
        const wsList = Array.isArray(wsResult) ? wsResult : [];
        const dedupedWorkspaces = Array.from(new Map(wsList.map((ws) => [ws.id, ws])).values());
        setWorkspaces(dedupedWorkspaces);

        const personalConversations = await conversationsApi.list();
        const workspaceConversationGroups = await Promise.all(
          dedupedWorkspaces.map((ws) => conversationsApi.list(ws.id).catch(() => []))
        );
        const all = [
          ...(Array.isArray(personalConversations) ? personalConversations : []),
          ...workspaceConversationGroups.flat().filter((c) => !!c),
        ] as Conversation[];
        const deduped = Array.from(new Map(all.map((c) => [c.id, c])).values());
        setConversations(deduped);
      } catch (err) {
        console.error('Error fetching sidebar data:', err);
      }
    };
    fetchData();
  }, []);

  const routeWorkspaceId = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return params.get('workspace_id');
  }, [location.search]);

  const activeWorkspaceId = useMemo(() => {
    const candidateWorkspaceId = routeWorkspaceId ?? workspaceSelection;
    if (!candidateWorkspaceId) {
      return null;
    }
    return workspaces.some((workspace) => workspace.id === candidateWorkspaceId)
      ? candidateWorkspaceId
      : null;
  }, [routeWorkspaceId, workspaceSelection, workspaces]);

  const previousChats = useMemo(() => {
    if (activeWorkspaceId) {
      return conversations.filter((conversation) => conversation.workspace_id === activeWorkspaceId);
    }
    return conversations.filter((conversation) => !conversation.workspace_id);
  }, [conversations, activeWorkspaceId]);

  const handleNewChat = (workspaceId?: string | null) => {
    const selectedWorkspaceId = workspaceId === undefined ? activeWorkspaceId : workspaceId;
    const targetWorkspaceId = selectedWorkspaceId && selectedWorkspaceId !== 'personal' ? selectedWorkspaceId : null;
    const chatUrl = targetWorkspaceId ? `/chat?workspace_id=${targetWorkspaceId}` : '/chat';
    navigate(chatUrl);
    window.dispatchEvent(new CustomEvent('new-chat', { detail: { workspaceId: targetWorkspaceId } }));
  };

  const userInitials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : user?.email?.slice(0, 2).toUpperCase() || 'U';

  const handleDeleteConversation = async (conversationId: string, conversationTitle: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent navigation when clicking delete
    
    if (confirm(`Are you sure you want to delete "${conversationTitle}"? This action cannot be undone.`)) {
      try {
        await conversationsApi.delete(conversationId);
        
        // Remove the conversation from local state
        setConversations(prevConversations => 
          prevConversations.filter(conv => conv.id !== conversationId)
        );
        
        // If we're currently viewing the deleted conversation, navigate away
        if (location.pathname === `/chat/${conversationId}`) {
          navigate('/chat');
        }
      } catch (error) {
        console.error('Error deleting conversation:', error);
        alert('Failed to delete conversation. Please try again.');
      }
    }
  };

  const isProfileRoute = location.pathname.startsWith('/profile');

  const profileSidebarItems = [
    { title: 'Profile', url: '/profile', icon: User },
    { title: 'Agents', url: '/profile/agents', icon: Bot },
    { title: 'AI Models', url: '/profile/models', icon: Cpu },
    { title: 'Preferences', url: '/profile/preferences', icon: Settings2 },
    { title: 'Integrations', url: '/profile/integrations', icon: Plug },
    { title: 'Security', url: '/profile/security', icon: Shield },
    { title: 'Settings', url: '/profile/settings', icon: LayoutDashboard }
  ];

  return (
    <Sidebar collapsible="icon" className="font-sans">
      <SidebarHeader className="h-24 justify-center border-b border-white/10 bg-gradient-to-b from-purple-900/35 via-purple-950/20 to-transparent px-4 group-data-[collapsible=icon]:h-16 group-data-[collapsible=icon]:px-1.5 group-data-[collapsible=icon]:py-2">
        <div className="flex w-full items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-purple-600 via-purple-500 to-fuchsia-600 shadow-[0_0_20px_rgba(168,85,247,0.4)] border border-white/20 p-2">
            <img src="/logo.svg" alt="NeuroGraph" className="h-full w-full brightness-0 invert drop-shadow-[0_0_6px_rgba(255,255,255,0.4)]" />
          </div>
          {!collapsed && (
            <div className="flex min-w-0 flex-col cursor-pointer" onClick={() => navigate('/')}>
              <span className="truncate text-base font-semibold tracking-tight text-white">NeuroGraph</span>
              <ShinyText text="Context Intelligence" speed={5} className="text-[10px] uppercase tracking-[0.2em] text-purple-200/80" />
            </div>
          )}
        </div>
        {!collapsed && (
          <div className="mt-3 flex w-full gap-2">
            <Button
              size="sm"
              variant="outline"
              className="h-8 flex-1 border-white/15 bg-white/10 text-white/85 hover:bg-white/15"
              onClick={() => navigate('/chat')}
            >
              <Home className="mr-1.5 h-3.5 w-3.5" />
              Home
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="h-8 border-white/15 bg-white/10 text-white/85 hover:bg-white/15"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            >
              {sidebarCollapsed ? <PanelLeftOpen className="h-3.5 w-3.5" /> : <PanelLeftClose className="h-3.5 w-3.5" />}
            </Button>
          </div>
        )}
      </SidebarHeader>

      <SidebarContent className="flex flex-col gap-4 px-2 py-4 group-data-[collapsible=icon]:px-1 group-data-[collapsible=icon]:py-3">
        {isProfileRoute ? (
          <SidebarGroup>
            <SidebarGroupLabel className="text-white/60">Profile Navigation</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {profileSidebarItems.map(item => {
                  const isActive = item.url === '/profile'
                    ? location.pathname === '/profile'
                    : location.pathname.startsWith(item.url);
                  return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton 
                      tooltip={item.title} 
                      onClick={() => navigate(item.url)}
                      isActive={isActive}
                      className="group/menu"
                    >
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  );
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ) : (
          <>
            <SidebarGroup className="p-0">
              <SidebarMenu>
                <SidebarMenuItem>
                    <SidebarMenuButton
                      tooltip="New Chat"
                      onClick={() => handleNewChat()}
                      className="gradient-primary text-primary-foreground h-11 rounded-2xl"
                    >
                      <Plus className="h-4 w-4" />
                      <span>New Chat</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroup>

            {!collapsed && (
              <>
                <SidebarGroup className="p-0">
                  <SidebarGroupLabel className="px-2 pb-1 text-[10px] uppercase tracking-[0.22em] text-white/45">
                    Workspaces
                  </SidebarGroupLabel>
                  <SidebarGroupContent>
                    <div className="px-2">
                      <Select
                        value={activeWorkspaceId ?? 'personal'}
                        onValueChange={(value) => {
                          const workspaceId = value === 'personal' ? null : value;
                          setWorkspaceSelection(workspaceId);
                          navigate(workspaceId ? `/chat?workspace_id=${workspaceId}` : '/chat');
                        }}
                      >
                        <SelectTrigger className="h-10 rounded-xl border-white/10 bg-white/5 text-white/85 hover:bg-white/10">
                          <SelectValue placeholder="Personal" />
                        </SelectTrigger>
                        <SelectContent className="border-white/10 bg-[#110825] text-white">
                          <SelectItem value="personal">Personal</SelectItem>
                          {workspaces.map((workspace) => (
                            <SelectItem key={workspace.id} value={workspace.id}>
                              {workspace.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </SidebarGroupContent>
                </SidebarGroup>

                <SidebarGroup className="min-h-0 flex-1 p-0">
                  <SidebarGroupLabel className="px-2 pb-1 text-[10px] uppercase tracking-[0.22em] text-white/45">
                    Previous Chats
                  </SidebarGroupLabel>
                  <SidebarGroupContent className="min-h-0">
                    <SidebarMenu className="max-h-[44vh] overflow-y-auto px-2 pb-1">
                      {previousChats.slice(0, 30).map((chat) => (
                        <SidebarMenuItem key={chat.id} className="relative group">
                          <SidebarMenuButton
                            tooltip={chat.title}
                            onClick={() => navigate('/chat/' + chat.id)}
                            isActive={location.pathname === '/chat/' + chat.id}
                            className="h-8 rounded-xl text-white/75 hover:text-white pr-8"
                          >
                            <History className="h-3.5 w-3.5" />
                            <span className="truncate text-xs">{chat.title}</span>
                          </SidebarMenuButton>
                          
                          <DropdownMenu>
                            <DropdownMenuTrigger className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity rounded hover:bg-white/10 flex items-center justify-center">
                              <MoreVertical className="h-3 w-3 text-white/60" />
                            </DropdownMenuTrigger>
                            <DropdownMenuContent className="w-48 bg-[#110825] border-white/10" align="end">
                              <DropdownMenuItem
                                onClick={(e) => handleDeleteConversation(chat.id, chat.title, e)}
                                className="text-red-400 hover:text-red-300 hover:bg-red-400/10"
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                Delete conversation
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </SidebarMenuItem>
                      ))}
                      {previousChats.length === 0 && (
                        <div className="px-3 py-2 text-xs text-white/40">
                          No previous chats yet
                        </div>
                      )}
                    </SidebarMenu>
                  </SidebarGroupContent>
                </SidebarGroup>
              </>
            )}

          </>
        )}
      </SidebarContent>

      <SidebarFooter className="border-t border-white/10 p-3 group-data-[collapsible=icon]:p-1.5">
        <div className="mb-2 rounded-2xl border border-white/10 bg-white/5 p-1.5 group-data-[collapsible=icon]:px-1 group-data-[collapsible=icon]:py-1">
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton
                onClick={() => navigate('/memory')}
                tooltip="MEMORY"
                isActive={location.pathname.startsWith('/memory')}
                className="rounded-xl"
              >
                <Brain className="h-4 w-4" />
                <span>MEMORY</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
            <SidebarMenuItem>
              <SidebarMenuButton
                onClick={() => navigate('/graph')}
                tooltip="GRAPH"
                isActive={location.pathname.startsWith('/graph')}
                className="rounded-xl text-cyan-100/85 hover:text-cyan-100"
              >
                <GitBranch className="h-4 w-4" />
                <span>GRAPH</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger className="flex w-full min-w-0 items-center gap-3 overflow-hidden rounded-2xl p-2 text-left outline-none transition-colors hover:bg-white/5 group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:gap-0 group-data-[collapsible=icon]:p-0">
            <Avatar className="h-8 w-8 shrink-0 border border-white/10">
              <AvatarFallback className="bg-purple-900/50 text-xs font-medium text-purple-200">
                {userInitials}
              </AvatarFallback>
            </Avatar>
            {!collapsed && (
              <div 
                className="flex min-w-0 flex-1 flex-col cursor-pointer"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate('/profile');
                }}
              >
                <span className="truncate text-sm font-medium text-white hover:text-purple-200 transition-colors">{user?.full_name || 'User'}</span>
                <span className="truncate text-xs text-white/40 hover:text-white/60 transition-colors">{user?.email}</span>
              </div>
            )}
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56 bg-[#110825] border-white/10" align="end" side="right" sideOffset={12}>
            <DropdownMenuLabel className="text-white/70 font-normal">Account</DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-white/10" />
            <DropdownMenuItem onClick={() => navigate('/profile')} className="text-white hover:bg-white/10">
              <User className="mr-2 h-4 w-4" /> Profile
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => navigate('/profile/settings')} className="text-white hover:bg-white/10">
              <Settings2 className="mr-2 h-4 w-4" /> Settings
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="text-white hover:bg-white/10"
            >
              {sidebarCollapsed ? <PanelLeftOpen className="mr-2 h-4 w-4" /> : <PanelLeftClose className="mr-2 h-4 w-4" />}
              {sidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
            </DropdownMenuItem>
            <DropdownMenuSeparator className="bg-white/10" />
            <DropdownMenuItem onClick={logout} className="text-red-400 hover:text-red-300 hover:bg-red-400/10">
              <LogOut className="mr-2 h-4 w-4" /> Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarFooter>
    </Sidebar>
  );
}




