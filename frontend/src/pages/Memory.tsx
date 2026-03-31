import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { memoryApi } from '@/services/api';
import { useNavigate } from 'react-router-dom';
import GraphVisualization from '@/components/graph/GraphVisualization';
import {
  Brain,
  Users,
  Globe,
  Plus,
  Search,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Clock,
  Trash2,
  Network,
  RefreshCw,
} from 'lucide-react';

interface MemoryItem {
  id: string;
  content: string;
  layer: string;
  confidence: number;
  score: number;
  created_at: string;
}

interface MemoryCounts {
  personal: number;
  workspace: number;
  global: number;
  total: number;
}

export default function Memory() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('personal');
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [counts, setCounts] = useState<MemoryCounts>({ personal: 0, workspace: 0, global: 0, total: 0 });
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [newMemory, setNewMemory] = useState('');
  const [isStoring, setIsStoring] = useState(false);
  const [storeSuccess, setStoreSuccess] = useState(false);
  const [error, setError] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadCounts = useCallback(async () => {
    try {
      const result = await memoryApi.getCount() as MemoryCounts;
      setCounts(result);
    } catch (err) {
      console.error('Failed to load counts:', err);
    }
  }, []);

  const loadMemories = useCallback(async (query = '') => {
    setIsLoading(true);
    setError('');
    try {
      if (activeTab === 'graph') { setMemories([]); setIsLoading(false); return; }
      if (query.trim()) {
        // Search mode
        const result = await memoryApi.recall(query, 50, [activeTab === 'workspace' ? 'tenant' : activeTab]) as MemoryItem[];
        setMemories(Array.isArray(result) ? result : []);
      } else {
        // List mode - use the list endpoint
        const result = await memoryApi.list(activeTab as 'personal' | 'workspace' | 'global', 100, 0) as MemoryItem[];
        setMemories(Array.isArray(result) ? result : []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load memories');
      setMemories([]);
    } finally {
      setIsLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    loadMemories(searchQuery);
    loadCounts();
  }, [activeTab, loadMemories, loadCounts, searchQuery]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadMemories(searchQuery);
  };

  const handleStore = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMemory.trim()) return;
    
    setIsStoring(true);
    setError('');
    setStoreSuccess(false);
    
    try {
      await memoryApi.store(newMemory, activeTab as 'personal' | 'workspace' | 'global');
      setStoreSuccess(true);
      setNewMemory('');
      setTimeout(() => {
        loadMemories(searchQuery);
        loadCounts();
        setStoreSuccess(false);
      }, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to store memory');
    } finally {
      setIsStoring(false);
    }
  };

  const handleDelete = async (memoryId: string) => {
    setDeletingId(memoryId);
    try {
      await memoryApi.delete(memoryId);
      setMemories(prev => prev.filter(m => m.id !== memoryId));
      loadCounts();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete memory');
    } finally {
      setDeletingId(null);
    }
  };

  const getLayerIcon = (layer: string) => {
    switch (layer) {
      case 'personal': return <Brain className="w-4 h-4" />;
      case 'tenant':
      case 'workspace': return <Users className="w-4 h-4" />;
      case 'global': return <Globe className="w-4 h-4" />;
      default: return <Brain className="w-4 h-4" />;
    }
  };

  const getLayerColor = (layer: string) => {
    switch (layer) {
      case 'personal': return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
      case 'tenant':
      case 'workspace': return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
      case 'global': return 'bg-green-500/20 text-green-300 border-green-500/30';
      default: return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="h-full w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Memory Store</h2>
          <p className="text-white/60 text-sm mt-1">
            {counts.total} memories across all layers
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => { loadMemories(searchQuery); loadCounts(); }}
            className="border-white/20 text-white hover:bg-white/10"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/graph')}
            className="border-purple-500/30 text-purple-300 hover:bg-purple-500/10"
          >
            <Network className="w-4 h-4 mr-2" />
            Knowledge Graph
          </Button>
        </div>
      </div>

      {/* Memory Layer Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="flex w-full max-w-2xl bg-white/5 border border-white/10 p-1 rounded-xl">
          <TabsTrigger
            value="personal"
            className="flex-1 data-[state=active]:bg-purple-500/20 data-[state=active]:text-purple-300 rounded-lg"
          >
            <Brain className="w-4 h-4 mr-2" />
            Personal
            <Badge variant="outline" className="ml-2 text-xs border-purple-500/30 text-purple-300">{counts.personal}</Badge>
          </TabsTrigger>
          <TabsTrigger
            value="workspace"
            className="flex-1 data-[state=active]:bg-blue-500/20 data-[state=active]:text-blue-300 rounded-lg"
          >
            <Users className="w-4 h-4 mr-2" />
            Workspace
            <Badge variant="outline" className="ml-2 text-xs border-blue-500/30 text-blue-300">{counts.workspace}</Badge>
          </TabsTrigger>
          <TabsTrigger
            value="global"
            className="flex-1 data-[state=active]:bg-green-500/20 data-[state=active]:text-green-300 rounded-lg"
          >
            <Globe className="w-4 h-4 mr-2" />
            Global
            <Badge variant="outline" className="ml-2 text-xs border-green-500/30 text-green-300">{counts.global}</Badge>
          </TabsTrigger>
          <TabsTrigger
            value="graph"
            className="flex-1 data-[state=active]:bg-orange-500/20 data-[state=active]:text-orange-300 rounded-lg"
          >
            <Network className="w-4 h-4 mr-2" />
            Knowledge Graph
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-6 space-y-6">
          {/* Add Memory Form */}
          <Card className="border-white/10 bg-white/5 backdrop-blur-md">
            <CardHeader className="pb-4">
              <CardTitle className="text-white text-lg flex items-center gap-2">
                <Plus className="w-5 h-5" />
                Add New Memory
              </CardTitle>
              <CardDescription className="text-white/60">
                Store new knowledge in your {activeTab} memory layer
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleStore} className="flex gap-3">
                <Input
                  value={newMemory}
                  onChange={(e) => setNewMemory(e.target.value)}
                  placeholder="Enter a fact, relationship, or piece of knowledge..."
                  className="flex-1 bg-black/30 border-white/10 text-white placeholder:text-white/40"
                  disabled={isStoring}
                />
                <Button
                  type="submit"
                  disabled={isStoring || !newMemory.trim()}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white"
                >
                  {isStoring ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : storeSuccess ? (
                    <CheckCircle2 className="w-4 h-4" />
                  ) : (
                    <Plus className="w-4 h-4" />
                  )}
                  <span className="ml-2">Store</span>
                </Button>
              </form>
              {storeSuccess && (
                <p className="mt-2 text-sm text-green-400 flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4" />
                  Memory stored successfully!
                </p>
              )}
            </CardContent>
          </Card>

          {/* Search */}
          <Card className="border-white/10 bg-white/5 backdrop-blur-md">
            <CardHeader className="pb-4">
              <CardTitle className="text-white text-lg flex items-center gap-2">
                <Search className="w-5 h-5" />
                Search Memories
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSearch} className="flex gap-3">
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search for memories... (leave empty to show all)"
                  className="flex-1 bg-black/30 border-white/10 text-white placeholder:text-white/40"
                />
                <Button
                  type="submit"
                  disabled={isLoading}
                  variant="outline"
                  className="border-white/20 text-white hover:bg-white/10"
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Search className="w-4 h-4" />
                  )}
                  <span className="ml-2">Search</span>
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Error Display */}
          {error && (
            <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-200 text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          {/* Memories List */}
          <div className="space-y-3">
            <h3 className="text-white/80 font-medium flex items-center gap-2">
              {getLayerIcon(activeTab)}
              {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Memories
              <Badge variant="outline" className="ml-2 text-white/60 border-white/20">
                {memories.length} shown
              </Badge>
            </h3>

            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
              </div>
            ) : memories.length === 0 ? (
              <Card className="border-white/10 bg-white/5 backdrop-blur-md">
                <CardContent className="py-12 text-center">
                  <Brain className="w-12 h-12 mx-auto text-white/20 mb-4" />
                  <p className="text-white/60">No memories found in this layer</p>
                  <p className="text-white/40 text-sm mt-1">
                    Add some knowledge using the form above
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {memories.map((memory) => (
                  <Card
                    key={memory.id}
                    className="border-white/10 bg-white/5 backdrop-blur-md hover:bg-white/8 transition-colors group"
                  >
                    <CardContent className="py-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <p className="text-white">{memory.content}</p>
                          <div className="flex items-center gap-3 mt-3 flex-wrap">
                            <Badge className={getLayerColor(memory.layer)}>
                              {getLayerIcon(memory.layer)}
                              <span className="ml-1">{memory.layer === 'tenant' ? 'workspace' : memory.layer}</span>
                            </Badge>
                            <span className="text-white/40 text-xs flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {formatDate(memory.created_at)}
                            </span>
                            <span className="text-white/40 text-xs">
                              Confidence: {(memory.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(memory.id)}
                          disabled={deletingId === memory.id}
                          className="opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-300 hover:bg-red-500/10"
                        >
                          {deletingId === memory.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Trash2 className="w-4 h-4" />
                          )}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </TabsContent>
              <TabsContent value="graph" className="mt-6 flex-1 h-[600px] rounded-2xl border border-white/10 bg-[#0d0620]/65 overflow-hidden">
          <GraphVisualization />
        </TabsContent>
      </Tabs>
    </div>
  );
}



