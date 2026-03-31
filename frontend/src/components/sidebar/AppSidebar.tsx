import {
  History,
  Network,
  LogOut,
  
  Brain,
  User,
  Plus,
  FolderOpen,
  ChevronRight,
  Bot,
  Cpu,
  Settings2,
  Plug,
  Shield,
  LayoutDashboard
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
  useSidebar
} from '@/components/ui/sidebar';
import { Avatar, AvatarFallback,  } from '@/components/ui/avatar';
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
  const { state = 'expanded' } = useSidebar() || {};
  const collapsed = state === 'collapsed';

  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [wsResult, convResult] = await Promise.all([
          workspaceApi.list(),
          conversationsApi.list()
        ]);
        setWorkspaces(Array.isArray(wsResult) ? wsResult : []);
        setConversations(Array.isArray(convResult) ? convResult : []);
      } catch (err) {
        console.error('Error fetching sidebar data:', err);
      }
    };
    fetchData();
  }, []);

  const handleNewChat = () => {
    navigate('/chat');
    window.dispatchEvent(new CustomEvent('new-chat'));
  };

  const userInitials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : user?.email?.slice(0, 2).toUpperCase() || 'U';

  const personalConversations = conversations.filter(c => !c.workspace_id).slice(0, 10);
  const isProfileRoute = location.pathname.startsWith('/profile');

  const profileSidebarItems = [
    { title: 'Profile', url: '/profile', icon: User },
    { title: 'Agents', url: '/profile/agents', icon: Bot },
    { title: 'AI Models', url: '/profile/models', icon: Cpu },
    { title: 'Preferences', url: '/profile/preferences', icon: Settings2 },
    { title: 'Integrations', url: '/profile/integrations', icon: Plug },
    { title: 'Security', url: '/profile/security', icon: Shield },
    { title: 'Settings', url: '/settings', icon: LayoutDashboard }
  ];

  return (
    <Sidebar collapsible="icon" className="font-sans">
      <SidebarHeader className="h-24 justify-center border-b border-white/10 bg-gradient-to-b from-purple-900/35 via-purple-950/20 to-transparent px-4">
        <div className="flex w-full items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-purple-200 via-purple-100 to-fuchsia-100 shadow-[0_12px_28px_-14px_rgba(212,166,255,0.95)]">
            <Network className="h-5 w-5 text-purple-950 stroke-[2.2]" />
          </div>
          {!collapsed && (
            <div className="flex min-w-0 flex-col cursor-pointer" onClick={() => navigate('/')}>
              <span className="truncate text-base font-semibold tracking-tight text-white">NeuroGraph</span>
              <ShinyText text="Context Intelligence" speed={5} className="text-[10px] uppercase tracking-[0.2em] text-purple-200/80" />
            </div>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent className="flex flex-col gap-5 px-3 py-5">
        {isProfileRoute ? (
          <SidebarGroup>
            <SidebarGroupLabel className="text-white/60">Profile Navigation</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {profileSidebarItems.map(item => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton 
                      tooltip={item.title} 
                      onClick={() => navigate(item.url)}
                      isActive={location.pathname === item.url}
                      className="group/menu"
                    >
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
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
                    onClick={handleNewChat}
                    className="gradient-primary text-primary-foreground h-11 rounded-2xl"
                  >
                    <Plus className="h-4 w-4" />
                    <span>New Chat</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroup>

            {workspaces.map(ws => (
              <Collapsible key={ws.id} asChild defaultOpen className="group/collapsible">
                <SidebarGroup>
                  <SidebarGroupLabel>
                    <CollapsibleTrigger className="text-white/60 hover:text-white">
                      <FolderOpen className="mr-2 h-4 w-4" />
                      {ws.name}
                      <ChevronRight className="ml-auto transition-transform group-data-[state=open]/collapsible:rotate-90" />
                    </CollapsibleTrigger>
                  </SidebarGroupLabel>
                  <CollapsibleContent>
                    <SidebarGroupContent>
                      <SidebarMenu>
                        {conversations.filter(c => c.workspace_id === ws.id).map(chat => (
                          <SidebarMenuItem key={chat.id}>
                            <SidebarMenuButton onClick={() => navigate('/chat/' + chat.id)}>
                              <History className="h-4 w-4" />
                              <span className="truncate">{chat.title}</span>
                            </SidebarMenuButton>
                          </SidebarMenuItem>
                        ))}
                      </SidebarMenu>
                    </SidebarGroupContent>
                  </CollapsibleContent>
                </SidebarGroup>
              </Collapsible>
            ))}

            <SidebarGroup>
              <SidebarGroupLabel className="text-white/60">Prev chats</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {personalConversations.map(chat => (
                    <SidebarMenuItem key={chat.id}>
                      <SidebarMenuButton onClick={() => navigate('/chat/' + chat.id)}>
                        <History className="h-4 w-4" />
                        <span className="truncate">{chat.title}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup className="mt-auto">
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton onClick={() => navigate('/memory')} tooltip="MEMORY">
                      <Brain className="h-4 w-4" />
                      <span>MEMORY</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton onClick={() => navigate('/profile')} tooltip="Profile">
                      <User className="h-4 w-4" />
                      <span>Profile</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </>
        )}
      </SidebarContent>

            <SidebarFooter className="border-t border-white/10 p-3">
        <DropdownMenu>
          <DropdownMenuTrigger className="flex w-full outline-none items-center gap-3 rounded-2xl p-2 text-left hover:bg-white/5 transition-colors">
            <Avatar className="h-8 w-8 border border-white/10">
              <AvatarFallback className="bg-purple-900/50 text-xs font-medium text-purple-200">
                {userInitials}
              </AvatarFallback>
            </Avatar>
            {!collapsed && (
              <div className="flex min-w-0 flex-1 flex-col">
                <span className="truncate text-sm font-medium text-white">{user?.full_name || 'User'}</span>
                <span className="truncate text-xs text-white/40">{user?.email}</span>
              </div>
            )}
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56 bg-[#110825] border-white/10" align="end" side="right" sideOffset={12}>
            <DropdownMenuLabel className="text-white/70 font-normal">Account</DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-white/10" />
            <DropdownMenuItem onClick={() => navigate('/profile')} className="text-white hover:bg-white/10">
              <User className="mr-2 h-4 w-4" /> Profile
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => navigate('/settings')} className="text-white hover:bg-white/10">
              <Settings2 className="mr-2 h-4 w-4" /> Settings
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




