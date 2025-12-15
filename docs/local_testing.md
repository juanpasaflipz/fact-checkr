# Pruebas Locales para WhatsApp Bot

Este documento describe cómo probar el bot de WhatsApp en tu entorno local usando `localtunnel` y la API de WhatsApp Cloud (o herramientas de prueba como Postman).

## Prerrequisitos

1.  **Backend corriendo**: Asegúrate de que tu backend esté ejecutándose (`python -m app.main` o similar).
2.  **Worker de Celery corriendo**: `celery -A app.worker.celery_app worker --loglevel=info`.
3.  **Redis corriendo**: Necesario para Celery.
4.  **ngrok** (recomendado) o `localtunnel`: Para exponer tu puerto local (8000) a internet.

## Configuración del Túnel

Para recibir webhooks de Meta, tu servidor local debe ser accesible públicamente.

```bash
ngrok http 8000
```
Copia la URL HTTPS generada (ej. `https://tu-url-random.ngrok-free.app`).

## Configuración en Meta for Developers

1.  Ve a tu App en Meta for Developers > WhatsApp > Configuration.
2.  Edita la **Webhook URL**.
3.  Pega tu URL de ngrok + `/whatsapp/webhook` (ej. `https://tu-url-random.ngrok-free.app/whatsapp/webhook`).
4.  Asegúrate de que el **Verify Token** coincida con el que tienes configurado (aunque para desarrollo a veces se simplifica, nuestro código verifica la firma HMAC).

## Probando el Flujo Completo

### 1. Enviar un Mensaje (Simulación de Webhook)

Puedes simular un webhook entrante usando Postman o enviando un mensaje real a tu número de prueba si tienes el túnel configurado.

**Payload JSON para Postman (`POST https://tu-url-ngrok/whatsapp/webhook`):**

Asegúrate de calcular la firma `X-Hub-Signature-256` correcta si tienes validación activada, o desactivarla temporalmente para pruebas puramente locales.

```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "YOUR_WHATSAPP_BUSINESS_ACCOUNT_ID",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "1234567890",
              "phone_number_id": "YOUR_PHONE_NUMBER_ID"
            },
            "contacts": [
              {
                "profile": {
                  "name": "Juan Perez"
                },
                "wa_id": "5215512345678"
              }
            ],
            "messages": [
              {
                "from": "5215512345678",
                "id": "wamid.HBgL...",
                "timestamp": "1702654321",
                "text": {
                  "body": "Es verdad que el cielo es verde?"
                },
                "type": "text"
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

### 2. Verificar Logs del Backend

Deberías ver:
- Log de `Coming message...` en el router.
- Verificación de firma (exitosa).
- "Message processed and task enqueued".

### 3. Verificar Logs de Celery

Deberías ver:
- Task `app.tasks.whatsapp.process_message` received.
- "Processing message with ID...".
- Pasos de extracción de claims, búsqueda, verificación...
- "Task succeeded".

### 4. Verificar Recepción de Mensaje

Si usaste un número real y el túnel está bien configurado, deberías recibir:
1.  (Opcional) Mensaje de "Estamos verificando...".
2.  Mensaje final con el veredicto (Verdadero/Falso/Etc).

## Unit Tests

Para verificar la lógica de formateo de mensajes sin enviar nada real:

```bash
cd backend
pytest tests/test_whatsapp_utils.py
```
