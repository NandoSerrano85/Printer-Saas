// stores/appStore.js
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useAppStore = create(
  persist(
    (set, get) => ({
      // User state
      user: null,
      isAuthenticated: false,
      
      // Shop data
      shopData: null,
      listings: [],
      
      // UI state
      sidebarOpen: true,
      currentPage: 'dashboard',
      
      // Actions
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setShopData: (shopData) => set({ shopData }),
      setListings: (listings) => set({ listings }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setCurrentPage: (page) => set({ currentPage: page }),
      
      // Reset state on logout
      logout: () => set({
        user: null,
        isAuthenticated: false,
        shopData: null,
        listings: [],
      }),
    }),
    {
      name: 'etsy-automater-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
);