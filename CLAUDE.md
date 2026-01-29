# 🤖 Instruções para Claude - MotoFlash

> Este arquivo é lido automaticamente pelo Claude Code no VS Code.

---

## 📋 REGRAS OBRIGATÓRIAS

### 1. Antes de Qualquer Coisa
- **SEMPRE** leia `PROGRESSO_SESSAO.md` para entender onde paramos
- **SEMPRE** consulte `docs/` antes de modificar código
- **SEMPRE** pergunte qual tarefa o usuário quer continuar

### 2. Durante o Trabalho
- Faça **um passo de cada vez** e confirme antes de prosseguir
- **Documente tudo** que fizer em `docs/` e `PROGRESSO_SESSAO.md`
- Siga o estilo dos arquivos existentes
- Teste isolamento multi-tenant (CRÍTICO 🔒)

### 3. Sobre Tokens/Contexto
- **AVISE** quando perceber que a conversa está ficando longa
- **SUGIRA** salvar o progresso no `PROGRESSO_SESSAO.md` antes de acabar
- **NUNCA** deixe trabalho sem documentar antes de encerrar

### 4. Ao Finalizar Qualquer Tarefa
- Atualize `PROGRESSO_SESSAO.md` com o que foi feito
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
| Qualquer mudança | `PROGRESSO_SESSAO.md` + `CHANGELOG.md`|

#### Padrão de Documentação MotoFlash:

```markdown
# 📚 Título do Documento

**Versão:** x.x.x
**Data:** YYYY-MM-DD
**Status:** ✅ ou 🔄

---

## 📊 Seção Principal

### Subseção
- Item 1
- Item 2

#### Se for correção/mudança:
- **Problema**: O que estava errado
- **Solução**: O que foi feito
- **Motivo/Aprendizado**: Por que essa solução

---
```

#### Regras de Formatação:
- ✅ Usar emojis nos títulos (📚 📊 🔧 ✅ 🔄 ⭐ 🎯)
- ✅ Tabelas para resumos e comparações
- ✅ Blocos de código com linguagem especificada
- ✅ Separadores `---` entre seções
- ✅ Estrutura Problema → Solução → Motivo para correções
- ✅ Versão e data no cabeçalho
- ❌ NUNCA deixar mudança sem documentar

---

## 📂 Documentação do Projeto

| Arquivo | Propósito | Quando Atualizar |
|---------|-----------|------------------|
| `PROGRESSO_SESSAO.md` | **CONTEXTO** - Onde paramos | Sempre, ao final de cada tarefa |
| `CHANGELOG.md` | Histórico de versões | A cada nova versão |
| `README.md` | Documentação principal | Mudanças significativas |

### Pasta `docs/` - Documentação Técnica

| Arquivo | Propósito | Quando Atualizar |
|---------|-----------|------------------|
| `docs/README.md` | Índice da documentação | Novo documento criado |
| `docs/API_ENDPOINTS.md` | Referência de endpoints | Novo/modificado endpoint |
| `docs/ARQUITETURA.md` | Visão geral do sistema | Nova feature/módulo |
| `docs/ARQUITETURA_MODULAR.md` | Estrutura do frontend | Mudança no frontend |
| `docs/FLUXOS.md` | Fluxos de dados | Nova funcionalidade |
| `docs/FRONTEND_BACKEND.md` | Integração front/back | Mudança em páginas |
| `docs/TESTES.md` | Guia de testes | Novo teste/correção |
| `docs/CI_CD.md` | Pipeline GitHub Actions | Mudança no CI/CD |
| `docs/FIREBASE.md` | Push notifications | Mudança em notificações |

---

## 🚀 Como Iniciar uma Sessão

```
Oi Claude! Leia PROGRESSO_SESSAO.md e me diga onde paramos.
Quero continuar com [descrição da tarefa].
```

### Ou para tarefas específicas:

```
Claude, leia docs/ARQUITETURA.md e me ajude a [tarefa].
```

```
Claude, rode os testes e me diga se algo quebrou.
```

---

## ⚠️ Avisos de Contexto Longo

Quando a conversa estiver longa, Claude deve:

1. **Avisar proativamente:**
   > "⚠️ Estamos com bastante contexto acumulado. Sugiro salvarmos o progresso no PROGRESSO_SESSAO.md antes de continuar."

2. **Salvar o estado atual:**
   - Atualizar seção "✅ O QUE JÁ FOI FEITO"
   - Atualizar seção "🎯 PRÓXIMOS PASSOS"
   - Atualizar "Mensagem para o Próximo Claude"

3. **Dar comando para continuar:**
   > "Para continuar em nova sessão, diga: 'Claude, leia PROGRESSO_SESSAO.md e continue de onde paramos.'"

---

## 🔧 Padrões do Projeto

### Tecnologias
- Backend: Python FastAPI + SQLite + SQLModel
- Frontend: React 18 (CDN) + Tailwind CSS
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

# Ver logs do Railway (se CLI instalado)
railway logs
```

### Regras de Código
- Multi-tenant: SEMPRE filtrar por `restaurant_id`
- Imports: Seguir padrão dos arquivos existentes
- Testes: Criar para toda feature nova
- Documentação: Atualizar sempre

---

## 🎯 Fluxo de Trabalho Ideal

```
1. Ler PROGRESSO_SESSAO.md
   ↓
2. Ler docs/ relevantes
   ↓
3. Fazer tarefa (um passo por vez)
   ↓
4. Rodar testes (pytest)
   ↓
5. DOCUMENTAR (ver checklist abaixo)
   ↓
6. Atualizar PROGRESSO_SESSAO.md
   ↓
7. Sugerir próximos passos
```

### ✅ Checklist de Documentação (OBRIGATÓRIO)

Antes de finalizar qualquer tarefa, verificar:

- [ ] `PROGRESSO_SESSAO.md` atualizado com o que foi feito
- [ ] `CHANGELOG.md` atualizado (se nova versão)
- [ ] Documento correto em `docs/` atualizado (ver tabela acima)
- [ ] Versão e data atualizados nos arquivos modificados
- [ ] Código documentado com comentários quando necessário

**NUNCA encerrar sessão sem documentar!**

---

**Última atualização:** 2026-01-28
**Versão do projeto:** v1.1.0