"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { AUTH_EVENT_LOGOUT } from '@/lib/api-client';

interface User {
    id: number;
    username: string;
    email: string | null;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (token: string, user: User) => void;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();

    const validateSession = useCallback(async (storedToken: string) => {
        try {
            const res = await fetch('/api/v1/auth/me', {
                headers: {
                    'Authorization': `Bearer ${storedToken}`
                }
            });

            if (res.ok) {
                const userData = await res.json();
                setUser(userData);
                setToken(storedToken);
                // Ensure cookie is set for middleware
                document.cookie = "vsa_auth=true; path=/; max-age=86400; SameSite=Lax";
            } else {
                throw new Error('Session invalid');
            }
        } catch (error) {
            console.error("Session validation failed:", error);
            logout();
        } finally {
            setIsLoading(false);
        }
    }, []);

    const logout = useCallback(() => {
        localStorage.removeItem('vsa_token');
        localStorage.removeItem('vsa_user');
        document.cookie = "vsa_auth=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        setToken(null);
        setUser(null);
        router.push('/login');
    }, [router]);

    useEffect(() => {
        const storedToken = localStorage.getItem('vsa_token');
        if (storedToken) {
            validateSession(storedToken);
        } else {
            setIsLoading(false);
        }

        const handleAuthLogout = () => logout();
        window.addEventListener(AUTH_EVENT_LOGOUT, handleAuthLogout);

        return () => {
            window.removeEventListener(AUTH_EVENT_LOGOUT, handleAuthLogout);
        };
    }, [validateSession, logout]);

    const login = useCallback((newToken: string, newUser: User) => {
        localStorage.setItem('vsa_token', newToken);
        localStorage.setItem('vsa_user', JSON.stringify(newUser));
        document.cookie = "vsa_auth=true; path=/; max-age=86400; SameSite=Lax";
        setToken(newToken);
        setUser(newUser);
        router.push('/');
    }, [router]);

    return (
        <AuthContext.Provider
            value={{
                user,
                token,
                isAuthenticated: !!token,
                isLoading,
                login,
                logout,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
