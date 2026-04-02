import { useEffect } from 'react';

interface SeoConfig {
  title: string;
  description: string;
  robots: 'index,follow' | 'noindex,nofollow';
}

const LOGO_PATH = '/logo.svg';
const DEFAULT_THEME_COLOR = '#050110';
const FALLBACK_SITE_URL = 'https://neurograph-ai.vercel.app';
const configuredSiteUrl = (import.meta.env.VITE_SITE_URL as string | undefined)?.trim();
const SITE_URL = (configuredSiteUrl || FALLBACK_SITE_URL).replace(/\/+$/, '');

const DEFAULT_SEO: SeoConfig = {
  title: 'NeuroGraph | Agentic Context Engine',
  description:
    'NeuroGraph is a neural-inspired context engine for building, traversing, and explaining graph memory with AI-powered reasoning.',
  robots: 'index,follow',
};

const ROUTE_SEO: Array<{ match: (pathname: string) => boolean; config: SeoConfig }> = [
  {
    match: (pathname) => pathname === '/',
    config: {
      title: 'NeuroGraph | Neural-inspired Memory System',
      description:
        'Build, traverse, and visualize explainable memory graphs with NeuroGraph, an AI-first context engine for intelligent workflows.',
      robots: 'index,follow',
    },
  },
  {
    match: (pathname) => pathname === '/login',
    config: {
      title: 'Login | NeuroGraph',
      description:
        'Sign in to NeuroGraph to access your AI workspace, graph memory, and reasoning-driven chat experience.',
      robots: 'noindex,nofollow',
    },
  },
  {
    match: (pathname) => pathname === '/signup',
    config: {
      title: 'Sign Up | NeuroGraph',
      description:
        'Create your NeuroGraph account to start building neural-inspired graph memory and AI-enhanced context workflows.',
      robots: 'noindex,nofollow',
    },
  },
  {
    match: (pathname) => pathname === '/404',
    config: {
      title: '404 | NeuroGraph',
      description: 'The requested NeuroGraph page could not be found.',
      robots: 'noindex,nofollow',
    },
  },
  {
    match: (pathname) => pathname.startsWith('/chat'),
    config: {
      title: 'Chat Workspace | NeuroGraph',
      description:
        'Use NeuroGraph chat to reason across your memory graph with source-backed responses and adaptive context retrieval.',
      robots: 'noindex,nofollow',
    },
  },
  {
    match: (pathname) => pathname.startsWith('/graph'),
    config: {
      title: 'Knowledge Graph | NeuroGraph',
      description:
        'Explore entities, relationships, and centrality in NeuroGraph’s live knowledge graph visualization workspace.',
      robots: 'noindex,nofollow',
    },
  },
  {
    match: (pathname) => pathname.startsWith('/memory'),
    config: {
      title: 'Memory Canvas | NeuroGraph',
      description:
        'Manage and inspect layered memory nodes, confidence, and graph connections in NeuroGraph Memory Canvas.',
      robots: 'noindex,nofollow',
    },
  },
  {
    match: (pathname) => pathname.startsWith('/profile') || pathname.startsWith('/settings'),
    config: {
      title: 'Profile & Settings | NeuroGraph',
      description:
        'Customize models, preferences, and account configuration for your NeuroGraph intelligence workspace.',
      robots: 'noindex,nofollow',
    },
  },
  {
    match: (pathname) => pathname.startsWith('/integrations'),
    config: {
      title: 'Integrations | NeuroGraph',
      description:
        'Connect external tools and data sources to NeuroGraph for richer context, memory synchronization, and automation.',
      robots: 'noindex,nofollow',
    },
  },
  {
    match: (pathname) => pathname.startsWith('/admin'),
    config: {
      title: 'Admin Dashboard | NeuroGraph',
      description:
        'Monitor platform-level metrics, graph activity, and memory system status from the NeuroGraph admin dashboard.',
      robots: 'noindex,nofollow',
    },
  },
];

const setMeta = (attribute: 'name' | 'property', key: string, content: string) => {
  let element = document.head.querySelector(`meta[${attribute}="${key}"]`) as HTMLMetaElement | null;
  if (!element) {
    element = document.createElement('meta');
    element.setAttribute(attribute, key);
    document.head.appendChild(element);
  }
  element.setAttribute('content', content);
};

const setCanonical = (href: string) => {
  let link = document.head.querySelector('link[rel="canonical"]') as HTMLLinkElement | null;
  if (!link) {
    link = document.createElement('link');
    link.setAttribute('rel', 'canonical');
    document.head.appendChild(link);
  }
  link.setAttribute('href', href);
};

const resolveSeo = (pathname: string): SeoConfig =>
  ROUTE_SEO.find((route) => route.match(pathname))?.config ?? DEFAULT_SEO;

export const applySeoForPath = (pathname: string) => {
  const seo = resolveSeo(pathname);
  const path = pathname.startsWith('/') ? pathname : `/${pathname}`;
  const canonicalUrl = new URL(path, SITE_URL).toString();
  const imageUrl = new URL(LOGO_PATH, SITE_URL).toString();

  document.title = seo.title;

  setMeta('name', 'description', seo.description);
  setMeta('name', 'robots', seo.robots);
  setMeta('name', 'theme-color', DEFAULT_THEME_COLOR);
  setMeta('name', 'application-name', 'NeuroGraph');
  setMeta('name', 'twitter:card', 'summary_large_image');
  setMeta('name', 'twitter:title', seo.title);
  setMeta('name', 'twitter:description', seo.description);
  setMeta('name', 'twitter:image', imageUrl);
  setMeta('name', 'twitter:image:alt', 'NeuroGraph logo');

  setMeta('property', 'og:type', 'website');
  setMeta('property', 'og:site_name', 'NeuroGraph');
  setMeta('property', 'og:title', seo.title);
  setMeta('property', 'og:description', seo.description);
  setMeta('property', 'og:url', canonicalUrl);
  setMeta('property', 'og:image', imageUrl);
  setMeta('property', 'og:image:alt', 'NeuroGraph logo');

  setCanonical(canonicalUrl);
};

export const useRouteSeo = (pathname: string) => {
  useEffect(() => {
    applySeoForPath(pathname);
  }, [pathname]);
};
