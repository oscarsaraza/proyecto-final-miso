# Web

This project was generated using [Angular CLI](https://github.com/angular/angular-cli) version 22.2.1.

## Development server

Para iniciar el servidor de desarrollo local con proxy inverso conectado al backend FastAPI en `localhost:8000`:

```bash
npm start
```

La aplicación estará disponible en `http://localhost:4200/`.

Para consultar las credenciales de prueba del asesor comercial (`HU-WEB-13`), política de bloqueo y generación de tokens 2FA (TOTP), consulte la [Sección 4.2 del README principal](../README.md#42-autenticación-y-acceso-del-asesor-comercial-hu-web-13).

## Code scaffolding

Angular CLI includes powerful code scaffolding tools. To generate a new component, run:

```bash
ng generate component component-name
```

For a complete list of available schematics (such as `components`, `directives`, or `pipes`), run:

```bash
ng generate --help
```

## Building

To build the project run:

```bash
ng build
```

This will compile your project and store the build artifacts in the `dist/` directory. By default, the production build optimizes your application for performance and speed.

## Running unit tests

To execute unit tests with the [Vitest](https://vitest.dev/) test runner, use the following command:

```bash
ng test
```

## Running end-to-end tests

For end-to-end (e2e) testing, run:

```bash
ng e2e
```

Angular CLI does not come with an end-to-end testing framework by default. You can choose one that suits your needs.

## Additional Resources

For more information on using the Angular CLI, including detailed command references, visit the [Angular CLI Overview and Command Reference](https://angular.dev/tools/cli) page.
