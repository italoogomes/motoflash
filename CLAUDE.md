# 🤖 Instruções para Claude - MotoFlash

> Este arquivo é lido automaticamente pelo Claude Code no VS Code.

---

## 📋 REGRAS OBRIGATÓRIAS

### 1. Antes de Qualquer Coisa
- **SEMPRE** leia `PROGRESSO_SESSAO.md` para entender onde paramos
- **SEMPRE** consulte a pasta `docs/` antes de fazer mudanças
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

---

## 📂 Documentação do Projeto

| Arquivo | Propósito |
|---------|-----------|
| `PROGRESSO_SESSAO.md` | **CONTEXTO** - Onde paramos, próximos passos |
| `docs/ARQUITETURA.md` | Estrutura do sistema |
| `docs/TESTES.md` | Guia de testes + correções |
| `docs/CI_CD.md` | Pipeline GitHub Actions |
| `CHANGELOG.md` | Histórico de versões |
| `README.md` | Documentação principal |

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

### Comandos Frequentes
```bash
# Rodar testes (SEMPRE deve passar 100%)
cd backend && pytest

# Rodar com detalhes
pytest -v

# Iniciar servidor
uvicorn main:app --reload
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
5. Atualizar documentação
   ↓
6. Atualizar PROGRESSO_SESSAO.md
   ↓
7. Sugerir próximos passos
```

---

**Última atualização:** 2026-01-28
**Versão do projeto:** v1.1.0
