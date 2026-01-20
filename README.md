# 🏍️ MotoFlash - Deploy no Render

Sistema de despacho inteligente para restaurantes com entregadores próprios.

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
│   └── uploads/          # Imagens (não commitado)
├── frontend/
│   ├── index.html        # Dashboard
│   ├── motoboy.html      # App do Motoboy (PWA)
│   └── icons/            # Ícones do PWA
├── render.yaml           # Configuração do Render
└── .gitignore
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

## 📞 Suporte

Dúvidas? Entre em contato com o desenvolvedor.
