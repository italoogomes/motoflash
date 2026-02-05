# 🤖 Instruções para Claude - MotoFlash

> Este arquivo é lido automaticamente pelo Claude Code no VS Code.

---

## 📋 REGRAS OBRIGATÓRIAS

### 1. Antes de Qualquer Coisa
- **SEMPRE** leia `PROGRESSO_ATUAL.md` para entender o estado do projeto
- **SEMPRE** consulte `docs/` antes de modificar código
- **SEMPRE** pergunte qual tarefa o usuário quer continuar

### 2. Durante o Trabalho
- Faça **um passo de cada vez** e confirme antes de prosseguir
- **Documente tudo** que fizer em `docs/` e `PROGRESSO_ATUAL.md`
- Siga o estilo dos arquivos existentes
- Teste isolamento multi-tenant (CRÍTICO 🔒)

### 3. Sobre Tokens/Contexto
- **AVISE** quando perceber que a conversa está ficando longa
- **SUGIRA** salvar o progresso no `PROGRESSO_ATUAL.md` antes de acabar
- **NUNCA** deixe trabalho sem documentar antes de encerrar

### 4. Ao Finalizar Qualquer Tarefa
- Atualize `PROGRESSO_ATUAL.md` com o que foi feito
- Atualize `CHANGELOG.md` se houve mudança de versão
- Rode os testes: `pytest` (deve passar 100%)
- Liste os próximos passos claros

### 5. Documentação Obrigatória (CRÍTICO 📝)

**Toda criação ou modificação DEVE ser documentada seguindo o padrão da pasta `docs/`.**

#### Quando criar/modificar código:
| O que mudou | Onde documentar |
|-------------|-----------------|
| Novo endpoint | `docs/API_ENDPOINTS.md` |
| Nova funcionalidade | `docs/ARQUITETURA.md` + `docs/FLUXOS.md` |
| Novo teste | `docs/TESTES.md` |
| Mudança no frontend | `docs/FRONTEND_BACKEND.md` |
| Novo serviço/módulo | `docs/ARQUITETURA.md` |
| Correção de bug | `docs/TESTES.md` (seção correções) |
| Qualquer mudança | `PROGRESSO_ATUAL.md` + `CHANGELOG.md` |

---

## 📂 Documentação do Projeto

| Arquivo | Propósito | Quando Atualizar |
|---------|-----------|------------------|
| `PROGRESSO_ATUAL.md` | **CONTEXTO** - Estado atual do projeto (~100 linhas) | Sempre, ao final de cada tarefa |
| `docs/PROGRESSO_HISTORICO.md` | Timeline condensada de todas as versões | Nova versão lançada |
| `CHANGELOG.md` | Histórico de versões | A cada nova versão |
| `README.md` | Documentação principal | Mudanças significativas |

### Pasta `docs/` - Documentação Técnica

| Arquivo | Propósito |
|---------|-----------|
| `docs/API_ENDPOINTS.md` | Referência de endpoints |
| `docs/ARQUITETURA.md` | Visão geral do sistema |
| `docs/ARQUITETURA_MODULAR.md` | Estrutura do frontend |
| `docs/FLUXOS.md` | Fluxos de dados |
| `docs/FRONTEND_BACKEND.md` | Integração front/back |
| `docs/TESTES.md` | Guia de testes |
| `docs/CI_CD.md` | Pipeline GitHub Actions |
| `docs/FIREBASE.md` | Push notifications |
| `docs/RASTREAMENTO.md` | Sistema de rastreamento |
| `docs/PROGRESSO_HISTORICO.md` | Timeline completa do desenvolvimento |

---

## 🚀 Como Iniciar uma Sessão

```
Oi Claude! Leia PROGRESSO_ATUAL.md e me diga onde paramos.
Quero continuar com [descrição da tarefa].
```

### Para histórico detalhado (se precisar):
```
Claude, leia docs/PROGRESSO_HISTORICO.md para ver como resolvemos [problema].
```

---

## ⚠️ Avisos de Contexto Longo

Quando a conversa estiver longa, Claude deve:

1. **Avisar proativamente:**
   > "⚠️ Estamos com bastante contexto acumulado. Sugiro salvarmos o progresso antes de continuar."

2. **Salvar o estado atual:**
   - Atualizar `PROGRESSO_ATUAL.md` (manter ≤100 linhas!)
   - Adicionar entrada em `docs/PROGRESSO_HISTORICO.md` se nova versão
   - Atualizar `CHANGELOG.md`

3. **IMPORTANTE:** `PROGRESSO_ATUAL.md` deve ter no máximo ~100 linhas. Se crescer demais, mova detalhes para `docs/PROGRESSO_HISTORICO.md`.

---

## 🔧 Padrões do Projeto

### Tecnologias
- Backend: Python FastAPI + PostgreSQL + SQLAlchemy
- Frontend: React 18 (CDN) + Tailwind CSS + Leaflet.js
- Testes: Pytest (deve passar 100%)
- CI/CD: GitHub Actions
- Deploy: Railway (produção)

### 🚀 Ambiente de Produção (Railway)

**O app NÃO roda local, está em produção no Railway:**

| Recurso | URL |
|---------|-----|
| **Login** | https://motoflash-production.up.railway.app/login |
| **App Motoboy** | https://motoflash-production.up.railway.app/motoboy |

**Importante:**
- ⚠️ **NÃO tente rodar `uvicorn` localmente** - use o Railway
- ✅ Testes rodam local com `pytest` (usa SQLite em memória)
- ✅ Para testar endpoints, use a URL de produção
- ✅ Deploy automático via push para `main`

### Comandos Frequentes
```bash
# Rodar testes (SEMPRE deve passar 100%)
cd backend && pytest

# Rodar com detalhes
pytest -v
```

### Regras de Código
- Multi-tenant: SEMPRE filtrar por `restaurant_id`
- Imports: Seguir padrão dos arquivos existentes
- Testes: Criar para toda feature nova
- Documentação: Atualizar sempre

---

## 🎯 Fluxo de Trabalho

```
1. Ler PROGRESSO_ATUAL.md
   ↓
2. Ler docs/ relevantes
   ↓
3. Fazer tarefa (um passo por vez)
   ↓
4. Rodar testes (pytest)
   ↓
5. Atualizar PROGRESSO_ATUAL.md (manter ≤100 linhas!)
   ↓
6. Atualizar docs/ e CHANGELOG.md se necessário
   ↓
7. Sugerir próximos passos
```

---

**Última atualização:** 2026-02-05
**Versão do projeto:** v1.5.0