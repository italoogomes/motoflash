

* **Caminho:** cd "C:\Users\italo.gomes\OneDrive - MMarra Distribuidora Automotiva\Documentos\motoflash"

* **Ativar: ambiente:** .\motoapp\Scripts\activate

* **Pasta Backend:** cd backend

* **Ligar o servidor:** uvicorn main:app --reload

* **Rodar Backend:** python -m uvicorn main:app --host 0.0.0.0 --port 8000

* **Autenticar Ngrok:** ngrok config add-authtoken 38IfmsZvfffa6SJEPZe5AMxHwOI_rZGwmVyp8Pef916KnNuW

* **Rodar Frontend no Ngrok:** ngrok http 8000

* **Abrir App Motoboy:** https://luxuriant-staci-uncheckmated.ngrok-free.dev/motoboy

* **Rodar Painel de Controle:** https://luxuriant-staci-uncheckmated.ngrok-free.dev/dashboard

* **Configure o endereço do restaurante:** http://localhost:8000/docs

   {
     "restaurant_name": "Nome do Restaurante",
     "address": "Rua Visconde de Inhauma, 2235 - Jardim Sumaré, Ribeirão Preto"
   } 