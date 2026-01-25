# 🚂 Configuração no Railway - MotoFlash

Este guia explica como configurar as variáveis de ambiente necessárias para rodar o MotoFlash no Railway.

---

## 📋 Pré-requisitos

Antes de configurar o Railway, você precisa obter:

1. **Google Maps API Key** (obrigatório)
   - Acesse: https://console.cloud.google.com/apis/credentials
   - Crie um novo projeto ou use um existente
   - Ative as seguintes APIs:
     - Geocoding API
     - Directions API
   - Crie uma credencial (API Key)
   - Copie a chave (formato: `AIzaSy...`)

2. **Secret Key para JWT** (obrigatório)
   - Execute no terminal local:
     ```bash
     python -c "import secrets; print(secrets.token_urlsafe(32))"
     ```
   - Copie o resultado

---

## ⚙️ Configuração das Variáveis no Railway

### 1. Acesse o Painel do Railway

1. Acesse [railway.app](https://railway.app)
2. Selecione seu projeto MotoFlash
3. Clique na aba **"Variables"** ou **"Environment Variables"**

### 2. Adicione as Variáveis Obrigatórias

Adicione cada variável clicando em **"New Variable"**:

| Nome da Variável | Valor | Obrigatório? |
|------------------|-------|--------------|
| `GOOGLE_MAPS_API_KEY` | Sua chave do Google Maps (AIzaSy...) | ✅ SIM |
| `SECRET_KEY` | Chave gerada pelo comando acima | ✅ SIM |
| `DATA_DIR` | `/data` | ✅ SIM |
| `ALLOWED_ORIGINS` | URL do seu app (veja abaixo) | ⚠️ Recomendado |

### 3. Configurando ALLOWED_ORIGINS (Segurança CORS)

O `ALLOWED_ORIGINS` define quais domínios podem acessar sua API.

**Opção 1 - Desenvolvimento/Teste:**
```
Deixe vazio
```
Isso permite apenas localhost (menos seguro, mas funciona para testes)

**Opção 2 - Produção (Recomendado):**
```
https://seu-app.up.railway.app
```
Substitua `seu-app.up.railway.app` pela URL real do Railway.

**Opção 3 - Múltiplos domínios:**
```
https://seu-app.up.railway.app,https://motoflash.com,https://www.motoflash.com
```
Separe por vírgula se tiver domínio customizado.

---

## 🗂️ Volume Persistente (Importante!)

O MotoFlash usa SQLite e precisa de um volume persistente para não perder dados.

### Configure o Volume:

1. No Railway, vá em **"Settings"** do seu serviço
2. Procure por **"Volumes"** ou **"Persistent Storage"**
3. Adicione um volume:
   - **Mount Path:** `/data`
   - **Size:** 1GB (inicial)

Isso garante que o banco de dados (`/data/motoboy.db`) e os uploads (`/data/uploads/`) sejam preservados entre deploys.

---

## 🚀 Deploy

Após configurar as variáveis:

1. **Commit das alterações** (as correções de segurança)
2. **Push para o repositório**
3. Railway fará deploy automaticamente
4. Monitore os logs para verificar se tudo iniciou corretamente

### Verificando os Logs:

```bash
# No terminal do Railway ou localmente:
railway logs
```

Você deve ver:
- ✅ `🔒 CORS configurado para: ['https://seu-app.up.railway.app']`
- ✅ Sem avisos de `GOOGLE_MAPS_API_KEY não configurada`
- ✅ Sem avisos de `SECRET_KEY não configurada`

---

## 🧪 Testando Localmente Antes do Deploy

Antes de fazer deploy no Railway, teste localmente:

### 1. Crie arquivo `.env` (nunca commite esse arquivo!)

```bash
cd backend
cp .env.example .env
```

### 2. Edite o `.env` com suas chaves:

```bash
SECRET_KEY=sua-chave-gerada-aqui
GOOGLE_MAPS_API_KEY=AIzaSy...sua-chave-aqui
DATA_DIR=
ALLOWED_ORIGINS=http://localhost:8000
```

### 3. Instale a nova dependência:

```bash
pip install -r requirements.txt
```

### 4. Execute o servidor:

```bash
uvicorn main:app --reload
```

### 5. Verifique a saída:

- ✅ Não deve aparecer avisos de variáveis faltando
- ✅ Deve mostrar `🔒 CORS configurado para: ...`

---

## ❓ Problemas Comuns

### Erro: "GOOGLE_MAPS_API_KEY não configurada"
- **Solução:** Certifique-se de adicionar a variável no Railway exatamente como `GOOGLE_MAPS_API_KEY`
- **Caso especial:** Após adicionar, faça um novo deploy (Railway não reinicia automaticamente)

### Erro: "SECRET_KEY não configurada"
- **Solução:** Gere uma chave forte e adicione no Railway

### CORS bloqueando requisições
- **Solução:** Adicione a URL completa do Railway em `ALLOWED_ORIGINS`
- **Exemplo:** `https://motoflash-production.up.railway.app`

### Banco de dados resetando
- **Solução:** Verifique se o volume `/data` está configurado corretamente
- **Importante:** Volumes são vinculados ao projeto, não ao código

---

## 📝 Checklist Final

Antes de considerar o deploy em produção completo:

- [ ] `GOOGLE_MAPS_API_KEY` configurada no Railway
- [ ] `SECRET_KEY` forte configurada no Railway
- [ ] `DATA_DIR` = `/data` configurada
- [ ] `ALLOWED_ORIGINS` com URL do Railway configurada
- [ ] Volume persistente `/data` criado
- [ ] Deploy realizado com sucesso
- [ ] Logs verificados (sem avisos de segurança)
- [ ] Teste de login funcionando
- [ ] Teste de geocoding funcionando (criar pedido)

---

## 🔐 Segurança Adicional (Opcional)

Para aumentar ainda mais a segurança:

### Restrições da API do Google Maps:

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Clique na sua API Key
3. Em **"Restrições de aplicativo"**:
   - Selecione "Referenciadores HTTP (sites)"
   - Adicione: `seu-app.up.railway.app/*`
4. Em **"Restrições de API"**:
   - Selecione "Restringir chave"
   - Marque apenas: Geocoding API e Directions API

Isso impede que alguém use sua chave se ela vazar.

---

## 📞 Suporte

Se encontrar problemas, verifique:
1. Logs do Railway (`railway logs`)
2. Console do navegador (F12) para erros CORS
3. Documentação do Railway: https://docs.railway.app/

---

**Última atualização:** 2026-01-25
