# Acceso a AWS — Renovación obligatoria de sesión SSO

Antes de ejecutar cualquier comando o herramienta que se conecte a una cuenta AWS, renovar la sesión del perfil objetivo mediante el skill `aws-sso-refresh`:

```bash
bash skills/devops/aws-sso-refresh/scripts/aws-refresh.sh <perfil-aws>
```

## Flujo obligatorio

1. Identificar el perfil AWS de la cuenta requerida.
2. Ejecutar `aws-sso-refresh` para renovar sus credenciales temporales, incluso si no se ha recibido todavía un error de expiración.
3. Verificar la cuenta autenticada sin exponer credenciales:

   ```bash
   aws sts get-caller-identity --profile <perfil-aws>
   ```

4. Confirmar que el `Account` resultante corresponde a la cuenta esperada antes de hacer consultas o cambios.
5. Solo después de esa verificación, ejecutar la operación AWS solicitada por el usuario.

## Reglas de seguridad

- Esta regla aplica a operaciones de lectura y escritura que hagan llamadas a AWS; listar perfiles locales no requiere renovación.
- Nunca mostrar, copiar, registrar ni versionar claves temporales, tokens de sesión o archivos de credenciales.
- No sustituir `aws-sso-refresh` por credenciales estáticas, `aws configure`, perfiles no confirmados ni mecanismos de autenticación alternos.
- Si la renovación, el navegador de autenticación o la validación de identidad falla, informar el bloqueo y no continuar con operaciones AWS contra una identidad incierta.
- La renovación de SSO autentica; no autoriza modificaciones productivas. Las operaciones de escritura continúan requiriendo la confirmación y los controles aplicables.
