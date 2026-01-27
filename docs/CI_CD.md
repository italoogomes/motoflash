# 🔄 CI/CD - Integração e Deploy Contínuos

**Versão:** 1.0.5
**Data:** 2026-01-26

---

## 📊 Visão Geral

O MotoFlash utiliza **GitHub Actions** para automatizar testes e deploy. Cada commit dispara o pipeline de CI/CD que valida o código antes de permitir merge ou deploy.

---

## 🚀 Pipeline Atual

### Workflow: Tests

**Arquivo:** `.github/workflows/tests.yml`

**Triggers:**
- Push para `main` ou `develop`
- Pull requests para `main`

**Etapas:**

1. **Checkout** - Baixa o código do repositório
2. **Setup Python** - Instala Python 3.11
3. **Cache Dependencies** - Cache de dependências pip (acelera builds)
4. **Install Dependencies** - `pip install -r requirements.txt`
5. **Run Tests** - Executa pytest com 70 testes
6. **Test Summary** - Resumo dos resultados

---

## ✅ Status de Aprovação

### Badge de Status

Adicione ao README.md:

```markdown
![Tests](https://github.com/SEU_USUARIO/motoflash/actions/workflows/tests.yml/badge.svg)
```

### Como Funciona

```
┌─────────────┐
│ Developer   │
│ faz commit  │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ GitHub Actions      │
│ roda testes (70)    │
└──────┬──────────────┘
       │
       ▼
   ┌───────┐
   │ Pass? │
   └───┬───┘
       │
   ┌───┴───┐
   │  Sim  │         │  Não  │
   ▼       │         ▼       │
✅ Merge  │      ❌ Bloqueia │
Permitido │      Merge       │
```

---

## 🔧 Configuração Local

### Instalar Dependências

```bash
cd backend
pip install -r requirements.txt
```

### Rodar Testes Localmente

```bash
cd backend
pytest -v
```

### Simular CI Localmente

```bash
cd backend
export TESTING=true
export GOOGLE_MAPS_API_KEY=test_key
export FIREBASE_PRIVATE_KEY_ID=test_key_id
export FIREBASE_PRIVATE_KEY=test_private_key
export FIREBASE_CLIENT_EMAIL=test@test.com
export FIREBASE_PROJECT_ID=test_project
pytest -v --tb=short
```

---

## 📋 Requisitos para Merge

Para fazer merge de um Pull Request, o código deve:

1. ✅ **Passar em todos os testes** (70/70)
2. ✅ **Não ter erros de sintaxe**
3. ✅ **Tempo de execução < 5 minutos**

---

## 🛡️ Branch Protection Rules

### Configurar no GitHub

1. Vá em **Settings** → **Branches**
2. Clique em **Add rule**
3. Configure:
   - Branch name pattern: `main`
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - Status checks: `test`
   - ✅ Do not allow bypassing the above settings

---

## 🚀 Deploy Automático (Futuro)

### Railway (Planejado)

Adicionar deploy automático após testes passarem:

```yaml
deploy:
  needs: test
  runs-on: ubuntu-latest
  if: github.ref == 'refs/heads/main'
  steps:
    - name: Deploy to Railway
      run: |
        # Deploy automático para Railway
        railway up
```

---

## 📊 Métricas de CI/CD

### Tempo Médio de Build

- **Setup**: ~30 segundos
- **Dependencies**: ~20 segundos (com cache)
- **Tests**: ~50 segundos
- **Total**: ~1-2 minutos

### Taxa de Sucesso

- **Atual**: 100% (70/70 testes passando)
- **Meta**: Manter 100%

---

## 🐛 Troubleshooting

### Erro: "Tests failed"

**Solução:**
1. Rode testes localmente: `pytest -v`
2. Corrija os testes falhando
3. Commit e push novamente

### Erro: "Module not found"

**Solução:**
1. Verifique `requirements.txt` está atualizado
2. Rode `pip freeze > requirements.txt`
3. Commit e push

### Erro: "Rate limit exceeded"

**Solução:**
- GitHub Actions tem limite de 2000 minutos/mês (plano gratuito)
- Otimize testes para rodar mais rápido
- Use cache de dependências

---

## 📚 Próximos Passos

### Fase 2: Observabilidade

- [ ] Cobertura de código com pytest-cov
- [ ] Relatórios de cobertura no GitHub
- [ ] Badges de cobertura

### Fase 3: Deploy Contínuo

- [ ] Deploy automático para Railway
- [ ] Rollback automático se testes falharem
- [ ] Notificações de deploy

### Fase 4: Qualidade de Código

- [ ] Linting com flake8
- [ ] Formatação com black
- [ ] Type checking com mypy

---

## 🔗 Links Úteis

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [pytest Docs](https://docs.pytest.org/)
- [Railway Docs](https://docs.railway.app/)

---

**Última atualização:** 2026-01-26
**Status:** ✅ Ativo e funcionando
