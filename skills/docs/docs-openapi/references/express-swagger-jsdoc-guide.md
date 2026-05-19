# Express — swagger-jsdoc + swagger-ui-express: guía

## Instalación

```bash
npm install swagger-jsdoc swagger-ui-express
# TypeScript:
npm install --save-dev @types/swagger-jsdoc @types/swagger-ui-express
```

---

## Configuración mínima (src/swagger.js)

```javascript
const swaggerJsdoc = require('swagger-jsdoc');
const swaggerUi = require('swagger-ui-express');

const spec = swaggerJsdoc({
  definition: {
    openapi: '3.0.3',
    info: { title: 'Mi API', version: '1.0.0' },
  },
  apis: ['./src/routes/**/*.js'],  // archivos que contienen @swagger JSDoc
});

module.exports = (app) => {
  app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(spec));
  app.get('/api-docs.json', (_, res) => res.json(spec));
};
```

Registrar en `app.js`:
```javascript
require('./swagger')(app);
```

---

## Formato del JSDoc por tipo

### Definir un schema (solo una vez, normalmente al inicio del archivo de rutas)

```javascript
/**
 * @swagger
 * components:
 *   schemas:
 *     User:
 *       type: object
 *       required: [name, email]
 *       properties:
 *         id:
 *           type: integer
 *           example: 1
 *         name:
 *           type: string
 *           example: "Juan García"
 *         email:
 *           type: string
 *           format: email
 *           example: "juan@example.com"
 *         role:
 *           type: string
 *           enum: [ADMIN, USER, VIEWER]
 *           example: USER
 *         createdAt:
 *           type: string
 *           format: date-time
 */
```

### GET lista con paginación

```javascript
/**
 * @swagger
 * /api/v1/users:
 *   get:
 *     tags: [Users]
 *     summary: Lista usuarios paginados
 *     security:
 *       - BearerAuth: []
 *     parameters:
 *       - in: query
 *         name: page
 *         schema: { type: integer, default: 1 }
 *         description: Número de página
 *       - in: query
 *         name: limit
 *         schema: { type: integer, default: 20, maximum: 100 }
 *         description: Items por página
 *       - in: query
 *         name: status
 *         schema:
 *           type: string
 *           enum: [active, inactive]
 *         required: false
 *         description: Filtrar por estado
 *     responses:
 *       200:
 *         description: Lista obtenida
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 data:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/User'
 *                 total:
 *                   type: integer
 *                   example: 150
 *       401:
 *         $ref: '#/components/responses/Unauthorized'
 */
router.get('/', authenticate, async (req, res, next) => { ... });
```

### POST con body

```javascript
/**
 * @swagger
 * /api/v1/users:
 *   post:
 *     tags: [Users]
 *     summary: Crea un usuario
 *     security:
 *       - BearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [name, email]
 *             properties:
 *               name:
 *                 type: string
 *                 example: "Juan García"
 *               email:
 *                 type: string
 *                 format: email
 *                 example: "juan@example.com"
 *     responses:
 *       201:
 *         description: Creado exitosamente
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/User'
 *       400:
 *         $ref: '#/components/responses/BadRequest'
 */
router.post('/', authenticate, async (req, res, next) => { ... });
```

### GET por ID con path param

```javascript
/**
 * @swagger
 * /api/v1/users/{id}:
 *   get:
 *     tags: [Users]
 *     summary: Obtiene un usuario por ID
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: integer
 *         example: 1
 *     responses:
 *       200:
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/User'
 *       404:
 *         $ref: '#/components/responses/NotFound'
 */
router.get('/:id', async (req, res, next) => { ... });
```

---

## Responses y schemas reutilizables (definir en swagger config)

```javascript
const spec = swaggerJsdoc({
  definition: {
    openapi: '3.0.3',
    info: { ... },
    components: {
      responses: {
        BadRequest: {
          description: 'Solicitud inválida',
          content: { 'application/json': { schema: { $ref: '#/components/schemas/ErrorResponse' } } },
        },
        Unauthorized: { description: 'No autenticado' },
        NotFound: { description: 'Recurso no encontrado' },
      },
      schemas: {
        ErrorResponse: {
          type: 'object',
          required: ['code', 'message'],
          properties: {
            code: { type: 'string', example: 'NOT_FOUND' },
            message: { type: 'string', example: 'El recurso no existe' },
          },
        },
      },
      securitySchemes: {
        BearerAuth: { type: 'http', scheme: 'bearer', bearerFormat: 'JWT' },
      },
    },
    security: [{ BearerAuth: [] }],
  },
  apis: ['./src/routes/**/*.js'],
});
```

---

## Alternativa: openapi-jsdoc (TypeScript con decoradores)

Si el proyecto usa TypeScript y clases de servicio, considerar `tsoa` que genera el spec desde tipos TypeScript automáticamente, sin JSDoc manual.

```bash
npm install tsoa
npx tsoa spec-and-routes
```
