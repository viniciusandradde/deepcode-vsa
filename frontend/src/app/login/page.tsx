"use client";

import React, { useState } from 'react';
import { useAuth } from '@/state/auth-context';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/toast';
import { LogIn, Lock, User as UserIcon, Loader2 } from 'lucide-react';

export default function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const { login } = useAuth();
    const { addToast } = useToast();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);

        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            const res = await fetch('/api/v1/auth/login', {
                method: 'POST',
                body: formData,
            });

            if (!res.ok) {
                const error = await res.json();
                throw new Error(error.detail || 'Falha na autenticação');
            }

            const { access_token } = await res.json();

            // Get user info
            const userRes = await fetch('/api/v1/auth/me', {
                headers: {
                    'Authorization': `Bearer ${access_token}`,
                },
            });

            if (!userRes.ok) {
                throw new Error('Falha ao obter dados do usuário');
            }

            const userData = await userRes.json();
            login(access_token, userData);
            addToast('Bem-vindo ao DeepCode VSA', 'success');
        } catch (error: any) {
            addToast(error.message, 'error');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-[#050505]">
            {/* Background Decorative Elements */}
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-brand-primary/10 blur-[120px] rounded-full" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-brand-secondary/10 blur-[120px] rounded-full" />

            <div className="w-full max-w-md relative z-10">
                <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-8 rounded-3xl shadow-2xl">
                    <div className="text-center mb-10">
                        <div className="inline-flex items-center justify-center w-16 h-16 bg-brand-primary/20 rounded-2xl mb-4 border border-brand-primary/30">
                            <LogIn className="w-8 h-8 text-brand-primary" />
                        </div>
                        <h1 className="font-sans text-3xl font-bold text-white tracking-tight">DeepCode <span className="text-brand-primary">VSA</span></h1>
                        <p className="text-white/50 mt-2 font-mono text-sm uppercase tracking-widest">Virtual Support Agent</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="space-y-2">
                            <label className="text-xs font-mono text-white/40 ml-1 uppercase tracking-wider">Usuário</label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                    <UserIcon className="h-5 w-5 text-white/20 group-focus-within:text-brand-primary transition-colors" />
                                </div>
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="block w-full pl-12 pr-4 py-3 bg-black/40 border border-white/10 rounded-xl text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-primary/50 focus:border-brand-primary transition-all font-sans"
                                    placeholder="Seu nome de usuário"
                                    required
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-mono text-white/40 ml-1 uppercase tracking-wider">Senha</label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                    <Lock className="h-5 w-5 text-white/20 group-focus-within:text-brand-primary transition-colors" />
                                </div>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="block w-full pl-12 pr-4 py-3 bg-black/40 border border-white/10 rounded-xl text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-primary/50 focus:border-brand-primary transition-all font-sans"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                        </div>

                        <Button
                            type="submit"
                            disabled={isSubmitting}
                            className="w-full py-6 bg-brand-primary hover:bg-brand-primary-hover text-white rounded-xl font-bold text-lg shadow-lg shadow-brand-primary/20 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:scale-100"
                        >
                            {isSubmitting ? (
                                <Loader2 className="w-5 h-5 animate-spin mr-2" />
                            ) : null}
                            {isSubmitting ? 'Autenticando...' : 'Entrar'}
                        </Button>
                    </form>

                    <div className="mt-8 text-center pt-6 border-t border-white/5">
                        <p className="text-white/40 text-sm">
                            Não tem uma conta?{' '}
                            <a href="/register" className="text-brand-primary hover:text-brand-primary-hover font-bold ml-1 transition-colors">
                                Contatar TI
                            </a>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
