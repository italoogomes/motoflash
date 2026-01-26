const { useState, useEffect, useCallback } = React;

// ============ CONFIGURAÇÃO ============
const API_URL = window.location.origin;

// ============ AUTENTICAÇÃO ============

const getToken = () => localStorage.getItem('motoflash_token');
const isLoggedIn = () => !!getToken();

const authFetch = async (url, options = {}) => {
    const token = getToken();
    
    if (!token) {
        window.location.href = '/login';
        throw new Error('Não autenticado');
    }
    
    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };
    
    if (options.body && typeof options.body === 'string') {
        headers['Content-Type'] = 'application/json';
    }
    
    const response = await fetch(url, { ...options, headers });
    
    if (response.status === 401) {
        localStorage.removeItem('motoflash_token');
        localStorage.removeItem('motoflash_user');
        localStorage.removeItem('motoflash_restaurant');
        window.location.href = '/login';
        throw new Error('Sessão expirada');
    }
    
    return response;
};

// Verifica login ao carregar
if (!isLoggedIn()) {
    window.location.href = '/login';
