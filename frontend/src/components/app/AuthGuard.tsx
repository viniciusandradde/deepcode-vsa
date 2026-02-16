"use client";

import React, { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/state/auth-context';
import { Loader2 } from 'lucide-react';

export const AuthGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { isAuthenticated, isLoading } = useAuth();
    const router = useRouter();
    const pathname = usePathname();
    const [isChecking, setIsChecking] = useState(true);

    useEffect(() => {
        // Only redirect after initial loading check is complete
        if (!isLoading) {
            const isLoginPage = pathname === '/login';
            const isRegisterPage = pathname === '/register';

            if (!isAuthenticated && !isLoginPage && !isRegisterPage) {
                router.push('/login');
            } else if (isAuthenticated && (isLoginPage || isRegisterPage)) {
                // If authenticated, redirect to home strictly
                router.push('/');
            } else {
                // Safe to render content
                setIsChecking(false);
            }
        }
    }, [isAuthenticated, isLoading, router, pathname]);

    if (isLoading || isChecking) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-[#050505] text-white">
                <div className="flex flex-col items-center gap-4">
                    <Loader2 className="w-10 h-10 text-brand-primary animate-spin" />
                    <p className="font-mono text-xs uppercase tracking-widest text-white/40">Autenticando...</p>
                </div>
            </div>
        );
    }

    return <>{children}</>;
};
