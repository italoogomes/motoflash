# 🏍️ MotoFlash - Sistema de Entregas Inteligente

**Versão:** 1.0.2 (Arquitetura Modular + Testes)
**Deploy:** Railway

Sistema de despacho inteligente para restaurantes com entregadores próprios.

## ⭐ Novidades v1.0.2

- **Testes de Pedidos:** 16 testes cobrindo criação, listagem, QR Code e transições de status
- **Cobertura Expandida:** 24 testes no total (autenticação + pedidos)

## ⭐ Novidades v1.0.1

- **Testes Automatizados:** Pytest configurado com 8 testes de autenticação
- **Documentação de Testes:** Guia completo em `docs/TESTES.md`

## ⭐ Novidades v1.0.0

- **Arquitetura Modular:** Dashboard refatorado de 3732 → 36 linhas
- **Performance:** Cache de CSS e JS separados
- **Manutenção:** Código organizado por responsabilidade
- **SPA Mantida:** Navegação suave sem recarregar página

## 📁 Estrutura do Projeto

```
motoflash/
├── backend/
│   ├── main.py           # API FastAPI
│   ├── database.py       # Configuração SQLite
│   ├── models.py         # Modelos do banco
│   ├── requirements.txt  # Dependências Python
│   ├── routers/          # Rotas da API
│   ├── services/         # Lógica de negócio
│   ├── static/           # Frontend (Arquitetura Modular)
│   │   ├── index.html    # Dashboard (36 linhas)
│   │   ├── motoboy.html  # App PWA
│   │   ├── css/
│   │   │   └── dashboard.css
│   │   └── js/
│   │       ├── utils/helpers.js
│   │       ├── components.js
│   │       └── app.js
│   └── uploads/          # Imagens
├── docs/                 # Documentação completa
│   ├── ARQUITETURA.md
│   ├── ARQUITETURA_MODULAR.md ⭐ NOVO
│   ├── API_ENDPOINTS.md
│   ├── FLUXOS.md
│   ├── FRONTEND_BACKEND.md
│   └── FIREBASE.md
└── RAILWAY_SETUP.md
```

## 🚀 Deploy no Render (Passo a Passo)

### 1. Crie uma conta no GitHub (se não tiver)
- Acesse: https://github.com
- Crie uma conta gratuita

### 2. Crie um repositório no GitHub
- Clique em "New repository"
- Nome: `motoflash`
- Marque "Private" (privado)
- Clique em "Create repository"

### 3. Faça upload dos arquivos
- Na página do repositório, clique em "uploading an existing file"
- Arraste TODOS os arquivos desta pasta
- Clique em "Commit changes"

### 4. Crie uma conta no Render
- Acesse: https://render.com
- Clique em "Get Started for Free"
- Faça login com sua conta GitHub

### 5. Crie o Web Service
- No dashboard do Render, clique em "New +"
- Selecione "Web Service"
- Conecte ao seu repositório `motoflash`
- Configure:
  - **Name**: motoflash
  - **Region**: Oregon (US West)
  - **Branch**: main
  - **Root Directory**: backend
  - **Runtime**: Python 3
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 6. Adicione o Disco Persistente
- Na página do serviço, vá em "Disks"
- Clique em "Add Disk"
- **Name**: motoflash-data
- **Mount Path**: /data
- **Size**: 1 GB

### 7. Adicione as Variáveis de Ambiente
- Vá em "Environment"
- Adicione:
  - `DATA_DIR` = `/data`
  - `PYTHON_VERSION` = `3.11`

### 8. Deploy!
- Clique em "Create Web Service"
- Aguarde o deploy (cerca de 2-5 minutos)
- Quando aparecer "Live", seu app está no ar! 🎉

## 🌐 Acessando o App

Após o deploy, você terá uma URL tipo:
- `https://motoflash-xxxx.onrender.com`

Páginas:
- `/` - Dashboard principal
- `/motoboy` - App do Motoboy (PWA)
- `/docs` - Documentação da API

## ⚠️ Limitações do Plano Gratuito

- O app "dorme" após 15 minutos sem acesso
- Demora ~30 segundos para "acordar"
- Para uso em produção, considere o plano pago (~$7/mês)

## 🔧 Desenvolvimento Local

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Acesse: http://localhost:8000

## 🧪 Testes Automatizados

```bash
cd backend
pytest                    # Rodar todos os testes
pytest -v                 # Modo verbose
pytest tests/test_auth.py # Testar apenas autenticação
```

Ver documentação completa: [`docs/TESTES.md`](docs/TESTES.md)

## 📞 Suporte

Dúvidas? Entre em contato com o desenvolvedor.
